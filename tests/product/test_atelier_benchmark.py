"""W12.E — atelier-wide benchmark snapshots (learning loop)."""
from __future__ import annotations


def _project(client, h, pid="BM1"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    return pid


def _task(client, h, pid, **kw):
    body = {"title": "T", "priority": "p2"}; body.update(kw)
    return client.post(f"/api/projects/{pid}/tasks", json=body, headers=h).json()["task"]


def test_snapshot_with_no_data_returns_empty_ratios(client, owner):
    r = client.post("/api/orgs/benchmark/snapshot", json={"note": "first"}, headers=owner["headers"])
    assert r.status_code == 201
    bm = r.json()["benchmark"]
    assert bm["duration_ratios"] == {}
    assert bm["cost_factor"] is None
    assert bm["note"] == "first"


def test_snapshot_captures_phase_ratios(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    # 3 done tasks in phase 32 with ratio 1.5 (10 → 15)
    for i in range(3):
        t = _task(client, h, pid, title=f"T{i}", estimate_hours=10, phase_code="32")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 15}, headers=h)
    r = client.post("/api/orgs/benchmark/snapshot", headers=h).json()["benchmark"]
    assert r["duration_ratios"].get("32") == 1.5
    assert r["n_tasks_done"] == 3


def test_list_benchmarks_returns_most_recent_first(client, owner):
    h = owner["headers"]
    client.post("/api/orgs/benchmark/snapshot", json={"note": "a"}, headers=h)
    client.post("/api/orgs/benchmark/snapshot", json={"note": "b"}, headers=h)
    r = client.get("/api/orgs/benchmark", headers=h).json()
    assert r["total"] == 2
    assert r["benchmarks"][0]["note"] == "b"  # newer first


def test_latest_404_when_empty(client, owner):
    r = client.get("/api/orgs/benchmark/latest", headers=owner["headers"])
    assert r.status_code == 404


def test_latest_returns_most_recent_after_snapshot(client, owner):
    client.post("/api/orgs/benchmark/snapshot", json={"note": "fresh"}, headers=owner["headers"])
    r = client.get("/api/orgs/benchmark/latest", headers=owner["headers"]).json()
    assert r["benchmark"]["note"] == "fresh"
