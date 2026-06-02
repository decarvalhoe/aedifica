"""Scoped approvals across reports, dossiers and adapters.

An approval is never a generic "yes". Each approval carries a scope, and an
action only proceeds when an approval matches the required scope. A report
approval can never authorize an adapter mutation; an adapter dry-run approval can
never authorize an execution.
"""
from __future__ import annotations

from datetime import datetime, timezone

SCOPES = {"report_review", "dossier_readiness", "adapter_dry_run", "adapter_execution"}

# An execution approval also covers a dry-run; nothing else cross-authorizes.
SCOPE_IMPLICATIONS = {
    "report_review": {"report_review"},
    "dossier_readiness": {"dossier_readiness"},
    "adapter_dry_run": {"adapter_dry_run"},
    "adapter_execution": {"adapter_execution", "adapter_dry_run"},
}


class ApprovalScopeError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_approval(approved_by: str, scope: str, basis: str, approved_at: str | None = None) -> dict:
    if scope not in SCOPES:
        raise ApprovalScopeError(f"unknown approval scope: {scope}")
    return {
        "approved_by": approved_by,
        "scope": scope,
        "basis": basis,
        "approved_at": approved_at or _now(),
    }


def authorizes(approval: dict, required_scope: str) -> bool:
    if not isinstance(approval, dict):
        return False
    granted = approval.get("scope")
    return required_scope in SCOPE_IMPLICATIONS.get(granted, set())


def check_scope(approval: dict, required_scope: str) -> tuple:
    """Return (ok, message). The message explains a denial clearly."""
    if required_scope not in SCOPES:
        return False, f"Unknown required scope: {required_scope}"
    if not isinstance(approval, dict) or not approval.get("scope"):
        return False, f"No approval present for required scope '{required_scope}'."
    granted = approval.get("scope")
    if authorizes(approval, required_scope):
        return True, f"Approval scope '{granted}' authorizes '{required_scope}'."
    return False, (
        f"Approval scope '{granted}' does NOT authorize '{required_scope}'. "
        f"A '{required_scope}' action requires an explicit '{required_scope}' approval."
    )


def require_scope(approval: dict, required_scope: str) -> dict:
    ok, message = check_scope(approval, required_scope)
    if not ok:
        raise ApprovalScopeError(message)
    return approval
