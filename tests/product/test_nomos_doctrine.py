"""W19-04 NOMOS doctrine retriever tests."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402
from aedifica.api.config import Settings  # noqa: E402
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
from aedifica.retrieval.doctrine import answer_doctrine_question  # noqa: E402
from aedifica.retrieval.lens import KnowledgeLens  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def _project(session, project_id: str = "P-NOMOS") -> Project:
    org = Org(name=f"Atelier {project_id}")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email=f"{project_id}@test.ch", name="Owner", role="owner"))
    project = Project(org_id=org.id, project_id=project_id, name=project_id, commune="Lausanne", canton="VD")
    session.add(project)
    session.flush()
    return project


def test_doctrine_answer_cites_entailing_project_source(session):
    project = _project(session)
    session.add(
        ProjectKnowledgeChunk(
            project_id=project.id,
            chunk_id="lausanne-zone-centre",
            text="Zone centre: l'indice d'utilisation du sol IUS autorise 0.7.",
            source_hash="a" * 64,
            source_path="reglements/lausanne-rpga.pdf",
            span={"start": 120, "end": 176},
            facets={"discipline": "architect.permit", "trust_tier": "certified", "provenance": "official"},
            trust_tier="certified",
            provenance="official",
        )
    )
    session.commit()

    response = answer_doctrine_question(
        session,
        project,
        "Quel IUS pour la zone centre ?",
        nomos_enabled=True,
    )

    assert response["requires_human_decision"] is False
    assert "IUS" in response["answer"]
    assert response["structured_facts"][0]["chunk_id"] == "lausanne-zone-centre"
    assert response["citations"] == [
        {
            "chunk_id": "lausanne-zone-centre",
            "scope": "project",
            "source_path": "reglements/lausanne-rpga.pdf",
            "source_hash": "a" * 64,
            "span": {"start": 120, "end": 176},
            "trust_tier": "certified",
            "provenance": "official",
        }
    ]


def test_doctrine_answer_abstains_without_entailing_source(session):
    project = _project(session)
    session.add(
        JurisdictionKnowledgeChunk(
            country="CH",
            canton="VD",
            commune="Lausanne",
            chunk_id="lausanne-parking",
            text="Les places velo doivent etre couvertes.",
            source_hash="b" * 64,
            source_path="reglements/lausanne-rpga.pdf",
            facets={"discipline": "architect.permit", "trust_tier": "certified", "provenance": "official"},
            trust_tier="certified",
            provenance="official",
        )
    )
    session.commit()

    response = answer_doctrine_question(session, project, "Quelle hauteur maximale ?", nomos_enabled=True)

    assert response == {
        "answer": "Abstention: aucune source NOMOS entailante n'a ete trouvee pour cette question.",
        "structured_facts": [],
        "citations": [],
        "requires_human_decision": True,
    }


def test_doctrine_answer_respects_lens_filters(session):
    project = _project(session)
    session.add_all(
        [
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="permit-public",
                text="Le dossier de permis doit inclure le plan de situation.",
                source_hash="c" * 64,
                source_path="public.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "public"},
            ),
            ProjectKnowledgeChunk(
                project_id=project.id,
                chunk_id="permit-confidential",
                text="Le dossier de permis contient une convention confidentielle.",
                source_hash="d" * 64,
                source_path="confidential.pdf",
                facets={"discipline": "architect.permit", "confidentiality": "confidential"},
            ),
        ]
    )
    session.commit()

    response = answer_doctrine_question(
        session,
        project,
        "Que doit inclure le dossier de permis ?",
        nomos_enabled=True,
        lens=KnowledgeLens(exclude={"confidentiality": "confidential"}),
    )

    assert [citation["chunk_id"] for citation in response["citations"]] == ["permit-public"]


def _bootstrap_project(client: TestClient) -> dict:
    owner = client.post("/api/orgs", json={"org_name": "Atelier Test", "user_email": "owner@test.ch"})
    assert owner.status_code == 201
    headers = {"Authorization": f"Bearer {owner.json()['token']}"}
    project = client.post(
        "/api/projects",
        json={"project_id": "P-NOMOS", "name": "Rue Centrale", "commune": "Lausanne", "canton": "VD"},
        headers=headers,
    )
    assert project.status_code == 201
    return headers


def test_api_nomos_doctrine_endpoint_is_flag_gated(engine):
    app = create_app(engine=engine, settings=Settings(nomos_enabled=False))
    client = TestClient(app)
    headers = _bootstrap_project(client)

    response = client.post(
        "/api/projects/P-NOMOS/copilote/nomos",
        json={"question": "Quel IUS pour la zone centre ?"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOMOS_DISABLED"
