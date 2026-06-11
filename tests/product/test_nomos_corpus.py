"""W21-2 — corpus visibility endpoint: what the doctrine retriever can see.

GET /api/projects/{id}/nomos/corpus aggregates over the SAME lens-scoped pools
the doctrine path queries (project silo + jurisdiction pool). These tests prove:
flag OFF -> 403 with the explicit code; empty atelier -> honest zeros; a real
import through the API is reflected count-for-count; and the corpus is scoped
to the project's jurisdiction (another commune sees none of it).
"""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402


def _bundle() -> dict:
    """Minimal CUE-valid legacy-shape bundle (1 node, Lausanne/VD)."""
    return {
        "schema_version": "ckm-bundle-v1",
        "bundle_id": "nomos-built-environment-stub",
        "version": "2026.06-stub",
        "feeds": [
            {
                "feed_id": "vd-lausanne-rpga",
                "version": "vd-lausanne-rpga-2026-06",
                "jurisdiction": {"commune": "Lausanne", "canton": "VD"},
                "source_authority": "Commune de Lausanne",
                "valid_as_of": "2026-06-01",
                "review_due": "2026-12-01",
                "trace_manifest": {"bundle_sha256": "b" * 64, "feed_sha256": "c" * 64},
                "rag_metadata": {"NODE-ZONE-CENTRE": {"chunk_id": "chunk-1"}},
                "nodes": [
                    {
                        "node_id": "NODE-ZONE-CENTRE",
                        "text": "Zone centre: indice d'utilisation du sol 0.7.",
                        "source_path": "reglements/lausanne-rpga.pdf",
                        "source_hash": "a" * 64,
                        "span": {"start": 120, "end": 176},
                        "parent_chain": ["RPGA", "ART-7"],
                        "facets": {
                            "nature": "rule",
                            "scope_level": "atom",
                            "trust_tier": "certified",
                            "provenance": "source_backed",
                            "confidentiality": "public",
                        },
                        "claim": {
                            "claim_id": "lausanne-zone-centre",
                            "title": "Zone centre IUS",
                            "zone": "Zone centre",
                            "value": {"ius": 0.7},
                        },
                    }
                ],
            }
        ],
    }


def _client(tmp_path, monkeypatch, *, flag_on: bool, name: str):
    database_url = "sqlite:///" + (tmp_path / f"{name}.sqlite").as_posix()
    monkeypatch.setenv("AEDIFICA_DATABASE_URL", database_url)
    if flag_on:
        monkeypatch.setenv("AEDIFICA_NOMOS_ENABLED", "1")
    else:
        monkeypatch.delenv("AEDIFICA_NOMOS_ENABLED", raising=False)
    app = create_app(create_all=True)
    client = TestClient(app)
    r = client.post("/api/orgs", json={"org_name": f"Atelier {name}", "user_email": f"{name}@test.ch"})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    p = client.post(
        "/api/projects",
        json={"project_id": "P-CORPUS", "name": "Rue Centrale", "commune": "Lausanne", "canton": "VD"},
        headers=headers,
    )
    assert p.status_code == 201
    return client, headers


def test_corpus_flag_off_is_403_with_explicit_code(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch, flag_on=False, name="corpus-off")
    r = client.get("/api/projects/P-CORPUS/nomos/corpus", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "NOMOS_DISABLED"


def test_corpus_starts_empty_then_reflects_the_import_count_for_count(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch, flag_on=True, name="corpus-on")

    r0 = client.get("/api/projects/P-CORPUS/nomos/corpus", headers=headers)
    assert r0.status_code == 200
    corpus0 = r0.json()["corpus"]
    assert corpus0["jurisdiction"] == {"country": "CH", "canton": "VD", "commune": "Lausanne"}
    assert corpus0["jurisdiction_chunks"] == 0
    assert corpus0["project_chunks"] == 0
    assert corpus0["embedded"] == 0
    assert corpus0["sources"] == 0
    assert corpus0["feeds"] == []

    imp = client.post(
        "/api/projects/P-CORPUS/nomos/import",
        json={"bundle": _bundle(), "activate": True},
        headers=headers,
    )
    assert imp.status_code == 200, imp.text
    imported = imp.json()["imported"]

    r1 = client.get("/api/projects/P-CORPUS/nomos/corpus", headers=headers)
    assert r1.status_code == 200
    corpus = r1.json()["corpus"]
    # Count-for-count against what the importer reported — never invented.
    assert corpus["jurisdiction_chunks"] == imported["chunks"] == 1
    assert corpus["embedded"] == imported["embedded"] == 1
    assert corpus["project_chunks"] == 0
    assert corpus["sources"] == 1
    assert corpus["by_tier"]["certified"] == 1
    assert corpus["by_tier"]["indicative"] == 0
    assert corpus["by_tier"]["unverified"] == 0
    assert [f["version"] for f in corpus["feeds"]] == ["vd-lausanne-rpga-2026-06"]
    assert corpus["feeds"][0]["feed_id"] == "vd-lausanne-rpga"
    assert corpus["feeds"][0]["bundle_id"] == "nomos-built-environment-stub"
    assert corpus["feeds"][0]["status"] == "supported"


def test_corpus_is_scoped_to_the_project_jurisdiction(tmp_path, monkeypatch):
    client, headers = _client(tmp_path, monkeypatch, flag_on=True, name="corpus-scope")
    imp = client.post(
        "/api/projects/P-CORPUS/nomos/import",
        json={"bundle": _bundle(), "activate": True},
        headers=headers,
    )
    assert imp.status_code == 200

    # Same atelier, different commune: the Lausanne corpus must NOT leak there.
    p = client.post(
        "/api/projects",
        json={"project_id": "P-GE", "name": "Quai du Seujet", "commune": "Genève", "canton": "GE"},
        headers=headers,
    )
    assert p.status_code == 201
    r = client.get("/api/projects/P-GE/nomos/corpus", headers=headers)
    assert r.status_code == 200
    corpus = r.json()["corpus"]
    assert corpus["jurisdiction_chunks"] == 0
    assert corpus["sources"] == 0
    assert corpus["feeds"] == []
