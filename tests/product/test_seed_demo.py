"""W23-6 — the self-seeding demo: a deployed boot turns the empty login screen
into a fully-functional showcase, version-gated, fail-soft, and scoped to the
demo org only."""
from __future__ import annotations

import pytest

from aedifica.api import auth
from aedifica.api import seed_demo as sd
from aedifica.db import models as m
from aedifica.db.session import make_session_factory


def _sf(engine):
    return make_session_factory(engine)


def test_seed_builds_a_fully_functional_atelier(engine):
    sf = _sf(engine)
    with sf() as s:
        summary = sd.seed_demo(s, nomos_enabled=True)
    assert summary is not None

    with sf() as s:
        # 1. A working, advertised login (the critical missing piece).
        user = s.query(m.User).filter_by(email=sd.DEMO_EMAIL).one()
        assert user.role == "owner"
        assert auth.verify_password(sd.DEMO_PASSWORD, user.password_hash)
        org = s.get(m.Org, user.org_id)
        assert org.name == sd.DEMO_ORG_NAME

        # 2. A real Lausanne project with the SIA checklist + operating layer.
        proj = s.query(m.Project).filter_by(org_id=org.id, project_id=sd.DEMO_PROJECT_ID).one()
        assert proj.commune == "Lausanne" and proj.canton == "VD"
        assert s.query(m.ChecklistItem).filter_by(project_id=proj.id).count() > 0
        assert s.query(m.ChecklistItem).filter_by(project_id=proj.id, status="done").count() >= 1
        assert proj.permit_dossier  # seed_reference_reports populated the dossier
        assert s.query(m.Intervenant).filter_by(project_id=proj.id).count() >= 2
        assert s.query(m.Document).filter_by(project_id=proj.id, validation_level="canonical").count() == 1

        # 3. Communes référentiels — the whole request→ingest→promote lifecycle.
        assert s.query(m.CommunePack).filter_by(commune="Lausanne", status="supported").count() >= 1
        assert s.query(m.CommunePack).filter_by(commune="Renens", status="seed").count() == 1
        assert s.query(m.CommunePack).filter_by(commune="Prilly", status="supported").count() == 1

        # 4. The NOMOS corpus lands in the Lausanne jurisdiction pool so the
        #    Copilote doctrine can cite real sources (cite-or-abstain alive).
        pool = s.query(m.JurisdictionKnowledgeChunk).filter_by(
            country="CH", canton="VD", commune="Lausanne"
        ).count()
        assert pool > 0
        assert isinstance(summary["nomos"], dict) and summary["nomos"]["chunks"] > 0


def test_seed_is_idempotent_when_current(engine):
    sf = _sf(engine)
    with sf() as s:
        assert sd.seed_demo(s, nomos_enabled=False) is not None
    with sf() as s:
        assert sd.seed_demo(s, nomos_enabled=False) is None  # already at SEED_VERSION


def test_seed_rebuilds_on_version_bump(engine, monkeypatch):
    sf = _sf(engine)
    with sf() as s:
        sd.seed_demo(s, nomos_enabled=False)
    with sf() as s:
        first_org_id = s.query(m.User).filter_by(email=sd.DEMO_EMAIL).one().org_id

    monkeypatch.setattr(sd, "SEED_VERSION", "test-next")
    monkeypatch.setattr(sd, "DEMO_ORG_NAME", "Atelier Démo Aedifica (test-next)")
    with sf() as s:
        assert sd.seed_demo(s, nomos_enabled=False) is not None  # rebuilt

    with sf() as s:
        users = s.query(m.User).filter_by(email=sd.DEMO_EMAIL).all()
        assert len(users) == 1  # the stale org was dropped, not duplicated
        # The single surviving demo org now carries the new version marker.
        assert s.get(m.Org, users[0].org_id).name == "Atelier Démo Aedifica (test-next)"
        # And the old org id is gone (or reused) — never two demo orgs at once.
        assert s.query(m.Org).filter(m.Org.name.like("Atelier Démo Aedifica%")).count() == 1
        _ = first_org_id


def test_seed_never_touches_other_orgs(engine):
    sf = _sf(engine)
    with sf() as s:
        other = m.Org(name="Vrai Atelier")
        s.add(other)
        s.flush()
        s.add(m.User(org_id=other.id, email="real@atelier.ch", name="Réel",
                     role="owner", api_token="tok-real-xyz"))
        s.commit()
        other_id = other.id
    with sf() as s:
        sd.seed_demo(s, nomos_enabled=True)
    with sf() as s:
        assert s.get(m.Org, other_id) is not None
        assert s.query(m.User).filter_by(email="real@atelier.ch").count() == 1


def test_maybe_seed_demo_is_noop_without_the_flag(engine, monkeypatch):
    monkeypatch.delenv("AEDIFICA_SEED_DEMO", raising=False)
    sf = _sf(engine)
    sd.maybe_seed_demo(sf, nomos_enabled=True)
    with sf() as s:
        assert s.query(m.User).filter_by(email=sd.DEMO_EMAIL).count() == 0


def test_maybe_seed_demo_runs_under_the_flag(engine, monkeypatch):
    monkeypatch.setenv("AEDIFICA_SEED_DEMO", "true")
    monkeypatch.delenv("AEDIFICA_RESET_ATELIERS", raising=False)
    sf = _sf(engine)
    sd.maybe_seed_demo(sf, nomos_enabled=False)
    with sf() as s:
        assert s.query(m.User).filter_by(email=sd.DEMO_EMAIL).count() == 1


def test_reset_others_wipes_every_pre_existing_atelier(engine):
    """W23-6b clean slate: with reset_others, the rebuild purges ALL ateliers
    (test orgs, ops orgs, the pilot — everything) and leaves only the demo."""
    sf = _sf(engine)
    with sf() as s:
        for name, email in [("Atelier Pilote", "etienne.pilote@aedifica.ch"),
                            ("Ops REFERENTIELS-CH", "ops@aedifica.ch"),
                            ("Org de test", "probe@test.ch")]:
            org = m.Org(name=name)
            s.add(org)
            s.flush()
            s.add(m.User(org_id=org.id, email=email, name=name, role="owner",
                         api_token=f"tok-{email}"))
        s.commit()
        assert s.query(m.Org).count() == 3

    with sf() as s:
        summary = sd.seed_demo(s, nomos_enabled=False, reset_others=True)
    assert summary is not None

    with sf() as s:
        orgs = s.query(m.Org).all()
        assert len(orgs) == 1  # only the demo survives
        assert orgs[0].name == sd.DEMO_ORG_NAME
        # the pilot and the test orgs are gone
        assert s.query(m.User).filter_by(email="etienne.pilote@aedifica.ch").count() == 0
        assert s.query(m.User).filter_by(email="probe@test.ch").count() == 0
        assert s.query(m.User).filter_by(email=sd.DEMO_EMAIL).count() == 1


def test_default_seed_does_not_wipe_other_ateliers(engine):
    """Without reset_others, a non-demo atelier is never touched (the default
    is conservative; only the opt-in Fly demo resets)."""
    sf = _sf(engine)
    with sf() as s:
        org = m.Org(name="Vrai Atelier")
        s.add(org)
        s.flush()
        s.add(m.User(org_id=org.id, email="real@atelier.ch", name="R", role="owner", api_token="tok-r"))
        s.commit()
    with sf() as s:
        sd.seed_demo(s, nomos_enabled=False, reset_others=False)
    with sf() as s:
        assert s.query(m.User).filter_by(email="real@atelier.ch").count() == 1
