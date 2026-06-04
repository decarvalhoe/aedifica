"""Runtime action loop — the top-down half of ArchiOS in the product.

Productizes the engine's adapter contracts (E28) + ledger/approval (E27) over the
DB: capability discovery -> dry-run plan/diff -> scoped approval -> execution gate
-> ledger. Nothing mutates without an adapter_execution approval; every step
leaves a ledger row. Adapter-neutral (Archicad is the first thread, not identity).
"""
from __future__ import annotations

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
    return _cap.load_manifest(adapter_id).get("capabilities", {})


def dry_run(session, project, user, adapter_id: str, operations: list, endpoint: str | None = None) -> dict:
    """Build a dry-run transaction + before/after preview; persist a ledger row. No mutation.

    When ``endpoint`` is given, the preview inspects the **live** Archicad bridge
    (read-only: product info + selected elements), falling back to fixtures when
    the bridge is unreachable. Mutation never happens here.
    """
    manifest = _cap.load_manifest(adapter_id)  # raises AdapterCapabilityError on unknown adapter
    txn_id = f"TXN-{project.project_id}-{session.query(m.LedgerEntry).filter_by(project_id=project.id).count() + 1}"
    transaction = _txn.build_transaction(adapter_id, operations, txn_id, "dry_run")

    # Read-only inspection: live endpoint if provided + reachable, else fixtures.
    mode, product = "fixture", None
    if endpoint:
        info = _mbd.live_product_info(endpoint)
        if info.get("running"):
            mode, product = "live", info.get("product_info")
            selection = _mbd.live_selected_elements(endpoint)
        else:
            mode = "fixture_fallback"
            selection = _mbd.inspect_selected_elements()
    else:
        selection = _mbd.inspect_selected_elements()
    audit = _mbd.missing_metadata_audit(selection)
    preview = {
        "mode": mode,
        "product": product,
        "model_version": selection.get("source_model_version"),
        "selected_count": len(selection.get("selected_elements", [])),
        "missing_metadata": audit.get("missing_count"),
    }

    entry = repository.save_ledger_entry(
        session,
        project,
        {
            "ledger_id": _next_ledger_id(session, project),
            "event_type": "adapter_dry_run",
            "summary": f"Dry-run {txn_id} on {adapter_id} ({len(operations)} op){' · live' if mode == 'live' else ''}",
            "actor": _actor(user),
            "phase": {"phase_code": project.phase_code},
            "mutating": False,
        },
    )
    return {
        "adapter_id": adapter_id,
        "capabilities": manifest.get("capabilities", {}),
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
    """Execute a transaction only if the project holds an adapter_execution approval."""
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
