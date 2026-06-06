"""W9 P1 pilotage: tasks (priority / dependencies / blocking), SIA fee estimate,
historical prediction, cross-project collision."""
from __future__ import annotations


def _project(client, h, pid="PP"):
    client.post("/api/projects", json={"project_id": pid, "name": "T", "commune": "Lausanne"}, headers=h)
    return pid


def test_task_priority_deps_and_blocking(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    a = client.post(f"/api/projects/{pid}/tasks", json={"title": "Plans", "priority": "p0", "estimate_hours": 8}, headers=h).json()["task"]
    b = client.post(f"/api/projects/{pid}/tasks", json={"title": "Permis", "priority": "p1"}, headers=h).json()["task"]
    client.post(f"/api/projects/{pid}/tasks/{b['id']}/deps", json={"blocked_by_id": a["id"]}, headers=h)
    lst = client.get(f"/api/projects/{pid}/tasks", headers=h).json()
    assert lst["summary"]["by_priority"]["p0"] == 1 and lst["summary"]["blocked"] == 1
    bb = next(t for t in lst["tasks"] if t["id"] == b["id"])
    assert bb["is_blocked"] and bb["blocked_by"] == [a["id"]]
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": "x", "priority": "p9"}, headers=h).status_code == 400
    assert client.post(f"/api/projects/{pid}/tasks/{a['id']}/deps", json={"blocked_by_id": a["id"]}, headers=h).status_code == 400
    # completing the blocker unblocks b
    done = client.patch(f"/api/projects/{pid}/tasks/{a['id']}", json={"status": "done", "actual_hours": 10}, headers=h).json()["task"]
    assert done["status"] == "done" and done["actual_hours"] == 10
    lst2 = client.get(f"/api/projects/{pid}/tasks", headers=h).json()
    assert next(t for t in lst2["tasks"] if t["id"] == b["id"])["is_blocked"] is False


def test_fee_estimate_two_methods(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    r = client.post(f"/api/projects/{pid}/fee-estimate",
                    json={"cfc2": 750000, "project_type": "villa", "hourly_rate": 150, "hours": 600}, headers=h).json()["estimate"]
    assert r["by_cost_method"] == round(750000 * 0.13)   # ≈ 97'500
    assert r["by_time_method"] == 150 * 600               # 90'000
    assert r["by_phase"]["32"] > 0 and r["recommended"] == r["by_cost_method"]


def test_predict_hours_from_atelier_history(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    for hours in (10, 14):
        t = client.post(f"/api/projects/{pid}/tasks", json={"title": "Plans d'exécution"}, headers=h).json()["task"]
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}", json={"status": "done", "actual_hours": hours}, headers=h)
    new = client.post(f"/api/projects/{pid}/tasks", json={"title": "Plans d'exécution étage"}, headers=h).json()["task"]
    pred = client.post(f"/api/projects/{pid}/tasks/{new['id']}/predict", headers=h).json()
    assert pred["prediction"] == 12.0 and pred["samples"] == 2 and pred["basis"] == "similar"


def test_atelier_collision_across_projects(client, owner):
    h = owner["headers"]
    for pid in ("PA", "PB"):
        _project(client, h, pid)
        client.post(f"/api/projects/{pid}/tasks", json={"title": "Gros rendu", "estimate_hours": 30, "due_date": "2026-07-03"}, headers=h)
    at = client.get("/api/atelier/tasks", headers=h).json()
    assert at["projects"] >= 2 and len(at["tasks"]) >= 2
    # 30h + 30h = 60h in one ISO week > 40h capacity → overloaded
    assert len(at["collision"]["overloaded"]) >= 1


def test_captures_friction_photo_regulation(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "PC")
    f = client.post(f"/api/projects/{pid}/captures", json={"kind": "friction", "content": "Le client a changé d'avis sur la cuisine"}, headers=h).json()["capture"]
    assert f["kind"] == "friction" and f["author"]  # author auto-set to the acting user
    client.post(f"/api/projects/{pid}/captures", json={"kind": "photo", "content": "Fissure mur nord", "source_ref": "https://x/p.jpg"}, headers=h)
    client.post(f"/api/projects/{pid}/captures", json={"kind": "regulation", "content": "PGA en révision — hauteurs à confirmer"}, headers=h)
    lst = client.get(f"/api/projects/{pid}/captures", headers=h).json()
    assert lst["by_kind"]["friction"] == 1 and lst["by_kind"]["photo"] == 1
    assert len(lst["regulation_alerts"]) == 1  # regulation watch surfaces separately (#231)
    assert client.post(f"/api/projects/{pid}/captures", json={"kind": "bogus", "content": "x"}, headers=h).status_code == 400
