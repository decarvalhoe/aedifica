"""Claim envelope + trust footer — the product trust contract.

Re-exported from ``pilot.claims`` and ``pilot.trust``.
"""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import claims as _claims
import trust as _trust

CLAIM_STATES = _claims.CLAIM_STATES
ClaimValidationError = _claims.ClaimValidationError
make_claim = _claims.make_claim
unknown_claim = _claims.unknown_claim
validate_claim = _claims.validate_claim
validate_claims = _claims.validate_claims

render_footer = _trust.render_footer
PROVENANCE_TAGS = _trust.PROVENANCE_TAGS

__all__ = [
    "CLAIM_STATES",
    "ClaimValidationError",
    "make_claim",
    "unknown_claim",
    "validate_claim",
    "validate_claims",
    "render_footer",
    "PROVENANCE_TAGS",
]
