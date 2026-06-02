"""Repository round-trip: the engine brief persists with identical trust states."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica import workspace  # noqa: E402  (engine facade over pilot)
from aedifica.db import Base, make_engine, make_session_factory  # noqa: E402
from aedifica.db import repository  # noqa: E402

DEMO = os.path.join(ROOT, "pilot", "projects", "demo_lausanne_palud")


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def test_brief_round_trips_with_identical_trust_states(session):
    brief = workspace.generate_offline_parcel_brief(DEMO)
    org = repository.get_or_create_org(session)
    project = repository.create_project(
        session, org.id, brief["project_id"], brief["project_summary"]["name"], commune="Lausanne"
    )
    counts = repository.save_brief(session, project, brief)
    session.commit()

    db_states = {c["claim_id"]: c["state"] for c in repository.claims_for(session, project)}
    engine_states = {c["claim_id"]: c["state"] for c in brief["claims"]}
    assert db_states == engine_states
    assert counts["claims"] == len(brief["claims"])

    summary = repository.project_summary(session, project)
    assert summary["claims"] == len(brief["claims"])
    assert summary["sources"] >= 1


def test_report_and_ledger_persist(session):
    org = repository.get_or_create_org(session)
    project = repository.create_project(session, org.id, "P1", "P1", commune="Lausanne")
    repository.save_report(
        session,
        project,
        {"report_id": "R1", "kind": "parcel_brief", "path": "reports/r1.json", "content_sha256": "a" * 64, "source_refs": [{"source_id": "VD-OEREB"}]},
    )
    repository.save_ledger_entry(
        session,
        project,
        {
            "ledger_id": "LED-1",
            "event_type": "report_generation",
            "summary": "Generated R1",
            "actor": {"name": "Architecte", "role": "architect"},
            "phase": {"phase_code": "0"},
            "content_sha256": "a" * 64,
        },
    )
    session.commit()
    summary = repository.project_summary(session, project)
    assert summary["reports"] == 1 and summary["ledger_entries"] == 1
