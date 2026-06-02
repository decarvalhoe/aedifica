"""On-demand commune ingestion service over the SQL store."""
from __future__ import annotations

import datetime as _dt
import glob
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
        return {"commune": commune, "canton": canton, "state": "unsupported", "usable": False, "pack_id": None}
    best = max(packs, key=lambda p: STATUS_RANK.get(p.status, 0))
    return {
        "commune": commune,
        "canton": canton,
        "state": best.status,
        "usable": best.status == "supported",
        "pack_id": best.id,
        "version": best.version,
    }


def list_packs(session) -> list[dict]:
    return [
        {"id": p.id, "commune": p.commune, "canton": p.canton, "version": p.version, "status": p.status, "review_due": p.review_due}
        for p in session.query(m.CommunePack).order_by(m.CommunePack.commune, m.CommunePack.id).all()
    ]


def seed_from_static(session) -> list[str]:
    """Bootstrap CommunePacks from the validated static pilot packs (Lausanne/Pully)."""
    created = []
    for path in sorted(glob.glob(os.path.join(PILOT, "*", "rpga_zones.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        commune = data.get("commune")
        document = data.get("document", {})
        source_version = data.get("source_version", {})
        version = document.get("version", "static-seed")
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
                data={"zones": data.get("zones", {})},
            )
        )
        created.append(commune)
    session.flush()
    return created
