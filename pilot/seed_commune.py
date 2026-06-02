#!/usr/bin/env python3
"""Next-commune seed workflow.

Turns the ingestion checklist into a repeatable scaffold: it creates a new
commune in an explicit ``seed`` / unsupported state — with NO fabricated legal
values — plus a checklist that names the source authority and the missing items
to capture. The scaffold is written as ``<slug>/rpga_zones.seed.json`` so it is
NOT picked up as an active pack until a human promotes it to ``rpga_zones.json``
after real ingestion; until then the route service reports the commune as
``unsupported`` and no report can render zero values.

Usage:
    python pilot/seed_commune.py --commune Vevey --canton VD [--out pilot]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SEED_STATUS = "seed"
REQUIRED_INPUTS = [
    "Plan d'affectation communal (PGA/PACom) — official PDF",
    "Règlement communal des constructions (RCC/RPGA) — official PDF",
    "Cantonal geoportal layer reference for the commune",
    "Adoption/in-force date and current revision status",
]
SOURCE_CAPTURE_STEPS = [
    "Download the official règlement PDF from the commune or cantonal portal.",
    "Record the document title, version, in-force date and source URL.",
    "Extract per-zone indices (IUS/IBUS/IOS), heights, levels and setbacks.",
    "Attach a provenance (article + url + confidence) to every zone value.",
]
VALIDATION_STEPS = [
    "Run python pilot/validate_packs.py once promoted to rpga_zones.json.",
    "Run python pilot/validate_commune_packs.py after adding regression anchors.",
    "Confirm the route service reports the commune as supported.",
]


def _slug(commune: str) -> str:
    return (commune or "").strip().lower().replace(" ", "-")


def build_seed_pack(commune: str, canton: str, authority_url: str | None = None) -> dict:
    """Return a seed commune pack scaffold with NO fabricated legal values."""
    return {
        "schema_version": "1.0",
        "commune": commune,
        "canton": canton,
        "status": SEED_STATUS,
        "ingested_at": None,
        "source_authority": authority_url or f"Commune de {commune} / géoportail {canton}",
        "source_version": {
            "source_status": SEED_STATUS,
            "verified_at": None,
            "review_due": None,
            "notes": "Seed scaffold — not authoritative. No legal value until ingested and promoted.",
        },
        "document": {
            "title": f"Règlement communal {commune} — À INGÉRER",
            "version": "DRAFT",
            "in_force": "unknown",
            "url": authority_url or "",
            "note": "Placeholder; capture the official règlement before any reliance.",
        },
        "required_inputs": REQUIRED_INPUTS,
        "missing_items": REQUIRED_INPUTS,
        "zones": {},
    }


def build_ingestion_checklist(commune: str, canton: str) -> str:
    inputs = "\n".join(f"- [ ] {item}" for item in REQUIRED_INPUTS)
    capture = "\n".join(f"- [ ] {item}" for item in SOURCE_CAPTURE_STEPS)
    validation = "\n".join(f"- [ ] {item}" for item in VALIDATION_STEPS)
    return f"""# Ingestion checklist — {commune} ({canton})

> Status: **seed / unsupported**. This commune has no authoritative pack yet.
> No envelope value may be rendered until this checklist is complete and the
> scaffold is promoted from `rpga_zones.seed.json` to `rpga_zones.json`.

## Source authority

Commune de {commune} and the {canton} cantonal geoportal. Record the exact source
URL and adoption date for every value captured.

## Required inputs
{inputs}

## Source capture
{capture}

## Validation
{validation}

Until done, the route service reports {commune} as `unsupported`; reports show
missing indices as `unknown`, never as zero.
"""


def seed_commune(commune: str, canton: str, out_root: str = HERE, authority_url: str | None = None) -> dict:
    slug = _slug(commune)
    commune_dir = os.path.join(out_root, slug)
    os.makedirs(commune_dir, exist_ok=True)
    pack_path = os.path.join(commune_dir, "rpga_zones.seed.json")
    checklist_path = os.path.join(commune_dir, "INGESTION.md")
    pack = build_seed_pack(commune, canton, authority_url)
    with open(pack_path, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if not os.path.exists(checklist_path):
        with open(checklist_path, "w", encoding="utf-8") as f:
            f.write(build_ingestion_checklist(commune, canton))
    return {"commune": commune, "slug": slug, "pack_path": pack_path, "checklist_path": checklist_path, "status": SEED_STATUS}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Scaffold a new commune in seed/unsupported state.")
    parser.add_argument("--commune", required=True)
    parser.add_argument("--canton", required=True)
    parser.add_argument("--out", default=HERE, help="Root under which <slug>/ is created.")
    parser.add_argument("--authority-url", default=None)
    args = parser.parse_args(argv)
    result = seed_commune(args.commune, args.canton, args.out, args.authority_url)
    print(f"Seeded {result['commune']} ({result['status']}) -> {result['pack_path']}")
    print(f"Checklist -> {result['checklist_path']}")
    print("Commune stays UNSUPPORTED until promoted to rpga_zones.json after real ingestion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
