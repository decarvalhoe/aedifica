"""Cite-or-abstain doctrine answers over NOMOS retrieval chunks."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from ..db import models as m
from .lens import KnowledgeLens, jurisdiction_pool_query, project_chunk_query


class NomosDoctrineError(ValueError):
    """Raised when the dormant NOMOS doctrine path is unavailable."""


STOPWORDS = {
    "avec",
    "dans",
    "des",
    "doit",
    "du",
    "est",
    "for",
    "inclure",
    "les",
    "pour",
    "que",
    "quel",
    "quelle",
    "the",
    "une",
}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{3,}", _normalize(text)) if token not in STOPWORDS}


def _row_tokens(row: Any) -> set[str]:
    facets = row.facets or {}
    facet_text = " ".join(str(value) for value in facets.values())
    return _tokens(f"{row.text} {row.chunk_id} {facet_text}")


def _citation(row: Any, scope: str) -> dict:
    return {
        "chunk_id": row.chunk_id,
        "scope": scope,
        "source_path": row.source_path,
        "source_hash": row.source_hash,
        "span": row.span,
        "trust_tier": row.trust_tier,
        "provenance": row.provenance,
    }


def _fact(row: Any, scope: str) -> dict:
    return {
        "chunk_id": row.chunk_id,
        "scope": scope,
        "text": row.text,
        "trust_tier": row.trust_tier,
        "provenance": row.provenance,
        "facets": row.facets or {},
    }


def _ranked_matches(question: str, rows: list[tuple[str, Any]], limit: int) -> list[tuple[str, Any]]:
    q_tokens = _tokens(question)
    if not q_tokens:
        return []
    threshold = 2 if len(q_tokens) >= 2 else 1
    scored = []
    for scope, row in rows:
        score = len(q_tokens & _row_tokens(row))
        if score >= threshold:
            scored.append((score, scope, row))
    scored.sort(key=lambda item: (-item[0], item[1], item[2].id))
    return [(scope, row) for _, scope, row in scored[:limit]]


def answer_doctrine_question(
    session,
    project: m.Project,
    question: str,
    *,
    nomos_enabled: bool = False,
    lens: KnowledgeLens | dict | None = None,
    limit: int = 3,
) -> dict:
    """Return a sourced answer shape, or abstain when no source entails it."""
    if not nomos_enabled:
        raise NomosDoctrineError("NOMOS doctrine retriever is disabled")
    if not question.strip():
        raise NomosDoctrineError("question is required")

    rows: list[tuple[str, Any]] = [
        ("project", row)
        for row in project_chunk_query(session, project.id, lens).all()
    ]
    rows.extend(
        ("jurisdiction", row)
        for row in jurisdiction_pool_query(
            session,
            country=project.country,
            canton=project.canton,
            commune=project.commune,
            lens=lens,
        ).all()
    )
    matches = _ranked_matches(question, rows, limit)
    if not matches:
        return {
            "answer": "Abstention: aucune source NOMOS entailante n'a ete trouvee pour cette question.",
            "structured_facts": [],
            "citations": [],
            "requires_human_decision": True,
        }

    facts = [_fact(row, scope) for scope, row in matches]
    citations = [_citation(row, scope) for scope, row in matches]
    return {
        "answer": " ".join(fact["text"] for fact in facts),
        "structured_facts": facts,
        "citations": citations,
        "requires_human_decision": any(fact["trust_tier"] != "certified" for fact in facts),
    }
