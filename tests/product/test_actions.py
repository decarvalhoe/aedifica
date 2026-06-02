"""Runtime action loop: capabilities -> dry-run -> scoped approval -> execute -> ledger."""
from __future__ import annotations

OP = [{"op_id": "O1", "kind": "set_property", "target": "AC-SPACE-101", "before": "", "after": "office", "undo": "restore"}]


def _project(client, owner):
    client.post("/api/projects", json={"project_id": "P", "name": "P", "commune": "Lausanne"}, headers=owner["headers"])


def test_capabilities(client, owner):
    _project(client, owner)
    caps = client.get("/api/adapters/archicad_json/capabilities", headers=owner["headers"]).json()["capabilities"]
    assert caps["transaction"] is True and "set_properties" in caps["write"]
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
    # adapter_execution approval -> executes, leaves a mutating ledger row
    client.post("/api/projects/P/approvals", json={"scope": "adapter_execution", "basis": "go"}, headers=h)
    ex = client.post("/api/projects/P/adapter/execute", json={"transaction": txn}, headers=h).json()
    assert ex["executed"] is True
    led = client.get("/api/projects/P/ledger", headers=h).json()["ledger"]
    assert any(e["event_type"] == "adapter_execution" and e["mutating"] for e in led)
    assert any(e["event_type"] == "approval" and e["approval_scope"] == "adapter_execution" for e in led)
