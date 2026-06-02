"""Durable ledger writer for the project workspace.

Appends validated ledger entries to ``<project>/memory/ledger.json`` for report
generation, approvals and adapter dry-runs. Repeated actions append (never
overwrite); every entry validates against the ledger contract before it is
written, and carries actor, timestamp, input refs, output refs and a hash when
available.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os

import ledger

LEDGER_REL = os.path.join("memory", "ledger.json")


def ledger_path(project_dir: str) -> str:
    return os.path.join(project_dir, LEDGER_REL)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {"schema_version": ledger.LEDGER_VERSION, "entries": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_ledger_entry(project_dir: str, entry: dict) -> dict:
    """Validate and append a ledger entry. Raises on invalid or duplicate id."""
    ledger.validate_entry(entry)
    path = ledger_path(project_dir)
    data = _load(path)
    if any(e.get("ledger_id") == entry["ledger_id"] for e in data.get("entries", [])):
        raise ledger.LedgerValidationError(f"duplicate ledger_id {entry['ledger_id']}")
    data["schema_version"] = ledger.LEDGER_VERSION
    data.setdefault("entries", []).append(entry)
    _write(path, data)
    return entry


def read_ledger(project_dir: str) -> dict:
    return _load(ledger_path(project_dir))


def report_generation_entry(project_id: str, phase_code: str, report_entry: dict, actor: dict, ledger_id: str, timestamp: str | None = None) -> dict:
    return {
        "ledger_id": ledger_id,
        "timestamp": timestamp or _now(),
        "project_id": project_id,
        "event_type": "report_generation",
        "summary": f"Generated {report_entry.get('kind')} report {report_entry.get('report_id')}",
        "actor": actor,
        "phase": {"phase_code": phase_code},
        "basis": {
            "source_refs": report_entry.get("source_refs", []),
            "evidence_refs": [
                {
                    "evidence_id": report_entry.get("report_id"),
                    "kind": report_entry.get("kind"),
                    "file_ref": f"project://{report_entry.get('path')}",
                }
            ],
        },
        "inputs": {"report_id": report_entry.get("report_id")},
        "outputs": {"path": report_entry.get("path"), "content_sha256": report_entry.get("content_sha256")},
        "content_sha256": report_entry.get("content_sha256"),
    }


def approval_entry(project_id: str, phase_code: str, approval: dict, actor: dict, ledger_id: str, timestamp: str | None = None) -> dict:
    return {
        "ledger_id": ledger_id,
        "timestamp": timestamp or _now(),
        "project_id": project_id,
        "event_type": "approval",
        "summary": f"Approval granted for scope {approval.get('scope')}",
        "actor": actor,
        "phase": {"phase_code": phase_code},
        "basis": {"source_refs": [{"source_id": "ARCHITECT-DECISION", "locator": approval.get("scope"), "valid_as_of": approval.get("approved_at"), "confidence": "high"}]},
        "approval": approval,
        "inputs": {"scope": approval.get("scope")},
        "outputs": {},
    }


def adapter_dry_run_entry(project_id: str, phase_code: str, action: dict, actor: dict, ledger_id: str, timestamp: str | None = None) -> dict:
    return {
        "ledger_id": ledger_id,
        "timestamp": timestamp or _now(),
        "project_id": project_id,
        "event_type": "adapter_dry_run",
        "summary": f"Adapter dry-run {action.get('action_id')} on {action.get('adapter_id')}",
        "actor": actor,
        "phase": {"phase_code": phase_code},
        "basis": {"evidence_refs": action.get("evidence_refs", [{"evidence_id": action.get("action_id"), "kind": "adapter_dry_run", "file_ref": "memory://dry_run"}])},
        "inputs": {"action_id": action.get("action_id"), "selected_elements": action.get("selected_elements", [])},
        "outputs": {"dry_run_plan": action.get("dry_run_plan")},
    }
