"""Auth: token requirement, tenant isolation, capability gates."""
from __future__ import annotations

from aedifica.api import auth
from aedifica.db import make_session_factory, models as m


def test_capability_model():
    assert auth.has_capability("owner", "adapter.execute")
    assert auth.has_capability("member", "project.write")
    assert not auth.has_capability("viewer", "project.write")
    assert not auth.has_capability("member", "adapter.execute")


def test_password_hash_roundtrip():
    h = auth.hash_password("motdepasse1")
    assert h.startswith("pbkdf2_sha256$") and h != "motdepasse1"
    assert auth.verify_password("motdepasse1", h)
    assert not auth.verify_password("mauvais", h)
    assert not auth.verify_password("anything", None)  # no hash set
    assert not auth.verify_password("x", "garbage")  # malformed stored value


def test_register_with_password_then_login(client):
    reg = client.post(
        "/api/orgs",
        json={"org_name": "Atelier", "user_email": "owner@a.ch", "password": "motdepasse1"},
    ).json()
    # login returns the same session token, never the password
    lg = client.post("/api/auth/login", json={"email": "owner@a.ch", "password": "motdepasse1"})
    assert lg.status_code == 200
    body = lg.json()
    assert body["token"] == reg["token"] and body["role"] == "owner"
    # the token actually authorizes
    assert client.get("/api/projects", headers={"Authorization": f"Bearer {body['token']}"}).status_code == 200


def test_login_wrong_password_is_401(client):
    client.post("/api/orgs", json={"org_name": "Atelier", "user_email": "owner@a.ch", "password": "motdepasse1"})
    r = client.post("/api/auth/login", json={"email": "owner@a.ch", "password": "WRONG"})
    assert r.status_code == 401 and r.json()["detail"]["code"] == "BAD_CREDENTIALS"


def test_login_without_password_set_is_401(client):
    # back-compat: an atelier created without a password still works via token,
    # but email+password login must not succeed for it.
    client.post("/api/orgs", json={"org_name": "Legacy", "user_email": "legacy@a.ch"})
    assert client.post("/api/auth/login", json={"email": "legacy@a.ch", "password": "x"}).status_code == 401


def test_invited_member_can_login_with_password(client, owner):
    client.post(
        "/api/orgs/users",
        json={"email": "claire@a.ch", "name": "Claire", "role": "member", "password": "clairepass1"},
        headers=owner["headers"],
    )
    lg = client.post("/api/auth/login", json={"email": "claire@a.ch", "password": "clairepass1"})
    assert lg.status_code == 200 and lg.json()["role"] == "member"


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


def test_team_management(client, owner):
    h = owner["headers"]
    # owner sees themselves
    users = client.get("/api/orgs/users", headers=h).json()["users"]
    assert len(users) == 1 and users[0]["role"] == "owner" and users[0]["is_you"]
    # add a member -> gets a token
    add = client.post("/api/orgs/users", json={"email": "m@a.ch", "name": "Membre", "role": "member"}, headers=h).json()
    mid, mtoken = add["user"]["id"], add["token"]
    hm = {"Authorization": f"Bearer {mtoken}"}
    # the member cannot manage the team
    assert client.get("/api/orgs/users", headers=hm).status_code == 403
    # promote then demote
    assert client.patch(f"/api/orgs/users/{mid}", json={"role": "owner"}, headers=h).json()["user"]["role"] == "owner"
    assert client.patch(f"/api/orgs/users/{mid}", json={"role": "viewer"}, headers=h).status_code == 200
    # cannot demote the last owner
    me = next(u for u in client.get("/api/orgs/users", headers=h).json()["users"] if u["is_you"])
    assert client.patch(f"/api/orgs/users/{me['id']}", json={"role": "member"}, headers=h).status_code == 400


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
