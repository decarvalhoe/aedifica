"""Trust-claim envelope used by project reports.

The schema is deliberately small and stdlib-only. It enforces the important
product rule: a regulatory fact cannot render as sourced without evidence.
"""
from __future__ import annotations


CLAIM_STATES = {"sourced", "computed", "assumption", "unknown", "conflict", "decision"}


class ClaimValidationError(ValueError):
    pass


def make_claim(
    claim_id: str,
    title: str,
    state: str,
    value=None,
    confidence: str = "medium",
    source_refs: list | None = None,
    required_human_check: str | None = None,
    next_action: str | None = None,
    formula: str | None = None,
    inputs: dict | None = None,
    claim_type: str = "regulatory",
) -> dict:
    return {
        "claim_id": claim_id,
        "title": title,
        "claim_type": claim_type,
        "state": state,
        "value": value,
        "confidence": confidence,
        "source_refs": source_refs or [],
        "required_human_check": required_human_check,
        "next_action": next_action,
        "formula": formula,
        "inputs": inputs or {},
    }


def validate_claim(claim: dict) -> None:
    claim_id = claim.get("claim_id") or "<missing>"
    state = claim.get("state")
    if state not in CLAIM_STATES:
        raise ClaimValidationError(f"{claim_id}: state must be one of {sorted(CLAIM_STATES)}")
    if not claim.get("title"):
        raise ClaimValidationError(f"{claim_id}: title is required")
    source_refs = claim.get("source_refs") or []
    if state == "sourced" and claim.get("claim_type") == "regulatory" and not source_refs:
        raise ClaimValidationError(f"{claim_id}: sourced regulatory claims require source_refs")
    if state == "computed":
        if not claim.get("formula"):
            raise ClaimValidationError(f"{claim_id}: computed claims require formula")
        if not source_refs:
            raise ClaimValidationError(f"{claim_id}: computed claims require source_refs for inputs")
    if state in {"assumption", "unknown", "conflict"}:
        if not (claim.get("required_human_check") or claim.get("next_action")):
            raise ClaimValidationError(f"{claim_id}: {state} claims require a human check or next action")


def validate_claims(claims: list[dict]) -> None:
    if not isinstance(claims, list) or not claims:
        raise ClaimValidationError("reports require at least one claim")
    for claim in claims:
        validate_claim(claim)


def unknown_claim(claim_id: str, title: str, next_action: str, required_human_check: str | None = None) -> dict:
    return make_claim(
        claim_id,
        title,
        "unknown",
        value=None,
        confidence="low",
        next_action=next_action,
        required_human_check=required_human_check or next_action,
    )
