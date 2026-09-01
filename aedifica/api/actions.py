"""Runtime action loop — the top-down half of ArchiOS in the product.

Productizes the engine's adapter contracts (E28) + ledger/approval (E27) over the
DB: capability discovery -> dry-run plan/diff -> scoped approval -> simulation or
execution gate -> ledger. The current Archicad path is read-only and never sends a
write command. Adapter-neutral (Archicad is the first thread, not identity).
"""
from __future__ import annotations

import copy

from aedifica import _bootstrap  # noqa: F401  (pilot engine on sys.path)

import adapter_capability as _cap  # noqa: E402
import adapter_transaction as _txn  # noqa: E402
import approval as _approval  # noqa: E402
import model_bridge_demo as _mbd  # noqa: E402

from ..db import models as m, repository


def _next_ledger_id(session, project) -> str:
    n = session.query(m.LedgerEntry).filter_by(project_id=project.id).count()
    return f"LED-{project.project_id}-{n + 1}"


def _actor(user) -> dict:
    return {"name": user.email, "role": user.role}


def capabilities(adapter_id: str) -> dict:
    capabilities = copy.deepcopy(_cap.load_manifest(adapter_id).get("capabilities", {}))
    if adapter_id == "archicad_json":
        capabilities["live_mutation"] = False
        capabilities["execution_mode"] = "simulation"
    return capabilities


def _requested_properties(operations: list) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            operation.get("property") or operation.get("property_name")
            for operation in operations
            if operation.get("kind") == "set_property"
            and (operation.get("property") or operation.get("property_name"))
        )
    )


def _hydrate_live_before_values(operations: list, selection: dict) -> tuple[list, str | None]:
    selected = {
        item.get("element_id"): item
        for item in selection.get("selected_elements") or []
        if item.get("element_id")
    }
    hydrated = copy.deepcopy(operations)
    for operation in hydrated:
        target = selected.get(operation.get("target"))
        if target is None:
            return hydrated, f"operation target {operation.get('target')!r} is not in the live selection"
        if operation.get("kind") == "set_property":
            property_name = operation.get("property") or operation.get("property_name")
            state = (target.get("property_states") or {}).get(property_name, {})
            if state.get("status") not in {"normal", "userUndefined"}:
                return hydrated, f"property {property_name!r} has no readable live value"
            operation["before"] = (target.get("properties") or {}).get(property_name)
        elif operation.get("kind") == "set_category":
            operation["before"] = target.get("classification")
        else:
            return hydrated, f"operation {operation.get('kind')!r} has no read-only live preview"
    return hydrated, None


def dry_run(session, project, user, adapter_id: str, operations: list, endpoint: str | None = None) -> dict:
    """Build a dry-run transaction + before/after preview; persist a ledger row. No mutation.

    When ``endpoint`` is given, the preview inspects the **live** Archicad bridge
    (read-only: product info + selected elements), falling back to fixtures when
    the bridge is unreachable. Mutation never happens here.
    """
    manifest = _cap.load_manifest(adapter_id)  # raises AdapterCapabilityError on unknown adapter
    txn_id = f"TXN-{project.project_id}-{session.query(m.LedgerEntry).filter_by(project_id=project.id).count() + 1}"
    operations = copy.deepcopy(operations)

    # Read-only inspection: live endpoint if provided + reachable, else fixtures.
    mode, product, live_error = "fixture", None, None
    if endpoint:
        info = _mbd.live_product_info(endpoint)
        if info.get("running"):
            mode, product = "live", info.get("product_info")
            selection = _mbd.live_selected_elements(
                endpoint,
                required_properties=_requested_properties(operations),
            )
            live_error = _mbd.selection_problem(selection)
            if not live_error:
                operations, live_error = _hydrate_live_before_values(operations, selection)
            if live_error:
                mode = "live_error"
        else:
            mode = "fixture_fallback"
            selection = _mbd.inspect_selected_elements()
    else:
        selection = _mbd.inspect_selected_elements()
    transaction = _txn.build_transaction(adapter_id, operations, txn_id, "dry_run")
    if live_error:
        transaction["status"] = "blocked"
        transaction["blocked_reason"] = live_error
    audit = _mbd.missing_metadata_audit(selection)
    preview = {
        "mode": mode,
        "product": product,
        "model_version": selection.get("source_model_version"),
        "selected_count": len(selection.get("selected_elements", [])),
        "missing_metadata": audit.get("missing_count"),
        "error": live_error,
    }

    entry = repository.save_ledger_entry(
        session,
        project,
        {
            "ledger_id": _next_ledger_id(session, project),
            "event_type": "adapter_dry_run",
            "summary": f"Dry-run {txn_id} on {adapter_id} ({len(operations)} op) · {mode}",
            "actor": _actor(user),
            "phase": {"phase_code": project.phase_code},
            "mutating": False,
        },
    )
    return {
        "adapter_id": adapter_id,
        "capabilities": capabilities(adapter_id),
        "transaction": transaction,
        "blocked": _txn.is_blocked(transaction),
        "preview": preview,
        "mode": mode,
        "ledger_id": entry.ledger_id,
        "mutated": False,
    }


def create_approval(session, project, user, scope: str, basis: str) -> dict:
    """Persist a scoped approval as a ledger row + Approval child. Validates the scope."""
    approval = _approval.make_approval(user.email, scope, basis)  # raises on unknown scope
    entry = repository.save_ledger_entry(
        session,
        project,
        {
            "ledger_id": _next_ledger_id(session, project),
            "event_type": "approval",
            "summary": f"Approval granted for scope {scope}",
            "actor": _actor(user),
            "phase": {"phase_code": project.phase_code},
            "approval": approval,
        },
    )
    return {"ledger_id": entry.ledger_id, "scope": scope}


def has_approval(session, project, required_scope: str) -> bool:
    rows = (
        session.query(m.Approval)
        .join(m.LedgerEntry, m.Approval.ledger_entry_id == m.LedgerEntry.id)
        .filter(m.LedgerEntry.project_id == project.id)
        .all()
    )
    return any(_approval.authorizes({"scope": a.scope}, required_scope) for a in rows)


def execute(session, project, user, transaction: dict) -> dict:
    """Simulate Archicad transactions; execute other adapters only with approval."""
    if transaction.get("adapter_id") == "archicad_json":
        if _txn.is_blocked(transaction):
            return {
                "executed": False,
                "simulated": False,
                "blocked": True,
                "reason": transaction.get("blocked_reason") or "the Archicad preview is blocked",
            }
        if not has_approval(session, project, "adapter_dry_run"):
            return {
                "executed": False,
                "simulated": False,
                "blocked": True,
                "reason": "no adapter_dry_run approval; live Archicad mutation is not implemented",
            }
        simulation_approval = _approval.make_approval(user.email, "adapter_dry_run", "runtime simulation")
        repository.save_ledger_entry(
            session,
            project,
            {
                "ledger_id": _next_ledger_id(session, project),
                "event_type": "adapter_simulation",
                "summary": f"Simulated {transaction.get('transaction_id')} on archicad_json; no write command sent",
                "actor": _actor(user),
                "phase": {"phase_code": project.phase_code},
                "mutating": False,
                "approval": simulation_approval,
            },
        )
        return {"executed": False, "simulated": True, "blocked": False, "mutated": False}
    if not has_approval(session, project, "adapter_execution"):
        return {
            "executed": False,
            "blocked": True,
            "reason": "no adapter_execution approval — report/dry-run approvals never authorize a mutation",
        }
    execution_approval = _approval.make_approval(user.email, "adapter_execution", "runtime execution")
    approved = _txn.authorize_execution(transaction, execution_approval)
    done = _txn.execute(approved)
    repository.save_ledger_entry(
        session,
        project,
        {
            "ledger_id": _next_ledger_id(session, project),
            "event_type": "adapter_execution",
            "summary": f"Executed {done.get('transaction_id')} on {done.get('adapter_id')}",
            "actor": _actor(user),
            "phase": {"phase_code": project.phase_code},
            "mutating": True,
            "approval": execution_approval,
        },
    )
    return {"executed": True, "blocked": False, "verification": done.get("verification")}


def ledger(session, project) -> list:
    rows = session.query(m.LedgerEntry).filter_by(project_id=project.id).order_by(m.LedgerEntry.id).all()
    return [
        {
            "ledger_id": e.ledger_id,
            "event_type": e.event_type,
            "summary": e.summary,
            "actor": {"name": e.actor_name, "role": e.actor_role},
            "phase_code": e.phase_code,
            "mutating": e.mutating,
            "approval_scope": e.approval.scope if e.approval else None,
        }
        for e in rows
    ]
