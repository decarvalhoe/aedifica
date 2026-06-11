"""W19-H1 semantic lens retrieval — adversarial proofs.

The audit graded W19-03 *PARTIAL*: the ``embedding`` column existed but was never
queried, so ranking was lexical token-overlap. These tests prove the column is now
**populated and queried**, and that the ranking is **semantic, not lexical** — by
showing the engine surfaces a synonym source that the lexical ranker abstains on,
and that removing the embedding makes that capability disappear (revert-and-confirm).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.db import (  # noqa: E402
    Base,
    Org,
    Project,
    ProjectKnowledgeChunk,
    User,
    make_engine,
    make_session_factory,
)
from aedifica.retrieval import backfill_embeddings, get_default_embedder  # noqa: E402
from aedifica.retrieval.doctrine import answer_doctrine_question  # noqa: E402
from aedifica.retrieval.embedding import EMBEDDING_DIM  # noqa: E402
from aedifica.retrieval.lens import KnowledgeLens  # noqa: E402

# A query that is a *synonym* of "permis" with zero token overlap with any chunk —
# the lexical ranker cannot bridge it; only the concept-aware embedding can.
PERMIT_QUESTION = "Quelle autorisation faut-il deposer ?"


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def _project(session, project_id: str = "P-SEM") -> Project:
    org = Org(name=f"Atelier {project_id}")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email=f"{project_id}@test.ch", name="Owner", role="owner"))
    project = Project(org_id=org.id, project_id=project_id, name=project_id, commune="Lausanne", canton="VD")
    session.add(project)
    session.flush()
    return project


def _seed_permit_and_height(session, project) -> None:
    session.add_all(
        [
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="permis-batir",
                text="Le permis de batir releve de la police des constructions communale.",
                source_hash="a" * 64,
                source_path="reglements/permis.pdf",
                span={"start": 10, "end": 70},
                facets={"discipline": "architect.permit", "trust_tier": "certified", "provenance": "official"},
                trust_tier="certified",
                provenance="official",
            ),
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="hauteur-gabarit",
                text="La hauteur maximale du gabarit atteint douze metres au faitage.",
                source_hash="b" * 64,
                source_path="reglements/hauteur.pdf",
                facets={"discipline": "architect.permit", "trust_tier": "certified", "provenance": "official"},
                trust_tier="certified",
                provenance="official",
            ),
        ]
    )
    session.commit()


def test_lexical_ranker_abstains_on_a_synonym_only_match(session):
    """Baseline: without embeddings the engine cannot bridge autorisation~permis."""
    project = _project(session)
    _seed_permit_and_height(session, project)

    lexical = answer_doctrine_question(session, project, PERMIT_QUESTION, nomos_enabled=True)

    assert lexical["citations"] == []
    assert lexical["requires_human_decision"] is True


def test_semantic_ranking_surfaces_the_synonym_source(session):
    """With embeddings populated and queried, the permit source is retrieved."""
    project = _project(session)
    _seed_permit_and_height(session, project)

    filled = backfill_embeddings(session)
    assert filled == 2

    semantic = answer_doctrine_question(
        session, project, PERMIT_QUESTION, nomos_enabled=True, embedder=get_default_embedder()
    )

    chunk_ids = [citation["chunk_id"] for citation in semantic["citations"]]
    assert chunk_ids == ["permis-batir"]  # permit surfaced, unrelated height dropped
    assert "permis" in semantic["answer"]


def test_nulling_the_embedding_removes_the_capability(session):
    """Revert-and-confirm: the column is *actually consulted*, not incidental."""
    project = _project(session)
    _seed_permit_and_height(session, project)
    backfill_embeddings(session)

    # Adversarial revert: drop only the permit chunk's embedding.
    permit = (
        session.query(ProjectKnowledgeChunk)
        .filter(ProjectKnowledgeChunk.chunk_id == "permis-batir")
        .one()
    )
    permit.embedding = None
    session.commit()

    semantic = answer_doctrine_question(
        session, project, PERMIT_QUESTION, nomos_enabled=True, embedder=get_default_embedder()
    )

    # Without its embedding the permit chunk falls back to lexical (zero overlap)
    # and drops out — proving the cosine-over-embedding path is what surfaced it.
    assert [c["chunk_id"] for c in semantic["citations"]] == []


def test_backfill_populates_full_width_vectors_and_is_idempotent(session):
    project = _project(session)
    _seed_permit_and_height(session, project)

    assert backfill_embeddings(session) == 2

    rows = session.query(ProjectKnowledgeChunk).all()
    assert all(row.embedding is not None and len(row.embedding) == EMBEDDING_DIM for row in rows)

    # A second run fills nothing — only NULL embeddings are (re)computed.
    assert backfill_embeddings(session) == 0


def test_semantic_ranking_still_obeys_the_lens(session):
    """Semantic similarity only re-orders what the facet lens already allowed."""
    project = _project(session)
    session.add_all(
        [
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="permis-public",
                text="Le permis de batir public mentionne le plan de situation.",
                source_hash="c" * 64,
                source_path="public.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "public"},
            ),
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="permis-confidential",
                text="Le permis de batir confidentiel cite une convention privee.",
                source_hash="d" * 64,
                source_path="confidential.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "confidential"},
            ),
        ]
    )
    session.commit()
    backfill_embeddings(session)

    semantic = answer_doctrine_question(
        session,
        project,
        PERMIT_QUESTION,
        nomos_enabled=True,
        embedder=get_default_embedder(),
        lens=KnowledgeLens(exclude={"confidentiality": "confidential"}),
    )

    assert [c["chunk_id"] for c in semantic["citations"]] == ["permis-public"]
