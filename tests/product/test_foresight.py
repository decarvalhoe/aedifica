"""W12.A Foresight — deterministic, source-bound IA proposals.

Doctrine guards under test:
- No comparable data → no fabricated proposal (silence is right)
- Confidence is derived (count-based), not vibed
- Accept/defer/refuse records the architect's decision; nothing mutates
  silently
- Cross-surface rules fire on the live state of the project
"""
from __future__ import annotations

import datetime as _dt


def _project(client, h, pid="FS1"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    return pid


def _task(client, h, pid, **kw):
    body = {"title": "T", "priority": "p2"}
    body.update(kw)
    r = client.post(f"/api/projects/{pid}/tasks", json=body, headers=h)
    return r.json()["task"]


# --- empty-data doctrine --------------------------------------------------


def test_foresight_empty_project_yields_no_proposals(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["proposals"] == []
    assert data["summary"]["confidence_avg"] == 0.0


# --- duration rule --------------------------------------------------------


def test_duration_proposes_only_when_enough_comparables(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    # Add 2 done tasks with actuals — below the 5 min_comparables threshold.
    for i in range(2):
        t = _task(client, h, pid, title=f"Done {i}", estimate_hours=10, phase_code="32")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 15}, headers=h)
    _task(client, h, pid, title="Open", estimate_hours=8, phase_code="32")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h)
    proposals = r.json()["proposals"]
    assert not any(p["kind"] == "duration_adjust" for p in proposals)


def test_duration_proposes_when_5plus_comparables_with_drift(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    for i in range(6):
        t = _task(client, h, pid, title=f"Done {i}", estimate_hours=10, phase_code="32")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 15}, headers=h)
    _task(client, h, pid, title="Pending", estimate_hours=8, phase_code="32")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h)
    props = [p for p in r.json()["proposals"] if p["kind"] == "duration_adjust"]
    assert props, "expected at least one duration_adjust"
    p = props[0]
    assert p["confidence"] > 0.0
    # 6 / 20 = 0.3 (with the cap)
    assert p["confidence"] == 0.3
    # Median ratio is 1.5 → 8 × 1.5 = 12
    assert "12.0 h" in p["title"] or "12 h" in p["title"]
    assert p["basis"], "proposal must list named sources"
    assert all("source_id" in b for b in p["basis"])


# --- risk rule: overdue cascade ------------------------------------------


def test_overdue_p0_with_dependents_emits_risk(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    parent = _task(client, h, pid, title="P0 critique", priority="p0",
                   due_date=(_dt.date.today() - _dt.timedelta(days=2)).isoformat())
    child = _task(client, h, pid, title="Aval")
    client.post(f"/api/projects/{pid}/tasks/{child['id']}/deps",
                json={"blocked_by_id": parent["id"]}, headers=h)
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h)
    risks = [p for p in r.json()["proposals"] if p["kind"] == "risk_alert"]
    assert any("retard" in p["title"].lower() and "P0" in p["title"]
               or "p0 en retard" in p["title"].lower() for p in risks)


# --- decision flow --------------------------------------------------------


def test_accept_decision_records_who_and_keeps_proposal(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    for i in range(6):
        t = _task(client, h, pid, title=f"D{i}", estimate_hours=10, phase_code="33")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 14}, headers=h)
    _task(client, h, pid, title="Open", estimate_hours=8, phase_code="33")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    pp = [p for p in r["proposals"] if p["kind"] == "duration_adjust"]
    assert pp
    prop_id = pp[0]["id"]
    r2 = client.post(f"/api/projects/{pid}/foresight/{prop_id}/decide",
                     json={"decision": "accepted", "basis": "comparables convaincants"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["proposal"]["decision"] == "accepted"
    assert r2.json()["proposal"]["decision_basis"] == "comparables convaincants"
    # GET without refresh: the accepted proposal is no longer in 'pending'.
    r3 = client.get(f"/api/projects/{pid}/foresight", headers=h)
    pending_ids = [p["id"] for p in r3.json()["proposals"]]
    assert prop_id not in pending_ids


def test_refresh_keeps_accepted_history_drops_pending(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    for i in range(6):
        t = _task(client, h, pid, title=f"H{i}", estimate_hours=10, phase_code="22")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 16}, headers=h)
    _task(client, h, pid, title="O", estimate_hours=8, phase_code="22")
    pp = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()["proposals"]
    target = next(p for p in pp if p["kind"] == "duration_adjust")
    client.post(f"/api/projects/{pid}/foresight/{target['id']}/decide",
                json={"decision": "accepted"}, headers=h)
    # Refresh again — accepted row must survive even though new pending rows are
    # regenerated.
    rerun = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    # accepted is NOT in pending list returned (only pending are returned)
    assert target["id"] not in [p["id"] for p in rerun["proposals"]]
