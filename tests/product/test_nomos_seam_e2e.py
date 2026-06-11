"""W20 NOMOS->Aedifica seam e2e (#300/#301/#303) — the CI gate for the real contract.

These tests import the *vendored, unmodified* output of the real ``nomos bundle``
emitter (tests/fixtures/nomos/canonical-knowledge-bundle.emitted.json, generated
from NOMOS pr-528 over the portable golden corpus) through the real HTTP API:

- flag ON via the real env override (``AEDIFICA_NOMOS_ENABLED=1``), never by
  injecting a Settings object — the 12-factor path is what production runs;
- a file-backed temp SQLite database, so the API's own session factory is used;
- no hand-crafted bundle shapes: what NOMOS emits is what Aedifica must accept.

They run by default (no skip, no external service) and are the adversarial proof
that the importer speaks the emitted ``ckm-bundle-v1`` contract, end to end.
"""
from __future__ import annotations

import copy
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402
from aedifica.db import (  # noqa: E402
    Claim,
    CommunePack,
    Evidence,
    JurisdictionKnowledgeChunk,
    ProjectKnowledgeChunk,
    Source,
    make_engine,
    make_session_factory,
)

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "nomos", "canonical-knowledge-bundle.emitted.json")

# Golden expectations, pinned against the vendored fixture (regenerating the
# fixture is a deliberate act that must update these numbers in the same change).
GOLDEN_NODES = 74
GOLDEN_SOURCES = 10  # unique source files in the portable golden corpus
GOLDEN_FEEDS = 1


def _load_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def emitted_bundle() -> dict:
    return _load_fixture()


@pytest.fixture()
def seam(tmp_path, monkeypatch):
    """Real app over a temp SQLite db with the NOMOS flag ON via env override."""
    database_url = "sqlite:///" + (tmp_path / "seam.sqlite").as_posix()
    monkeypatch.setenv("AEDIFICA_DATABASE_URL", database_url)
    monkeypatch.setenv("AEDIFICA_NOMOS_ENABLED", "1")
    app = create_app(create_all=True)
    client = TestClient(app)

    owner = client.post("/api/orgs", json={"org_name": "Atelier Seam", "user_email": "owner@test.ch"})
    assert owner.status_code == 201
    headers = {"Authorization": f"Bearer {owner.json()['token']}"}
    project = client.post(
        "/api/projects",
        json={"project_id": "P-SEAM", "name": "Rue Centrale", "commune": "Lausanne", "canton": "VD"},
        headers=headers,
    )
    assert project.status_code == 201

    factory = make_session_factory(make_engine(database_url))
    return {"client": client, "headers": headers, "factory": factory}


def _import_bundle(seam, bundle: dict):
    return seam["client"].post(
        "/api/projects/P-SEAM/nomos/import",
        json={"bundle": bundle, "activate": True},
        headers=seam["headers"],
    )


# --------------------------------------------------------------------------- #
# W20-1 (#300): the emitted bundle imports UNMODIFIED through the real API.    #
# --------------------------------------------------------------------------- #
def test_emitted_bundle_imports_unmodified_with_golden_counts(seam, emitted_bundle):
    response = _import_bundle(seam, emitted_bundle)

    assert response.status_code == 200, response.text
    imported = response.json()["imported"]
    assert imported["packs"] == GOLDEN_FEEDS
    assert imported["sources"] == GOLDEN_SOURCES
    assert imported["evidence"] == GOLDEN_NODES
    assert imported["claims"] == GOLDEN_NODES

    # The fixture really is the emitter's output shape, not a softened copy.
    assert emitted_bundle["schema_version"] == "ckm-bundle-v1"
    assert len(emitted_bundle["feeds"]) == GOLDEN_FEEDS
    assert len(emitted_bundle["feeds"][0]["nodes"]) == GOLDEN_NODES
    assert isinstance(emitted_bundle["rag_metadata"], list)

    with seam["factory"]() as session:
        assert session.query(CommunePack).count() == GOLDEN_FEEDS
        assert session.query(Source).count() == GOLDEN_SOURCES
        assert session.query(Evidence).count() == GOLDEN_NODES
        assert session.query(Claim).count() == GOLDEN_NODES

        # The pack landed on the project's jurisdiction (the emitter has none).
        pack = session.query(CommunePack).one()
        assert (pack.commune, pack.canton) == ("Lausanne", "VD")
        # Per-node rag metadata joined from the bundle-level list — not lost as {}.
        rag = pack.data["nomos"]["rag_metadata"]
        assert len(rag) == GOLDEN_NODES

        # One claim carries the emitted node verbatim: facets, tiers, traceability.
        node = emitted_bundle["feeds"][0]["nodes"][0]
        feed_id = emitted_bundle["feeds"][0]["feed_id"]
        claim = session.query(Claim).filter_by(claim_id=f"nomos:{feed_id}:{node['node_id']}").one()
        assert claim.facets == node["facets"]
        assert claim.trust_tier == node["facets"]["trust_tier"]
        assert claim.provenance == node["facets"]["provenance"]
        ref = claim.source_refs[0]
        assert ref["node_id"] == node["node_id"]
        assert ref["span"] == {"start_line": node["span"]["start_line"], "end_line": node["span"]["end_line"]}
        assert ref["source_hash"] == node["source_hash"]
        assert ref["source_hash"].startswith("sha256:") and len(ref["source_hash"]) == 71

        # The 71-char prefixed hash is stored verbatim (the columns are wide enough).
        source = session.query(Source).filter_by(source_id=ref["source_id"]).one()
        assert source.sha256 == node["source_hash"]


def test_schema_version_gate_rejects_unknown_bundle_via_api(seam, emitted_bundle):
    """W20-1 adversarial: strip/forge schema_version -> 422 with the explicit code."""
    absent = copy.deepcopy(emitted_bundle)
    del absent["schema_version"]
    response = _import_bundle(seam, absent)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "NOMOS_BUNDLE_SCHEMA_UNSUPPORTED"

    forged = copy.deepcopy(emitted_bundle)
    forged["schema_version"] = "ckm-bundle-v2"
    response = _import_bundle(seam, forged)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "NOMOS_BUNDLE_SCHEMA_UNSUPPORTED"

    with seam["factory"]() as session:
        assert session.query(CommunePack).count() == 0
        assert session.query(Claim).count() == 0
        assert session.query(JurisdictionKnowledgeChunk).count() == 0
        assert session.query(ProjectKnowledgeChunk).count() == 0
