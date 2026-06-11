"""Self-seeding demo so https://aedifica-demo.fly.dev/workspace is a FULLY
FUNCTIONAL showcase of the current feature set, not an empty login screen.

Philosophy (extends W21-0 « auto-deploy so the demo never goes stale » to the
DATA): on boot, when AEDIFICA_SEED_DEMO is on, ensure a rich demo atelier
exists — a real Lausanne project with a seeded SIA checklist, intervenants,
documents, the operating-layer reports, the NOMOS canonical corpus imported
(so the Copilote doctrine actually CITES with honest trust tiers), and the
Communes référentiels populated through the full request→ingest→promote
lifecycle.

Safety contract:
- It only ever touches the demo org (owner = DEMO_EMAIL). Real ateliers
  (e.g. the Etienne pilot) are never read or mutated.
- It is version-gated: when SEED_VERSION changes, the old demo org is dropped
  (project-scoped data cascades) and rebuilt — the shared, capitalizable pools
  (JurisdictionKnowledgeChunk, CommunePack) are content-addressed/idempotent
  and survive, so no other org's retrieval is affected.
- It is fail-soft: any error is swallowed and logged. A demo-seed failure must
  NEVER prevent the API from booting.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from sqlalchemy import select

from ..db import models as m
from ..db import repository
from ..ingestion import service as commune_service
from ..ingestion.nomos_bundle import NomosBundleError, import_nomos_bundle
from . import auth, reports
from . import sia_checklist as _siacl

log = logging.getLogger("aedifica.seed_demo")

# Bump to force a clean rebuild of the demo atelier on the next boot.
# 2026-06-11b — clean-slate reset: on this rebuild, when AEDIFICA_RESET_ATELIERS
# is set (the Fly demo opts in), EVERY pre-existing atelier is purged so the
# deployed demo holds only the current showcase, nothing created before the maj.
SEED_VERSION = "2026-06-11b"
DEMO_EMAIL = "demo@aedifica.ch"
DEMO_PASSWORD = "demo123"
DEMO_ORG_NAME = f"Atelier Démo Aedifica ({SEED_VERSION})"
DEMO_PROJECT_ID = "DEMO-LAUSANNE"

_BUNDLE_PATH = Path(__file__).with_name("demo_assets") / "canonical-bundle.json"


def _demo_orgs(session) -> list[m.Org]:
    """Every org that owns a DEMO_EMAIL user — the demo's footprint, nothing else."""
    org_ids = {
        uid
        for (uid,) in session.execute(
            select(m.User.org_id).where(m.User.email == DEMO_EMAIL)
        )
    }
    if not org_ids:
        return []
    return list(session.execute(select(m.Org).where(m.Org.id.in_(org_ids))).scalars())


def _is_current(orgs: list[m.Org]) -> bool:
    return any(o.name == DEMO_ORG_NAME for o in orgs)


def seed_demo(session, *, nomos_enabled: bool, reset_others: bool = False) -> dict | None:
    """Ensure the demo atelier reflects the current build. Returns a small
    summary dict when it (re)built, None when already current.

    When ``reset_others`` is set, the rebuild path ALSO purges every other
    atelier (clean slate) — a deliberate, version-gated sweep that only fires
    on a SEED_VERSION transition, never on a routine auto-start boot, so
    ateliers a visitor creates after the sweep are never touched.
    """
    existing = _demo_orgs(session)
    if _is_current(existing):
        return None

    # Version drift (or first boot): drop the old demo footprint, rebuild fresh.
    # With reset_others, drop EVERY atelier — the clean-slate reset.
    if reset_others:
        purged = 0
        for org in session.execute(select(m.Org)).scalars():
            session.delete(org)
            purged += 1
        log.info("demo seed: clean-slate reset purged %d atelier(s)", purged)
    else:
        for org in existing:
            session.delete(org)
    session.flush()

    org = m.Org(name=DEMO_ORG_NAME)
    session.add(org)
    session.flush()
    owner = m.User(
        org_id=org.id,
        email=DEMO_EMAIL,
        name="Architecte démo",
        role="owner",
        api_token=auth.new_token(),
        password_hash=auth.hash_password(DEMO_PASSWORD),
    )
    session.add(owner)
    session.flush()

    project = repository.create_project(
        session, org.id, DEMO_PROJECT_ID, "Villa des Cèdres — Lausanne",
        commune="Lausanne", country="CH", canton="VD", phase_code="31",
    )

    # SIA checklist seeded at phase 31 (earlier phases retroactive); mark the
    # first couple done so the dashboard shows real progress, not a blank slate.
    rows = _siacl.seed_rows("31")
    done = 0
    for r in rows:
        item = m.ChecklistItem(project_id=project.id, **r)
        if not item.is_retroactive and item.actor == "architecte" and done < 3:
            item.status = "done"
            done += 1
        session.add(item)

    # Operating layer: the reference dossier so permit/compliance/cost/site
    # surfaces have content (KPIs alive).
    reports.seed_reference_reports(project)

    # Intervenants: client (MO) + an engineering discipline with a person.
    session.add(m.Intervenant(
        project_id=project.id, name="M. & Mme Berger", role="maître de l'ouvrage",
        email="berger@example.ch", is_responsible=False,
    ))
    group = m.IntervenantGroup(project_id=project.id, name="Ingénierie civile", kind="discipline")
    session.add(group)
    session.flush()
    engineer = m.Intervenant(
        project_id=project.id, group_id=group.id, name="A. Civilis",
        role="ingénieur civil", organization="Civilis SA", email="a@civilis.ch",
        is_responsible=True,
    )
    session.add(engineer)

    # Documents: a pending permit (validation queue) + a canonical-promoted
    # piece (W22-1) so the doctrine can cite the atelier's own source.
    pending = m.Document(
        project_id=project.id, official_name="Permis CAMAC 2026-0421 (à valider)",
        category="permit", validation_level="pending",
    )
    session.add(pending)
    canonical = m.Document(
        project_id=project.id, official_name="Note de conformité énergétique (SIA 380/1)",
        category="conformite", validation_level="canonical",
        validated_by=owner.name, validated_at="2026-06-01",
    )
    session.add(canonical)
    session.flush()
    session.add(m.DocumentVersion(document_id=canonical.id, label="v1", source="manual"))

    # BRS register + a séance capture so the operating surfaces are populated.
    session.add(m.BrsEntry(
        project_id=project.id, content="Toiture plate végétalisée souhaitée (réunion du 03.06).",
        kind="requirement", channel="meeting", emitter_label="M. & Mme Berger",
    ))
    session.add(m.CaptureNote(
        project_id=project.id, kind="seance",
        content="Séance de cadrage : gabarit et recul nord à confirmer avec la commune.",
        author=owner.name,
    ))

    # Communes référentiels: the static supported packs (Lausanne/Pully) + a
    # fresh request (seed) + an ingested→promoted pack, i.e. the whole W22-2
    # lifecycle visible in one view. Each guarded so a shared cache survives.
    commune_service.seed_from_static(session)
    if not _pack_exists(session, "Renens", "VD"):
        commune_service.request_commune(session, "Renens", "VD")
    if not _pack_exists(session, "Prilly", "VD", status="supported"):
        ingested = commune_service.ingest_pack(
            session, "Prilly", "VD", version="prilly-rpga-2026-06",
            zones={"Zone village": {"ius": 0.45, "hauteur_max_m": 9}},
            source_authority="Commune de Prilly / géoportail VD",
            valid_as_of="2026-06-01", review_due="2026-12-01",
            sources=[{"title": "RPGA Prilly", "url": "https://www.prilly.ch"}],
        )
        commune_service.promote(session, ingested.id)

    summary = {"org": org.name, "project": project.project_id, "nomos": False}

    # NOMOS canonical corpus → the Lausanne jurisdiction pool, so the Copilote
    # doctrine answers with real cited sources (cite-or-abstain) and the Corpus
    # view is populated. Not activated: Terrain keeps the static pack's zones.
    if nomos_enabled and _BUNDLE_PATH.exists():
        try:
            bundle = json.loads(_BUNDLE_PATH.read_text(encoding="utf-8"))
            # Unique pack version per seed version → reseeds never collide with
            # the immutable cache; jurisdiction chunks dedupe by content.
            bundle["bundle_id"] = f"aedifica-demo-{SEED_VERSION}"
            imported = import_nomos_bundle(
                session, project, bundle, nomos_enabled=True, activate=False,
            )
            summary["nomos"] = {"chunks": imported.get("chunks"), "claims": imported.get("claims")}
        except (NomosBundleError, Exception) as exc:  # noqa: BLE001 - fail soft
            log.warning("demo seed: NOMOS bundle import skipped: %s", exc)

    session.commit()
    log.info("demo seed: rebuilt %s", summary)
    return summary


def _pack_exists(session, commune: str, canton: str, status: str | None = None) -> bool:
    q = session.query(m.CommunePack).filter_by(commune=commune, canton=canton)
    if status is not None:
        q = q.filter_by(status=status)
    return session.query(q.exists()).scalar()


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def maybe_seed_demo(session_factory, *, nomos_enabled: bool) -> None:
    """Boot hook: run the seed in its own session, fail-soft. Never raises."""
    if not _flag("AEDIFICA_SEED_DEMO"):
        return
    reset_others = _flag("AEDIFICA_RESET_ATELIERS")
    try:
        with session_factory() as session:
            result = seed_demo(session, nomos_enabled=nomos_enabled, reset_others=reset_others)
        if result is None:
            log.info("demo seed: already current (%s)", SEED_VERSION)
    except Exception as exc:  # noqa: BLE001 - a demo seed must never break boot
        log.warning("demo seed: skipped after error: %s", exc)
