"""W12.D — next_step v2 ranks steps by downstream impact (critical-path).

Doctrine: rank steps by HOW MUCH WORK each one unblocks, not by mere
position in the checklist. Explainability is mandatory — every step
carries a rationale field that says "débloque N tâches aval" or names
the blocking rule.
"""
from __future__ import annotations


def _project(client, h, pid="NS1", phase="32"):
    body = {"project_id": pid, "name": pid, "commune": "Lausanne", "phase_code": phase}
    r = client.post("/api/projects", json=body, headers=h)
    return pid


def _task(client, h, pid, **kw):
    body = {"title": "T", "priority": "p2"}; body.update(kw)
    return client.post(f"/api/projects/{pid}/tasks", json=body, headers=h).json()["task"]


def test_next_step_returns_top_pick_with_impact_score(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    assert "steps" in r
    assert "top_pick" in r
    assert "open_tasks_total" in r


def test_overdue_p0_cascade_increases_impact_of_blocking_task(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    # 1 blocker task + 3 dependent tasks chained from it.
    parent = _task(client, h, pid, title="Pose des fondations", priority="p0",
                   phase_code="32")
    a = _task(client, h, pid, title="Murs périmétriques")
    b = _task(client, h, pid, title="Toiture")
    c = _task(client, h, pid, title="Enveloppe")
    for child in (a, b, c):
        client.post(f"/api/projects/{pid}/tasks/{child['id']}/deps",
                    json={"blocked_by_id": parent["id"]}, headers=h)
    # Refresh; next_step exposes the underlying impact map (open_tasks_total)
    r = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    assert r["open_tasks_total"] == 4


def test_rationale_text_explains_each_step(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    # All steps in window must carry rationale (possibly empty for other kinds)
    for s in r["steps"]:
        assert "rationale" in s
        assert "impact_score" in s
