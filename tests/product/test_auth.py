"""Auth: token requirement, tenant isolation, capability gates."""
from __future__ import annotations

from aedifica.api import auth
from aedifica.db import make_session_factory, models as m


def test_capability_model():
    assert auth.has_capability("owner", "adapter.execute")
    assert auth.has_capability("member", "project.write")
    assert not auth.has_capability("viewer", "project.write")
    assert not auth.has_capability("member", "adapter.execute")


def test_missing_or_bad_token_is_401(client):
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_tenant_isolation(client):
    t1 = client.post("/api/orgs", json={"org_name": "A", "user_email": "a@a.ch"}).json()["token"]
    t2 = client.post("/api/orgs", json={"org_name": "B", "user_email": "b@b.ch"}).json()["token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    client.post("/api/projects", json={"project_id": "P-A", "name": "A", "commune": "Lausanne"}, headers=h1)
    client.post("/api/projects", json={"project_id": "P-B", "name": "B", "commune": "Pully"}, headers=h2)
    assert client.get("/api/projects", headers=h1).json()["projects"] == ["P-A"]
    assert client.get("/api/projects", headers=h2).json()["projects"] == ["P-B"]
    # org A cannot see org B's project
    assert client.get("/api/projects/P-B", headers=h1).status_code == 404


def test_viewer_cannot_write(client, engine):
    with make_session_factory(engine)() as s:
        org = m.Org(name="Viewer Org")
        s.add(org)
        s.flush()
        s.add(m.User(org_id=org.id, email="v@v.ch", name="V", role="viewer", api_token="VIEWER-TOKEN"))
        s.commit()
    h = {"Authorization": "Bearer VIEWER-TOKEN"}
    assert client.get("/api/projects", headers=h).status_code == 200
    r = client.post("/api/projects", json={"project_id": "X", "name": "X", "commune": "Lausanne"}, headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "FORBIDDEN"
