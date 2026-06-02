"""FastAPI product API tests (auth + CRUD + brief)."""
from __future__ import annotations


def test_health_is_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_requires_token(client):
    assert client.get("/api/projects").status_code == 401


def test_project_crud(client, owner):
    h = owner["headers"]
    assert client.get("/api/projects", headers=h).json() == {"projects": []}
    r = client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "Palud", "commune": "Lausanne"}, headers=h)
    assert r.status_code == 201 and r.json()["created"]["project_id"] == "DEMO-LAUSANNE-PALUD"
    assert client.get("/api/projects", headers=h).json()["projects"] == ["DEMO-LAUSANNE-PALUD"]
    assert client.get("/api/projects/DEMO-LAUSANNE-PALUD", headers=h).status_code == 200
    dup = client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "x", "commune": "Lausanne"}, headers=h)
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "PROJECT_EXISTS"
    nf = client.get("/api/projects/NOPE", headers=h)
    assert nf.status_code == 404 and nf.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_generate_brief_persists(client, owner):
    h = owner["headers"]
    client.post("/api/projects", json={"project_id": "DEMO-LAUSANNE-PALUD", "name": "Palud", "commune": "Lausanne"}, headers=h)
    r = client.post("/api/projects/DEMO-LAUSANNE-PALUD/brief", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["persisted"]["claims"] >= 1
    assert {"sourced", "unknown"}.issubset(set(body["claim_state_summary"]))
    assert body["project"]["claims"] >= 1 and body["project"]["sources"] >= 1
