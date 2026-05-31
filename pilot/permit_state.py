"""Permit dossier state machine.

Defines the explicit states a permit dossier moves through and the legal valid
transitions between them, before any UI or report is built on top. Aedifica is
NOT an authority: these states describe the architect's preparation and the
human actions that move the dossier, never an authority decision.

States:
    draft               -> dossier opened, evidence being assembled
    missing_evidence    -> required evidence still missing
    ready_for_review    -> no required blockers; awaiting architect review
    architect_approved  -> architect has reviewed and approved for submission
    submitted_external  -> submitted to the authority (external, out of our hands)
"""
from __future__ import annotations

STATES = ["draft", "missing_evidence", "ready_for_review", "architect_approved", "submitted_external"]

# from -> set of allowed next states
TRANSITIONS = {
    "draft": {"missing_evidence", "ready_for_review"},
    "missing_evidence": {"ready_for_review", "draft"},
    "ready_for_review": {"architect_approved", "missing_evidence"},
    "architect_approved": {"submitted_external", "ready_for_review"},
    "submitted_external": {"ready_for_review"},
}

# Human action + evidence change that justifies each transition.
TRANSITION_ACTIONS = {
    ("draft", "missing_evidence"): "Open dossier; required evidence still missing.",
    ("draft", "ready_for_review"): "All required evidence present from the start.",
    ("missing_evidence", "ready_for_review"): "Architect added the missing required evidence.",
    ("missing_evidence", "draft"): "Architect re-opened the dossier for restructuring.",
    ("ready_for_review", "architect_approved"): "Architect reviewed and approved the dossier.",
    ("ready_for_review", "missing_evidence"): "Required evidence was removed or invalidated.",
    ("architect_approved", "submitted_external"): "Architect submitted the dossier to the authority.",
    ("architect_approved", "ready_for_review"): "Approval withdrawn pending changes.",
    ("submitted_external", "ready_for_review"): "Authority returned the dossier for completion.",
}

NON_AUTHORITY_NOTE = (
    "Aedifica prepares and tracks the dossier. The permit decision belongs to the "
    "competent authority; 'ready_for_review' and 'architect_approved' never mean approved."
)


class PermitStateError(ValueError):
    """Raised on an invalid permit dossier state transition."""


def is_valid_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, set())


def transition(from_state: str, to_state: str) -> str:
    if from_state not in STATES:
        raise PermitStateError(f"unknown from state: {from_state}")
    if to_state not in STATES:
        raise PermitStateError(f"unknown to state: {to_state}")
    if not is_valid_transition(from_state, to_state):
        raise PermitStateError(f"invalid transition {from_state} -> {to_state}")
    return to_state


def derive_state(completeness: dict, *, architect_approved: bool = False, submitted: bool = False) -> str:
    """Derive the dossier state from a completeness report + human flags."""
    summary = (completeness or {}).get("summary", {})
    if submitted:
        return "submitted_external"
    if architect_approved:
        return "architect_approved"
    if summary.get("required_blockers", 0) > 0:
        return "missing_evidence"
    if summary.get("present_count", 0) > 0:
        return "ready_for_review"
    return "draft"


def state_summary(state: str, completeness: dict | None = None) -> dict:
    return {
        "state": state,
        "is_authority_decision": False,
        "note": NON_AUTHORITY_NOTE,
        "required_blockers": (completeness or {}).get("summary", {}).get("required_blockers", 0),
        "next_states": sorted(TRANSITIONS.get(state, set())),
    }
