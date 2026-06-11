"""W23-5b — project-scaffold withdrawal (the « Neuchâtel (VD) » project purge).

Mirror of the w22-2b seed-pack rule, applied to projects: a scaffold created
by mistake is disposable; the moment a project carries user work, withdrawal
is refused and the refusal NAMES what it found. A seeded-but-untouched SIA
checklist is template, not work.
"""
from __future__ import annotations


def _create(client, h, pid, **extra):
    body = {"project_id": pid, "name": pid, "commune": "Lausanne", "canton": "VD"}
    body.update(extra)
    r = client.post("/api/projects", json=body, headers=h)
    assert r.status_code == 201, r.text
    return r


def test_scaffold_withdrawal_and_recreation(client, owner):
    h = owner["headers"]
    _create(client, h, "P-SCAF")
    r = client.delete("/api/projects/P-SCAF", headers=h)
    assert r.status_code == 200
    assert r.json()["withdrawn"] == "P-SCAF"
    assert "P-SCAF" not in client.get("/api/projects", headers=h).json()["projects"]
    # The id is free again — no tombstone, a scaffold leaves no trace.
    _create(client, h, "P-SCAF")


def test_seeded_untouched_checklist_does_not_block(client, owner):
    """The UI seeds the parametric checklist when an entry phase is picked at
    creation — that template alone must not make the scaffold immortal."""
    h = owner["headers"]
    _create(client, h, "P-CHK")
    r = client.post("/api/projects/P-CHK/checklist/seed", json={"entry_phase": "31"}, headers=h)
    assert r.status_code == 201 and r.json()["seeded"] > 0
    r = client.delete("/api/projects/P-CHK", headers=h)
    assert r.status_code == 200


def test_worked_checklist_blocks(client, owner):
    h = owner["headers"]
    _create(client, h, "P-CHKW")
    client.post("/api/projects/P-CHKW/checklist/seed", json={"entry_phase": "31"}, headers=h)
    items = client.get("/api/projects/P-CHKW/checklist", headers=h).json()["items"]
    r = client.patch(f"/api/projects/P-CHKW/checklist/{items[0]['id']}",
                     json={"status": "done"}, headers=h)
    assert r.status_code == 200
    r = client.delete("/api/projects/P-CHKW", headers=h)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "PROJECT_NOT_SCAFFOLD"
    assert "checklist travaillée" in detail["message"]


def test_substance_blocks_and_is_named(client, owner):
    h = owner["headers"]
    _create(client, h, "P-WORK")
    r = client.post("/api/projects/P-WORK/documents",
                    json={"official_name": "Plan de situation", "category": "plans"}, headers=h)
    assert r.status_code == 201, r.text
    r = client.delete("/api/projects/P-WORK", headers=h)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["code"] == "PROJECT_NOT_SCAFFOLD"
    assert "documents" in detail["message"]
    # Still listed, untouched.
    assert "P-WORK" in client.get("/api/projects", headers=h).json()["projects"]


def test_json_column_work_blocks(client, owner):
    """Work also lives in JSON columns on the project row (permit dossier,
    compliance/cost/site inputs) — seed_reports fills exactly those, so the
    reference project is immortal too."""
    h = owner["headers"]
    _create(client, h, "P-REP", seed_reports=True)
    r = client.delete("/api/projects/P-REP", headers=h)
    assert r.status_code == 409
    assert "dossier permis" in r.json()["detail"]["message"]
