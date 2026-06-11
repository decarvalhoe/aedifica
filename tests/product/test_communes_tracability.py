"""W22-2 — packs communaux traçables de la demande à la promotion (via l'API).

The enriched /api/communes list carries the official-source register
(authority, validity, review) + every ingestion job, so the UI can follow a
pack end-to-end without touching the DB. Shape is a superset of the historic
one (additive only — test_ingestion.py keeps passing untouched).
"""
from __future__ import annotations


def test_pack_follows_request_ingest_promote_with_full_traceability(client, owner):
    h = owner["headers"]

    # 1. Request: seed pack + a traced 'requested' job, no fabricated values.
    r = client.post("/api/communes", json={"commune": "Vevey", "canton": "VD"}, headers=h)
    assert r.status_code == 201

    packs = client.get("/api/communes", headers=h).json()["communes"]
    seed = next(p for p in packs if p["commune"] == "Vevey" and p["status"] == "seed")
    assert seed["version"] == "seed"
    assert seed["source_authority"]  # the default authority hint, never empty
    assert seed["nomos"] is False
    assert seed["n_zones"] == 0
    assert [j["status"] for j in seed["jobs"]] == ["requested"]
    assert "capture the official règlement" in seed["jobs"][0]["notes"]

    # 2. Manual ingest of the official règlement: NEW immutable version row,
    #    'done' job, full provenance register.
    r = client.post(f"/api/communes/{seed['id']}/ingest", json={
        "version": "vevey-rpga-2026-06",
        "zones": {"Zone village": {"ius": 0.4, "hauteur_max_m": 9}},
        "source_authority": "Commune de Vevey",
        "valid_as_of": "2026-06-01",
        "review_due": "2026-12-01",
        "sources": [{"title": "RPGA Vevey", "url": "https://www.vevey.ch/rpga"}],
    }, headers=h)
    assert r.status_code == 200, r.text
    ingested_id = r.json()["ingested"]["id"]

    packs = client.get("/api/communes", headers=h).json()["communes"]
    ing = next(p for p in packs if p["id"] == ingested_id)
    assert ing["status"] == "ingested"
    assert ing["version"] == "vevey-rpga-2026-06"
    assert ing["source_authority"] == "Commune de Vevey"
    assert ing["valid_as_of"] == "2026-06-01"
    assert ing["review_due"] == "2026-12-01"
    assert ing["ingested_at"]
    assert ing["n_zones"] == 1
    assert [j["status"] for j in ing["jobs"]] == ["done"]
    assert ing["jobs"][0]["n_sources"] == 1
    # The seed row survives untouched (immutable versions, no mutation).
    assert any(p["id"] == seed["id"] and p["status"] == "seed" for p in packs)

    # 3. Promote after human review: ingested -> supported, usable for projects.
    r = client.post(f"/api/communes/{ingested_id}/promote", headers=h)
    assert r.status_code == 200
    packs = client.get("/api/communes", headers=h).json()["communes"]
    assert next(p for p in packs if p["id"] == ingested_id)["status"] == "supported"

    support = client.get("/api/communes/Vevey/VD/support", headers=h).json()["support"]
    assert support["usable"] is True
    assert support["version"] == "vevey-rpga-2026-06"


def test_register_contradicting_pair_is_refused(client, owner):
    """W22-2b — the « Neuchâtel (VD) » shame case: a commune the OFS register
    KNOWS cannot enter the shared cache under the wrong canton."""
    h = owner["headers"]
    r = client.post("/api/communes", json={"commune": "Neuchâtel", "canton": "VD"}, headers=h)
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "COMMUNE_CANTON_MISMATCH"
    assert "NE" in detail["message"]  # the register's canton is NAMED

    # The registered canton sails through.
    r = client.post("/api/communes", json={"commune": "Neuchâtel", "canton": "NE"}, headers=h)
    assert r.status_code == 201

    # Out-of-register communes stay accepted (the register is the authority
    # only on what it contains — test/fictional communes keep working).
    r = client.post("/api/communes", json={"commune": "Commune-Fictive-W22b", "canton": "VD"}, headers=h)
    assert r.status_code == 201


def test_project_creation_refuses_register_contradicting_pair(client, owner):
    """W23-5 — the SAME guard covers project creation (the original hole: a
    « Neuchâtel (VD) » PROJECT was creatable with an explicit wrong canton)."""
    h = owner["headers"]
    r = client.post("/api/projects",
                    json={"project_id": "P-NEVD", "name": "X", "commune": "Neuchâtel", "canton": "VD"},
                    headers=h)
    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "COMMUNE_CANTON_MISMATCH"
    assert "NE" in detail["message"]

    r = client.post("/api/projects",
                    json={"project_id": "P-NENE", "name": "X", "commune": "Neuchâtel", "canton": "NE"},
                    headers=h)
    assert r.status_code == 201

    # Unknown communes keep working with an explicit canton (picker contract).
    r = client.post("/api/projects",
                    json={"project_id": "P-FICT", "name": "X", "commune": "Fictive-W23-5", "canton": "VD"},
                    headers=h)
    assert r.status_code == 201


def test_withdraw_removes_only_seed_scaffolds(client, owner):
    """W22-2b — a request scaffold is withdrawable; an ingested referential
    version is immutable (the capitalizable-cache promise)."""
    h = owner["headers"]
    client.post("/api/communes", json={"commune": "Morges", "canton": "VD"}, headers=h)
    packs = client.get("/api/communes", headers=h).json()["communes"]
    seed = next(p for p in packs if p["commune"] == "Morges" and p["status"] == "seed")

    r = client.delete(f"/api/communes/{seed['id']}", headers=h)
    assert r.status_code == 200
    packs = client.get("/api/communes", headers=h).json()["communes"]
    assert not any(p["id"] == seed["id"] for p in packs)  # jobs cascade with it

    # Adversarial: ingested -> the withdrawal is refused and the pack survives.
    seed_r = client.post("/api/communes", json={"commune": "Pully", "canton": "VD"}, headers=h)
    ing = client.post(f"/api/communes/{seed_r.json()['requested']['id']}/ingest", json={
        "version": "pully-w22b-test",
        "zones": {"Zone test": {"ius": 0.3}},
        "source_authority": "Commune de Pully",
        "valid_as_of": "2026-06-01",
        "review_due": "2026-12-01",
        "sources": [],
    }, headers=h)
    assert ing.status_code == 200
    ingested_id = ing.json()["ingested"]["id"]
    r = client.delete(f"/api/communes/{ingested_id}", headers=h)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "PACK_NOT_SEED"
    packs = client.get("/api/communes", headers=h).json()["communes"]
    assert any(p["id"] == ingested_id for p in packs)  # still there, immutable


def test_promote_refuses_a_seed_pack(client, owner):
    """Adversarial: promotion is gated on a real ingested version — a seed
    scaffold cannot be promoted into reliance."""
    h = owner["headers"]
    client.post("/api/communes", json={"commune": "Nyon", "canton": "VD"}, headers=h)
    packs = client.get("/api/communes", headers=h).json()["communes"]
    seed = next(p for p in packs if p["commune"] == "Nyon" and p["status"] == "seed")
    r = client.post(f"/api/communes/{seed['id']}/promote", headers=h)
    assert r.status_code == 200  # endpoint answers, but…
    packs = client.get("/api/communes", headers=h).json()["communes"]
    assert next(p for p in packs if p["id"] == seed["id"])["status"] == "seed"  # …no silent upgrade
