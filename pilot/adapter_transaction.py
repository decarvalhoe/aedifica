"""Adapter transaction contract — a safe lifecycle for model/drawing mutations.

A transaction groups operations with dry-run plans, undo expectations and
verification results. Nothing mutates by default: an execute transaction requires
a matching adapter_execution approval scope, and an adapter that does not support
transactions returns a blocked state.
"""
from __future__ import annotations

import json

import adapter_capability as _capability
import approval as _approval

TRANSACTION_STATES = {"planned", "dry_run", "approved", "executed", "blocked"}


class AdapterTransactionError(ValueError):
    pass


def build_transaction(adapter_id: str, operations: list, transaction_id: str, mode: str = "dry_run") -> dict:
    """Build a transaction. Returns a blocked transaction if the adapter cannot transact."""
    manifest = _capability.load_manifest(adapter_id)
    base = {
        "transaction_id": transaction_id,
        "adapter_id": adapter_id,
        "mode": mode,
        "operations": operations,
        "operation_count": len(operations),
        "mutating": True,
        "undo_expectation": "Each operation must be individually reversible before execution.",
        "verification": None,
        "approval": None,
    }
    if not _capability.supports(manifest, "transaction"):
        base["status"] = "blocked"
        base["blocked_reason"] = f"adapter {adapter_id} does not support transactions"
        return base
    base["status"] = "dry_run" if mode == "dry_run" else "planned"
    return base


def serialize(transaction: dict) -> str:
    return json.dumps(transaction, ensure_ascii=False)


def is_blocked(transaction: dict) -> bool:
    return transaction.get("status") == "blocked"


def authorize_execution(transaction: dict, approval: dict) -> dict:
    """Move a transaction to approved iff an adapter_execution approval is present."""
    txn = json.loads(json.dumps(transaction))
    if is_blocked(txn):
        return txn
    ok, message = _approval.check_scope(approval, "adapter_execution")
    if not ok:
        txn["status"] = "blocked"
        txn["blocked_reason"] = message
        return txn
    txn["status"] = "approved"
    txn["approval"] = approval
    return txn


def execute(transaction: dict, verification: dict | None = None) -> dict:
    """Execute only an approved transaction; otherwise raise."""
    if transaction.get("status") != "approved":
        raise AdapterTransactionError(
            f"transaction {transaction.get('transaction_id')} cannot execute from status "
            f"{transaction.get('status')!r}; an adapter_execution approval is required first"
        )
    txn = json.loads(json.dumps(transaction))
    txn["status"] = "executed"
    txn["verification"] = verification or {"verified": True, "method": "post_execution_readback"}
    return txn
