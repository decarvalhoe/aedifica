"""On-demand commune ingestion: seed -> ingested -> supported, no fabricated values."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.db import Base, make_engine, make_session_factory  # noqa: E402
from aedifica.ingestion import service as ingestion  # noqa: E402
from aedifica.api.config import get_settings  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def test_request_is_seed_and_not_usable(session):
    pack = ingestion.request_commune(session, "Vevey", "VD")
    session.commit()
    assert pack.status == "seed" and pack.data == {}
    state = ingestion.support_state(session, "Vevey", "VD")
    assert state["state"] == "seed" and state["usable"] is False


def test_ingest_then_promote_makes_supported(session):
    ingestion.ingest_pack(session, "Vevey", "VD", "RCC-2021", {"Zone test": {"ius": 0.6}}, "Commune de Vevey", "2026-06-01", "2026-12-01")
    session.commit()
    state = ingestion.support_state(session, "Vevey", "VD")
    assert state["state"] == "ingested" and state["usable"] is False
    ingestion.promote(session, state["pack_id"])
    session.commit()
    assert ingestion.support_state(session, "Vevey", "VD")["usable"] is True


def test_seed_from_static_loads_pilot_packs(session):
    created = ingestion.seed_from_static(session)
    session.commit()
    assert {"Lausanne", "Pully"}.issubset(set(created))
    assert ingestion.support_state(session, "Lausanne", "VD")["usable"] is True


def test_unknown_commune_is_unsupported(session):
    assert ingestion.support_state(session, "Genève", "GE")["state"] == "unsupported"


def test_commune_api_lifecycle(client, owner):
    h = owner["headers"]
    r = client.post("/api/communes", json={"commune": "Vevey", "canton": "VD"}, headers=h)
    assert r.status_code == 201 and r.json()["requested"]["status"] == "seed"
    assert client.get("/api/communes/Vevey/VD/support", headers=h).json()["support"]["usable"] is False
    pack_id = client.get("/api/communes", headers=h).json()["communes"][0]["id"]
    ing = client.post(f"/api/communes/{pack_id}/ingest", json={"version": "RCC-2021", "zones": {"Z": {"ios": 0.2}}, "source_authority": "Commune de Vevey", "valid_as_of": "2026-06-01", "review_due": "2026-12-01"}, headers=h)
    assert ing.status_code == 200
    new_id = ing.json()["ingested"]["id"]
    assert client.post(f"/api/communes/{new_id}/promote", headers=h).json()["promoted"]["status"] == "supported"
    assert client.get("/api/communes/Vevey/VD/support", headers=h).json()["support"]["usable"] is True


def test_nomos_flag_off_preserves_commune_ingestion_lifecycle(monkeypatch, session):
    monkeypatch.setenv("AEDIFICA_NOMOS_ENABLED", "0")
    assert get_settings().nomos_enabled is False

    requested = ingestion.request_commune(session, "Montreux", "VD")
    session.commit()
    assert requested.status == "seed"
    assert requested.data == {}

    seed_state = ingestion.support_state(session, "Montreux", "VD")
    assert seed_state["state"] == "seed"
    assert seed_state["usable"] is False
    assert seed_state["required_inputs"] == ingestion.REQUIRED_INPUTS

    ingested = ingestion.ingest_pack(
        session,
        "Montreux",
        "VD",
        "RCC-2024",
        {"Zone centre": {"ius": 0.7}},
        "Commune de Montreux",
        "2026-06-01",
        "2026-12-01",
        sources=[{"locator": "https://example.test/rcc.pdf", "sha256": "a" * 64}],
    )
    session.commit()
    assert ingested.status == "ingested"
    assert ingested.data == {"zones": {"Zone centre": {"ius": 0.7}}}
    assert ingestion.support_state(session, "Montreux", "VD")["usable"] is False

    ingestion.promote(session, ingested.id)
    session.commit()
    supported = ingestion.support_state(session, "Montreux", "VD")
    assert supported["state"] == "supported"
    assert supported["usable"] is True
