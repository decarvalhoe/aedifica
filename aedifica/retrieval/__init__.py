"""Retrieval scaffolding for future NOMOS-backed assistants."""
from __future__ import annotations

from .doctrine import NomosDoctrineError, answer_doctrine_question
from .embedding import ConceptHashingEmbedder, backfill_embeddings, get_default_embedder
from .lens import KnowledgeLens, apply_lens, jurisdiction_pool_query, project_chunk_query
from .semantic import cosine, semantic_chunk_search

__all__ = [
    "KnowledgeLens",
    "NomosDoctrineError",
    "answer_doctrine_question",
    "apply_lens",
    "project_chunk_query",
    "jurisdiction_pool_query",
    "ConceptHashingEmbedder",
    "backfill_embeddings",
    "get_default_embedder",
    "cosine",
    "semantic_chunk_search",
]
