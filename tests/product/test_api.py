"""FastAPI product API tests (in-memory SQLite, shared via StaticPool)."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402
from aedifica.db import Base  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
    )
    Base.metadata.create_all(engine)
    return TestClient(create_app(engine=engine))


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_project_crud(client):
    assert client.get("/api/projects").json() == {"projects": []}
    r = client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "Palud", "commune": "Lausanne"})
    assert r.status_code == 201 and r.json()["created"]["project_id"] == "DEMO-LAUSANNE-PALUD"
    assert client.get("/api/projects").json()["projects"] == ["DEMO-LAUSANNE-PALUD"]
    assert client.get("/api/projects/DEMO-LAUSANNE-PALUD").status_code == 200
    # duplicate -> structured 409
    dup = client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "x", "commune": "Lausanne"})
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "PROJECT_EXISTS"
    # unknown -> structured 404
    nf = client.get("/api/projects/NOPE")
    assert nf.status_code == 404 and nf.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_generate_brief_persists(client):
    client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "Palud", "commune": "Lausanne"})
    r = client.post("/api/projects/DEMO-LAUSANNE-PALUD/brief")
    assert r.status_code == 200
    body = r.json()
    assert body["persisted"]["claims"] >= 1
    assert {"sourced", "unknown"}.issubset(set(body["claim_state_summary"]))
    assert body["project"]["claims"] >= 1 and body["project"]["sources"] >= 1
