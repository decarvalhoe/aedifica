"""W11 P0: PATCH /api/projects/{id} updates phase_code so the top phase rail
can actually switch the project from one SIA sub-phase to another."""
from __future__ import annotations


def _project(client, h, pid="W11P"):
    client.post("/api/projects", json={"project_id": pid, "name": "W11", "commune": "Lausanne"}, headers=h)
    return pid


def test_patch_project_phase_code_changes_phase_and_coordination_follows(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    # Default phase is "0"; seeding the checklist at 21 produces phase 11 retroactive.
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "21"}, headers=h)
    assert client.get(f"/api/projects/{pid}", headers=h).json()["project"]["phase_code"] == "0"
    # Switch to phase 32 — projet de l'ouvrage.
    r = client.patch(f"/api/projects/{pid}", json={"phase_code": "32"}, headers=h).json()
    assert r["project"]["phase_code"] == "32"
    # Now /coordination must reflect the new phase (external blockers count etc.).
    coord = client.get(f"/api/projects/{pid}/coordination", headers=h).json()
    assert coord["project"]["phase_code"] == "32"
    # Switching to a phase past steps converts them to external blockers when not done.
    assert coord["blockers"]["counts"]["external"] >= 1


def test_patch_project_rejects_unknown_phase(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "W11Q")
    r = client.patch(f"/api/projects/{pid}", json={"phase_code": "99"}, headers=h)
    assert r.status_code == 400
    body = r.json()
    assert body["detail"]["code"] == "BAD_PHASE"


def test_patch_project_phase_requires_write_capability(client, owner):
    """A viewer (project.read only) cannot move the project's phase."""
    h_owner = owner["headers"]
    pid = _project(client, h_owner, "W11R")
    # Add a viewer
    r = client.post("/api/orgs/users", json={"email": "v@x.ch", "name": "V", "role": "viewer"},
                    headers=h_owner).json()
    h_viewer = {"Authorization": f"Bearer {r['token']}"}
    # GET allowed
    assert client.get(f"/api/projects/{pid}", headers=h_viewer).status_code == 200
    # PATCH forbidden
    assert client.patch(f"/api/projects/{pid}", json={"phase_code": "32"}, headers=h_viewer).status_code == 403
