"""W19-03 Lens-scoped retrieval scaffold tests."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api.config import get_settings  # noqa: E402
from aedifica.db import (  # noqa: E402
    Base,
    JurisdictionKnowledgeChunk,
    Org,
    Project,
    ProjectKnowledgeChunk,
    User,
    make_engine,
    make_session_factory,
)
from aedifica.retrieval.lens import KnowledgeLens, jurisdiction_pool_query, project_chunk_query  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def _project(session, project_id: str, commune: str = "Lausanne") -> Project:
    org = Org(name=f"Atelier {project_id}")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email=f"{project_id}@test.ch", name="Owner", role="owner"))
    project = Project(org_id=org.id, project_id=project_id, name=project_id, commune=commune, canton="VD")
    session.add(project)
    session.flush()
    return project


def test_project_lens_query_defaults_to_project_silo_without_lens(session):
    p1 = _project(session, "P1")
    p2 = _project(session, "P2")
    session.add_all(
        [
            ProjectKnowledgeChunk(
                project_id=p1.id,
                chunk_id="p1-permit",
                text="Permit doctrine",
                source_hash="a" * 64,
                source_path="p1.pdf",
                facets={"discipline": "architect.permit"},
            ),
            ProjectKnowledgeChunk(
                project_id=p2.id,
                chunk_id="p2-site",
                text="Site doctrine",
                source_hash="b" * 64,
                source_path="p2.pdf",
                facets={"discipline": "site-supervision"},
            ),
        ]
    )
    session.commit()

    rows = project_chunk_query(session, p1.id).all()

    assert [row.chunk_id for row in rows] == ["p1-permit"]


def test_lens_applies_include_and_exclude_as_query_filters(session):
    p = _project(session, "P1")
    session.add_all(
        [
            ProjectKnowledgeChunk(
                project_id=p.id,
                chunk_id="permit-public",
                text="Permit public",
                source_hash="a" * 64,
                source_path="permit.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "public"},
            ),
            ProjectKnowledgeChunk(
                project_id=p.id,
                chunk_id="permit-confidential",
                text="Permit confidential",
                source_hash="b" * 64,
                source_path="permit-private.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "confidential"},
            ),
            ProjectKnowledgeChunk(
                project_id=p.id,
                chunk_id="site-public",
                text="Site public",
                source_hash="c" * 64,
                source_path="site.pdf",
                facets={"discipline": "site-supervision", "confidentiality": "public"},
            ),
        ]
    )
    session.commit()

    lens = KnowledgeLens(
        include={"discipline": "architect.permit"},
        exclude={"confidentiality": "confidential"},
    )
    rows = project_chunk_query(session, p.id, lens).all()

    assert [row.chunk_id for row in rows] == ["permit-public"]


def test_jurisdiction_pool_query_is_shared_by_jurisdiction_and_lens(session):
    session.add_all(
        [
            JurisdictionKnowledgeChunk(
                country="CH",
                canton="VD",
                commune="Lausanne",
                chunk_id="lausanne-permit",
                text="Lausanne permit",
                source_hash="a" * 64,
                source_path="lausanne.pdf",
                facets={"discipline": "architect.permit", "scope_level": "local"},
            ),
            JurisdictionKnowledgeChunk(
                country="CH",
                canton="VD",
                commune="Pully",
                chunk_id="pully-permit",
                text="Pully permit",
                source_hash="b" * 64,
                source_path="pully.pdf",
                facets={"discipline": "architect.permit", "scope_level": "local"},
            ),
        ]
    )
    session.commit()

    rows = jurisdiction_pool_query(
        session,
        country="CH",
        canton="VD",
        commune="Lausanne",
        lens=KnowledgeLens(include={"discipline": "architect.permit"}),
    ).all()

    assert [row.chunk_id for row in rows] == ["lausanne-permit"]


def test_nomos_flag_off_keeps_lens_scaffold_dormant(monkeypatch, session):
    monkeypatch.setenv("AEDIFICA_NOMOS_ENABLED", "0")

    assert get_settings().nomos_enabled is False
    assert project_chunk_query(session, project_id=123).all() == []
