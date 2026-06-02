"""Product DB model tests — trust invariant + round-trip (SQLite in-memory).

Run: python -m pytest tests/product/test_models.py
Requires the `product` + `test` optional dependencies (SQLAlchemy, pytest).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.db import (  # noqa: E402
    Base,
    Claim,
    Org,
    Project,
    Source,
    TrustInvariantError,
    User,
    make_engine,
    make_session_factory,
)


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")  # in-memory
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def _project(session) -> Project:
    org = Org(name="Atelier Test")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email="a@test.ch", name="Architecte", role="owner"))
    project = Project(org_id=org.id, project_id="DEMO-PALUD", name="Palud", commune="Lausanne", phase_code="31")
    session.add(project)
    session.flush()
    return project


def test_sourced_regulatory_claim_without_evidence_is_rejected(session):
    project = _project(session)
    session.add(Claim(project_id=project.id, claim_id="C1", title="Zone", claim_type="regulatory", state="sourced", value="Zone X", source_refs=[]))
    with pytest.raises(TrustInvariantError):
        session.flush()


def test_sourced_claim_with_source_refs_persists(session):
    project = _project(session)
    session.add(Source(project_id=project.id, source_id="VD-OEREB", title="OEREB", kind="api_extract", valid_as_of="2026-05-29"))
    session.add(Claim(project_id=project.id, claim_id="C1", title="Zone", claim_type="regulatory", state="sourced", value="Zone X", source_refs=[{"source_id": "VD-OEREB"}]))
    session.commit()
    got = session.query(Claim).filter_by(claim_id="C1").one()
    assert got.state == "sourced" and got.source_refs[0]["source_id"] == "VD-OEREB"


def test_unknown_claim_without_source_refs_is_allowed(session):
    project = _project(session)
    session.add(Claim(project_id=project.id, claim_id="C2", title="SBP", claim_type="regulatory", state="unknown", value=None, source_refs=[], next_action="vérifier le règlement"))
    session.commit()
    assert session.query(Claim).filter_by(claim_id="C2").one().state == "unknown"


def test_multitenant_scoping_round_trip(session):
    p = _project(session)
    session.commit()
    assert session.query(Project).filter_by(org_id=p.org_id).count() == 1
    assert session.query(User).filter_by(org_id=p.org_id).one().role == "owner"
