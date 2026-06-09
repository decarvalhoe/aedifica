"""Lens query helpers for dormant NOMOS retrieval scaffolding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import or_

from ..db import models as m


@dataclass(frozen=True)
class KnowledgeLens:
    """Facet include/exclude rules compiled into database filters."""

    include: dict[str, str] = field(default_factory=dict)
    exclude: dict[str, str] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.include and not self.exclude


def _coerce_lens(lens: KnowledgeLens | dict | None) -> KnowledgeLens | None:
    if lens is None:
        return None
    if isinstance(lens, KnowledgeLens):
        return lens
    return KnowledgeLens(
        include={str(k): str(v) for k, v in (lens.get("include") or {}).items()},
        exclude={str(k): str(v) for k, v in (lens.get("exclude") or {}).items()},
    )


def _facet_text(model: Any, key: str):
    return model.facets[key].as_string()


def apply_lens(query, model: Any, lens: KnowledgeLens | dict | None):
    """Apply lens facets as WHERE predicates; no lens returns the query unchanged."""
    normalized = _coerce_lens(lens)
    if normalized is None or normalized.is_empty:
        return query
    for key, value in normalized.include.items():
        query = query.filter(_facet_text(model, key) == value)
    for key, value in normalized.exclude.items():
        facet = _facet_text(model, key)
        query = query.filter(or_(facet.is_(None), facet != value))
    return query


def project_chunk_query(session, project_id: int, lens: KnowledgeLens | dict | None = None):
    query = (
        session.query(m.ProjectKnowledgeChunk)
        .filter(m.ProjectKnowledgeChunk.project_id == project_id)
        .order_by(m.ProjectKnowledgeChunk.id)
    )
    return apply_lens(query, m.ProjectKnowledgeChunk, lens)


def jurisdiction_pool_query(
    session,
    *,
    country: str = "CH",
    canton: str | None = None,
    commune: str | None = None,
    lens: KnowledgeLens | dict | None = None,
):
    query = session.query(m.JurisdictionKnowledgeChunk).filter(m.JurisdictionKnowledgeChunk.country == country)
    if canton is not None:
        query = query.filter(m.JurisdictionKnowledgeChunk.canton == canton)
    if commune is not None:
        query = query.filter(m.JurisdictionKnowledgeChunk.commune == commune)
    query = query.order_by(m.JurisdictionKnowledgeChunk.id)
    return apply_lens(query, m.JurisdictionKnowledgeChunk, lens)
