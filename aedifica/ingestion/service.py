"""On-demand commune ingestion service over the SQL store."""
from __future__ import annotations

import datetime as _dt
import glob
import hashlib
import json
import os

from ..db import models as m

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PILOT = os.path.join(ROOT, "pilot")
STATUS_RANK = {"seed": 1, "ingested": 2, "supported": 3}
REQUIRED_INPUTS = [
    "Plan d'affectation communal (PGA/PACom) — official PDF",
    "Règlement communal des constructions (RCC/RPGA) — official PDF",
    "Cantonal geoportal layer reference",
    "Adoption / in-force date and revision status",
]


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def request_commune(session, commune: str, canton: str, source_authority: str | None = None) -> m.CommunePack:
    """Register a new commune at runtime in seed state — NO fabricated values."""
    pack = m.CommunePack(
        commune=commune,
        canton=canton,
        version="seed",
        status="seed",
        source_authority=source_authority or f"Commune de {commune} / géoportail {canton}",
        data={},
    )
    session.add(pack)
    session.flush()
    session.add(
        m.IngestionJob(
            commune_pack_id=pack.id,
            status="requested",
            sources=[],
            notes="seed scaffold — capture the official règlement before reliance; required: " + "; ".join(REQUIRED_INPUTS),
        )
    )
    session.flush()
    return pack


def ingest_pack(
    session,
    commune: str,
    canton: str,
    version: str,
    zones: dict,
    source_authority: str,
    valid_as_of: str,
    review_due: str,
    sources: list | None = None,
) -> m.CommunePack:
    """Ingest a captured/parsed commune pack (zones from the official règlement)."""
    pack = m.CommunePack(
        commune=commune,
        canton=canton,
        version=version,
        status="ingested",
        source_authority=source_authority,
        valid_as_of=valid_as_of,
        review_due=review_due,
        ingested_at=_now_iso(),
        data={"zones": zones},
    )
    session.add(pack)
    session.flush()
    session.add(m.IngestionJob(commune_pack_id=pack.id, status="done", sources=sources or [], notes="ingested"))
    session.flush()
    return pack


def promote(session, pack_id: int) -> m.CommunePack | None:
    """ingested -> supported (after human review)."""
    pack = session.get(m.CommunePack, pack_id)
    if pack and pack.status == "ingested":
        pack.status = "supported"
        session.flush()
    return pack


def support_state(session, commune: str, canton: str) -> dict:
    packs = session.query(m.CommunePack).filter_by(commune=commune, canton=canton).all()
    if not packs:
        return {"commune": commune, "canton": canton, "state": "unsupported",
                "usable": False, "pack_id": None,
                "required_inputs": list(REQUIRED_INPUTS),
                "job": None}
    best = max(packs, key=lambda p: STATUS_RANK.get(p.status, 0))
    # W14.A — surface honest job state: when did the request land, how old
    # is it, and what's actually needed before this commune becomes usable.
    job = (session.query(m.IngestionJob)
           .filter_by(commune_pack_id=best.id)
           .order_by(m.IngestionJob.id.desc()).first())
    job_dict = None
    if job:
        ts = getattr(job, "requested_at", None)
        created_iso = ts.isoformat() if ts else None
        age_days = None
        if ts:
            # SQLite can hand back naive datetimes — normalise both sides to
            # UTC-aware before subtracting so we always get a real int.
            try:
                if ts.tzinfo is None:
                    ts_aware = ts.replace(tzinfo=_dt.timezone.utc)
                else:
                    ts_aware = ts
                age_days = (_dt.datetime.now(_dt.timezone.utc) - ts_aware).days
            except Exception:
                age_days = None
        job_dict = {"id": job.id, "status": job.status,
                    "requested_at": created_iso, "age_days": age_days,
                    "notes": job.notes}
    return {
        "commune": commune,
        "canton": canton,
        "state": best.status,
        "usable": best.status == "supported",
        "pack_id": best.id,
        "version": best.version,
        "required_inputs": list(REQUIRED_INPUTS) if best.status != "supported" else [],
        "job": job_dict,
    }


def list_packs(session) -> list[dict]:
    """W22-2 — full traceability per pack: the official-source register
    (authority, validity, review) + every ingestion job, so a pack can be
    followed from the request to the promotion without touching the DB.
    Superset of the historical shape (additive keys only)."""
    out = []
    for p in session.query(m.CommunePack).order_by(m.CommunePack.commune, m.CommunePack.id).all():
        out.append({
            "id": p.id, "commune": p.commune, "canton": p.canton, "version": p.version,
            "status": p.status, "review_due": p.review_due,
            "source_authority": p.source_authority,
            "valid_as_of": p.valid_as_of,
            "ingested_at": p.ingested_at,
            # A pack fed by a NOMOS bundle (vs OFS-direct / manual capture).
            "nomos": bool((p.data or {}).get("nomos")),
            "n_zones": len((p.data or {}).get("zones") or {}),
            "jobs": [
                {"id": j.id, "status": j.status, "notes": j.notes,
                 "requested_at": str(j.requested_at) if j.requested_at else None,
                 "n_sources": len(j.sources or [])}
                for j in sorted(p.jobs, key=lambda j: j.id)
            ],
        })
    return out


def _pack_version_id(document: dict, source_version: dict) -> str:
    """A bounded, stable identifier for CommunePack.version.

    `version` is a VARCHAR(40) and part of the (commune, canton, version) unique
    key — an identifier, not prose. Static packs legitimately carry a full legal
    validity sentence in `document.version` (Lausanne's runs to 368 characters):
    SQLite silently accepts it, Postgres raises StringDataRightTruncation and the
    whole demo seed is skipped. Index on a short digest-backed id and keep the
    sentence itself in the pack payload, where it is not length-bound.
    """
    raw = (document.get("version") or "").strip()
    verified = (source_version.get("verified_at") or "").strip()
    if not raw:
        return f"static-{verified}"[:40] if verified else "static-seed"
    if len(raw) <= 40:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
    return f"static-{verified or 'seed'}-{digest}"[:40]


def seed_from_static(session) -> list[str]:
    """Bootstrap CommunePacks from the validated static pilot packs (Lausanne/Pully)."""
    created = []
    for path in sorted(glob.glob(os.path.join(PILOT, "*", "rpga_zones.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        commune = data.get("commune")
        document = data.get("document", {})
        source_version = data.get("source_version", {})
        version = _pack_version_id(document, source_version)
        if session.query(m.CommunePack).filter_by(commune=commune, canton="VD", version=version).first():
            continue
        session.add(
            m.CommunePack(
                commune=commune,
                canton="VD",
                version=version,
                status="supported",
                source_authority=document.get("title"),
                valid_as_of=source_version.get("verified_at"),
                review_due=source_version.get("review_due"),
                ingested_at=source_version.get("verified_at"),
                data={
                    "zones": data.get("zones", {}),
                    # The full legal validity statement, preserved verbatim out of
                    # the length-bound identifier column.
                    "document_version": document.get("version"),
                },
            )
        )
        created.append(commune)
    session.flush()
    return created
