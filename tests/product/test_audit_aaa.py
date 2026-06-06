"""W11.F AAA — audit log, token rotation, external scoping.

Doctrine: cross-project security events (invitations, token rotations,
revocations) live in a dedicated AuditEvent table (append-only, never
edited). External users only see documents they have an AccessGrant on
via their linked intervenant — never the full list.
"""
from __future__ import annotations


def _project(client, h, pid="AAA1"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    return pid


def _intervenant(client, h, pid="AAA1", name="Étienne Test", role="architecte"):
    r = client.post(f"/api/projects/{pid}/intervenants",
                    json={"name": name, "role": role}, headers=h)
    assert r.status_code in (200, 201), r.text
    return r.json()["intervenant"]


def _doc(client, h, pid, name="Plan PDF"):
    r = client.post(f"/api/projects/{pid}/documents",
                    json={"official_name": name, "category": "general"}, headers=h)
    return r.json()["document"]


# --- token rotation -------------------------------------------------------


def test_rotate_token_returns_new_token_and_invalidates_old(client, owner):
    h = owner["headers"]; old = owner["token"]
    r = client.post("/api/auth/me/rotate-token", headers=h)
    assert r.status_code == 200, r.text
    new = r.json()["token"]
    assert new and new != old
    # Old token no longer works.
    r2 = client.get("/api/projects", headers=h)
    assert r2.status_code == 401
    # New token works.
    r3 = client.get("/api/projects", headers={"Authorization": f"Bearer {new}"})
    assert r3.status_code == 200


def test_revoke_token_signs_out(client, owner):
    r = client.post("/api/auth/me/revoke-token", headers=owner["headers"])
    assert r.status_code == 200
    assert r.json()["revoked"] is True
    r2 = client.get("/api/projects", headers=owner["headers"])
    assert r2.status_code == 401


def test_rotate_logs_audit_event(client, owner):
    client.post("/api/auth/me/rotate-token", headers=owner["headers"])
    # Use the now-rotated token via owner's email + password? owner has no pw.
    # Easier: query the audit log via a fresh owner.
    # Re-bootstrap a second org so we have a known-good auth header.
    # Instead, since rotate-token returns the new token, capture it.
    pass  # covered by the rotate-then-list test below


def test_rotate_then_org_audit_shows_token_rotated(client, owner):
    new_token = client.post("/api/auth/me/rotate-token", headers=owner["headers"]).json()["token"]
    h2 = {"Authorization": f"Bearer {new_token}"}
    r = client.get("/api/orgs/audit", headers=h2)
    assert r.status_code == 200
    events = r.json()["events"]
    kinds = {e["event_type"] for e in events}
    assert "token_rotated" in kinds


# --- invite + redeem + audit ----------------------------------------------


def test_invite_then_accept_logs_audit(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    iv = _intervenant(client, h)
    r = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                    json={"email": "etienne@ext.ch", "name": "Étienne"}, headers=h)
    assert r.status_code == 201
    token = r.json()["invite_token"]
    # Accept invite
    r2 = client.post("/api/auth/accept-invite",
                     json={"token": token, "password": "motdepasse2"})
    assert r2.status_code == 200
    # Org audit should show both events.
    audit = client.get("/api/orgs/audit", headers=h).json()
    kinds = [e["event_type"] for e in audit["events"]]
    assert "invite_issued" in kinds
    assert "invite_redeemed" in kinds
    assert "password_set" in kinds


# --- grant/revoke audit ----------------------------------------------------


def test_grant_and_revoke_access_log_events(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    iv = _intervenant(client, h)
    d = _doc(client, h, pid)
    g = client.post(f"/api/projects/{pid}/documents/{d['id']}/grants",
                    json={"intervenant_id": iv["id"], "level": "read"}, headers=h)
    assert g.status_code == 201
    gid = g.json()["document"]["grants"][0]["id"]
    client.delete(f"/api/projects/{pid}/documents/{d['id']}/grants/{gid}", headers=h)
    audit = client.get(f"/api/projects/{pid}/audit", headers=h).json()
    kinds = [e["event_type"] for e in audit["events"]]
    assert "access_granted" in kinds
    assert "access_revoked" in kinds


# --- external scoping ------------------------------------------------------


def test_external_sees_only_granted_documents(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    iv = _intervenant(client, h, name="Externe", role="entreprise")
    d_secret = _doc(client, h, pid, name="Cost-secret")
    d_shared = _doc(client, h, pid, name="Plan-shared")
    # Grant only the shared one
    client.post(f"/api/projects/{pid}/documents/{d_shared['id']}/grants",
                json={"intervenant_id": iv["id"], "level": "read"}, headers=h)
    # Invite + accept
    inv = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "ext@x.ch", "name": "Externe"}, headers=h).json()
    tok = client.post("/api/auth/accept-invite",
                      json={"token": inv["invite_token"], "password": "pw01234"}).json()["token"]
    h_ext = {"Authorization": f"Bearer {tok}"}
    r = client.get(f"/api/projects/{pid}/documents", headers=h_ext)
    assert r.status_code == 200, r.text
    payload = r.json()
    names = [d["official_name"] for d in payload["documents"]]
    assert "Plan-shared" in names
    assert "Cost-secret" not in names
    assert payload.get("scoped") == "external"


def test_external_cannot_read_org_audit(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    iv = _intervenant(client, h, name="Externe2", role="entreprise")
    inv = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "ext2@x.ch", "name": "E2"}, headers=h).json()
    tok = client.post("/api/auth/accept-invite",
                      json={"token": inv["invite_token"], "password": "pw01234"}).json()["token"]
    r = client.get("/api/orgs/audit", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
