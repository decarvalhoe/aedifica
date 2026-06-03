"""Project report endpoints: permit / opposition / compliance (engine-backed)."""
from __future__ import annotations


def _project(client, owner):
    client.post("/api/projects", json={"project_id": "P", "name": "P", "commune": "Lausanne"}, headers=owner["headers"])


def test_permit_report(client, owner):
    _project(client, owner)
    r = client.get("/api/projects/P/permit", headers=owner["headers"])
    assert r.status_code == 200
    permit = r.json()["permit"]
    assert permit["state"] in {"draft", "missing_evidence", "ready_for_review", "architect_approved", "submitted_external"}
    assert permit["groups"] and permit["disclaimers"]


def test_opposition_report(client, owner):
    _project(client, owner)
    opp = client.get("/api/projects/P/opposition", headers=owner["headers"]).json()["opposition"]
    assert opp["claims_prediction"] is False and "signals" in opp and opp["overall"]


def test_compliance_report(client, owner):
    _project(client, owner)
    comp = client.get("/api/projects/P/compliance", headers=owner["headers"]).json()["compliance"]
    assert comp["legal"] and "summary" in comp
    assert any(g["domain"] == "bim" for g in comp["contractual"])


def test_cost_report(client, owner):
    _project(client, owner)
    cost = client.get("/api/projects/P/cost", headers=owner["headers"]).json()["cost"]
    assert cost["cockpit"]["estimated_fee_chf"] > 0 and cost["cockpit"]["margin_risk"] in {"low", "medium", "high"}
    assert cost["tender_assumptions"] and cost["quantity_rows"]


def test_site_report(client, owner):
    _project(client, owner)
    site = client.get("/api/projects/P/site", headers=owner["headers"]).json()["site"]
    assert site["handover"] and site["defects"]
    assert site["summary"]["handover_blocked"] >= 1


def test_reports_require_auth(client, owner):
    _project(client, owner)
    assert client.get("/api/projects/P/permit").status_code == 401
