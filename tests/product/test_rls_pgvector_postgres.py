"""W19-H1 — RLS isolation + pgvector ranking on a *real* Postgres.

The audit graded the project-silo RLS policy and the ``vector(1536)`` column as
*scaffolded but never exercised*: the prior migration test only asserted that the
policy SQL appears as a **string** in the migration file. That proves nothing — a
typo'd or disabled policy passes a string match.

This test runs the real migration on a real Postgres (pgvector image in CI), then
proves, adversarially:

1. **The embedding column holds a real ``vector(1536)``** — ``vector_dims`` works.
2. **RLS isolates by project** — under a *non-owner* role, a bare
   ``SELECT * FROM project_knowledge_chunk`` (no ``WHERE``) returns only the
   project named in ``aedifica.project_id``; flipping the GUC flips the rows;
   an empty GUC returns nothing; the table owner (RLS-bypassing) sees everything.
   If RLS were not enforced, the GUC would not matter and rows would leak.
3. **pgvector actually ranks** — ``embedding <=> CAST(:q AS vector)`` orders by
   semantic distance under RLS: a permit query ranks the permit chunk first, a
   height query ranks the height chunk first (the order *flips* with the query),
   and every returned row still belongs to the scoped project.

Gated on ``AEDIFICA_TEST_POSTGRES_URL`` (set in CI). It is skipped — never silently
passed — when no Postgres is configured locally.
"""
from __future__ import annotations

import os
import sys

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.db import (  # noqa: E402
    Org,
    Project,
    ProjectKnowledgeChunk,
    make_session_factory,
)
from aedifica.db import models as m  # noqa: E402
from aedifica.retrieval import backfill_embeddings, get_default_embedder, semantic_chunk_search  # noqa: E402

POSTGRES_URL = os.environ.get("AEDIFICA_TEST_POSTGRES_URL")
ROLE = "aedifica_rls_probe"  # a non-owner, non-superuser role subject to RLS

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="set AEDIFICA_TEST_POSTGRES_URL (e.g. postgresql+psycopg://postgres:postgres@localhost:5432/aedifica_test)",
)


def _chunk(project_id: int, chunk_id: str, body: str, hash_seed: str) -> ProjectKnowledgeChunk:
    return ProjectKnowledgeChunk(
        project_id=project_id,
        chunk_id=chunk_id,
        text=body,
        source_hash=hash_seed * 64,
        source_path=f"{chunk_id}.pdf",
        facets={"discipline": "architect.permit"},
    )


@pytest.fixture(scope="module")
def pg():
    """Fresh schema + migrated tables + seeded two-project corpus on real Postgres."""
    engine = create_engine(POSTGRES_URL, future=True)

    # Clean slate so the *migration* (not create_all) builds the vector column + RLS.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", POSTGRES_URL)
    command.upgrade(cfg, "head")

    factory = make_session_factory(engine)
    with factory() as session:
        org = Org(name="Atelier RLS")
        session.add(org)
        session.flush()
        p1 = Project(org_id=org.id, project_id="P1", name="P1", commune="Lausanne", canton="VD")
        p2 = Project(org_id=org.id, project_id="P2", name="P2", commune="Pully", canton="VD")
        session.add_all([p1, p2])
        session.flush()
        session.add_all(
            [
                _chunk(p1.id, "p1-permis", "Le permis de batir releve de la police des constructions.", "a"),
                _chunk(p1.id, "p1-hauteur", "La hauteur maximale du gabarit atteint douze metres au faitage.", "b"),
                _chunk(p2.id, "p2-permis", "Le permis de construire de l'autre dossier reste distinct.", "c"),
            ]
        )
        session.commit()
        # Real pipeline run: populate the vector(1536) column via CAST(:v AS vector).
        assert backfill_embeddings(session) == 3
        session.commit()
        p1_id, p2_id = p1.id, p2.id

    # A non-owner role that is genuinely subject to RLS (owner/superuser bypass it).
    # The schema reset above already dropped any stale grants, so DROP ROLE is safe.
    with engine.begin() as conn:
        conn.execute(text(f"DROP ROLE IF EXISTS {ROLE}"))
        conn.execute(text(f"CREATE ROLE {ROLE} LOGIN PASSWORD 'probe'"))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {ROLE}"))
        conn.execute(text(f"GRANT SELECT ON project_knowledge_chunk TO {ROLE}"))

    try:
        yield {"engine": engine, "factory": factory, "p1": p1_id, "p2": p2_id}
    finally:
        with engine.begin() as conn:
            conn.execute(text(f"DROP OWNED BY {ROLE}"))
            conn.execute(text(f"DROP ROLE IF EXISTS {ROLE}"))
        engine.dispose()


def _scoped(factory, project_id):
    """A session whose transaction runs as the RLS-bound role with the GUC set."""
    session = factory()
    session.execute(text(f"SET LOCAL ROLE {ROLE}"))
    session.execute(text("SELECT set_config('aedifica.project_id', :pid, true)"), {"pid": str(project_id)})
    return session


def test_embedding_is_a_real_1536d_vector(pg):
    with pg["factory"]() as session:
        dims = session.execute(text("SELECT vector_dims(embedding) FROM project_knowledge_chunk LIMIT 1")).scalar_one()
    assert dims == 1536


def test_rls_isolates_rows_by_project_guc(pg):
    factory, p1, p2 = pg["factory"], pg["p1"], pg["p2"]
    select = text("SELECT chunk_id FROM project_knowledge_chunk ORDER BY chunk_id")

    # Scoped to P1 -> only P1 rows, with no project_id filter in the query at all.
    session = _scoped(factory, p1)
    try:
        assert [r[0] for r in session.execute(select)] == ["p1-hauteur", "p1-permis"]

        # Adversarial: flip the GUC to P2 -> the visible set flips. The policy reads
        # the GUC, it is not a constant.
        session.execute(text("SELECT set_config('aedifica.project_id', :pid, true)"), {"pid": str(p2)})
        assert [r[0] for r in session.execute(select)] == ["p2-permis"]

        # Adversarial: no project context -> NULLIF('','')::int is NULL -> no rows leak.
        session.execute(text("SELECT set_config('aedifica.project_id', '', true)"))
        assert session.execute(select).all() == []
    finally:
        session.rollback()
        session.close()

    # Contrast: the table owner (superuser) bypasses RLS and sees every project.
    with factory() as owner:
        assert [r[0] for r in owner.execute(select)] == ["p1-hauteur", "p1-permis", "p2-permis"]


def test_pgvector_ranks_under_rls_and_order_flips_with_query(pg):
    factory, p1 = pg["factory"], pg["p1"]
    embedder = get_default_embedder()

    def ranked(question_text: str) -> list[tuple[str, int]]:
        # Capture primitives while the session is live (rollback would expire them).
        hits = semantic_chunk_search(
            session,
            session.query(ProjectKnowledgeChunk),
            m.ProjectKnowledgeChunk,
            query_vector=embedder.embed(question_text),
            question=question_text,
            limit=5,
        )
        return [(row.chunk_id, row.project_id) for row, _ in hits]

    session = _scoped(factory, p1)
    try:
        permit_hits = ranked("Quelle autorisation de construire deposer ?")
        height_hits = ranked("Quelle hauteur de gabarit au faitage ?")
    finally:
        session.rollback()
        session.close()

    # RLS still scopes the pgvector query: only P1 rows come back.
    assert {project_id for _, project_id in permit_hits} == {p1}
    assert {project_id for _, project_id in height_hits} == {p1}

    # pgvector <=> actually orders by semantic distance: the top hit flips with
    # the query (permit query -> permit chunk; height query -> height chunk).
    assert permit_hits[0][0] == "p1-permis"
    assert height_hits[0][0] == "p1-hauteur"
