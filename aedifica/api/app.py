"""FastAPI product API over the engine + SQL store (multi-tenant).

Auth: bootstrap an org+owner (`POST /api/orgs`, with an optional password) to get
a bearer token; returning users exchange email + password for that token at
`POST /api/auth/login`. Send `Authorization: Bearer <token>` on every other call.
Projects are scoped to the caller's org; mutations require a capability (see
api.auth). Errors are structured: HTTP status + {"detail": {"code", "message"}}.
"""
from __future__ import annotations

import datetime as _dt
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import Base, make_engine, make_session_factory, models as m, repository
from ..ingestion import service as ingestion
from . import actions, auth, orchestration
from .config import get_settings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO_DIR = os.path.join(ROOT, "pilot", "projects", "demo_lausanne_palud")


class OrgIn(BaseModel):
    org_name: str
    user_email: str
    user_name: str = "Owner"
    password: str = ""  # when set, the owner can sign in with email + password


class LoginIn(BaseModel):
    email: str
    password: str


class UserIn(BaseModel):
    email: str
    name: str = "Membre"
    role: str = "member"
    password: str = ""  # when set, the member can sign in with email + password


class RoleIn(BaseModel):
    role: str


class SubmitPieceIn(BaseModel):
    item_id: str
    present: bool = True


class ProjectIn(BaseModel):
    project_id: str
    name: str
    commune: str = "Lausanne"
    country: str = "CH"
    canton: str = "VD"
    phase_code: str = "0"
    seed_reports: bool = False


class IntakeIn(BaseModel):
    query: str
    live: bool = True


class DryRunIn(BaseModel):
    adapter_id: str = "archicad_json"
    operations: list = []
    adapter_endpoint: str | None = None  # live Archicad JSON bridge (read-only inspection)


class ApprovalIn(BaseModel):
    scope: str
    basis: str = "architect approval"


class ExecuteIn(BaseModel):
    transaction: dict


class CommuneIn(BaseModel):
    commune: str
    canton: str = "VD"
    source_authority: str | None = None


class CommuneIngestIn(BaseModel):
    version: str
    zones: dict
    source_authority: str
    valid_as_of: str
    review_due: str
    sources: list | None = None


# ---- W9 operating layer ---------------------------------------------------- #
class GroupIn(BaseModel):
    name: str
    kind: str = "group"
    parent_id: int | None = None


class IntervenantIn(BaseModel):
    name: str
    role: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    is_responsible: bool = False
    group_id: int | None = None


class IntervenantPatch(BaseModel):
    name: str | None = None
    role: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    is_responsible: bool | None = None
    group_id: int | None = None


class DocumentIn(BaseModel):
    official_name: str
    category: str = "general"
    confidential: bool = False
    note: str | None = None
    version_label: str = "v1"
    file_ref: str | None = None
    source: str = "manual"


class DocumentPatch(BaseModel):
    confidential: bool | None = None
    note: str | None = None
    category: str | None = None


class ValidateIn(BaseModel):
    level: str  # canonical | indicative | refused | pending


class BrsIn(BaseModel):
    content: str
    kind: str = "requirement"  # requirement | change | decision
    channel: str = "other"  # phone | email | pv | meeting | other
    emitter_intervenant_id: int | None = None
    emitter_label: str | None = None
    source_ref: str | None = None
    supersedes_id: int | None = None


class BrsPatch(BaseModel):
    status: str | None = None  # active | superseded | locked
    content: str | None = None


class ChecklistSeedIn(BaseModel):
    entry_phase: str = "11"


class ChecklistItemIn(BaseModel):
    phase_code: str
    title: str
    description: str | None = None
    actor: str = "architecte"  # mo | architecte | mandataire | entreprise
    responsible_intervenant_id: int | None = None


class ChecklistPatch(BaseModel):
    status: str | None = None  # todo | done | deferred | skipped
    actor: str | None = None  # mo | architecte | mandataire | entreprise
    responsible_intervenant_id: int | None = None


class TaskIn(BaseModel):
    title: str
    priority: str = "p2"  # p0 | p1 | p2
    status: str = "todo"  # todo | doing | done | blocked
    assignee_user_id: int | None = None
    estimate_hours: float | None = None
    due_date: str | None = None
    is_quick_win: bool = False
    phase_code: str | None = None
    checklist_item_id: int | None = None


class TaskPatch(BaseModel):
    title: str | None = None
    priority: str | None = None
    status: str | None = None
    assignee_user_id: int | None = None
    estimate_hours: float | None = None
    actual_hours: float | None = None
    due_date: str | None = None
    is_quick_win: bool | None = None


class DepIn(BaseModel):
    blocked_by_id: int


class FeeIn(BaseModel):
    cfc2: float = 0
    project_type: str = "autre"
    hourly_rate: float | None = None
    hours: float | None = None


class CaptureIn(BaseModel):
    kind: str = "observation"  # friction|observation|photo|decision|regulation
    content: str
    source_ref: str | None = None


# ---- W10 multi-actor invite / accept ---------------------------------- #
class InviteIn(BaseModel):
    email: str
    name: str | None = None


class AcceptInviteIn(BaseModel):
    token: str
    password: str
    name: str | None = None


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def create_app(engine=None, create_all: bool = False, settings=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Aedifica API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    engine = engine or make_engine(settings.database_url)
    if create_all:
        Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)

    def get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def current_user(session: Session = Depends(get_session), authorization: str | None = Header(default=None)) -> m.User:
        token = (authorization or "").removeprefix("Bearer ").strip()
        if not token:
            raise _err(401, "NO_TOKEN", "Authorization: Bearer <token> is required")
        user = session.query(m.User).filter_by(api_token=token).first()
        if user is None:
            raise _err(401, "INVALID_TOKEN", "unknown token")
        return user

    def require(user: m.User, capability: str) -> None:
        if not auth.has_capability(user.role, capability):
            raise _err(403, "FORBIDDEN", f"role {user.role!r} lacks capability {capability!r}")

    def _project(session: Session, user: m.User, project_id: str) -> m.Project:
        project = session.query(m.Project).filter_by(org_id=user.org_id, project_id=project_id).first()
        if project is None:
            raise _err(404, "PROJECT_NOT_FOUND", project_id)
        return project

    # ---- public ---------------------------------------------------------- #
    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0", "env": settings.env}

    @app.get("/api/ready")
    def ready(session: Session = Depends(get_session)):
        try:
            session.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - DB down path
            raise _err(503, "DB_UNAVAILABLE", str(exc))
        return {"status": "ready"}

    @app.post("/api/orgs", status_code=201)
    def bootstrap_org(body: OrgIn, session: Session = Depends(get_session)):
        org = m.Org(name=body.org_name)
        session.add(org)
        session.flush()
        token = auth.new_token()
        pw_hash = auth.hash_password(body.password) if body.password else None
        session.add(m.User(org_id=org.id, email=body.user_email, name=body.user_name, role="owner", api_token=token, password_hash=pw_hash))
        session.commit()
        return {"org_id": org.id, "user_email": body.user_email, "role": "owner", "token": token}

    @app.post("/api/auth/login")
    def login(body: LoginIn, session: Session = Depends(get_session)):
        # Email is unique per org, not globally: match the user whose password verifies.
        for u in session.query(m.User).filter_by(email=body.email).all():
            if auth.verify_password(body.password, u.password_hash):
                if not u.api_token:
                    u.api_token = auth.new_token()
                    session.commit()
                return {"token": u.api_token, "user_email": u.email, "role": u.role, "org_id": u.org_id,
                        "linked_intervenant_id": u.linked_intervenant_id}
        raise _err(401, "BAD_CREDENTIALS", "e-mail ou mot de passe incorrect")

    @app.post("/api/auth/accept-invite")
    def accept_invite(body: AcceptInviteIn, session: Session = Depends(get_session)):
        """An external (client / mandataire / entreprise) redeems their invite token to set
        their password. The User row was created by the architect (POST .../invite); this
        endpoint just primes the password + name and returns the API token."""
        u = session.query(m.User).filter_by(invite_token=body.token).first()
        if not u:
            raise _err(404, "INVITE_INVALID", "invite token is invalid or already redeemed")
        u.password_hash = auth.hash_password(body.password)
        if body.name:
            u.name = body.name
        if not u.api_token:
            u.api_token = auth.new_token()
        u.invite_token = None  # one-shot
        session.commit()
        iv = session.query(m.Intervenant).filter_by(id=u.linked_intervenant_id).first() if u.linked_intervenant_id else None
        return {"token": u.api_token, "user_email": u.email, "role": u.role,
                "linked_intervenant": {"id": iv.id, "name": iv.name, "role": iv.role} if iv else None}

    # ---- org & team management (owner only) ------------------------------ #
    @app.get("/api/orgs/users")
    def list_users(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "org.manage")
        rows = session.query(m.User).filter_by(org_id=user.org_id).order_by(m.User.id).all()
        return {"users": [{"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_you": u.id == user.id} for u in rows]}

    @app.post("/api/orgs/users", status_code=201)
    def add_user(body: UserIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "org.manage")
        if body.role not in auth.ROLES:
            raise _err(400, "BAD_ROLE", f"role must be one of {auth.ROLES}")
        if session.query(m.User).filter_by(org_id=user.org_id, email=body.email).first():
            raise _err(409, "USER_EXISTS", body.email)
        token = auth.new_token()
        pw_hash = auth.hash_password(body.password) if body.password else None
        u = m.User(org_id=user.org_id, email=body.email, name=body.name, role=body.role, api_token=token, password_hash=pw_hash)
        session.add(u)
        session.commit()
        return {"user": {"id": u.id, "email": u.email, "name": u.name, "role": u.role}, "token": token}

    @app.patch("/api/orgs/users/{user_id}")
    def set_role(user_id: int, body: RoleIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "org.manage")
        if body.role not in auth.ROLES:
            raise _err(400, "BAD_ROLE", f"role must be one of {auth.ROLES}")
        target = session.query(m.User).filter_by(org_id=user.org_id, id=user_id).first()
        if target is None:
            raise _err(404, "USER_NOT_FOUND", str(user_id))
        if target.role == "owner" and body.role != "owner":
            owners = session.query(m.User).filter_by(org_id=user.org_id, role="owner").count()
            if owners <= 1:
                raise _err(400, "LAST_OWNER", "cannot demote the last owner of the organisation")
        target.role = body.role
        session.commit()
        return {"user": {"id": target.id, "email": target.email, "role": target.role}}

    # ---- projects (org-scoped) ------------------------------------------- #
    @app.get("/api/projects")
    def list_projects(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        rows = session.query(m.Project).filter_by(org_id=user.org_id).order_by(m.Project.id).all()
        return {"projects": [p.project_id for p in rows]}

    @app.post("/api/projects", status_code=201)
    def create_project(body: ProjectIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if session.query(m.Project).filter_by(org_id=user.org_id, project_id=body.project_id).first():
            raise _err(409, "PROJECT_EXISTS", f"{body.project_id} already exists")
        project = repository.create_project(
            session, user.org_id, body.project_id, body.name,
            commune=body.commune, country=body.country, canton=body.canton, phase_code=body.phase_code,
        )
        if body.seed_reports:
            from . import reports

            reports.seed_reference_reports(project)
        session.commit()
        return {"created": repository.project_summary(session, project)}

    @app.get("/api/projects/{project_id}")
    def open_project(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"project": repository.project_summary(session, _project(session, user, project_id))}

    # ---- W9 operating layer: intervenants, documents, access ---------------- #
    def _interv_dict(i: m.Intervenant) -> dict:
        return {"id": i.id, "name": i.name, "role": i.role, "organization": i.organization, "email": i.email,
                "phone": i.phone, "is_responsible": i.is_responsible, "group_id": i.group_id}

    def _group_dict(g: m.IntervenantGroup) -> dict:
        return {"id": g.id, "name": g.name, "kind": g.kind, "parent_id": g.parent_id}

    def _doc_dict(d: m.Document) -> dict:
        return {"id": d.id, "official_name": d.official_name, "category": d.category,
                "validation_level": d.validation_level, "confidential": d.confidential, "note": d.note,
                "validated_by": d.validated_by, "validated_at": d.validated_at,
                "versions": [{"label": v.label, "source": v.source, "file_ref": v.file_ref} for v in d.versions],
                "latest": (d.versions[-1].label if d.versions else None),
                "grants": [{"id": gr.id, "group_id": gr.group_id, "intervenant_id": gr.intervenant_id, "level": gr.level} for gr in d.grants]}

    @app.get("/api/projects/{project_id}/intervenants")
    def list_intervenants(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        groups = session.query(m.IntervenantGroup).filter_by(project_id=p.id).order_by(m.IntervenantGroup.id).all()
        people = session.query(m.Intervenant).filter_by(project_id=p.id).order_by(m.Intervenant.id).all()
        return {"groups": [_group_dict(g) for g in groups], "people": [_interv_dict(i) for i in people]}

    @app.post("/api/projects/{project_id}/intervenant-groups", status_code=201)
    def create_group(project_id: str, body: GroupIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        g = m.IntervenantGroup(project_id=p.id, name=body.name, kind=body.kind, parent_id=body.parent_id)
        session.add(g); session.commit()
        return {"group": _group_dict(g)}

    @app.delete("/api/projects/{project_id}/intervenant-groups/{group_id}")
    def delete_group(project_id: str, group_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        g = session.query(m.IntervenantGroup).filter_by(project_id=p.id, id=group_id).first()
        if not g:
            raise _err(404, "GROUP_NOT_FOUND", str(group_id))
        session.query(m.Intervenant).filter_by(group_id=group_id).update({"group_id": None})
        session.query(m.IntervenantGroup).filter_by(parent_id=group_id).update({"parent_id": None})
        session.query(m.AccessGrant).filter_by(group_id=group_id).delete()
        session.delete(g); session.commit()
        return {"deleted": group_id}

    @app.post("/api/projects/{project_id}/intervenants", status_code=201)
    def create_intervenant(project_id: str, body: IntervenantIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        i = m.Intervenant(project_id=p.id, name=body.name, role=body.role, organization=body.organization,
                          email=body.email, phone=body.phone, is_responsible=body.is_responsible, group_id=body.group_id)
        session.add(i); session.commit()
        return {"intervenant": _interv_dict(i)}

    @app.patch("/api/projects/{project_id}/intervenants/{intervenant_id}")
    def patch_intervenant(project_id: str, intervenant_id: int, body: IntervenantPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        i = session.query(m.Intervenant).filter_by(project_id=p.id, id=intervenant_id).first()
        if not i:
            raise _err(404, "INTERVENANT_NOT_FOUND", str(intervenant_id))
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(i, k, v)
        session.commit()
        return {"intervenant": _interv_dict(i)}

    @app.delete("/api/projects/{project_id}/intervenants/{intervenant_id}")
    def delete_intervenant(project_id: str, intervenant_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        i = session.query(m.Intervenant).filter_by(project_id=p.id, id=intervenant_id).first()
        if not i:
            raise _err(404, "INTERVENANT_NOT_FOUND", str(intervenant_id))
        session.query(m.AccessGrant).filter_by(intervenant_id=intervenant_id).delete()
        # Detach any external user linked to this intervenant — they lose their scope.
        session.query(m.User).filter_by(linked_intervenant_id=intervenant_id).update(
            {"linked_intervenant_id": None})
        session.delete(i); session.commit()
        return {"deleted": intervenant_id}

    # ---- W10: invite an intervenant as a scoped external user --------------- #
    @app.post("/api/projects/{project_id}/intervenants/{intervenant_id}/invite", status_code=201)
    def invite_intervenant(project_id: str, intervenant_id: int, body: InviteIn,
                           user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """The architect provisions a scoped User row for an intervenant. The intervenant
        redeems the returned ``invite_token`` via /api/auth/accept-invite to set a password.
        The new user has role ``external`` and only sees data linked to their intervenant."""
        require(user, "project.write")
        p = _project(session, user, project_id)
        iv = session.query(m.Intervenant).filter_by(project_id=p.id, id=intervenant_id).first()
        if not iv:
            raise _err(404, "INTERVENANT_NOT_FOUND", str(intervenant_id))
        # Disallow duplicate emails within the same org (matches existing user constraint).
        if session.query(m.User).filter_by(org_id=user.org_id, email=body.email).first():
            raise _err(409, "USER_EXISTS", body.email)
        invite = auth.new_token()
        u = m.User(org_id=user.org_id, email=body.email, name=body.name or iv.name,
                   role="external", linked_intervenant_id=iv.id, invite_token=invite,
                   api_token=None, password_hash=None)
        session.add(u); session.commit()
        # Also mirror the email back to the intervenant if blank (no-op otherwise).
        if not iv.email:
            iv.email = body.email
            session.commit()
        return {"user": {"id": u.id, "email": u.email, "name": u.name, "role": u.role,
                          "linked_intervenant_id": iv.id},
                "invite_token": invite}

    @app.get("/api/projects/{project_id}/documents")
    def list_documents(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        docs = session.query(m.Document).filter_by(project_id=p.id).order_by(m.Document.id).all()
        counts: dict = {lvl: 0 for lvl in m.VALIDATION_LEVELS}
        for d in docs:
            counts[d.validation_level] = counts.get(d.validation_level, 0) + 1
        return {"documents": [_doc_dict(d) for d in docs],
                "summary": {"total": len(docs), "by_level": counts, "pending": counts.get("pending", 0)}}

    @app.post("/api/projects/{project_id}/documents", status_code=201)
    def create_document(project_id: str, body: DocumentIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        d = m.Document(project_id=p.id, official_name=body.official_name, category=body.category,
                       confidential=body.confidential, note=body.note)
        d.versions.append(m.DocumentVersion(label=body.version_label, file_ref=body.file_ref, source=body.source))
        session.add(d); session.commit()
        return {"document": _doc_dict(d)}

    @app.post("/api/projects/{project_id}/documents/{document_id}/validate")
    def validate_document(project_id: str, document_id: int, body: ValidateIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.level not in m.VALIDATION_LEVELS:
            raise _err(400, "BAD_LEVEL", f"level must be one of {m.VALIDATION_LEVELS}")
        p = _project(session, user, project_id)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        d.validation_level = body.level
        d.validated_by = user.name if body.level != "pending" else None
        session.commit()
        return {"document": _doc_dict(d)}

    @app.patch("/api/projects/{project_id}/documents/{document_id}")
    def patch_document(project_id: str, document_id: int, body: DocumentPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(d, k, v)
        session.commit()
        return {"document": _doc_dict(d)}

    @app.delete("/api/projects/{project_id}/documents/{document_id}")
    def delete_document(project_id: str, document_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        session.delete(d); session.commit()
        return {"deleted": document_id}

    @app.post("/api/projects/{project_id}/documents/{document_id}/grants", status_code=201)
    def grant_access(project_id: str, document_id: int, body: dict, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        session.add(m.AccessGrant(document_id=d.id, group_id=body.get("group_id"),
                                  intervenant_id=body.get("intervenant_id"), level=body.get("level", "read")))
        session.commit()
        return {"document": _doc_dict(d)}

    @app.delete("/api/projects/{project_id}/documents/{document_id}/grants/{grant_id}")
    def revoke_access(project_id: str, document_id: int, grant_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        gr = session.query(m.AccessGrant).filter_by(id=grant_id, document_id=document_id).first()
        if gr:
            session.delete(gr); session.commit()
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        return {"document": _doc_dict(d) if d else None}

    # ---- BRS — business requirements register (#223) ------------------------ #
    def _brs_dict(b: m.BrsEntry, names: dict) -> dict:
        return {"id": b.id, "content": b.content, "kind": b.kind, "channel": b.channel,
                "emitter_intervenant_id": b.emitter_intervenant_id,
                "emitter": names.get(b.emitter_intervenant_id) or b.emitter_label,
                "source_ref": b.source_ref, "supersedes_id": b.supersedes_id, "status": b.status,
                "created_at": str(b.created_at) if b.created_at else None}

    @app.get("/api/projects/{project_id}/brs")
    def list_brs(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        rows = session.query(m.BrsEntry).filter_by(project_id=p.id).order_by(m.BrsEntry.id.desc()).all()
        names = {i.id: i.name for i in session.query(m.Intervenant).filter_by(project_id=p.id).all()}
        chans: dict = {}
        for b in rows:
            chans[b.channel] = chans.get(b.channel, 0) + 1
        return {"entries": [_brs_dict(b, names) for b in rows],
                "summary": {"total": len(rows), "active": sum(1 for b in rows if b.status == "active"), "by_channel": chans}}

    @app.post("/api/projects/{project_id}/brs", status_code=201)
    def add_brs(project_id: str, body: BrsIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.channel not in m.BRS_CHANNELS:
            raise _err(400, "BAD_CHANNEL", f"channel must be one of {m.BRS_CHANNELS}")
        p = _project(session, user, project_id)
        e = m.BrsEntry(project_id=p.id, content=body.content, kind=body.kind, channel=body.channel,
                       emitter_intervenant_id=body.emitter_intervenant_id, emitter_label=body.emitter_label,
                       source_ref=body.source_ref, supersedes_id=body.supersedes_id)
        session.add(e)
        if body.supersedes_id:
            prev = session.query(m.BrsEntry).filter_by(project_id=p.id, id=body.supersedes_id).first()
            if prev:
                prev.status = "superseded"
        session.commit()
        names = {i.id: i.name for i in session.query(m.Intervenant).filter_by(project_id=p.id).all()}
        return {"entry": _brs_dict(e, names)}

    @app.patch("/api/projects/{project_id}/brs/{entry_id}")
    def patch_brs(project_id: str, entry_id: int, body: BrsPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        e = session.query(m.BrsEntry).filter_by(project_id=p.id, id=entry_id).first()
        if not e:
            raise _err(404, "BRS_NOT_FOUND", str(entry_id))
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(e, k, v)
        session.commit()
        names = {i.id: i.name for i in session.query(m.Intervenant).filter_by(project_id=p.id).all()}
        return {"entry": _brs_dict(e, names)}

    @app.delete("/api/projects/{project_id}/brs/{entry_id}")
    def del_brs(project_id: str, entry_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        e = session.query(m.BrsEntry).filter_by(project_id=p.id, id=entry_id).first()
        if not e:
            raise _err(404, "BRS_NOT_FOUND", str(entry_id))
        session.delete(e); session.commit()
        return {"deleted": entry_id}

    # ---- parametric, per-actor SIA checklist (#221, W10 multi-actor) --------- #
    from . import sia_checklist as _siacl

    def _ci_dict(c: m.ChecklistItem, names: dict | None = None) -> dict:
        names = names or {}
        return {"id": c.id, "phase_code": c.phase_code, "title": c.title, "description": c.description,
                "status": c.status, "order_index": c.order_index, "is_retroactive": c.is_retroactive,
                "actor": c.actor, "actor_label": _siacl.ACTOR_LABEL.get(c.actor, c.actor),
                "is_external": c.actor in _siacl.EXTERNAL_ACTORS,
                "responsible_intervenant_id": c.responsible_intervenant_id,
                "responsible_name": names.get(c.responsible_intervenant_id)}

    def _ci_names(session: Session, project_pk: int) -> dict:
        return {i.id: i.name for i in session.query(m.Intervenant).filter_by(project_id=project_pk).all()}

    def _phase_rank(code: str) -> int:
        return _siacl.PHASE_ORDER.index(code) if code in _siacl.PHASE_ORDER else -1

    def _external_blockers(items: list[m.ChecklistItem], project_phase: str) -> list[m.ChecklistItem]:
        """External-actor (client/mandataire/entreprise) steps still ``todo`` that are due:
        either back-filled (retroactive) or in a phase already reached by the project."""
        proj_rank = _phase_rank(project_phase)
        out = []
        for c in items:
            if c.actor not in _siacl.EXTERNAL_ACTORS or c.status != "todo":
                continue
            if c.is_retroactive or (proj_rank >= 0 and _phase_rank(c.phase_code) <= proj_rank):
                out.append(c)
        return out

    @app.get("/api/projects/{project_id}/checklist")
    def list_checklist(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        items = session.query(m.ChecklistItem).filter_by(project_id=p.id).order_by(m.ChecklistItem.order_index).all()
        names = _ci_names(session, p.id)
        by_status: dict = {s: 0 for s in ("todo", "done", "deferred", "skipped")}
        by_actor: dict = {a: {"total": 0, "done": 0, "todo": 0} for a in _siacl.ACTORS}
        for c in items:
            by_status[c.status] = by_status.get(c.status, 0) + 1
            slot = by_actor.setdefault(c.actor, {"total": 0, "done": 0, "todo": 0})
            slot["total"] += 1
            if c.status == "done":
                slot["done"] += 1
            elif c.status == "todo":
                slot["todo"] += 1
        external_todo = sum(1 for c in items if c.actor in _siacl.EXTERNAL_ACTORS and c.status == "todo")
        return {"items": [_ci_dict(c, names) for c in items],
                "actors": _siacl.ACTOR_LABEL,
                "summary": {"total": len(items), "seeded": len(items) > 0,
                            "retroactive": sum(1 for c in items if c.is_retroactive),
                            "by_status": by_status, "by_actor": by_actor,
                            "external_todo": external_todo,
                            "external_blockers": len(_external_blockers(items, p.phase_code))}}

    @app.post("/api/projects/{project_id}/checklist/seed", status_code=201)
    def seed_checklist(project_id: str, body: ChecklistSeedIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        if session.query(m.ChecklistItem).filter_by(project_id=p.id).count():
            raise _err(409, "ALREADY_SEEDED", "checklist already seeded for this project")
        for r in _siacl.seed_rows(body.entry_phase):
            session.add(m.ChecklistItem(project_id=p.id, **r))
        session.commit()
        items = session.query(m.ChecklistItem).filter_by(project_id=p.id).order_by(m.ChecklistItem.order_index).all()
        names = _ci_names(session, p.id)
        return {"items": [_ci_dict(c, names) for c in items], "seeded": len(items)}

    @app.post("/api/projects/{project_id}/checklist", status_code=201)
    def add_checklist_item(project_id: str, body: ChecklistItemIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.actor not in _siacl.ACTORS:
            raise _err(400, "BAD_ACTOR", f"actor must be one of {sorted(_siacl.ACTORS)}")
        p = _project(session, user, project_id)
        if body.responsible_intervenant_id is not None:
            iv = session.query(m.Intervenant).filter_by(project_id=p.id, id=body.responsible_intervenant_id).first()
            if not iv:
                raise _err(404, "INTERVENANT_NOT_FOUND", str(body.responsible_intervenant_id))
        nxt = (session.query(m.ChecklistItem).filter_by(project_id=p.id).count()) + 100
        c = m.ChecklistItem(project_id=p.id, phase_code=body.phase_code, title=body.title,
                            description=body.description, actor=body.actor,
                            responsible_intervenant_id=body.responsible_intervenant_id, order_index=nxt)
        session.add(c); session.commit()
        return {"item": _ci_dict(c, _ci_names(session, p.id))}

    @app.patch("/api/projects/{project_id}/checklist/{item_id}")
    def patch_checklist_item(project_id: str, item_id: int, body: ChecklistPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.status is not None and body.status not in ("todo", "done", "deferred", "skipped"):
            raise _err(400, "BAD_STATUS", "status must be todo|done|deferred|skipped")
        if body.actor is not None and body.actor not in _siacl.ACTORS:
            raise _err(400, "BAD_ACTOR", f"actor must be one of {sorted(_siacl.ACTORS)}")
        p = _project(session, user, project_id)
        c = session.query(m.ChecklistItem).filter_by(project_id=p.id, id=item_id).first()
        if not c:
            raise _err(404, "ITEM_NOT_FOUND", str(item_id))
        if body.responsible_intervenant_id is not None:
            iv = session.query(m.Intervenant).filter_by(project_id=p.id, id=body.responsible_intervenant_id).first()
            if not iv:
                raise _err(404, "INTERVENANT_NOT_FOUND", str(body.responsible_intervenant_id))
            c.responsible_intervenant_id = body.responsible_intervenant_id
        if body.status is not None:
            c.status = body.status
        if body.actor is not None:
            c.actor = body.actor
        session.commit()
        return {"item": _ci_dict(c, _ci_names(session, p.id))}

    @app.delete("/api/projects/{project_id}/checklist/{item_id}")
    def del_checklist_item(project_id: str, item_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        c = session.query(m.ChecklistItem).filter_by(project_id=p.id, id=item_id).first()
        if not c:
            raise _err(404, "ITEM_NOT_FOUND", str(item_id))
        session.delete(c); session.commit()
        return {"deleted": item_id}

    # ---- validation queue / "à valider" (#222 + W10 external blockers) ------ #
    @app.get("/api/projects/{project_id}/to-validate")
    def to_validate(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        pending_docs = session.query(m.Document).filter_by(project_id=p.id, validation_level="pending").all()
        items = session.query(m.ChecklistItem).filter_by(project_id=p.id).all()
        todo = sum(1 for c in items if c.status == "todo")
        retro_todo = sum(1 for c in items if c.status == "todo" and c.is_retroactive)
        names = _ci_names(session, p.id)
        ext = _external_blockers(items, p.phase_code)
        return {"pending_documents": [{"id": d.id, "official_name": d.official_name} for d in pending_docs],
                "external_blockers": [_ci_dict(c, names) for c in ext],
                "counts": {"documents": len(pending_docs), "checklist_todo": todo,
                           "checklist_retroactive_todo": retro_todo,
                           "external_blockers": len(ext)}}

    # ---- W10 single point of truth: Coordination ---------------------------- #
    # Four panes: (1) who-owes-what (by actor) · (2) blockers (external + atelier) ·
    # (3) documents (latest, pending first) · (4) validation queue (architect).
    @app.get("/api/projects/{project_id}/coordination")
    def coordination(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        items = session.query(m.ChecklistItem).filter_by(project_id=p.id).order_by(m.ChecklistItem.order_index).all()
        names = _ci_names(session, p.id)
        # (1) who-owes-what: bucket every todo step by actor (and by responsible person if set)
        owes: dict = {a: [] for a in _siacl.ACTORS}
        for c in items:
            if c.status == "todo":
                owes.setdefault(c.actor, []).append(_ci_dict(c, names))
        # (2) blockers
        external = [_ci_dict(c, names) for c in _external_blockers(items, p.phase_code)]
        # atelier blockers = blocked tasks owned by this project
        tasks = session.query(m.Task).filter_by(project_id=p.id).all()
        task_ids = [t.id for t in tasks]
        blocked_by = _deps_for(session, task_ids)
        done_ids = {t.id for t in tasks if t.status == "done"}
        u_names = {u.id: (u.name or u.email) for u in session.query(m.User).all()}
        atelier = [_task_dict(t, u_names, blocked_by, done_ids)
                   for t in tasks
                   if t.status != "done" and (t.status == "blocked"
                                              or any(b not in done_ids for b in blocked_by.get(t.id, [])))]
        # (3) documents — latest first, pending first
        docs = session.query(m.Document).filter_by(project_id=p.id).order_by(m.Document.id.desc()).all()
        def _doc_dict(d: m.Document) -> dict:
            return {"id": d.id, "official_name": d.official_name, "category": d.category,
                    "validation_level": d.validation_level, "confidential": d.confidential}
        docs_payload = sorted([_doc_dict(d) for d in docs], key=lambda x: 0 if x["validation_level"] == "pending" else 1)
        # (4) architect queue
        pending_docs = [d for d in docs if d.validation_level == "pending"]
        return {
            "project": {"project_id": p.project_id, "phase_code": p.phase_code},
            "actors": _siacl.ACTOR_LABEL,
            "who_owes_what": owes,
            "blockers": {"external": external, "atelier": atelier,
                         "counts": {"external": len(external), "atelier": len(atelier)}},
            "documents": {"items": docs_payload, "pending_count": len(pending_docs)},
            "to_validate": {"documents": [_doc_dict(d) for d in pending_docs],
                            "checklist_todo": sum(1 for c in items if c.status == "todo")},
        }

    # ---- tasks & pilotage (#225-#229) --------------------------------------- #
    def _task_dict(t: m.Task, names: dict, blocked_by: dict, done_ids: set) -> dict:
        deps = blocked_by.get(t.id, [])
        return {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status,
                "assignee_user_id": t.assignee_user_id, "assignee": names.get(t.assignee_user_id),
                "estimate_hours": t.estimate_hours, "actual_hours": t.actual_hours, "due_date": t.due_date,
                "is_quick_win": t.is_quick_win, "phase_code": t.phase_code, "checklist_item_id": t.checklist_item_id,
                "blocked_by": deps, "is_blocked": any(b not in done_ids for b in deps)}

    def _deps_for(session, task_ids: list) -> dict:
        bb: dict = {}
        if task_ids:
            for d in session.query(m.TaskDependency).filter(m.TaskDependency.task_id.in_(task_ids)).all():
                bb.setdefault(d.task_id, []).append(d.blocked_by_id)
        return bb

    @app.get("/api/projects/{project_id}/tasks")
    def list_tasks(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        tasks = session.query(m.Task).filter_by(project_id=p.id).order_by(m.Task.id).all()
        names = {u.id: u.name for u in session.query(m.User).filter_by(org_id=p.org_id).all()}
        bb = _deps_for(session, [t.id for t in tasks])
        done = {t.id for t in tasks if t.status == "done"}
        prio: dict = {x: 0 for x in m.TASK_PRIORITIES}
        st: dict = {x: 0 for x in m.TASK_STATUS}
        for t in tasks:
            prio[t.priority] = prio.get(t.priority, 0) + 1
            st[t.status] = st.get(t.status, 0) + 1
        items = [_task_dict(t, names, bb, done) for t in tasks]
        return {"tasks": items, "users": [{"id": uid, "name": n} for uid, n in names.items()],
                "summary": {"total": len(tasks), "by_priority": prio, "by_status": st,
                            "blocked": sum(1 for i in items if i["is_blocked"] and i["status"] != "done"),
                            "quick_wins": sum(1 for t in tasks if t.is_quick_win and t.status != "done")}}

    @app.post("/api/projects/{project_id}/tasks", status_code=201)
    def add_task(project_id: str, body: TaskIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.priority not in m.TASK_PRIORITIES or body.status not in m.TASK_STATUS:
            raise _err(400, "BAD_TASK", "invalid priority or status")
        p = _project(session, user, project_id)
        t = m.Task(project_id=p.id, title=body.title, priority=body.priority, status=body.status,
                   assignee_user_id=body.assignee_user_id, estimate_hours=body.estimate_hours, due_date=body.due_date,
                   is_quick_win=body.is_quick_win, phase_code=body.phase_code, checklist_item_id=body.checklist_item_id)
        session.add(t); session.commit()
        names = {u.id: u.name for u in session.query(m.User).filter_by(org_id=p.org_id).all()}
        return {"task": _task_dict(t, names, {}, set())}

    @app.patch("/api/projects/{project_id}/tasks/{task_id}")
    def patch_task(project_id: str, task_id: int, body: TaskPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        t = session.query(m.Task).filter_by(project_id=p.id, id=task_id).first()
        if not t:
            raise _err(404, "TASK_NOT_FOUND", str(task_id))
        data = body.model_dump(exclude_unset=True)
        if data.get("priority") and data["priority"] not in m.TASK_PRIORITIES:
            raise _err(400, "BAD_PRIORITY", "invalid priority")
        if data.get("status") and data["status"] not in m.TASK_STATUS:
            raise _err(400, "BAD_STATUS", "invalid status")
        for k, v in data.items():
            setattr(t, k, v)
        if data.get("status") == "done" and not t.done_at:
            t.done_at = _dt.date.today().isoformat()
        session.commit()
        names = {u.id: u.name for u in session.query(m.User).filter_by(org_id=p.org_id).all()}
        bb = _deps_for(session, [task_id])
        done = {x.id for x in session.query(m.Task).filter_by(project_id=p.id, status="done").all()}
        return {"task": _task_dict(t, names, bb, done)}

    @app.delete("/api/projects/{project_id}/tasks/{task_id}")
    def del_task(project_id: str, task_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        t = session.query(m.Task).filter_by(project_id=p.id, id=task_id).first()
        if not t:
            raise _err(404, "TASK_NOT_FOUND", str(task_id))
        session.query(m.TaskDependency).filter((m.TaskDependency.task_id == task_id) | (m.TaskDependency.blocked_by_id == task_id)).delete()
        session.delete(t); session.commit()
        return {"deleted": task_id}

    @app.post("/api/projects/{project_id}/tasks/{task_id}/deps", status_code=201)
    def add_dep(project_id: str, task_id: int, body: DepIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        if body.blocked_by_id == task_id:
            raise _err(400, "SELF_DEP", "a task cannot block itself")
        owned = {x.id for x in session.query(m.Task).filter_by(project_id=p.id).all()}
        if task_id not in owned or body.blocked_by_id not in owned:
            raise _err(404, "TASK_NOT_FOUND", "task or dependency not in project")
        exists = session.query(m.TaskDependency).filter_by(task_id=task_id, blocked_by_id=body.blocked_by_id).first()
        if not exists:
            session.add(m.TaskDependency(task_id=task_id, blocked_by_id=body.blocked_by_id)); session.commit()
        return {"task_id": task_id, "blocked_by_id": body.blocked_by_id}

    @app.delete("/api/projects/{project_id}/tasks/{task_id}/deps/{blocked_by_id}")
    def del_dep(project_id: str, task_id: int, blocked_by_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        _project(session, user, project_id)
        session.query(m.TaskDependency).filter_by(task_id=task_id, blocked_by_id=blocked_by_id).delete()
        session.commit()
        return {"removed": [task_id, blocked_by_id]}

    @app.post("/api/projects/{project_id}/tasks/{task_id}/predict")
    def predict_task(project_id: str, task_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        t = session.query(m.Task).filter_by(project_id=p.id, id=task_id).first()
        if not t:
            raise _err(404, "TASK_NOT_FOUND", str(task_id))
        proj_ids = [x.id for x in session.query(m.Project).filter_by(org_id=p.org_id).all()]
        history = [{"title": h.title, "actual_hours": h.actual_hours}
                   for h in session.query(m.Task).filter(m.Task.project_id.in_(proj_ids), m.Task.actual_hours.isnot(None)).all()] if proj_ids else []
        from . import pilotage
        return {"task_id": task_id, **pilotage.predict_hours(t.title, history)}

    @app.post("/api/projects/{project_id}/fee-estimate")
    def fee_estimate_ep(project_id: str, body: FeeIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        _project(session, user, project_id)
        from . import pilotage
        return {"estimate": pilotage.fee_estimate(body.cfc2, body.project_type, body.hourly_rate, body.hours)}

    @app.get("/api/atelier/tasks")
    def atelier_tasks(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        projects = {p.id: p for p in session.query(m.Project).filter_by(org_id=user.org_id).all()}
        names = {u.id: u.name for u in session.query(m.User).filter_by(org_id=user.org_id).all()}
        tasks = session.query(m.Task).filter(m.Task.project_id.in_(list(projects))).all() if projects else []
        bb = _deps_for(session, [t.id for t in tasks])
        done = {t.id for t in tasks if t.status == "done"}
        items = []
        for t in tasks:
            pr = projects[t.project_id]
            items.append({**_task_dict(t, names, bb, done), "project_id": pr.project_id, "project_name": pr.name})
        from . import pilotage
        col = pilotage.collisions([{"status": t.status, "due_date": t.due_date, "estimate_hours": t.estimate_hours} for t in tasks])
        # per-collaborator open load
        by_assignee: dict = {}
        for t in tasks:
            if t.status == "done":
                continue
            key = names.get(t.assignee_user_id) or "non assigné"
            by_assignee[key] = round(by_assignee.get(key, 0.0) + float(t.estimate_hours or 0), 1)
        return {"tasks": items, "projects": len(projects), "collision": col, "load_by_assignee": by_assignee}

    # ---- capture notes: friction / photos / decisions / regulation watch (#231 #232) -- #
    def _cap_dict(c: m.CaptureNote) -> dict:
        return {"id": c.id, "kind": c.kind, "content": c.content, "author": c.author,
                "source_ref": c.source_ref, "created_at": str(c.created_at) if c.created_at else None}

    @app.get("/api/projects/{project_id}/captures")
    def list_captures(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        rows = session.query(m.CaptureNote).filter_by(project_id=p.id).order_by(m.CaptureNote.id.desc()).all()
        by_kind: dict = {}
        for c in rows:
            by_kind[c.kind] = by_kind.get(c.kind, 0) + 1
        return {"captures": [_cap_dict(c) for c in rows], "by_kind": by_kind,
                "regulation_alerts": [_cap_dict(c) for c in rows if c.kind == "regulation"]}

    @app.post("/api/projects/{project_id}/captures", status_code=201)
    def add_capture(project_id: str, body: CaptureIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        if body.kind not in m.CAPTURE_KINDS:
            raise _err(400, "BAD_KIND", f"kind must be one of {m.CAPTURE_KINDS}")
        p = _project(session, user, project_id)
        c = m.CaptureNote(project_id=p.id, kind=body.kind, content=body.content, author=user.name, source_ref=body.source_ref)
        session.add(c); session.commit()
        return {"capture": _cap_dict(c)}

    @app.delete("/api/projects/{project_id}/captures/{capture_id}")
    def del_capture(project_id: str, capture_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        c = session.query(m.CaptureNote).filter_by(project_id=p.id, id=capture_id).first()
        if not c:
            raise _err(404, "CAPTURE_NOT_FOUND", str(capture_id))
        session.delete(c); session.commit()
        return {"deleted": capture_id}

    @app.get("/api/projects/{project_id}/claims")
    def project_claims(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"claims": repository.claims_for(session, _project(session, user, project_id))}

    @app.get("/api/projects/{project_id}/permit")
    def project_permit(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        from . import reports

        return {"permit": reports.permit_view(project)}

    @app.post("/api/projects/{project_id}/permit/dossier")
    def submit_permit(project_id: str, body: SubmitPieceIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        from . import reports

        try:
            reports.submit_permit_piece(project, body.item_id, body.present)
        except ValueError as exc:
            raise _err(404, "UNKNOWN_ITEM", str(exc))
        session.commit()
        return {"permit": reports.permit_view(project)}

    @app.get("/api/projects/{project_id}/opposition")
    def project_opposition(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        from . import reports

        return {"opposition": reports.opposition_view(project)}

    @app.get("/api/projects/{project_id}/compliance")
    def project_compliance(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        from . import reports

        return {"compliance": reports.compliance_view(project)}

    @app.get("/api/projects/{project_id}/cost")
    def project_cost(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        from . import reports

        return {"cost": reports.cost_view(project)}

    @app.get("/api/projects/{project_id}/site")
    def project_site(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        from . import reports

        return {"site": reports.site_view(project)}

    # ---- action loop (E28+E27 in the runtime) ---------------------------- #
    @app.get("/api/projects/{project_id}/ledger")
    def project_ledger(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"ledger": actions.ledger(session, _project(session, user, project_id))}

    @app.get("/api/adapters/{adapter_id}/capabilities")
    def adapter_capabilities(adapter_id: str, user: m.User = Depends(current_user)):
        require(user, "project.read")
        try:
            return {"adapter_id": adapter_id, "capabilities": actions.capabilities(adapter_id)}
        except Exception:
            raise _err(404, "ADAPTER_NOT_FOUND", adapter_id)

    @app.post("/api/projects/{project_id}/adapter/dry-run")
    def adapter_dry_run(project_id: str, body: DryRunIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        try:
            result = actions.dry_run(session, project, user, body.adapter_id, body.operations, endpoint=body.adapter_endpoint)
        except Exception as exc:
            raise _err(404, "ADAPTER_NOT_FOUND", str(exc))
        session.commit()
        return result

    @app.post("/api/projects/{project_id}/approvals", status_code=201)
    def create_approval(project_id: str, body: ApprovalIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        try:
            result = actions.create_approval(session, project, user, body.scope, body.basis)
        except Exception as exc:
            raise _err(400, "INVALID_SCOPE", str(exc))
        session.commit()
        return {"approval": result}

    @app.post("/api/projects/{project_id}/adapter/execute")
    def adapter_execute(project_id: str, body: ExecuteIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "adapter.execute")
        project = _project(session, user, project_id)
        result = actions.execute(session, project, user, body.transaction)
        session.commit()
        return result

    # ---- memory queries + per-phase next step (north-star Q&A) ----------- #
    @app.get("/api/projects/{project_id}/memory/{kind}")
    def project_memory(project_id: str, kind: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        project = _project(session, user, project_id)
        fn = {"unknowns": orchestration.unknowns, "decisions": orchestration.decisions, "changes": orchestration.changes}.get(kind)
        if fn is None:
            raise _err(404, "UNKNOWN_QUERY", f"memory query {kind!r}; use unknowns|decisions|changes")
        return {kind: fn(session, project)}

    @app.get("/api/projects/{project_id}/memory/source/{source_id}")
    def project_memory_source(project_id: str, source_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return orchestration.source(session, _project(session, user, project_id), source_id)

    @app.get("/api/projects/{project_id}/next-step")
    def project_next_step(project_id: str, phase: str | None = None, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return orchestration.next_step(session, _project(session, user, project_id), phase)

    @app.post("/api/projects/{project_id}/brief")
    def generate_brief(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        if not os.path.isdir(DEMO_DIR):
            raise _err(422, "NO_INTAKE", "live parcel intake lands in AED-130 (#169)")
        from aedifica import workspace  # engine facade (stdlib)

        brief = workspace.generate_offline_parcel_brief(DEMO_DIR)
        counts = repository.save_brief(session, project, brief)
        session.commit()
        return {
            "brief_id": brief["brief_id"],
            "claim_state_summary": brief.get("claim_state_summary"),
            "persisted": counts,
            "project": repository.project_summary(session, project),
        }

    @app.post("/api/projects/{project_id}/intake")
    def parcel_intake(project_id: str, body: IntakeIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        from ..pipeline import build_live_brief

        brief = build_live_brief(body.query, body.live)
        counts = repository.save_brief(session, project, brief)
        session.commit()
        return {
            "mode": brief.get("mode"),
            "reason": brief.get("reason"),
            "persisted": counts,
            "claim_state_summary": sorted({c["state"] for c in brief.get("claims", [])}),
            "project": repository.project_summary(session, project),
        }

    # ---- communes (shared cache; write-gated) ---------------------------- #
    @app.get("/api/communes")
    def list_communes(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"communes": ingestion.list_packs(session)}

    @app.post("/api/communes", status_code=201)
    def request_commune(body: CommuneIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "commune.write")
        pack = ingestion.request_commune(session, body.commune, body.canton, body.source_authority)
        session.commit()
        return {"requested": {"id": pack.id, "commune": pack.commune, "status": pack.status}}

    @app.post("/api/communes/{pack_id}/ingest")
    def ingest_commune(pack_id: int, body: CommuneIngestIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "commune.write")
        pack = session.get(m.CommunePack, pack_id)
        if pack is None:
            raise _err(404, "PACK_NOT_FOUND", str(pack_id))
        ingested = ingestion.ingest_pack(
            session, pack.commune, pack.canton, body.version, body.zones,
            body.source_authority, body.valid_as_of, body.review_due, body.sources,
        )
        session.commit()
        return {"ingested": {"id": ingested.id, "commune": ingested.commune, "status": ingested.status}}

    @app.post("/api/communes/{pack_id}/promote")
    def promote_commune(pack_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "commune.write")
        pack = ingestion.promote(session, pack_id)
        if pack is None:
            raise _err(404, "PACK_NOT_FOUND", str(pack_id))
        session.commit()
        return {"promoted": {"id": pack.id, "commune": pack.commune, "status": pack.status}}

    @app.get("/api/communes/{commune}/{canton}/support")
    def commune_support(commune: str, canton: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"support": ingestion.support_state(session, commune, canton)}

    # ---- W10: scoped views for external users (client / mandataire / entreprise) -- #
    # These endpoints answer "what is my project · my devoirs · my documents"
    # from the perspective of the connected external user. No global access.
    def _external_scope(user_: m.User, session_: Session):
        """Return (intervenant, project) for a connected external user, or 401/403."""
        if user_.role != "external" or not user_.linked_intervenant_id:
            raise _err(403, "NOT_EXTERNAL", "this endpoint is reserved for external users")
        iv = session_.query(m.Intervenant).filter_by(id=user_.linked_intervenant_id).first()
        if not iv:
            raise _err(404, "INTERVENANT_GONE", "your invitation has been revoked")
        p = session_.query(m.Project).filter_by(id=iv.project_id).first()
        if not p:
            raise _err(404, "PROJECT_GONE", "your project no longer exists")
        return iv, p

    def _intervenant_actor_category(iv: m.Intervenant) -> str:
        """Map an intervenant.role free-text to one of the four actor categories.
        Heuristic, but consistent: anything that looks like the owner ↦ mo;
        engineers/specialists ↦ mandataire; companies ↦ entreprise; rest ↦ mandataire."""
        r = (iv.role or "").lower()
        if any(k in r for k in ("maître", "maitre", "ouvrage", "mo", "client", "propri")):
            return "mo"
        if any(k in r for k in ("entreprise", "constructeur", "société", "ouvrier", "general")):
            return "entreprise"
        return "mandataire"

    @app.get("/api/external/me")
    def external_me(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        iv, p = _external_scope(user, session)
        actor = _intervenant_actor_category(iv)
        return {"user": {"email": user.email, "name": user.name, "role": user.role},
                "intervenant": {"id": iv.id, "name": iv.name, "role": iv.role,
                                "organization": iv.organization, "actor_category": actor},
                "project": {"project_id": p.project_id, "name": p.name, "phase_code": p.phase_code,
                            "commune": p.commune},
                "phase_label": _siacl.PHASE_LABEL.get(p.phase_code, p.phase_code)}

    @app.get("/api/external/me/checklist")
    def external_my_checklist(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """My devoirs: checklist items where actor = my category OR responsible = me."""
        iv, p = _external_scope(user, session)
        actor = _intervenant_actor_category(iv)
        items = session.query(m.ChecklistItem).filter_by(project_id=p.id).order_by(m.ChecklistItem.order_index).all()
        mine = [c for c in items
                if c.actor == actor or c.responsible_intervenant_id == iv.id]
        # Vocabulaire client pour MO (Phase SIA ≠ Phase Client, cf. note 3 d'Etienne).
        client_phase_label = {
            "11": "On définit votre projet ensemble",
            "21": "On vérifie que c'est faisable",
            "22": "On choisit les spécialistes",
            "31": "On dessine le concept",
            "32": "On finalise le projet",
            "33": "On prépare le permis",
            "41": "On consulte les entreprises",
            "51": "On finalise les plans pour le chantier",
            "52": "Le chantier",
            "53": "Vos clefs et la garantie",
            "61": "On reste à vos côtés",
        }
        def _row(c: m.ChecklistItem) -> dict:
            label = (client_phase_label.get(c.phase_code, _siacl.PHASE_LABEL.get(c.phase_code))
                     if actor == "mo" else _siacl.PHASE_LABEL.get(c.phase_code, c.phase_code))
            return {"id": c.id, "phase_code": c.phase_code, "phase_label": label,
                    "title": c.title, "status": c.status, "is_retroactive": c.is_retroactive}
        done = sum(1 for c in mine if c.status == "done")
        return {"items": [_row(c) for c in mine],
                "summary": {"total": len(mine), "done": done, "todo": len(mine) - done,
                            "actor_category": actor}}

    @app.patch("/api/external/me/checklist/{item_id}")
    def external_tick_checklist(item_id: int, body: ChecklistPatch,
                                user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """An external can mark his own steps done / todo (the 'one click is done' UX)."""
        iv, p = _external_scope(user, session)
        actor = _intervenant_actor_category(iv)
        if body.status not in ("todo", "done"):
            raise _err(400, "BAD_STATUS", "external may only toggle todo|done")
        c = session.query(m.ChecklistItem).filter_by(project_id=p.id, id=item_id).first()
        if not c or (c.actor != actor and c.responsible_intervenant_id != iv.id):
            raise _err(404, "NOT_YOURS", "this step is not assigned to you")
        c.status = body.status
        session.commit()
        return {"item": {"id": c.id, "status": c.status}}

    @app.get("/api/external/me/documents")
    def external_my_documents(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """Documents I have access to via AccessGrant (group or person)."""
        iv, p = _external_scope(user, session)
        my_group_ids = [iv.group_id] if iv.group_id else []
        grants = session.query(m.AccessGrant).filter(
            (m.AccessGrant.intervenant_id == iv.id)
            | (m.AccessGrant.group_id.in_(my_group_ids) if my_group_ids else False)
        ).all()
        doc_ids = {g.document_id: g.level for g in grants}
        docs = session.query(m.Document).filter(m.Document.id.in_(doc_ids.keys())).all() if doc_ids else []
        out = [{"id": d.id, "official_name": d.official_name, "category": d.category,
                "validation_level": d.validation_level, "confidential": d.confidential,
                "access_level": doc_ids.get(d.id, "read")} for d in docs]
        return {"documents": out, "count": len(out)}

    return app


# Uvicorn entry point: `uvicorn aedifica.api.app:app` (dev; AEDIFICA_CREATE_ALL=1 to create tables).
app = create_app(create_all=get_settings().create_all)
