"""W22-1 — canon promu: a canonical document feeds the project knowledge silo.

The master architect's canonical validation IS the promotion act (séance §E).
These tests prove the full loop through the real API: promote -> the doctrine
cites the atelier's own piece (indicative / user_promoted — a promoted source
never usurps the official certified) -> demote -> retracted, the doctrine
abstains again. Plus: project isolation, deletion cleanup, and the flag-OFF
contract staying byte-compatible.
"""
from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402

EXTRACT = "La hauteur maximale au faîte est limitée à 9 mètres en zone village."


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
        json={"project_id": "P-CANON", "name": "Rue Centrale", "commune": "Lausanne", "canton": "VD"},
        headers=headers,
    )
    assert p.status_code == 201
    return client, headers


def _create_doc(client, headers, project="P-CANON", name="RPGA art. 12 — hauteurs"):
    r = client.post(f"/api/projects/{project}/documents",
                    json={"official_name": name, "category": "reglement", "source": "manual", "confidential": False},
                    headers=headers)
    assert r.status_code == 201
    return r.json()["document"]["id"]


def test_canonical_promotion_feeds_the_silo_and_the_doctrine_cites_it(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-on")
    doc_id = _create_doc(client, h)

    # Baseline: empty silo, the doctrine abstains.
    corpus0 = client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]
    assert corpus0["project_chunks"] == 0
    a0 = client.post("/api/projects/P-CANON/copilote/nomos",
                     json={"question": "Quelle hauteur maximale au faîte ?"}, headers=h).json()
    assert a0["citations"] == []

    # Promotion: canonical + citable extract.
    v = client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                    json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    assert v.status_code == 200
    assert v.json()["citable"] is True

    corpus = client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]
    assert corpus["project_chunks"] == 1
    assert corpus["embedded"] >= 1  # embedding ran at promotion time

    # The doctrine NOW cites the atelier's own piece — honestly tiered.
    a1 = client.post("/api/projects/P-CANON/copilote/nomos",
                     json={"question": "Quelle hauteur maximale au faîte ?"}, headers=h).json()
    assert a1["citations"], a1
    cit = a1["citations"][0]
    assert cit["scope"] == "project"
    assert cit["source_path"] == "RPGA art. 12 — hauteurs"
    assert cit["trust_tier"] == "indicative"   # never usurps certified
    assert cit["provenance"] == "user_promoted"
    assert cit["source_hash"].startswith("sha256:")
    assert a1["requires_human_decision"] is True
    assert EXTRACT in a1["answer"]

    # The documents list carries the citable flag for the UI chip.
    docs = client.get("/api/projects/P-CANON/documents", headers=h).json()["documents"]
    assert [d["citable"] for d in docs] == [True]


def test_repromotion_with_a_new_extract_reembeds_and_recites(tmp_path, monkeypatch):
    """The update path: same document, corrected extract -> the silo follows."""
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-repro")
    doc_id = _create_doc(client, h)
    client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    corrected = "La hauteur maximale au faîte est limitée à 12 mètres en zone village (révision)."
    v = client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                    json={"level": "canonical", "citable_text": corrected}, headers=h)
    assert v.status_code == 200 and v.json()["citable"] is True
    corpus = client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]
    assert corpus["project_chunks"] == 1   # updated in place, never duplicated
    assert corpus["embedded"] == 1         # re-embedded after the text change
    a = client.post("/api/projects/P-CANON/copilote/nomos",
                    json={"question": "Quelle hauteur maximale au faîte ?"}, headers=h).json()
    assert a["citations"], a
    assert corrected in a["answer"]
    assert EXTRACT not in a["answer"]


def test_demotion_retracts_the_chunk_and_the_doctrine_abstains_again(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-retract")
    doc_id = _create_doc(client, h)
    client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    assert client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]["project_chunks"] == 1

    # Revert-and-confirm: demote to indicative -> the chunk is GONE.
    v = client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                    json={"level": "indicative"}, headers=h)
    assert v.status_code == 200 and v.json()["citable"] is False
    assert client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]["project_chunks"] == 0
    a = client.post("/api/projects/P-CANON/copilote/nomos",
                    json={"question": "Quelle hauteur maximale au faîte ?"}, headers=h).json()
    assert a["citations"] == [] and a["requires_human_decision"] is True


def test_deleting_the_document_leaves_no_orphan_chunk(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-delete")
    doc_id = _create_doc(client, h)
    client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    client.delete(f"/api/projects/P-CANON/documents/{doc_id}", headers=h)
    assert client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]["project_chunks"] == 0


def test_promoted_canon_is_project_siloed(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-silo")
    doc_id = _create_doc(client, h)
    client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    # Same atelier, same commune, OTHER project: the promoted piece must not leak.
    client.post("/api/projects",
                json={"project_id": "P-AUTRE", "name": "Autre", "commune": "Lausanne", "canton": "VD"},
                headers=h)
    corpus = client.get("/api/projects/P-AUTRE/nomos/corpus", headers=h).json()["corpus"]
    assert corpus["project_chunks"] == 0
    a = client.post("/api/projects/P-AUTRE/copilote/nomos",
                    json={"question": "Quelle hauteur maximale au faîte ?"}, headers=h).json()
    assert a["citations"] == []


def test_canonical_without_extract_sets_level_but_promotes_nothing(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=True, name="canon-noext")
    doc_id = _create_doc(client, h)
    v = client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                    json={"level": "canonical"}, headers=h)
    assert v.status_code == 200
    assert v.json()["document"]["validation_level"] == "canonical"
    assert v.json()["citable"] is False  # nothing citable was provided — honest
    assert client.get("/api/projects/P-CANON/nomos/corpus", headers=h).json()["corpus"]["project_chunks"] == 0


def test_flag_off_validation_contract_is_unchanged(tmp_path, monkeypatch):
    client, h = _client(tmp_path, monkeypatch, flag_on=False, name="canon-off")
    doc_id = _create_doc(client, h)
    v = client.post(f"/api/projects/P-CANON/documents/{doc_id}/validate",
                    json={"level": "canonical", "citable_text": EXTRACT}, headers=h)
    assert v.status_code == 200
    assert v.json()["document"]["validation_level"] == "canonical"
    # The retrieval surfaces stay gated.
    assert client.get("/api/projects/P-CANON/nomos/corpus", headers=h).status_code == 403