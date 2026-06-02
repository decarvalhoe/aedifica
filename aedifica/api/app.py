"""FastAPI product API over the engine + SQL store.

Endpoints (single-org until multi-tenant auth lands in AED-128/#167):
    GET  /api/health
    GET  /api/projects
    POST /api/projects                       {project_id, name, commune, ...}
    GET  /api/projects/{project_id}
    POST /api/projects/{project_id}/brief    generate the parcel brief + persist

Errors are structured: HTTP status + {"detail": {"code", "message"}}.
"""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import Base, make_engine, make_session_factory, models as m, repository

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO_DIR = os.path.join(ROOT, "pilot", "projects", "demo_lausanne_palud")


class ProjectIn(BaseModel):
    project_id: str
    name: str
    commune: str = "Lausanne"
    country: str = "CH"
    canton: str = "VD"
    phase_code: str = "0"


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def create_app(engine=None, org_name: str = "Default Org", create_all: bool = False) -> FastAPI:
    app = FastAPI(title="Aedifica API", version="0.1.0")
    engine = engine or make_engine()
    if create_all:
        Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)

    def get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def _org(session: Session) -> m.Org:
        return repository.get_or_create_org(session, org_name)

    def _project(session: Session, project_id: str) -> m.Project:
        org = _org(session)
        project = session.query(m.Project).filter_by(org_id=org.id, project_id=project_id).first()
        if project is None:
            raise _err(404, "PROJECT_NOT_FOUND", project_id)
        return project

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/projects")
    def list_projects(session: Session = Depends(get_session)):
        org = _org(session)
        rows = session.query(m.Project).filter_by(org_id=org.id).order_by(m.Project.id).all()
        return {"projects": [p.project_id for p in rows]}

    @app.post("/api/projects", status_code=201)
    def create_project(body: ProjectIn, session: Session = Depends(get_session)):
        org = _org(session)
        if session.query(m.Project).filter_by(org_id=org.id, project_id=body.project_id).first():
            raise _err(409, "PROJECT_EXISTS", f"{body.project_id} already exists")
        project = repository.create_project(
            session, org.id, body.project_id, body.name,
            commune=body.commune, country=body.country, canton=body.canton, phase_code=body.phase_code,
        )
        session.commit()
        return {"created": repository.project_summary(session, project)}

    @app.get("/api/projects/{project_id}")
    def open_project(project_id: str, session: Session = Depends(get_session)):
        return {"project": repository.project_summary(session, _project(session, project_id))}

    @app.post("/api/projects/{project_id}/brief")
    def generate_brief(project_id: str, session: Session = Depends(get_session)):
        project = _project(session, project_id)
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

    return app


# Uvicorn entry point: `uvicorn aedifica.api.app:app` (dev; create tables once).
app = create_app(create_all=os.environ.get("AEDIFICA_CREATE_ALL") == "1")
