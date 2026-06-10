"""Semantic ranking over lens-scoped NOMOS chunks.

This is the W19-H1 retrieval half: the ``embedding`` column is not just populated
(see ``embedding.py``) but actually **queried**.

- On **Postgres** the ranking is pushed into SQL with the pgvector cosine-distance
  operator ``embedding <=> CAST(:qvec AS vector)`` — a real index-able vector
  query, exercised end-to-end (under RLS) by ``test_rls_pgvector_postgres``.
- On **SQLite** (dev / the 182-test suite) the same ordering is computed with a
  pure-Python cosine, so behaviour is identical without a Postgres dependency.

Either way the ranking is **combined with the existing facet filtering**: the
caller passes a lens-filtered, scope-filtered ``base_query`` (from
``lens.project_chunk_query`` / ``jurisdiction_pool_query``); semantic search only
*orders and truncates* what the lens already let through.
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy import Float, cast
from sqlalchemy.orm import defer

from .embedding import ConceptHashingEmbedder, Vector, _tokens


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def lexical_similarity(question: str, row: Any) -> float:
    """Jaccard token overlap in [0, 1] — fallback for a chunk without an embedding.

    Keeps a semantic-mode result set sane when only some rows are embedded; it is
    *not* the legacy ranker (that stays untouched in ``doctrine._ranked_matches``).
    """
    q_tokens = set(_tokens(question))
    facets = getattr(row, "facets", None) or {}
    facet_text = " ".join(str(value) for value in facets.values())
    r_tokens = set(_tokens(f"{row.text} {row.chunk_id} {facet_text}"))
    if not q_tokens or not r_tokens:
        return 0.0
    intersection = len(q_tokens & r_tokens)
    if intersection == 0:
        return 0.0
    return intersection / len(q_tokens | r_tokens)


def semantic_chunk_search(
    session,
    base_query,
    model,
    *,
    query_vector: list[float],
    question: str,
    limit: int,
) -> list[tuple[Any, float]]:
    """Rank a lens-filtered ``base_query`` by similarity to ``query_vector``.

    Returns ``(row, similarity)`` pairs, best first, ``similarity`` in [-1, 1]
    (cosine). Postgres ranks via pgvector; other dialects via Python cosine with a
    lexical fallback for rows that have no embedding yet.
    """
    if session.get_bind().dialect.name == "postgresql":
        # Real pgvector cosine-distance ordering, computed in SQL: the smaller the
        # ``<=>`` distance the closer the vectors. similarity = 1 - distance.
        distance = model.embedding.op("<=>", return_type=Float())(
            cast(query_vector, Vector())
        ).label("_distance")
        ranked = (
            base_query.filter(model.embedding.isnot(None))
            .options(defer(model.embedding))
            .order_by(None)
            .add_columns(distance)
            .order_by(distance)
            .limit(limit)
        )
        return [(entity, 1.0 - float(dist)) for entity, dist in ranked.all()]

    scored: list[tuple[Any, float]] = []
    for row in base_query.all():
        embedding = row.embedding
        similarity = cosine(query_vector, embedding) if embedding else lexical_similarity(question, row)
        scored.append((row, similarity))
    scored.sort(key=lambda item: (-item[1], item[0].id))
    return scored[:limit]
