"""W12.F — Foresight explainability + adversarial sparse-data tests.

Doctrine the suite enforces:
- /explain hydrates every basis entry with the LIVE row (not the cached
  ref string) so the architect can verify the source is real.
- Data-sparse contexts NEVER produce a fabricated number — the engine
  stays silent instead of inventing a confidence.
"""
from __future__ import annotations


def _project(client, h, pid="EX1", phase="32"):
    body = {"project_id": pid, "name": pid, "commune": "Lausanne", "phase_code": phase}
    client.post("/api/projects", json=body, headers=h)
    return pid


def _task(client, h, pid, **kw):
    body = {"title": "T", "priority": "p2"}; body.update(kw)
    return client.post(f"/api/projects/{pid}/tasks", json=body, headers=h).json()["task"]


# --- explainability -------------------------------------------------------


def test_explain_hydrates_basis_with_live_rows(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    for i in range(6):
        t = _task(client, h, pid, title=f"Hist {i}", estimate_hours=10, phase_code="32")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 18}, headers=h)
    _task(client, h, pid, title="Open", estimate_hours=8, phase_code="32")
    pp = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()["proposals"]
    p = next(x for x in pp if x["kind"] == "duration_adjust")
    explained = client.get(f"/api/projects/{pid}/foresight/explain/{p['id']}", headers=h).json()
    assert explained["rule"] == "duration_adjust"
    assert "comparable_count" in explained["confidence_formula"]
    assert len(explained["basis_hydrated"]) > 0
    # Every cited task source must resolve to a live row.
    resolved = [b for b in explained["basis_hydrated"] if b["source_kind"] == "task"]
    assert resolved
    for b in resolved:
        assert b["live_resolved"] is True
        assert b["live"]["title"].startswith("Hist")


def test_explain_404_on_unknown_proposal(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.get(f"/api/projects/{pid}/foresight/explain/99999", headers=h)
    assert r.status_code == 404


# --- adversarial sparse-data ----------------------------------------------


def test_no_duration_proposal_with_zero_comparables(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    _task(client, h, pid, title="Solo", estimate_hours=8, phase_code="32")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    assert all(p["kind"] != "duration_adjust" for p in r["proposals"])


def test_no_duration_proposal_with_4_comparables(client, owner):
    """Below the 5-min threshold: must stay silent, not produce a number."""
    h = owner["headers"]; pid = _project(client, h)
    for i in range(4):
        t = _task(client, h, pid, title=f"H{i}", estimate_hours=10, phase_code="32")
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 15}, headers=h)
    _task(client, h, pid, title="Open", estimate_hours=8, phase_code="32")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    assert all(p["kind"] != "duration_adjust" for p in r["proposals"])


def test_no_duration_proposal_when_ratios_are_within_noise(client, owner):
    """Even with enough comparables, if the median ratio is close to 1.0
    (within ±0.2), the engine stays silent — no need to retune."""
    h = owner["headers"]; pid = _project(client, h)
    for i in range(8):
        t = _task(client, h, pid, title=f"H{i}", estimate_hours=10, phase_code="32")
        # Mix actuals around 10 (ratio ~1.0)
        actual = [9.5, 10.5, 9.8, 10.2, 10.0, 9.9, 10.1, 10.3][i]
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": actual}, headers=h)
    _task(client, h, pid, title="Open", estimate_hours=8, phase_code="32")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    assert all(p["kind"] != "duration_adjust" for p in r["proposals"])


def test_no_cost_factor_without_archived_pairs(client, owner):
    """No project with both estimate AND actual cost → no cost_factor proposal."""
    h = owner["headers"]; pid = _project(client, h)
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    assert all(p["kind"] != "cost_factor" for p in r["proposals"])
