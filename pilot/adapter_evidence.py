"""Link adapter evidence records into the project ledger.

A model/drawing dry-run produces an adapter evidence record (before snapshot,
dry-run plan, approval, verification) linked to the project, phase and selected
elements. The record is ledger-ready; execution stays blocked until an explicit
adapter_execution approval exists.
"""
from __future__ import annotations

import approval as _approval
import ledger_writer as _ledger_writer


def build_adapter_evidence(
    project_id: str,
    phase_code: str,
    action_id: str,
    adapter_id: str,
    selected_elements: list,
    before_snapshot_ref: str,
    dry_run_plan_ref: str,
    approval: dict | None = None,
    verification_ref: str | None = None,
) -> dict:
    evidence_refs = [
        {"evidence_id": f"{action_id}-before", "kind": "adapter_before_snapshot", "file_ref": before_snapshot_ref},
        {"evidence_id": f"{action_id}-dryrun", "kind": "adapter_dry_run_plan", "file_ref": dry_run_plan_ref},
    ]
    if verification_ref:
        evidence_refs.append({"evidence_id": f"{action_id}-verify", "kind": "adapter_verification", "file_ref": verification_ref})
    return {
        "action_id": action_id,
        "project_id": project_id,
        "phase": {"phase_code": phase_code},
        "adapter_id": adapter_id,
        "selected_elements": [el.get("element_id") if isinstance(el, dict) else el for el in selected_elements],
        "evidence": {
            "before_snapshot": before_snapshot_ref,
            "dry_run_plan": dry_run_plan_ref,
            "approval": approval,
            "verification": verification_ref,
        },
        "evidence_refs": evidence_refs,
        "dry_run_plan": dry_run_plan_ref,
    }


def can_execute(adapter_evidence: dict) -> tuple:
    """Return (allowed, message). Execution requires an adapter_execution approval."""
    approval = (adapter_evidence.get("evidence") or {}).get("approval")
    return _approval.check_scope(approval, "adapter_execution")


def to_ledger_entry(adapter_evidence: dict, actor: dict, ledger_id: str, timestamp: str | None = None) -> dict:
    return _ledger_writer.adapter_dry_run_entry(
        adapter_evidence["project_id"],
        adapter_evidence["phase"]["phase_code"],
        adapter_evidence,
        actor,
        ledger_id,
        timestamp=timestamp,
    )


def write_dry_run_to_ledger(project_dir: str, adapter_evidence: dict, actor: dict, ledger_id: str) -> dict:
    entry = to_ledger_entry(adapter_evidence, actor, ledger_id)
    return _ledger_writer.write_ledger_entry(project_dir, entry)
