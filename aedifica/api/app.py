"""FastAPI product API over the engine + SQL store (multi-tenant).

Auth: bootstrap an org+owner (`POST /api/orgs`) to get a bearer token, then send
`Authorization: Bearer <token>` on every other call. Projects are scoped to the
caller's org; mutations require a capability (see api.auth). Errors are
structured: HTTP status + {"detail": {"code", "message"}}.
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
from . import auth
from .config import get_settings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO_DIR = os.path.join(ROOT, "pilot", "projects", "demo_lausanne_palud")


class OrgIn(BaseModel):
    org_name: str
    user_email: str
    user_name: str = "Owner"


class ProjectIn(BaseModel):
    project_id: str
    name: str
    commune: str = "Lausanne"
    country: str = "CH"
    canton: str = "VD"
    phase_code: str = "0"


class IntakeIn(BaseModel):
    query: str
    live: bool = True


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
        session.add(m.User(org_id=org.id, email=body.user_email, name=body.user_name, role="owner", api_token=token))
        session.commit()
        return {"org_id": org.id, "user_email": body.user_email, "role": "owner", "token": token}

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
        session.commit()
        return {"created": repository.project_summary(session, project)}

    @app.get("/api/projects/{project_id}")
    def open_project(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"project": repository.project_summary(session, _project(session, user, project_id))}

    @app.get("/api/projects/{project_id}/claims")
    def project_claims(project_id: str, user: m.User = Depends(current_user), session: Session = Depends(get_session)):
        require(user, "project.read")
        return {"claims": repository.claims_for(session, _project(session, user, project_id))}

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
