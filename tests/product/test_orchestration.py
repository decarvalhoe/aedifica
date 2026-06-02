"""Memory queries + per-phase next-step orchestration (north-star Q&A)."""
from __future__ import annotations


def _setup(client, owner):
    h = owner["headers"]
    client.post("/api/projects", json={"project_id": "P", "name": "P", "commune": "Lausanne"}, headers=h)
    client.post("/api/projects/P/intake", json={"query": "Place de la Palud, Lausanne", "live": False}, headers=h)
    return h


def test_memory_unknowns(client, owner):
    h = _setup(client, owner)
    u = client.get("/api/projects/P/memory/unknowns", headers=h).json()["unknowns"]
    assert u and all(c["state"] in {"unknown", "assumption"} for c in u)


def test_memory_source_resolves(client, owner):
    h = _setup(client, owner)
    s = client.get("/api/projects/P/memory/source/VD-OEREB", headers=h).json()
    assert s["source_id"] == "VD-OEREB" and (s["claims"] or s["sources"])


def test_unknown_memory_query_404(client, owner):
    h = _setup(client, owner)
    assert client.get("/api/projects/P/memory/nope", headers=h).status_code == 404


def test_decisions_after_approval(client, owner):
    h = _setup(client, owner)
    client.post("/api/projects/P/approvals", json={"scope": "report_review", "basis": "x"}, headers=h)
    d = client.get("/api/projects/P/memory/decisions", headers=h).json()["decisions"]
    assert any(x["event_type"] == "approval" and x["approval_scope"] == "report_review" for x in d)


def test_next_step_is_sourced_and_phase_aware(client, owner):
    h = _setup(client, owner)
    ns = client.get("/api/projects/P/next-step", headers=h).json()
    assert ns["claims_prediction"] is False and ns["steps"]
    assert any(s["kind"] == "resolve_unknown" for s in ns["steps"])
    ns33 = client.get("/api/projects/P/next-step?phase=33", headers=h).json()
    assert ns33["steps"] and all(s["phase"] == "33" for s in ns33["steps"])
