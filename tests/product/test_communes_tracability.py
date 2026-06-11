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
