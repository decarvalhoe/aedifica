"""Shared product test fixtures: in-memory app + bootstrapped owner token."""
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
from aedifica.db import Base  # noqa: E402


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def client(engine):
    return TestClient(create_app(engine=engine))


@pytest.fixture()
def owner(client):
    """Bootstrap an org + owner; return the bearer auth headers."""
    r = client.post("/api/orgs", json={"org_name": "Atelier Test", "user_email": "owner@test.ch"})
    assert r.status_code == 201
    token = r.json()["token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}
