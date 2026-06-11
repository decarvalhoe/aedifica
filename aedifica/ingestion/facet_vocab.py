"""Vendored NOMOS facet vocabulary snapshot + Aedifica-local extensions (W20-3).

NOMOS namespace (``NOMOS_VOCAB``)
    Frozen snapshot of the controlled vocabularies in NOMOS ``specs/facets.cue``
    (read at NOMOS pr-528 / commit c547b596bb78, the revision that ships the
    ``nomos bundle`` emitter). This is a **vendored snapshot pending the
    published vocabulary artifact from NOMOS SEAM-2/#535**; once NOMOS publishes
    the artifact, this module should consume it instead of vendoring.

    Imported bundles are validated *strictly* against this namespace: a facet
    value NOMOS itself would refuse (e.g. ``trust_tier: "trust-me-bro"`` or the
    never-specced ``provenance: "official"``) is a 422 at import, naming the
    offending axis and value. Aedifica does not invent NOMOS vocabulary.

Aedifica-local namespace (``AEDIFICA_LOCAL_VOCAB``)
    Values that exist only on rows Aedifica creates *itself* (OFS-direct
    ingestion, ORM column defaults), never accepted from a NOMOS bundle:

    - ``provenance: "official"`` — historical default for rows sourced directly
      from official Swiss registers (OFS / commune regulations fetched by
      Aedifica). Kept for those flows, but explicitly **not** part of
      ``specs/facets.cue`` — an imported bundle claiming it is refused.

Trust-tier policy (W20-3 note)
    NOMOS facet auto-derivation caps at ``indicative``: ``certified`` is an
    out-of-band certification act, never a side effect of atomization, so every
    bundle emitted today carries ``unverified``/``indicative`` nodes only.
    Aedifica's doctrine endpoint releases ``requires_human_decision: false``
    only when every cited fact is ``certified``. Both ends are intentional: the
    imported corpus stays decision-support (cite + escalate) until NOMOS
    promotion/certification flows exist. Claim ``confidence`` is derived from
    the tier (``CONFIDENCE_BY_TRUST_TIER``) instead of a blanket "high".

Validation scope
    Scalar axes are validated against the vocabulary; the term-list axes
    (``discipline_role``, ``activity``, ``vocabulary_refs``) are SKOS-style free
    term refs in CUE, so only their *shape* is checked (non-empty strings,
    presence implies at least one term). Unknown facet keys are tolerated
    (deviation from the closed CUE struct): legacy Aedifica bundles carry e.g. a
    ``zone`` key the importer maps to CommunePack zones, and a *new* axis in a
    future facets.cue must arrive with a schema_version bump, which the importer
    gates separately.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Any


class FacetVocabularyError(ValueError):
    """A facet value outside the NOMOS vocabulary; carries the offending axis/value."""

    def __init__(self, message: str, *, axis: str, value: Any):
        super().__init__(message)
        self.axis = axis
        self.value = value


#: Frozen snapshot of specs/facets.cue (NOMOS pr-528). Do not extend by hand —
#: see the module docstring (vendored pending NOMOS SEAM-2/#535).
NOMOS_VOCAB: MappingProxyType = MappingProxyType(
    {
        "nature": frozenset(
            {
                "rule",
                "definition",
                "obligation",
                "permission",
                "prohibition",
                "condition",
                "exception",
                "calculation",
                "evidence",
                "governance",
                "metier",
                "context",
            }
        ),
        "scope_level": frozenset({"source", "structure", "atom", "chunk", "domain", "product", "release"}),
        "trust_tier": frozenset({"certified", "indicative", "unverified"}),
        "provenance": frozenset({"source_backed", "derived", "inferred", "external_attested", "user_promoted"}),
        "confidentiality": frozenset(
            {"public", "internal", "restricted", "secret", "licensed_restricted", "customer_confidential"}
        ),
        "applicability": frozenset({"applicable", "partially_applicable", "not_applicable", "blocked", "unknown"}),
    }
)

#: Aedifica-local values (NOT in specs/facets.cue; never accepted from bundles).
AEDIFICA_LOCAL_VOCAB: MappingProxyType = MappingProxyType(
    {
        "provenance": frozenset({"official"}),
    }
)

#: CUE: `axis?: [#FacetTermRef, ...#FacetTermRef]` — free terms, present => >= 1.
TERM_LIST_AXES = ("discipline_role", "activity")

#: W20-3: claim confidence derives from the trust tier, never a blanket "high".
CONFIDENCE_BY_TRUST_TIER: MappingProxyType = MappingProxyType(
    {
        "unverified": "low",
        "indicative": "medium",
        "certified": "high",
    }
)


def confidence_for_trust_tier(trust_tier: str | None) -> str:
    """Map a trust tier onto claim confidence (unknown/absent tiers stay "low")."""
    return CONFIDENCE_BY_TRUST_TIER.get(trust_tier or "unverified", "low")


def validate_nomos_facets(facets: dict, *, context: str = "facets") -> None:
    """Validate a node's facets against the NOMOS vocabulary snapshot.

    Raises :class:`FacetVocabularyError` (naming the offending axis and value)
    for any scalar axis whose value NOMOS' own contract would refuse, and for
    malformed term-list axes. Mirrors ``Facets.Validate()`` in the NOMOS engine.
    """
    for axis, allowed in NOMOS_VOCAB.items():
        value = facets.get(axis)
        if value is None:
            continue
        if not isinstance(value, str) or value not in allowed:
            raise FacetVocabularyError(
                f"NOMOS bundle {context}.{axis} value {value!r} is not in the NOMOS facet vocabulary "
                f"(allowed: {', '.join(sorted(allowed))})",
                axis=axis,
                value=value,
            )
    for axis in TERM_LIST_AXES:
        terms = facets.get(axis)
        if terms is None:
            continue
        if not isinstance(terms, list) or not terms or any(not isinstance(t, str) or not t for t in terms):
            raise FacetVocabularyError(
                f"NOMOS bundle {context}.{axis} must be a non-empty list of non-empty terms",
                axis=axis,
                value=terms,
            )
    refs = facets.get("vocabulary_refs")
    if refs is not None and (not isinstance(refs, list) or any(not isinstance(r, str) or not r for r in refs)):
        raise FacetVocabularyError(
            f"NOMOS bundle {context}.vocabulary_refs must be a list of non-empty terms",
            axis="vocabulary_refs",
            value=refs,
        )
