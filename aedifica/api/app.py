"""FastAPI product API over the engine + SQL store (multi-tenant).

Auth: bootstrap an org+owner (`POST /api/orgs`, with an optional password) to get
a bearer token; returning users exchange email + password for that token at
`POST /api/auth/login`. Send `Authorization: Bearer <token>` on every other call.
Projects are scoped to the caller's org; mutations require a capability (see
api.auth). Errors are structured: HTTP status + {"detail": {"code", "message"}}.
"""
from __future__ import annotations

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
                return {"token": u.api_token, "user_email": u.email, "role": u.role, "org_id": u.org_id}
        raise _err(401, "BAD_CREDENTIALS", "e-mail ou mot de passe incorrect")

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
        session.delete(i); session.commit()
        return {"deleted": intervenant_id}

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

    return app


# Uvicorn entry point: `uvicorn aedifica.api.app:app` (dev; AEDIFICA_CREATE_ALL=1 to create tables).
app = create_app(create_all=get_settings().create_all)
