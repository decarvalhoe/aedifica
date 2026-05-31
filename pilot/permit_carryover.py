"""Carry permit conditions into tender and site memory.

Represents open permit conditions and unresolved assumptions as carryover memory
records, exposes them to the tender/site workflows, and proves that no obligation
is silently dropped between phases. Resolved carryover records stay traceable via
their links back to the originating condition.
"""
from __future__ import annotations

OPEN_STATUSES = {"open", "pending_human_review"}
DOWNSTREAM_PHASES = {"41", "52"}


def permit_conditions(memory: dict) -> list:
    """Open/unresolved permit conditions at phase 33."""
    return [
        record
        for record in memory.get("records", [])
        if record.get("phase_code") == "33" and record.get("status") in OPEN_STATUSES
    ]


def build_carryover_record(condition: dict, target_phase: str, memory_id: str) -> dict:
    """Create a tender(41)/site(52) carryover record linked to a permit condition."""
    record_type = "handoff" if target_phase == "41" else "site_issue"
    return {
        "memory_id": memory_id,
        "record_type": record_type,
        "phase_code": target_phase,
        "title": f"Carryover: {condition.get('title')}",
        "summary": f"Permit condition {condition.get('memory_id')} carried into phase {target_phase}.",
        "claim_state": condition.get("claim_state", "sourced"),
        "status": "open",
        "source_refs": condition.get("source_refs", []),
        "evidence_refs": condition.get("evidence_refs", []),
        "links": [condition.get("memory_id")],
    }


def carried_obligations(memory: dict) -> list:
    """For each permit condition, which downstream records carry it (and is it dropped)."""
    records = memory.get("records", [])
    results = []
    for condition in permit_conditions(memory):
        downstream = [
            record
            for record in records
            if condition.get("memory_id") in record.get("links", []) and record.get("phase_code") in DOWNSTREAM_PHASES
        ]
        results.append(
            {
                "condition": condition.get("memory_id"),
                "title": condition.get("title"),
                "carried_into": [record.get("memory_id") for record in downstream],
                "dropped": len(downstream) == 0,
            }
        )
    return results


def dropped_obligations(memory: dict) -> list:
    """Permit conditions with no downstream carryover — must never be silently dropped."""
    return [result for result in carried_obligations(memory) if result["dropped"]]
