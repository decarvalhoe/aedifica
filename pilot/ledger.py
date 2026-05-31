"""Decision ledger contract and carryover query helpers."""
from __future__ import annotations

from datetime import datetime


LEDGER_VERSION = "1.0"
EVENT_TYPES = {"decision", "approval", "adapter_dry_run", "adapter_execution", "report_generation"}
MUTATING_EVENTS = {"adapter_execution"}


class LedgerValidationError(ValueError):
    pass


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _iso_datetime(value):
    if not _nonempty(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_entry(entry: dict) -> None:
    ledger_id = entry.get("ledger_id") or "<missing>"
    for key in ("ledger_id", "timestamp", "project_id", "event_type", "summary"):
        if not _nonempty(entry.get(key)):
            raise LedgerValidationError(f"{ledger_id}.{key} must be a non-empty string")
    if not _iso_datetime(entry.get("timestamp")):
        raise LedgerValidationError(f"{ledger_id}.timestamp must be an ISO datetime")
    if entry.get("event_type") not in EVENT_TYPES:
        raise LedgerValidationError(f"{ledger_id}.event_type must be one of {sorted(EVENT_TYPES)}")
    for key in ("actor", "phase", "basis"):
        if not isinstance(entry.get(key), dict):
            raise LedgerValidationError(f"{ledger_id}.{key} must be an object")
    if not _nonempty(entry["actor"].get("name")) or not _nonempty(entry["actor"].get("role")):
        raise LedgerValidationError(f"{ledger_id}.actor requires name and role")
    if not _nonempty(entry["phase"].get("phase_code")):
        raise LedgerValidationError(f"{ledger_id}.phase.phase_code is required")
    if not (entry["basis"].get("source_refs") or entry["basis"].get("evidence_refs")):
        raise LedgerValidationError(f"{ledger_id}.basis requires source_refs or evidence_refs")
    if entry.get("event_type") in MUTATING_EVENTS or entry.get("mutating") is True:
        approval = entry.get("approval")
        if not isinstance(approval, dict):
            raise LedgerValidationError(f"{ledger_id}.approval is required for mutating actions")
        for key in ("approved_by", "approved_at", "basis", "scope"):
            if not _nonempty(approval.get(key)):
                raise LedgerValidationError(f"{ledger_id}.approval.{key} is required for mutating actions")
        if not _iso_datetime(approval["approved_at"]):
            raise LedgerValidationError(f"{ledger_id}.approval.approved_at must be an ISO datetime")


def validate_ledger(data: dict) -> None:
    if data.get("schema_version") != LEDGER_VERSION:
        raise LedgerValidationError(f"schema_version must be {LEDGER_VERSION!r}")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise LedgerValidationError("entries must be a non-empty list")
    seen = set()
    for entry in entries:
        validate_entry(entry)
        ledger_id = entry["ledger_id"]
        if ledger_id in seen:
            raise LedgerValidationError(f"duplicate ledger_id {ledger_id}")
        seen.add(ledger_id)


def carryover(memory: dict, intent: str):
    records = memory.get("records", [])
    if intent == "open_blockers_before_permit":
        return [
            r for r in records
            if r.get("phase_code") == "33" and r.get("status") in {"open", "pending_human_review"}
        ]
    if intent == "conditions_for_tender_site":
        return [
            r for r in records
            if r.get("phase_code") in {"41", "52"} and r.get("status") in {"open", "active", "pending_human_review"}
        ]
    if intent == "changes_since_report":
        return [
            r for r in records
            if r.get("record_type") in {"change", "claim_created", "report_generation"}
            and r.get("status") in {"active", "open", "pending_human_review"}
        ]
    return []
