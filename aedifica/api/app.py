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

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import Base, make_engine, make_session_factory, models as m, repository
from ..ingestion import service as ingestion
from ..ingestion.nomos_bundle import NomosBundleError, import_nomos_bundle
from ..retrieval.doctrine import NomosDoctrineError, answer_doctrine_question
from ..retrieval.embedding import get_default_embedder
from ..retrieval.lens import jurisdiction_pool_query, project_chunk_query
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
    # W17 — canton is now optional. When omitted, the backend tries to derive
    # it from (country, commune) via the jurisdiction resolver. If the commune
    # is unknown or matches several cantons, the request fails with a 400
    # carrying the candidates so the client can prompt the user.
    canton: str | None = None
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


class NomosImportIn(BaseModel):
    bundle: dict
    activate: bool = False


class NomosDoctrineIn(BaseModel):
    question: str
    lens: dict | None = None


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


def _err(status: int, code: str, message: str, extra: dict | None = None) -> HTTPException:
    detail: dict = {"code": code, "message": message}
    if extra:
        detail.update(extra)
    return HTTPException(status_code=status, detail=detail)


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

    # ---- W11.F AAA helpers ------------------------------------------------ #
    def _audit(session: Session, actor: m.User, event_type: str, target_summary: str,
               *, project: m.Project | None = None, target_user: m.User | None = None,
               meta: dict | None = None) -> None:
        """Append a security event to the audit log. Never raises — audit must
        never block the action being audited (we accept a small risk of missing
        rows to avoid masking actual failures)."""
        import json as _json
        if event_type not in m.AUDIT_EVENT_TYPES:
            return
        try:
            session.add(m.AuditEvent(
                org_id=actor.org_id,
                project_id=project.id if project else None,
                event_type=event_type,
                actor_user_id=actor.id,
                actor_name=actor.name or actor.email,
                actor_role=actor.role,
                target_user_id=target_user.id if target_user else None,
                target_summary=target_summary,
                meta_json=_json.dumps(meta) if meta else None,
            ))
            session.flush()
        except Exception:
            pass

    def _audit_dict(e: m.AuditEvent) -> dict:
        import json as _json
        return {"id": e.id, "event_type": e.event_type, "actor": e.actor_name,
                "actor_role": e.actor_role, "target": e.target_summary,
                "project_id": e.project_id, "target_user_id": e.target_user_id,
                "meta": _json.loads(e.meta_json) if e.meta_json else None,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None}

    def _merge_document_grants(grants: list[m.AccessGrant]) -> dict[int, dict]:
        merged: dict[int, dict] = {}
        for gr in grants:
            slot = merged.setdefault(gr.document_id, {"level": "read", "field_scope": []})
            if gr.level == "write":
                slot["level"] = "write"
            if gr.field_scope is None:
                slot["field_scope"] = None
            elif slot["field_scope"] is not None:
                for field in gr.field_scope:
                    if field not in slot["field_scope"]:
                        slot["field_scope"].append(field)
        return merged

    def _external_document_access(session: Session, project: m.Project, user: m.User) -> tuple[list[m.Document], dict[int, dict]]:
        """Return documents visible to an external user plus merged grant details."""
        if not user.linked_intervenant_id:
            return [], {}
        iv = session.query(m.Intervenant).filter_by(id=user.linked_intervenant_id, project_id=project.id).first()
        if not iv:
            return [], {}
        gids = [iv.group_id] if iv.group_id else []
        from sqlalchemy import or_ as _or
        grants = session.query(m.AccessGrant).filter(
            _or(m.AccessGrant.intervenant_id == iv.id,
                m.AccessGrant.group_id.in_(gids) if gids else False)
        ).all()
        access = _merge_document_grants(grants)
        doc_ids = set(access.keys())
        if not doc_ids:
            return [], {}
        docs = session.query(m.Document).filter(m.Document.project_id == project.id,
                                                m.Document.id.in_(doc_ids)).order_by(m.Document.id).all()
        return docs, {d.id: access[d.id] for d in docs if d.id in access}

    # ---- public ---------------------------------------------------------- #
    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0", "env": settings.env, "features": settings.features}

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
        # W11.F audit — redeemed invitations
        _audit(session, u, "invite_redeemed", f"{u.email} redeemed invite",
               target_user=u, meta={"role": u.role, "linked_intervenant_id": u.linked_intervenant_id})
        _audit(session, u, "password_set", f"{u.email} set password via invite", target_user=u)
        session.commit()
        iv = session.query(m.Intervenant).filter_by(id=u.linked_intervenant_id).first() if u.linked_intervenant_id else None
        return {"token": u.api_token, "user_email": u.email, "role": u.role,
                "linked_intervenant": {"id": iv.id, "name": iv.name, "role": iv.role} if iv else None}

    # ---- W11.F: token rotation + revocation (any authenticated user) ----- #
    @app.post("/api/auth/me/rotate-token")
    def rotate_token(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """Rotate the caller's API token. The old token stops working immediately;
        the new one is returned once (one-shot reveal). Audited."""
        new = auth.new_token()
        user.api_token = new
        _audit(session, user, "token_rotated", f"{user.email} rotated their API token", target_user=user)
        session.commit()
        return {"token": new, "user_email": user.email, "role": user.role}

    @app.post("/api/auth/me/revoke-token")
    def revoke_token(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        """Revoke the caller's API token (sign-out everywhere). The user will need
        to log in again via email+password. Audited."""
        user.api_token = None
        _audit(session, user, "token_revoked", f"{user.email} revoked their API token", target_user=user)
        session.commit()
        return {"revoked": True, "user_email": user.email}

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

    # ---- W17: jurisdiction resolver (commune → canton) ------------------- #
    # Used by the ProjectSwitcher to pre-fill the canton field as the user
    # types the commune. Three outcomes: exact (auto-fill), ambiguous
    # (homonym — show candidates), unknown (manual canton pick). No auth
    # gate: it's a pure read of a curated public dataset.
    @app.get("/api/jurisdictions/resolve")
    def jurisdiction_resolve(commune: str, country: str = "CH"):
        from .. import jurisdictions
        return jurisdictions.resolve(country, commune)

    @app.get("/api/jurisdictions/regions")
    def jurisdiction_regions(country: str = "CH"):
        from .. import jurisdictions
        return {"country": country, "regions": jurisdictions.list_regions(country)}

    @app.get("/api/jurisdictions/countries")
    def jurisdiction_countries():
        from .. import jurisdictions
        return {"countries": jurisdictions.list_countries()}

    @app.get("/api/jurisdictions/freshness")
    def jurisdiction_freshness(country: str = "CH"):
        """W18 — snapshot metadata so the UI can surface a "Données OFS au
        {date}" chip and reassure users that the dataset is live, not
        hand-curated."""
        from .. import jurisdictions
        return jurisdictions.freshness(country)

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
        # W17 — resolve canton when client omitted it. Honour an explicit
        # canton (frontend may have shown a picker for ambiguous/unknown
        # cases). Otherwise call the jurisdiction resolver and reject the
        # request when the result isn't exact, so we never silently land
        # a project in the wrong canton.
        from .. import jurisdictions
        canton = (body.canton or "").strip().upper() or None
        if canton is None:
            verdict = jurisdictions.resolve(body.country, body.commune)
            if verdict.get("confidence") == "exact":
                canton = verdict["canton"]
            else:
                raise _err(400, "CANTON_REQUIRED",
                           f"commune '{body.commune}' is {verdict.get('confidence')} — pick a canton",
                           extra={"resolver": verdict})
        project = repository.create_project(
            session, user.org_id, body.project_id, body.name,
            commune=body.commune, country=body.country, canton=canton, phase_code=body.phase_code,
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

    # W11 P0: navigate the project across SIA sub-phases (the top phase rail).
    # The frontend phase rail PATCHes here to set `phase_code` to a valid SIA code
    # (11/21/22/31/32/33/41/51/52/53/61). Other fields are ignored for now.
    @app.patch("/api/projects/{project_id}")
    def patch_project(project_id: str, body: dict, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        if "phase_code" in body:
            from . import sia_checklist as _sia
            code = str(body["phase_code"]).strip()
            if code and code not in _sia.PHASE_ORDER:
                raise _err(400, "BAD_PHASE", f"phase_code must be one of {_sia.PHASE_ORDER}")
            p.phase_code = code or "0"
        session.commit()
        return {"project": repository.project_summary(session, p)}

    # ---- W9 operating layer: intervenants, documents, access ---------------- #
    def _interv_dict(i: m.Intervenant) -> dict:
        return {"id": i.id, "name": i.name, "role": i.role, "organization": i.organization, "email": i.email,
                "phone": i.phone, "is_responsible": i.is_responsible, "group_id": i.group_id}

    def _group_dict(g: m.IntervenantGroup) -> dict:
        return {"id": g.id, "name": g.name, "kind": g.kind, "parent_id": g.parent_id}

    def _grant_dict(gr: m.AccessGrant) -> dict:
        return {"id": gr.id, "group_id": gr.group_id, "intervenant_id": gr.intervenant_id,
                "level": gr.level, "field_scope": gr.field_scope}

    def _doc_full_dict(d: m.Document) -> dict:
        return {"id": d.id, "official_name": d.official_name, "category": d.category,
                "validation_level": d.validation_level, "confidential": d.confidential, "note": d.note,
                "validated_by": d.validated_by, "validated_at": d.validated_at,
                "versions": [{"label": v.label, "source": v.source, "file_ref": v.file_ref} for v in d.versions],
                "latest": (d.versions[-1].label if d.versions else None),
                "grants": [_grant_dict(gr) for gr in d.grants]}

    def _doc_dict(d: m.Document, *, field_scope: list[str] | None = None,
                  access_level: str | None = None) -> dict:
        full = _doc_full_dict(d)
        if access_level is None:
            return full
        fields = list(m.DOCUMENT_ACCESS_FIELDS if field_scope is None else field_scope)
        out = {"id": d.id, "access_level": access_level,
               "access_fields": "all" if field_scope is None else fields}
        for field in fields:
            if field in full:
                out[field] = full[field]
        return out

    def _normalise_doc_field_scope(raw) -> list[str] | None:
        if raw is None:
            return None
        if not isinstance(raw, list):
            raise _err(400, "BAD_FIELD_SCOPE", "field_scope must be a list of document fields")
        fields: list[str] = []
        for value in raw:
            if not isinstance(value, str):
                raise _err(400, "BAD_FIELD_SCOPE", "field_scope entries must be strings")
            field = value.strip()
            if field and field not in fields:
                fields.append(field)
        if not fields:
            raise _err(400, "BAD_FIELD_SCOPE", "field_scope cannot be empty")
        bad = [f for f in fields if f not in m.DOCUMENT_ACCESS_FIELDS]
        if bad:
            raise _err(400, "BAD_FIELD_SCOPE",
                       f"unknown document field(s): {', '.join(bad)}",
                       extra={"allowed": list(m.DOCUMENT_ACCESS_FIELDS)})
        return fields

    @app.get("/api/projects/{project_id}/intervenants")
    def list_intervenants(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        groups = session.query(m.IntervenantGroup).filter_by(project_id=p.id).order_by(m.IntervenantGroup.id).all()
        people = session.query(m.Intervenant).filter_by(project_id=p.id).order_by(m.Intervenant.id).all()
        return {"groups": [_group_dict(g) for g in groups], "people": [_interv_dict(i) for i in people]}

    # W14.A — atelier-wide directory of intervenants (org scope), exposed so the
    # architect can re-use a contact already entered on another project rather
    # than retyping it. De-duplicated on (name, email) when both are present;
    # falls back to (name, organization) otherwise. Excludes intervenants
    # already on the current project so the UI offers ONLY net-new imports.
    @app.get("/api/orgs/intervenants-directory")
    def directory_intervenants(project_id: str | None = None,
                               user: m.User = Depends(current_user),
                               session: Session = Depends(get_session)):
        require(user, "project.read")
        org_projects = session.query(m.Project).filter_by(org_id=user.org_id).all()
        if not org_projects:
            return {"contacts": [], "total": 0}
        pids = {p.id for p in org_projects}
        cur_project = None
        if project_id:
            cur_project = next((p for p in org_projects if p.project_id == project_id), None)
        all_rows = (session.query(m.Intervenant)
                    .filter(m.Intervenant.project_id.in_(pids)).all())
        # Group by (name + email) to merge duplicates across projects.
        index: dict[tuple, dict] = {}
        for r in all_rows:
            key = (r.name.strip().lower(), (r.email or "").strip().lower(),
                   (r.organization or "").strip().lower())
            slot = index.get(key)
            if slot is None:
                slot = {"name": r.name, "role": r.role, "organization": r.organization,
                        "email": r.email, "phone": r.phone,
                        "seen_in_projects": [], "_project_ids": set()}
                index[key] = slot
            p_label = next((x.name or x.project_id for x in org_projects if x.id == r.project_id), str(r.project_id))
            if r.project_id not in slot["_project_ids"]:
                slot["_project_ids"].add(r.project_id)
                slot["seen_in_projects"].append({"project_id": next(x.project_id for x in org_projects if x.id == r.project_id), "name": p_label})
        # If a current project is provided, exclude contacts already living on it.
        out = []
        for slot in index.values():
            if cur_project and cur_project.id in slot.pop("_project_ids"):
                continue
            else:
                slot.pop("_project_ids", None)
            out.append(slot)
        out.sort(key=lambda s: (s["name"] or "").lower())
        return {"contacts": out, "total": len(out)}

    @app.post("/api/projects/{project_id}/intervenant-groups", status_code=201)
    def create_group(project_id: str, body: GroupIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "intervenants", "write", session)
        g = m.IntervenantGroup(project_id=p.id, name=body.name, kind=body.kind, parent_id=body.parent_id)
        session.add(g); session.commit()
        return {"group": _group_dict(g)}

    @app.delete("/api/projects/{project_id}/intervenant-groups/{group_id}")
    def delete_group(project_id: str, group_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "intervenants", "write", session)
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
        require_access(user, p, "intervenants", "write", session)
        i = m.Intervenant(project_id=p.id, name=body.name, role=body.role, organization=body.organization,
                          email=body.email, phone=body.phone, is_responsible=body.is_responsible, group_id=body.group_id)
        session.add(i); session.commit()
        return {"intervenant": _interv_dict(i)}

    @app.patch("/api/projects/{project_id}/intervenants/{intervenant_id}")
    def patch_intervenant(project_id: str, intervenant_id: int, body: IntervenantPatch, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "intervenants", "write", session)
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
        require_access(user, p, "intervenants", "write", session)
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
        require_access(user, p, "intervenants", "write", session)
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
        session.add(u); session.flush()
        # Also mirror the email back to the intervenant if blank (no-op otherwise).
        if not iv.email:
            iv.email = body.email
        # W11.F audit
        _audit(session, user, "invite_issued",
               f"{u.email} invited as external for intervenant {iv.name}",
               project=p, target_user=u,
               meta={"intervenant_id": iv.id, "intervenant_role": iv.role})
        session.commit()
        return {"user": {"id": u.id, "email": u.email, "name": u.name, "role": u.role,
                          "linked_intervenant_id": iv.id},
                "invite_token": invite}

    @app.get("/api/projects/{project_id}/documents")
    def list_documents(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        # W11.F: external users don't have project.read — they get a scoped view
        # of only the documents granted to their linked intervenant (directly or
        # via group). Other roles use the normal capability check.
        if user.role == "external":
            p = session.query(m.Project).filter_by(org_id=user.org_id, project_id=project_id).first()
            if p is None:
                raise _err(404, "PROJECT_NOT_FOUND", project_id)
            docs, access = _external_document_access(session, p, user)
            counts: dict = {lvl: 0 for lvl in m.VALIDATION_LEVELS}
            hidden_validation = 0
            for d in docs:
                scope = access.get(d.id, {}).get("field_scope")
                if scope is None or "validation_level" in scope:
                    counts[d.validation_level] = counts.get(d.validation_level, 0) + 1
                else:
                    hidden_validation += 1
            return {"documents": [_doc_dict(d, field_scope=access[d.id]["field_scope"],
                                            access_level=access[d.id]["level"]) for d in docs],
                    "summary": {"total": len(docs), "by_level": counts,
                                "pending": counts.get("pending", 0),
                                "hidden_validation": hidden_validation},
                    "scoped": "external"}
        require(user, "project.read")
        p = _project(session, user, project_id)
        docs = session.query(m.Document).filter_by(project_id=p.id).order_by(m.Document.id).all()
        counts: dict = {lvl: 0 for lvl in m.VALIDATION_LEVELS}
        for d in docs:
            counts[d.validation_level] = counts.get(d.validation_level, 0) + 1
        return {"documents": [_doc_dict(d) for d in docs],
                "summary": {"total": len(docs), "by_level": counts, "pending": counts.get("pending", 0)}}

    # ---- W11.F: audit log endpoints --------------------------------------- #
    @app.get("/api/orgs/audit")
    def list_org_audit(user: m.User = Depends(current_user), session: Session = Depends(get_session),
                      limit: int = 200):
        """Org-wide security log. Owner only — covers cross-project events too
        (token rotations, account-level revocations)."""
        require(user, "org.manage")
        rows = (session.query(m.AuditEvent).filter_by(org_id=user.org_id)
                .order_by(m.AuditEvent.id.desc()).limit(min(limit, 1000)).all())
        return {"events": [_audit_dict(e) for e in rows], "total": len(rows)}

    # ---- W16: fine-grained ACL for internal collaborators ----------------- #
    from .acl import resolve_access, user_access_map, has_level

    def _scope_dict(s: m.CollaboratorScope) -> dict:
        return {"id": s.id, "user_id": s.user_id, "project_id": s.project_id,
                "surface": s.surface, "level": s.level,
                "created_at": s.created_at.isoformat() if s.created_at else None}

    @app.get("/api/orgs/scopes")
    def list_scopes(user_id: int | None = None,
                    user: m.User = Depends(current_user),
                    session: Session = Depends(get_session)):
        """List CollaboratorScope rows. Owner only. Filter by user_id optional."""
        require(user, "org.manage")
        q = session.query(m.CollaboratorScope).filter_by(org_id=user.org_id)
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        rows = q.order_by(m.CollaboratorScope.id.desc()).all()
        return {"scopes": [_scope_dict(s) for s in rows]}

    @app.put("/api/orgs/scopes")
    def upsert_scope(body: dict, user: m.User = Depends(current_user),
                     session: Session = Depends(get_session)):
        """Owner sets a (user, project?, surface?) → level scope row.
        If a row with the same triple exists, its level is updated.
        Setting level='write' for a member is a no-op vs role default but stays
        recorded so the owner sees their intent.
        Owners CANNOT scope themselves down — silently ignored.
        Body: {user_id, project_id?, surface?, level}."""
        require(user, "org.manage")
        target_id = int(body.get("user_id") or 0)
        if not target_id:
            raise _err(400, "BAD_USER", "user_id required")
        target = session.query(m.User).filter_by(id=target_id, org_id=user.org_id).first()
        if not target:
            raise _err(404, "USER_NOT_FOUND", str(target_id))
        if target.role == "owner":
            # No-op: owners are always full-write.
            return {"scope": None, "noop": "owner stays full-write"}
        if target.role == "external":
            raise _err(400, "EXTERNAL_USER", "externals are scoped via AccessGrant, not this endpoint")
        level = (body.get("level") or "").strip()
        if level not in m.SCOPE_LEVELS:
            raise _err(400, "BAD_LEVEL", f"level must be one of {m.SCOPE_LEVELS}")
        surface = body.get("surface") or None
        if surface and surface not in m.SCOPED_SURFACES:
            raise _err(400, "BAD_SURFACE", f"surface must be one of {m.SCOPED_SURFACES}")
        project = None
        pid_in = body.get("project_id")
        if pid_in is not None:
            project = session.query(m.Project).filter_by(org_id=user.org_id, id=int(pid_in)).first()
            if not project:
                raise _err(404, "PROJECT_NOT_FOUND", str(pid_in))
        existing = (session.query(m.CollaboratorScope)
                    .filter_by(user_id=target_id,
                               project_id=project.id if project else None,
                               surface=surface).first())
        if existing:
            existing.level = level
            row = existing
        else:
            row = m.CollaboratorScope(
                org_id=user.org_id, user_id=target_id,
                project_id=project.id if project else None,
                surface=surface, level=level,
                created_by_user_id=user.id,
            )
            session.add(row); session.flush()
        _audit(session, user, "scope_granted",
               f"{target.email} → {project.project_id if project else 'org'}/{surface or 'all'} = {level}",
               project=project, target_user=target,
               meta={"surface": surface, "level": level,
                     "project_id": project.project_id if project else None})
        session.commit()
        return {"scope": _scope_dict(row)}

    @app.delete("/api/orgs/scopes/{scope_id}")
    def delete_scope(scope_id: int, user: m.User = Depends(current_user),
                     session: Session = Depends(get_session)):
        """Remove a scope row → user falls back to less specific resolution."""
        require(user, "org.manage")
        row = session.query(m.CollaboratorScope).filter_by(
            id=scope_id, org_id=user.org_id).first()
        if not row:
            raise _err(404, "SCOPE_NOT_FOUND", str(scope_id))
        target = session.query(m.User).filter_by(id=row.user_id).first()
        proj = session.query(m.Project).filter_by(id=row.project_id).first() if row.project_id else None
        _audit(session, user, "scope_revoked",
               f"{target.email if target else row.user_id} ← {proj.project_id if proj else 'org'}/{row.surface or 'all'} removed",
               project=proj, target_user=target,
               meta={"surface": row.surface, "level": row.level})
        session.delete(row); session.commit()
        return {"deleted": scope_id}

    @app.get("/api/auth/me/access")
    def my_access(user: m.User = Depends(current_user),
                  session: Session = Depends(get_session)):
        """Returns the access map for the current user (used by the workspace
        shell to hide / disable surfaces based on level). Includes role and
        per-project per-surface levels. Non-owner externals get the empty
        map; they go through ExternalView anyway."""
        return user_access_map(session, user)

    def require_access(user: m.User, project: m.Project | None, surface: str | None,
                       needed: str, session: Session) -> None:
        """Enforce a minimum access level. Used in route handlers that need
        finer granularity than the original capability check."""
        # Owner shortcut handled inside resolve_access.
        lvl = resolve_access(session, user, project, surface)
        if not has_level(lvl, needed):
            raise _err(403, "SCOPED_OUT",
                       f"your access to {surface or 'this resource'} is {lvl!r}, {needed!r} required")

    # Generic attachments hang off any owning row — derive the surface from
    # owner_kind so the ACL check matches the surface the attachment lives in.
    # Unknown kinds default to "documents" (file storage is the visible bucket).
    _OWNER_SURFACE = {
        "document": "documents",
        "brs": "brs",
        "task": "taches",
        "checklist_item": "checklist",
        "capture_note": "memoire",
        "capture": "memoire",
        "permit_piece": "permis",
        "permit": "permis",
        "opposition": "opposition",
        "opposition_item": "opposition",
        "conformity": "conformite",
        "conformity_item": "conformite",
        "intervenant": "intervenants",
        "cost": "couts",
        "site": "chantier",
        "proposal": "foresight",
    }
    def _owner_surface(owner_kind: str | None) -> str:
        if not owner_kind:
            return "documents"
        return _OWNER_SURFACE.get(owner_kind, "documents")

    @app.get("/api/projects/{project_id}/audit")
    def list_project_audit(project_id: str, user: m.User = Depends(current_user),
                           session: Session = Depends(get_session), limit: int = 200):
        """Per-project security log (invites, grants, revocations). Project
        members only — externals never see audit events."""
        require(user, "project.read")
        p = _project(session, user, project_id)
        rows = (session.query(m.AuditEvent).filter_by(org_id=user.org_id, project_id=p.id)
                .order_by(m.AuditEvent.id.desc()).limit(min(limit, 1000)).all())
        return {"events": [_audit_dict(e) for e in rows], "total": len(rows)}

    # ---- W12.E: atelier-wide benchmark snapshots -------------------------- #
    def _benchmark_dict(b: m.AtelierBenchmark) -> dict:
        import json as _json
        return {"id": b.id, "period_label": b.period_label,
                "n_projects": b.n_projects, "n_tasks_done": b.n_tasks_done,
                "duration_ratios": _json.loads(b.duration_ratios_json) if b.duration_ratios_json else {},
                "cost_factor": b.cost_factor, "note": b.note,
                "frozen_at": b.frozen_at.isoformat() if b.frozen_at else None}

    @app.post("/api/orgs/benchmark/snapshot", status_code=201)
    def snapshot_benchmark(body: dict | None = None,
                           user: m.User = Depends(current_user),
                           session: Session = Depends(get_session)):
        """Freeze the atelier's current learning state into an append-only
        AtelierBenchmark row. Owner only — capitalization is org-wide.
        Body: {"note": "..."} (optional)."""
        require(user, "org.manage")
        from ..foresight.benchmark import snapshot_atelier
        row = snapshot_atelier(session, user.org_id,
                               note=(body or {}).get("note"))
        session.commit()
        return {"benchmark": _benchmark_dict(row)}

    @app.get("/api/orgs/benchmark")
    def list_benchmarks(user: m.User = Depends(current_user),
                        session: Session = Depends(get_session)):
        """List all frozen snapshots, most recent first. Owner only."""
        require(user, "org.manage")
        rows = (session.query(m.AtelierBenchmark)
                .filter_by(org_id=user.org_id)
                .order_by(m.AtelierBenchmark.id.desc()).all())
        return {"benchmarks": [_benchmark_dict(b) for b in rows], "total": len(rows)}

    @app.get("/api/orgs/benchmark/latest")
    def get_latest_benchmark(user: m.User = Depends(current_user),
                             session: Session = Depends(get_session)):
        """Most-recent snapshot, or 404 if none. Any project-reader role."""
        require(user, "project.read")
        from ..foresight.benchmark import latest_snapshot
        row = latest_snapshot(session, user.org_id)
        if not row:
            raise _err(404, "NO_BENCHMARK", "no snapshot frozen yet")
        return {"benchmark": _benchmark_dict(row)}

    # ---- W12.A: Foresight — deterministic predictive layer ---------------- #
    def _proposal_dict(p: m.Proposal) -> dict:
        import json as _json
        return {"id": p.id, "kind": p.kind, "title": p.title, "detail": p.detail,
                "basis": _json.loads(p.basis_json) if p.basis_json else [],
                "confidence": p.confidence, "decision": p.decision,
                "apply_payload": (_json.loads(p.apply_payload_json) if p.apply_payload_json else None),
                "proposed_at": p.proposed_at.isoformat() if p.proposed_at else None,
                "decided_at": p.decided_at.isoformat() if p.decided_at else None,
                "decided_by": p.decided_by, "decision_basis": p.decision_basis}

    @app.get("/api/projects/{project_id}/foresight")
    def get_foresight(project_id: str, refresh: bool = False,
                      user: m.User = Depends(current_user),
                      session: Session = Depends(get_session)):
        """Read (and optionally refresh) the IA proposals for this project.
        Without refresh, returns the currently-persisted proposals + counts;
        with refresh, re-runs the deterministic engine over the live data
        and replaces the pending set. Accepted/refused proposals are kept
        as the architect's decision history."""
        require(user, "project.read")
        p = _project(session, user, project_id)
        from ..foresight import compute_proposals, thresholds
        thr = thresholds(session, p)  # W14.A — always exposed, even with no proposals.
        if refresh:
            rows, summary = compute_proposals(session, p)
            session.commit()
            comparables = [{"project_id": c.project_id, "label": c.project_label,
                            "score": c.score, "reasons": c.reasons} for c in summary.comparables]
            return {
                "proposals": [_proposal_dict(r) for r in rows],
                "summary": {"predictions": summary.predictions, "risks": summary.risks,
                            "suggestions": summary.suggestions, "confidence_avg": summary.confidence_avg},
                "comparables": comparables,
                "thresholds": thr,
                "freshness": summary.freshness.isoformat(),
            }
        rows = (session.query(m.Proposal).filter_by(project_id=p.id, decision="pending")
                .order_by(m.Proposal.id.desc()).all())
        return {
            "proposals": [_proposal_dict(r) for r in rows],
            "summary": {"predictions": sum(1 for r in rows if r.kind in ("duration_adjust", "cost_factor")),
                        "risks": sum(1 for r in rows if r.kind == "risk_alert"),
                        "suggestions": sum(1 for r in rows if r.kind in ("reuse_brs", "reuse_checklist", "rebalance")),
                        "confidence_avg": round(sum(r.confidence for r in rows) / len(rows), 2) if rows else 0.0},
            "comparables": [],
            "thresholds": thr,
            "freshness": None,
        }

    @app.get("/api/projects/{project_id}/foresight/explain/{proposal_id}")
    def explain_foresight(project_id: str, proposal_id: int,
                          user: m.User = Depends(current_user),
                          session: Session = Depends(get_session)):
        """W12.F — full explainability dump for one proposal.

        Returns every named source actually inspectable: the live row text
        for each task/BRS/ledger/capture cited in ``basis``, plus the rule
        that fired and the confidence formula's inputs. Doctrine: the
        architect must be able to answer ``pourquoi cette proposition ?``
        without leaving the workspace and without trusting a black box."""
        import json as _json
        require(user, "project.read")
        p = _project(session, user, project_id)
        row = session.query(m.Proposal).filter_by(project_id=p.id, id=proposal_id).first()
        if not row:
            raise _err(404, "PROPOSAL_NOT_FOUND", str(proposal_id))
        basis = _json.loads(row.basis_json) if row.basis_json else []
        hydrated = []
        for b in basis:
            kind = b.get("source_kind"); sid = b.get("source_id")
            live = None
            try:
                if kind == "task":
                    t = session.query(m.Task).filter_by(id=sid).first()
                    if t:
                        live = {"title": t.title, "status": t.status,
                                "estimate_hours": t.estimate_hours, "actual_hours": t.actual_hours,
                                "phase_code": t.phase_code, "priority": t.priority}
                elif kind == "brs":
                    e = session.query(m.BrsEntry).filter_by(id=sid).first()
                    if e:
                        live = {"content": e.content, "kind": e.kind,
                                "created_at": e.created_at.isoformat() if e.created_at else None}
                elif kind == "ledger":
                    le = session.query(m.LedgerEntry).filter_by(id=sid).first()
                    if le:
                        live = {"event_type": le.event_type, "summary": le.summary,
                                "phase_code": le.phase_code,
                                "timestamp": le.timestamp.isoformat() if le.timestamp else None}
                elif kind == "capture":
                    c = session.query(m.CaptureNote).filter_by(id=sid).first()
                    if c:
                        live = {"content": c.content, "kind": c.kind,
                                "source_ref": c.source_ref,
                                "created_at": c.created_at.isoformat() if c.created_at else None}
                elif kind == "user":
                    u = session.query(m.User).filter_by(id=sid).first()
                    if u:
                        live = {"name": u.name, "email": u.email, "role": u.role}
                elif kind == "project":
                    other = session.query(m.Project).filter_by(id=sid).first()
                    if other:
                        live = {"project_id": other.project_id, "name": other.name,
                                "commune": other.commune, "phase_code": other.phase_code}
            except Exception:
                live = None
            hydrated.append({**b, "live": live, "live_resolved": live is not None})
        return {
            "proposal": _proposal_dict(row),
            "basis_hydrated": hydrated,
            "rule": row.kind,
            "confidence_formula": {
                "duration_adjust": "min(1.0, comparable_count / 20)",
                "cost_factor": "min(1.0, archived_pair_count / 8)",
                "risk_alert": "règle-spécifique : 1.0 pour signaux durs, 0.7-0.9 pour signaux souples",
            }.get(row.kind, "—"),
            "freshness": row.proposed_at.isoformat() if row.proposed_at else None,
        }

    # ---- W12.C: LLM opt-in ------------------------------------------------ #
    @app.patch("/api/projects/{project_id}/llm-mode")
    def set_llm_mode(project_id: str, body: dict,
                     user: m.User = Depends(current_user),
                     session: Session = Depends(get_session)):
        """Flip a project's llm_mode between off | local | cloud.
        Audited. The default is 'off' — no LLM call ever leaves the API
        without an explicit flip here."""
        require(user, "project.write")
        p = _project(session, user, project_id)
        mode = (body.get("mode") or "").lower()
        if mode not in ("off", "local", "cloud"):
            raise _err(400, "BAD_MODE", "mode must be off|local|cloud")
        prev = p.llm_mode
        p.llm_mode = mode
        _audit(session, user, "llm_mode_changed",
               f"projet {p.project_id} : llm_mode {prev} → {mode}",
               project=p, meta={"from": prev, "to": mode})
        session.commit()
        return {"project_id": p.project_id, "llm_mode": p.llm_mode}

    @app.post("/api/projects/{project_id}/foresight/llm/brs-summary",
              status_code=201)
    def llm_brs_summary(project_id: str,
                        user: m.User = Depends(current_user),
                        session: Session = Depends(get_session)):
        """Ask the configured LLM (per project.llm_mode) to summarize the
        BRS thread. Returns a fresh Proposal — never mutates the BRS
        register. 400 when llm_mode='off' or no BRS entries to summarize."""
        require(user, "project.write")
        p = _project(session, user, project_id)
        if (p.llm_mode or "off") == "off":
            raise _err(400, "LLM_OFF", "llm_mode is off — set it to local|cloud first")
        from ..foresight.llm import summarize_brs_thread
        prop = summarize_brs_thread(session, p)
        if not prop:
            raise _err(503, "LLM_UNAVAILABLE",
                      "no BRS to summarize or LLM backend unavailable")
        import json as _json
        row = m.Proposal(
            project_id=p.id,
            kind=prop["kind"],
            title=prop["title"],
            detail=prop["detail"],
            basis_json=_json.dumps(prop["basis"], ensure_ascii=False),
            confidence=float(prop.get("confidence", 0.0)),
            apply_payload_json=_json.dumps(prop["apply_payload"], ensure_ascii=False),
            decision="pending",
        )
        session.add(row); session.flush()
        _audit(session, user, "llm_called",
               f"LLM ({p.llm_mode}) appelé sur le registre BRS",
               project=p, meta={"kind": prop["kind"], "basis_size": len(prop["basis"])})
        session.commit()
        return {"proposal": _proposal_dict(row)}

    @app.post("/api/projects/{project_id}/foresight/{proposal_id}/decide")
    def decide_foresight(project_id: str, proposal_id: int, body: dict,
                         user: m.User = Depends(current_user),
                         session: Session = Depends(get_session)):
        """Accept / defer / refuse a proposal. On accept, the apply_payload
        (when it has a method+path) is what the client will PATCH itself —
        this endpoint only records the decision + the architect's basis."""
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "foresight", "write", session)
        decision = body.get("decision", "")
        if decision not in ("accepted", "deferred", "refused"):
            raise _err(400, "BAD_DECISION", "decision must be accepted|deferred|refused")
        row = session.query(m.Proposal).filter_by(project_id=p.id, id=proposal_id).first()
        if not row:
            raise _err(404, "PROPOSAL_NOT_FOUND", str(proposal_id))
        row.decision = decision
        row.decided_at = _dt.datetime.now(_dt.timezone.utc)
        row.decided_by = user.name or user.email
        row.decision_basis = body.get("basis") or None
        session.commit()
        return {"proposal": _proposal_dict(row)}

    @app.post("/api/projects/{project_id}/documents", status_code=201)
    def create_document(project_id: str, body: DocumentIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "documents", "write", session)
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
        require_access(user, p, "documents", "write", session)
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
        require_access(user, p, "documents", "write", session)
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
        require_access(user, p, "documents", "write", session)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        session.delete(d); session.commit()
        return {"deleted": document_id}

    @app.post("/api/projects/{project_id}/documents/{document_id}/grants", status_code=201)
    def grant_access(project_id: str, document_id: int, body: dict, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "documents", "write", session)
        d = session.query(m.Document).filter_by(project_id=p.id, id=document_id).first()
        if not d:
            raise _err(404, "DOCUMENT_NOT_FOUND", str(document_id))
        level = body.get("level", "read")
        if level not in m.ACCESS_LEVELS:
            raise _err(400, "BAD_LEVEL", f"level must be one of {m.ACCESS_LEVELS}")
        field_scope = _normalise_doc_field_scope(body.get("field_scope"))
        gr = m.AccessGrant(document_id=d.id, group_id=body.get("group_id"),
                           intervenant_id=body.get("intervenant_id"), level=level,
                           field_scope=field_scope)
        session.add(gr); session.flush()
        # W11.F audit — track who got access to what
        target_label = []
        if body.get("intervenant_id"):
            iv = session.query(m.Intervenant).filter_by(id=body["intervenant_id"]).first()
            target_label.append(f"intervenant:{iv.name if iv else body['intervenant_id']}")
        if body.get("group_id"):
            g = session.query(m.IntervenantGroup).filter_by(id=body["group_id"]).first()
            target_label.append(f"group:{g.name if g else body['group_id']}")
        _audit(session, user, "access_granted",
               f"{d.official_name} → {' + '.join(target_label) or 'unknown'} (level={gr.level}, fields={field_scope or 'all'})",
               project=p, meta={"document_id": d.id, "grant_id": gr.id, "level": gr.level,
                                "field_scope": field_scope,
                                "intervenant_id": body.get("intervenant_id"), "group_id": body.get("group_id")})
        session.commit()
        return {"document": _doc_dict(d)}

    @app.delete("/api/projects/{project_id}/documents/{document_id}/grants/{grant_id}")
    def revoke_access(project_id: str, document_id: int, grant_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "documents", "write", session)
        gr = session.query(m.AccessGrant).filter_by(id=grant_id, document_id=document_id).first()
        if gr:
            d_for_audit = session.query(m.Document).filter_by(id=document_id).first()
            session.delete(gr)
            # W11.F audit
            _audit(session, user, "access_revoked",
                   f"{d_for_audit.official_name if d_for_audit else document_id}: grant {grant_id} removed",
                   project=p, meta={"document_id": document_id, "grant_id": grant_id})
            session.commit()
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
        require_access(user, p, "brs", "write", session)
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
        require_access(user, p, "brs", "write", session)
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
        require_access(user, p, "brs", "write", session)
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
                # W21-5 — feuille SIA Vaud: which actors carry deliverables in
                # each sub-phase (derived from the template, surfaced on the
                # dashboard as « intervenants par phase »).
                "sia_actors_by_phase": _siacl.actors_by_phase(),
                "summary": {"total": len(items), "seeded": len(items) > 0,
                            "retroactive": sum(1 for c in items if c.is_retroactive),
                            "by_status": by_status, "by_actor": by_actor,
                            "external_todo": external_todo,
                            "external_blockers": len(_external_blockers(items, p.phase_code))}}

    @app.post("/api/projects/{project_id}/checklist/seed", status_code=201)
    def seed_checklist(project_id: str, body: ChecklistSeedIn, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "checklist", "write", session)
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
        require_access(user, p, "checklist", "write", session)
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
        require_access(user, p, "checklist", "write", session)
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
        require_access(user, p, "checklist", "write", session)
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
        require_access(user, p, "taches", "write", session)
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
        require_access(user, p, "taches", "write", session)
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
        require_access(user, p, "taches", "write", session)
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
        require_access(user, p, "taches", "write", session)
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
        p = _project(session, user, project_id)
        require_access(user, p, "taches", "write", session)
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

    # W11.C: atelier-wide alerts derived from the task pool — pushed to the
    # Dashboard so the architect doesn't need to read the Gantt to know what's
    # *about* to bite. Each alert is a small structured dict:
    #   {severity: "info"|"warn"|"bad", kind: "...", title, detail, project_id?, task_id?, week?}
    # Categories: (a) upcoming P0 within 7 days, (b) overdue undone tasks, (c)
    # weeks overloaded against capacity, (d) collaborators carrying >40h open
    # work, (e) bloquant chains (>=2 levels deep), (f) quick wins so they get
    # done while waiting on something else.
    @app.get("/api/atelier/alerts")
    def atelier_alerts(user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        projects = {p.id: p for p in session.query(m.Project).filter_by(org_id=user.org_id).all()}
        if not projects:
            return {"alerts": []}
        names = {u.id: u.name for u in session.query(m.User).filter_by(org_id=user.org_id).all()}
        all_tasks = session.query(m.Task).filter(m.Task.project_id.in_(list(projects))).all()
        from datetime import date, datetime, timedelta
        today = date.today()
        alerts = []
        # (a) P0 dans 7 jours, (b) en retard
        for t in all_tasks:
            if t.status == "done":
                continue
            if not t.due_date:
                continue
            try:
                due = datetime.fromisoformat(t.due_date).date()
            except (TypeError, ValueError):
                continue
            pid = projects[t.project_id].project_id
            if due < today:
                alerts.append({"severity": "bad", "kind": "overdue",
                               "title": f"Tâche en retard : {t.title}",
                               "detail": f"Échéance {t.due_date} dépassée ({(today - due).days} j) — projet {projects[t.project_id].name}.",
                               "project_id": pid, "task_id": t.id})
            elif t.priority == "p0" and (due - today).days <= 7:
                alerts.append({"severity": "warn", "kind": "p0_soon",
                               "title": f"P0 dans {(due - today).days} jour(s) : {t.title}",
                               "detail": f"Échéance {t.due_date} — projet {projects[t.project_id].name}.",
                               "project_id": pid, "task_id": t.id})
        # (c) semaines surchargées (vient déjà de pilotage.collisions)
        from . import pilotage
        col = pilotage.collisions([{"status": t.status, "due_date": t.due_date, "estimate_hours": t.estimate_hours} for t in all_tasks])
        for o in col.get("overloaded", []) or []:
            alerts.append({"severity": "warn", "kind": "overloaded_week",
                           "title": f"Semaine surchargée — {o.get('week')}",
                           "detail": f"{o.get('hours')} h estimées (+{o.get('over')} h au-delà de {col.get('weekly_capacity')} h/sem).",
                           "week": o.get("week")})
        # (d) collaborateurs > 40 h ouvertes
        load: dict = {}
        for t in all_tasks:
            if t.status == "done":
                continue
            k = names.get(t.assignee_user_id) or "non assigné"
            load[k] = round(load.get(k, 0.0) + float(t.estimate_hours or 0), 1)
        for who, h in load.items():
            if h > 40 and who != "non assigné":
                alerts.append({"severity": "warn", "kind": "overloaded_assignee",
                               "title": f"{who} en surcharge",
                               "detail": f"{h} h ouvertes — au-delà du seuil hebdo de 40 h."})
        # (e) chaînes de dépendances bloquantes — toute tâche bloquée par une autre elle-même bloquée
        deps = _deps_for(session, [t.id for t in all_tasks])
        done = {t.id for t in all_tasks if t.status == "done"}
        for t in all_tasks:
            if t.status == "done":
                continue
            blockers = [d for d in deps.get(t.id, []) if d not in done]
            for b in blockers:
                bdeps = [d for d in deps.get(b, []) if d not in done]
                if bdeps:  # 2-level chain
                    bt = next((x for x in all_tasks if x.id == b), None)
                    alerts.append({"severity": "warn", "kind": "deep_block",
                                   "title": f"Chaîne de bloquants : {t.title}",
                                   "detail": f"Dépend de « {bt.title if bt else '?'} » qui dépend elle-même d'autres tâches non terminées.",
                                   "project_id": projects[t.project_id].project_id, "task_id": t.id})
                    break
        # (f) quick wins ouverts
        qw_count = sum(1 for t in all_tasks if t.status != "done" and t.is_quick_win)
        if qw_count > 0:
            alerts.append({"severity": "info", "kind": "quick_wins_available",
                           "title": f"{qw_count} quick win{'s' if qw_count > 1 else ''} ouvert{'s' if qw_count > 1 else ''}",
                           "detail": "Tâches courtes que vous pouvez tacler pendant qu'autre chose bloque."})
        return {"alerts": alerts[:24]}

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
        require_access(user, p, "memoire", "write", session)
        c = m.CaptureNote(project_id=p.id, kind=body.kind, content=body.content, author=user.name, source_ref=body.source_ref)
        session.add(c); session.commit()
        return {"capture": _cap_dict(c)}

    @app.delete("/api/projects/{project_id}/captures/{capture_id}")
    def del_capture(project_id: str, capture_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, "memoire", "write", session)
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
        require_access(user, project, "permis", "write", session)
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
        require_access(user, project, "copilote", "write", session)
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
        require_access(user, project, "copilote", "write", session)
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
        require_access(user, project, "copilote", "write", session)
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

    @app.post("/api/projects/{project_id}/copilote/nomos")
    def copilote_nomos_doctrine(
        project_id: str,
        body: NomosDoctrineIn,
        user: m.User = Depends(current_user),
        session: Session = Depends(get_session),
    ):
        require(user, "project.read")
        if not settings.nomos_enabled:
            raise _err(403, "NOMOS_DISABLED", "NOMOS doctrine retriever is disabled")
        project = _project(session, user, project_id)
        try:
            return answer_doctrine_question(
                session,
                project,
                body.question,
                nomos_enabled=settings.nomos_enabled,
                lens=body.lens,
                embedder=get_default_embedder(),
            )
        except NomosDoctrineError as exc:
            raise _err(422, "NOMOS_DOCTRINE_INVALID", str(exc))

    @app.post("/api/projects/{project_id}/brief")
    def generate_brief(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        project = _project(session, user, project_id)
        require_access(user, project, "copilote", "write", session)
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
        require_access(user, project, "terrain", "write", session)
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

    @app.post("/api/projects/{project_id}/nomos/import")
    def import_nomos_bundle_endpoint(
        project_id: str,
        body: NomosImportIn,
        user: m.User = Depends(current_user),
        session: Session = Depends(get_session),
    ):
        require(user, "project.write")
        if not settings.nomos_enabled:
            raise _err(403, "NOMOS_DISABLED", "NOMOS bundle import is disabled")
        project = _project(session, user, project_id)
        try:
            imported = import_nomos_bundle(
                session,
                project,
                body.bundle,
                nomos_enabled=settings.nomos_enabled,
                activate=body.activate,
            )
        except NomosBundleError as exc:
            session.rollback()
            # exc.code distinguishes the schema gate (NOMOS_BUNDLE_SCHEMA_UNSUPPORTED)
            # from a generally invalid payload (NOMOS_BUNDLE_INVALID).
            raise _err(422, exc.code, str(exc))
        session.commit()
        return {"imported": imported, "project": repository.project_summary(session, project)}

    @app.get("/api/projects/{project_id}/nomos/corpus")
    def nomos_corpus_endpoint(
        project_id: str,
        user: m.User = Depends(current_user),
        session: Session = Depends(get_session),
    ):
        """W21-2 — what the doctrine retriever can actually see for this project.

        Read-only aggregation over the SAME lens-scoped pools the doctrine path
        queries (project silo + jurisdiction pool), so the UI never claims a
        corpus the retriever would not use. Flag-gated like the other NOMOS
        endpoints; additive only.
        """
        require(user, "project.read")
        if not settings.nomos_enabled:
            raise _err(403, "NOMOS_DISABLED", "NOMOS knowledge layer is disabled")
        project = _project(session, user, project_id)
        juri_rows = jurisdiction_pool_query(
            session, country=project.country, canton=project.canton, commune=project.commune
        ).all()
        proj_rows = project_chunk_query(session, project.id).all()
        by_tier: dict[str, int] = {"certified": 0, "indicative": 0, "unverified": 0}
        embedded = 0
        sources: set[str] = set()
        for row in (*juri_rows, *proj_rows):
            tier = row.trust_tier or "unverified"
            by_tier[tier] = by_tier.get(tier, 0) + 1
            if row.embedding:
                embedded += 1
            sources.add(row.source_hash)
        feeds = []
        packs = (
            session.query(m.CommunePack)
            .filter(m.CommunePack.commune == project.commune, m.CommunePack.canton == project.canton)
            .order_by(m.CommunePack.id.desc())
            .all()
        )
        for pack in packs:
            nomos_meta = (pack.data or {}).get("nomos")
            if not nomos_meta:
                continue  # OFS-direct / hand-ingested packs are not NOMOS feeds
            feeds.append({
                "feed_id": nomos_meta.get("feed_id"),
                "bundle_id": nomos_meta.get("bundle_id"),
                "version": pack.version,
                "status": pack.status,
                "ingested_at": pack.ingested_at,
            })
        return {"corpus": {
            "jurisdiction": {"country": project.country, "canton": project.canton, "commune": project.commune},
            "jurisdiction_chunks": len(juri_rows),
            "project_chunks": len(proj_rows),
            "embedded": embedded,
            "sources": len(sources),
            "by_tier": by_tier,
            "feeds": feeds,
        }}

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
        _iv, p = _external_scope(user, session)
        docs, access = _external_document_access(session, p, user)
        out = [_doc_dict(d, field_scope=access[d.id]["field_scope"],
                         access_level=access[d.id]["level"]) for d in docs]
        return {"documents": out, "count": len(out)}

    # ---- W11.B: attachments (upload OR external link) ----------------------- #
    # Uploaded files land under /data/attachments/<project_id>/<sha[:2]>/<sha>.
    # External links are stored as URLs with a provider tag (gdrive/onedrive/…).
    # The polymorphic owner (owner_kind, owner_id) lets every domain object
    # reuse the same plumbing — Documents, BRS, Permis, Mémoire, Checklist, Tâches.
    import hashlib as _hashlib
    # Env vars read per-request, NOT at app boot, so tests can monkeypatch them.
    def _upload_root() -> str:
        return os.environ.get("AEDIFICA_UPLOAD_ROOT", "/data/attachments")
    def _upload_cap() -> int:
        return int(os.environ.get("AEDIFICA_UPLOAD_MAX_BYTES", str(25 * 1024 * 1024)))

    def _att_dict(a: m.Attachment, project_id: str | None = None) -> dict:
        # download_path uses the string `project_id` (the API path param), NOT the
        # integer FK — those are two different identifiers.
        return {"id": a.id, "owner_kind": a.owner_kind, "owner_id": a.owner_id,
                "kind": a.kind, "title": a.title, "url": a.url, "file_ref": a.file_ref,
                "provider": a.provider, "mime": a.mime, "size_bytes": a.size_bytes,
                "sha256": a.sha256, "note": a.note, "created_by": a.created_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "download_path": (f"/api/projects/{project_id}/attachments/{a.id}/download"
                                  if (a.kind == "upload" and project_id) else None)}

    def _verify_owner(session, project_pk: int, owner_kind: str, owner_id: str) -> None:
        """Belt-and-suspenders: refuse attachments pointing at non-existent owners,
        and never let owner_id span two projects."""
        if owner_kind not in m.ATTACHMENT_OWNERS:
            raise _err(400, "BAD_OWNER_KIND", f"owner_kind must be one of {sorted(m.ATTACHMENT_OWNERS)}")
        kind_to_model = {"document": m.Document, "brs": m.BrsEntry, "checklist": m.ChecklistItem,
                         "task": m.Task, "capture": m.CaptureNote}
        Model = kind_to_model.get(owner_kind)
        if Model is None:
            return  # "permit" items are derived from the permit gabarit, no row to check
        try:
            owner_pk = int(owner_id)
        except (TypeError, ValueError):
            raise _err(400, "BAD_OWNER_ID", "owner_id must be the integer id of the row")
        row = session.query(Model).filter_by(id=owner_pk, project_id=project_pk).first()
        if row is None:
            raise _err(404, "OWNER_NOT_FOUND", f"{owner_kind} #{owner_id} not in this project")

    @app.get("/api/projects/{project_id}/attachments")
    def list_attachments(project_id: str, owner_kind: str | None = None, owner_id: str | None = None,
                         user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        q = session.query(m.Attachment).filter_by(project_id=p.id)
        if owner_kind:
            q = q.filter_by(owner_kind=owner_kind)
        if owner_id:
            q = q.filter_by(owner_id=str(owner_id))
        rows = q.order_by(m.Attachment.id.desc()).all()
        return {"attachments": [_att_dict(a, project_id) for a in rows]}

    @app.post("/api/projects/{project_id}/attachments/link", status_code=201)
    def create_link_attachment(project_id: str, body: dict, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        url = (body.get("url") or "").strip()
        title = (body.get("title") or "").strip()
        owner_kind = (body.get("owner_kind") or "").strip()
        owner_id = str(body.get("owner_id") or "").strip()
        require_access(user, p, _owner_surface(owner_kind), "write", session)
        if not url or not title:
            raise _err(400, "BAD_LINK", "url and title are required for a link attachment")
        if body.get("provider") and body["provider"] not in m.ATTACHMENT_PROVIDERS:
            raise _err(400, "BAD_PROVIDER", f"provider must be one of {sorted(m.ATTACHMENT_PROVIDERS)}")
        _verify_owner(session, p.id, owner_kind, owner_id)
        a = m.Attachment(project_id=p.id, owner_kind=owner_kind, owner_id=owner_id,
                         kind="link", title=title, url=url,
                         provider=body.get("provider") or "url", note=body.get("note"),
                         created_by=user.name or user.email)
        session.add(a); session.commit()
        return {"attachment": _att_dict(a, project_id)}

    @app.post("/api/projects/{project_id}/attachments/upload", status_code=201)
    def create_upload_attachment(project_id: str,
                                 owner_kind: str = Form(...), owner_id: str = Form(...),
                                 title: str = Form(...), note: str | None = Form(None),
                                 file: UploadFile = File(...),
                                 user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        require_access(user, p, _owner_surface(owner_kind), "write", session)
        _verify_owner(session, p.id, owner_kind, owner_id)
        # Stream + hash; refuse over the cap.
        h = _hashlib.sha256()
        size = 0
        chunks = []
        while True:
            chunk = file.file.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            cap = _upload_cap()
            if size > cap:
                raise _err(413, "TOO_LARGE", f"upload exceeds {max(cap // (1024*1024), 1)} MB cap")
            h.update(chunk)
            chunks.append(chunk)
        sha = h.hexdigest()
        dest_dir = os.path.join(_upload_root(), project_id, sha[:2])
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, sha)
        with open(dest_path, "wb") as f:
            for c in chunks:
                f.write(c)
        a = m.Attachment(project_id=p.id, owner_kind=owner_kind, owner_id=str(owner_id),
                         kind="upload", title=title, file_ref=dest_path,
                         provider="local", mime=file.content_type, size_bytes=size, sha256=sha,
                         note=note, created_by=user.name or user.email)
        session.add(a); session.commit()
        return {"attachment": _att_dict(a, project_id)}

    @app.get("/api/projects/{project_id}/attachments/{att_id}/download")
    def download_attachment(project_id: str, att_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        p = _project(session, user, project_id)
        a = session.query(m.Attachment).filter_by(project_id=p.id, id=att_id).first()
        if not a:
            raise _err(404, "NOT_FOUND", str(att_id))
        if a.kind != "upload" or not a.file_ref or not os.path.exists(a.file_ref):
            raise _err(404, "NO_PAYLOAD", "this attachment has no uploaded payload")
        from fastapi.responses import FileResponse
        return FileResponse(a.file_ref, media_type=a.mime or "application/octet-stream", filename=a.title)

    @app.delete("/api/projects/{project_id}/attachments/{att_id}")
    def delete_attachment(project_id: str, att_id: int, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.write")
        p = _project(session, user, project_id)
        a = session.query(m.Attachment).filter_by(project_id=p.id, id=att_id).first()
        if not a:
            raise _err(404, "NOT_FOUND", str(att_id))
        require_access(user, p, _owner_surface(a.owner_kind), "write", session)
        if a.kind == "upload" and a.file_ref and os.path.exists(a.file_ref):
            try:
                os.remove(a.file_ref)
            except OSError:
                pass
        session.delete(a); session.commit()
        return {"deleted": att_id}

    return app


# Uvicorn entry point: `uvicorn aedifica.api.app:app` (dev; AEDIFICA_CREATE_ALL=1 to create tables).
app = create_app(create_all=get_settings().create_all)
