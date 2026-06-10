"""Deterministic, dependency-free embeddings for NOMOS lens retrieval.

Honest claim-boundary (cf. ``docs/strategy/hardening-discipline.md``): these are
*concept-aware feature-hashing* embeddings, **not** neural/LLM embeddings. They are

- **deterministic** — pure ``hashlib`` feature hashing, no network, no model
  weights, no process-salted ``hash()``. The same text always yields the same
  vector, on any machine, which is what makes the Postgres ``vector(1536)`` column
  and the test suite reproducible;
- **local / LPD-safe** — nothing leaves the process, so confidential project
  chunks can be embedded without a cloud LLM call (cf. development-approach §4);
- **semantic, not lexical** — a small *controlled* concept lexicon maps
  lexically-disjoint synonyms ("permis" ~ "autorisation" ~ "Baugesuch") onto a
  shared concept feature, so cosine similarity ranks a synonym match above an
  unrelated token. That is the property W19-H1 needs: ranking that is **not**
  token-overlap.

The embedder is intentionally pluggable: a richer model can be injected later
without touching the retrieval plumbing, because the engine only depends on the
``embed`` / ``embed_chunk`` contract.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any

from sqlalchemy import text
from sqlalchemy.types import UserDefinedType

from ..db import models as m

EMBEDDING_DIM = 1536
"""Must match ``project/jurisdiction_knowledge_chunk.embedding vector(1536)``.

A mismatch makes the Postgres ``CAST(... AS vector)`` insert fail loudly rather
than silently storing a wrong-width vector — that is the intended fail-fast.
"""

# Concepts dominate single tokens so a *shared concept with zero token overlap*
# still produces a clear positive cosine — the semantic signal we must prove.
_TOKEN_WEIGHT = 1.0
_CONCEPT_WEIGHT = 2.2
_TRIGRAM_WEIGHT = 0.45

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")

# Controlled multilingual concept lexicon for the Swiss SIA built environment
# (FR / DE / IT / EN). The *mechanic* lives in the core; a jurisdiction pack may
# extend the vocabulary, but it never owns the embedding logic.
_CONCEPT_TERMS: dict[str, tuple[str, ...]] = {
    "building_permit": ("permis", "autorisation", "permit", "baugesuch", "baubewilligung", "licenza", "bewilligung"),
    "construction": ("construire", "construction", "constructions", "batir", "chantier", "bauen", "costruzione", "build"),
    "height": ("hauteur", "gabarit", "hoehe", "hohe", "height", "altezza", "niveaux", "etages"),
    "plot_ratio": ("ius", "indice", "utilisation", "densite", "ausnutzung", "ausnutzungsziffer", "ratio", "coefficient"),
    "setback": ("recul", "distance", "abstand", "setback", "limite", "limites", "grenzabstand"),
    "parking": ("stationnement", "parking", "velo", "bicycle", "cycle", "stellplatz", "parcheggio", "places"),
    "zoning": ("zone", "affectation", "nutzung", "zonage", "zonierung", "zona", "secteur"),
    "energy": ("energie", "energy", "thermique", "cecb", "minergie", "energetico", "energetique"),
    "heritage": ("patrimoine", "monument", "isos", "heritage", "denkmal", "patrimonio", "historique"),
    "accessibility": ("accessibilite", "handicap", "accessibility", "behindertengerecht", "mobilite", "barrierefrei"),
    "fire_safety": ("feu", "incendie", "aeai", "fire", "brandschutz", "antincendio", "evacuation"),
    "noise": ("bruit", "nuisance", "larm", "noise", "rumore", "phonique", "acoustique"),
}

_CONCEPT_LEXICON: dict[str, str] = {}


def _fold(text_value: str) -> str:
    return unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii").lower()


for _concept, _terms in _CONCEPT_TERMS.items():
    for _term in _terms:
        _CONCEPT_LEXICON[_fold(_term)] = _concept


def _tokens(text_value: str) -> list[str]:
    return _TOKEN_RE.findall(_fold(text_value))


def _signed_bucket(feature: str) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    n = int.from_bytes(digest, "big")
    bucket = n % EMBEDDING_DIM
    sign = 1.0 if (n >> 40) & 1 else -1.0
    return bucket, sign


def _trigrams(token: str) -> list[str]:
    if len(token) < 4:
        return []
    padded = f"#{token}#"
    return [padded[i : i + 3] for i in range(len(padded) - 2)]


class ConceptHashingEmbedder:
    """Deterministic concept-aware feature-hashing embedder (the default).

    See module docstring for the claim-boundary. ``embed`` is the only thing the
    retrieval layer depends on, so this class is swappable.
    """

    dim = EMBEDDING_DIM

    def embed(self, text_value: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIM
        for token in _tokens(text_value):
            bucket, sign = _signed_bucket(f"tok:{token}")
            vector[bucket] += _TOKEN_WEIGHT * sign

            concept = _CONCEPT_LEXICON.get(token)
            if concept is not None:
                c_bucket, c_sign = _signed_bucket(f"concept:{concept}")
                vector[c_bucket] += _CONCEPT_WEIGHT * c_sign

            for trigram in _trigrams(token):
                t_bucket, t_sign = _signed_bucket(f"tri:{trigram}")
                vector[t_bucket] += _TRIGRAM_WEIGHT * t_sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]

    def embed_chunk(self, chunk: Any) -> list[float]:
        """Embed a chunk from its *content* (text + chunk_id slug).

        Deliberately **excludes facets**: facets are the lens (structured filter)
        dimension, not semantic content. Folding e.g. ``discipline=architect.permit``
        into the vector would stamp the ``building_permit`` concept onto every
        permit-tagged chunk regardless of what it actually says, drowning the
        content signal. The lens already filters on facets *before* ranking.
        """
        return self.embed(f"{chunk.text} {chunk.chunk_id}")


_DEFAULT_EMBEDDER = ConceptHashingEmbedder()


def get_default_embedder() -> ConceptHashingEmbedder:
    return _DEFAULT_EMBEDDER


def to_vector_literal(vector: list[float]) -> str:
    """Render a vector as a pgvector text literal: ``[v1,v2,...]``."""
    return "[" + ",".join(format(value, ".7g") for value in vector) + "]"


class Vector(UserDefinedType):
    """Minimal pgvector bind type so a Python list renders as ``CAST(:p AS vector)``.

    We avoid the optional ``pgvector`` package: the only thing the query layer needs
    is to send a query vector to Postgres' ``<=>`` operator, which this provides via
    the text literal form. ``cache_ok`` keeps SQLAlchemy's statement cache happy.
    """

    cache_ok = True

    def get_col_spec(self, **kw):  # pragma: no cover - DDL is owned by the migration
        return "vector"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return to_vector_literal(value)

        return process


_CHUNK_MODELS = (m.ProjectKnowledgeChunk, m.JurisdictionKnowledgeChunk)


def backfill_embeddings(session, *, embedder: ConceptHashingEmbedder | None = None) -> int:
    """Populate ``embedding`` for every chunk that lacks one. Returns the count.

    Dialect-aware: on Postgres the value is written through an explicit
    ``CAST(:v AS vector)`` (the ``vector(1536)`` column rejects a JSON blob); on
    SQLite the ORM JSON column stores the list directly. This is a *real* pipeline
    run — the W19-H1 tests call it and then query, rather than asserting a
    hand-placed embedding string.
    """
    embedder = embedder or _DEFAULT_EMBEDDER
    is_postgres = session.get_bind().dialect.name == "postgresql"
    filled = 0
    for model in _CHUNK_MODELS:
        rows = session.query(model).filter(model.embedding.is_(None)).all()
        for row in rows:
            vector = embedder.embed_chunk(row)
            if is_postgres:
                session.execute(
                    text(f"UPDATE {model.__tablename__} SET embedding = CAST(:vec AS vector) WHERE id = :id"),
                    {"vec": to_vector_literal(vector), "id": row.id},
                )
            else:
                row.embedding = vector
            filled += 1
    session.flush()
    return filled
