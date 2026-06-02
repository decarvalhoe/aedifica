"""Drawing / model export intent contract.

Represents export intents (PDF, DWG, IFC, BCF, report) as dry-run action items
with capability checks and expected artifact refs. An export is blocked when the
adapter cannot produce it, a supported intent yields a dry-run artifact plan, and
no export is ever claimed executed without verification evidence. ``report`` is
an Aedifica-native export and is not adapter-gated.
"""
from __future__ import annotations

import adapter_capability as _capability

EXPORT_FORMATS = {"pdf", "dwg", "ifc", "bcf", "report"}
NATIVE_FORMATS = {"report"}


class ExportIntentError(ValueError):
    pass


def build_export_intent(adapter_id: str, export_format: str, target: str, intent_id: str) -> dict:
    if export_format not in EXPORT_FORMATS:
        raise ExportIntentError(f"unknown export format: {export_format}")

    base = {
        "intent_id": intent_id,
        "adapter_id": adapter_id,
        "format": export_format,
        "target": target,
        "mutating": False,
        "executed": False,
        "verified": False,
        "verification": None,
    }

    if export_format in NATIVE_FORMATS:
        base["status"] = "dry_run"
        base["expected_artifact_ref"] = f"exports/{intent_id}.{export_format}"
        base["dry_run_plan"] = {"native": True, "produces": export_format}
        return base

    manifest = _capability.load_manifest(adapter_id)
    if not _capability.supports(manifest, "export", export_format):
        base["status"] = "blocked"
        base["blocked_reason"] = f"adapter {adapter_id} cannot export {export_format}"
        base["expected_artifact_ref"] = None
        return base

    base["status"] = "dry_run"
    base["expected_artifact_ref"] = f"exports/{intent_id}.{export_format}"
    base["dry_run_plan"] = {"native": False, "produces": export_format, "adapter": adapter_id}
    return base


def is_blocked(intent: dict) -> bool:
    return intent.get("status") == "blocked"


def mark_executed(intent: dict, verification: dict) -> dict:
    """Mark an export executed only with verification evidence."""
    if is_blocked(intent):
        raise ExportIntentError(f"blocked export {intent.get('intent_id')} cannot be executed")
    if not verification or not verification.get("artifact_ref"):
        raise ExportIntentError(
            f"export {intent.get('intent_id')} cannot be claimed executed without verification evidence"
        )
    executed = dict(intent)
    executed["executed"] = True
    executed["verified"] = True
    executed["verification"] = verification
    return executed
