"""Runtime action loop: capabilities -> dry-run -> scoped approval -> execute -> ledger."""
from __future__ import annotations

OP = [{"op_id": "O1", "kind": "set_property", "target": "AC-SPACE-101", "property": "RoomUsage", "before": "", "after": "office", "undo": "restore"}]


def _project(client, owner):
    client.post("/api/projects", json={"project_id": "P", "name": "P", "commune": "Lausanne"}, headers=owner["headers"])


def test_capabilities(client, owner):
    _project(client, owner)
    caps = client.get("/api/adapters/archicad_json/capabilities", headers=owner["headers"]).json()["capabilities"]
    assert caps["transaction"] is True and "set_properties" in caps["write"]
    assert caps["live_mutation"] is False and caps["execution_mode"] == "simulation"
    assert client.get("/api/adapters/nope/capabilities", headers=owner["headers"]).status_code == 404


def test_dry_run_no_mutation_and_ledger(client, owner):
    h = owner["headers"]
    _project(client, owner)
    dr = client.post("/api/projects/P/adapter/dry-run", json={"adapter_id": "archicad_json", "operations": OP}, headers=h).json()
    assert dr["transaction"]["status"] == "dry_run" and dr["mutated"] is False and dr["blocked"] is False
    led = client.get("/api/projects/P/ledger", headers=h).json()["ledger"]
    assert any(e["event_type"] == "adapter_dry_run" and e["mutating"] is False for e in led)


def test_execution_gated_by_scoped_approval(client, owner):
    h = owner["headers"]
    _project(client, owner)
    txn = client.post("/api/projects/P/adapter/dry-run", json={"adapter_id": "archicad_json", "operations": OP}, headers=h).json()["transaction"]
    # no approval -> blocked
    assert client.post("/api/projects/P/adapter/execute", json={"transaction": txn}, headers=h).json()["blocked"] is True
    # report approval never authorizes a mutation
    client.post("/api/projects/P/approvals", json={"scope": "report_review", "basis": "x"}, headers=h)
    assert client.post("/api/projects/P/adapter/execute", json={"transaction": txn}, headers=h).json()["executed"] is False
    # dry-run approval -> simulation only, with a non-mutating ledger row
    client.post("/api/projects/P/approvals", json={"scope": "adapter_dry_run", "basis": "go"}, headers=h)
    ex = client.post("/api/projects/P/adapter/execute", json={"transaction": txn}, headers=h).json()
    assert ex["executed"] is False and ex["simulated"] is True and ex["mutated"] is False
    led = client.get("/api/projects/P/ledger", headers=h).json()["ledger"]
    assert any(e["event_type"] == "adapter_simulation" and not e["mutating"] for e in led)
    assert any(e["event_type"] == "approval" and e["approval_scope"] == "adapter_dry_run" for e in led)


def test_dry_run_live_endpoint_inspects_read_only(client, owner, monkeypatch):
    """With an endpoint, the dry-run preview comes from the live bridge — still no mutation."""
    from aedifica.api import actions
    monkeypatch.setattr(actions._mbd, "live_product_info",
                        lambda ep, timeout=2.0: {"running": True, "product_info": {"name": "Archicad", "version": "REPLAY"}})
    monkeypatch.setattr(actions._mbd, "live_selected_elements",
                        lambda ep, timeout=2.0, required_properties=None: {
                            "source_model_version": "LIVE-1",
                            "selected_elements": [{
                                "element_id": "AC-SPACE-101",
                                "type": "Zone",
                                "classification": "IfcSpace",
                                "classifications_available": True,
                                "properties": {"RoomUsage": "meeting"},
                                "property_states": {"RoomUsage": {"status": "normal", "value": "meeting"}},
                                "properties_available": True,
                            }],
                            "unavailable_properties": {},
                            "error": None,
                        })
    _project(client, owner)
    r = client.post("/api/projects/P/adapter/dry-run",
                    json={"adapter_id": "archicad_json", "operations": OP, "adapter_endpoint": "http://127.0.0.1:8077"},
                    headers=owner["headers"]).json()
    assert r["mode"] == "live" and r["mutated"] is False
    assert r["preview"]["product"]["version"] == "REPLAY" and r["preview"]["model_version"] == "LIVE-1"
    assert r["transaction"]["operations"][0]["before"] == "meeting"


def test_dry_run_live_unreachable_falls_back(client, owner, monkeypatch):
    from aedifica.api import actions
    monkeypatch.setattr(actions._mbd, "live_product_info",
                        lambda ep, timeout=2.0: {"running": False, "error": "connection refused"})
    _project(client, owner)
    r = client.post("/api/projects/P/adapter/dry-run",
                    json={"adapter_id": "archicad_json", "operations": OP, "adapter_endpoint": "http://127.0.0.1:1"},
                    headers=owner["headers"]).json()
    assert r["mode"] == "fixture_fallback" and r["mutated"] is False


def test_dry_run_blocks_when_live_selection_enrichment_fails(client, owner, monkeypatch):
    from aedifica.api import actions

    monkeypatch.setattr(actions._mbd, "live_product_info",
                        lambda ep, timeout=2.0: {"running": True, "product_info": {"name": "Archicad", "version": 29}})
    monkeypatch.setattr(actions._mbd, "live_selected_elements",
                        lambda ep, timeout=2.0, required_properties=None: {
                            "source_model_version": None,
                            "selected_elements": [],
                            "error": "property values unavailable",
                        })
    _project(client, owner)
    r = client.post("/api/projects/P/adapter/dry-run",
                    json={"adapter_id": "archicad_json", "operations": OP, "adapter_endpoint": "http://127.0.0.1:8077"},
                    headers=owner["headers"]).json()

    assert r["mode"] == "live_error" and r["blocked"] is True
    assert r["preview"]["error"] == "property values unavailable"
