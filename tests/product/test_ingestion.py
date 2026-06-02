"""On-demand commune ingestion: seed -> ingested -> supported, no fabricated values."""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402
from aedifica.db import Base, make_engine, make_session_factory  # noqa: E402
from aedifica.ingestion import service as ingestion  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
    Base.metadata.create_all(engine)
    return TestClient(create_app(engine=engine))


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


def test_commune_api_lifecycle(client):
    r = client.post("/api/communes", json={"commune": "Vevey", "canton": "VD"})
    assert r.status_code == 201 and r.json()["requested"]["status"] == "seed"
    assert client.get("/api/communes/Vevey/VD/support").json()["support"]["usable"] is False
    pack_id = client.get("/api/communes").json()["communes"][0]["id"]
    ing = client.post(f"/api/communes/{pack_id}/ingest", json={"version": "RCC-2021", "zones": {"Z": {"ios": 0.2}}, "source_authority": "Commune de Vevey", "valid_as_of": "2026-06-01", "review_due": "2026-12-01"})
    assert ing.status_code == 200
    new_id = ing.json()["ingested"]["id"]
    assert client.post(f"/api/communes/{new_id}/promote").json()["promoted"]["status"] == "supported"
    assert client.get("/api/communes/Vevey/VD/support").json()["support"]["usable"] is True
