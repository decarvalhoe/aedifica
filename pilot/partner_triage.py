#!/usr/bin/env python3
"""Turn observed Partner Pilot frictions into an actionable backlog (#331).

Reads the frictions recorded by the product walkthrough (#312) — or any friction
list in the same shape — classifies each one, prioritises it, routes it to the
right parent issue and renders a ready-to-file issue draft carrying context,
impact, reproduction, expected result and testable acceptance criteria.

The pipeline never invents work: a run with no observed friction produces an
explicitly empty backlog rather than a plausible-looking one.

Run:
    python pilot/partner_triage.py
    python pilot/partner_triage.py --from docs/validation/evidence/product-walkthrough-312.json --write
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import redaction  # noqa: E402

EVIDENCE_DIR = os.path.join(ROOT, "docs", "validation", "evidence")
WALKTHROUGH_REPORT = os.path.join(EVIDENCE_DIR, "product-walkthrough-312.json")

# Surfaces whose frictions belong to the Archicad epic rather than the product test.
ARCHICAD_SURFACES = {"archicad", "maquette", "adapter"}

CATEGORIES = ("bug", "ux", "missing_data", "business_need", "performance", "out_of_scope")

# Surfaces that block real work outright when broken: a P0 candidate.
BLOCKING_SURFACES = {"projets", "checklist", "documents", "validation", "acces", "reglementaire"}


def classify(friction: dict) -> str:
    """Classify a friction from what was actually observed, not from its wording."""
    observed = (friction.get("observed") or "").lower()
    if " 5" in observed and "http 5" in observed:
        return "bug"
    if "http 4" in observed:
        # A refused call the run-of-show expected to succeed is a bug; a call the
        # product deliberately refuses is a comprehension gap, not a defect.
        return "bug" if "not_found" in observed or "500" in observed else "ux"
    if "entries=0" in observed or "no " in observed or "missing" in observed:
        return "missing_data"
    if "timeout" in observed or "slow" in observed:
        return "performance"
    return "ux"


def prioritise(friction: dict, category: str) -> str:
    surface = (friction.get("surface") or "").lower()
    if category == "bug" and surface in BLOCKING_SURFACES:
        return "P0"
    if category in ("bug", "missing_data"):
        return "P1"
    if category == "out_of_scope":
        return "P2"
    return "P1" if surface in BLOCKING_SURFACES else "P2"


def route(friction: dict) -> int:
    return 171 if (friction.get("surface") or "").lower() in ARCHICAD_SURFACES else 312


def draft(friction: dict) -> dict:
    category = classify(friction)
    priority = prioritise(friction, category)
    step = friction.get("step", "inconnu")
    surface = friction.get("surface", "inconnu")
    return {
        "title": f"[{surface}] {step} — {friction.get('expected', '')[:70]}",
        "category": category,
        "priority": priority,
        "parent_issue": route(friction),
        "surface": surface,
        "context": f"Observe pendant le parcours produit autonome, etape `{step}` sur la surface `{surface}`.",
        "impact": (
            "Bloque le travail reel sur une surface critique."
            if priority == "P0"
            else "Degrade le parcours sans le bloquer."
        ),
        "reproduction": f"python pilot/partner_walkthrough.py puis lire l'etape `{step}`.",
        "expected_result": friction.get("expected"),
        "observed_result": friction.get("observed"),
        "acceptance_criteria": [
            f"L'etape `{step}` du parcours autonome passe.",
            "Le parcours complet reste vert (aucune regression sur les autres etapes).",
        ],
        "validation": "python pilot/partner_walkthrough.py",
    }


def triage(frictions: list) -> dict:
    drafts = [draft(item) for item in frictions]
    by_priority: dict = {}
    by_category: dict = {}
    for item in drafts:
        by_priority[item["priority"]] = by_priority.get(item["priority"], 0) + 1
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
    return {
        "schema_version": "1.0",
        "evidence_id": "PARTNER-TRIAGE",
        "issue": 331,
        "friction_count": len(frictions),
        "issue_count": len(drafts),
        "by_priority": by_priority,
        "by_category": by_category,
        "routed_to": {str(issue): sum(1 for d in drafts if d["parent_issue"] == issue) for issue in (312, 171)},
        "backlog": drafts,
        "note": (
            "Aucune friction observee: le parcours autonome est passe sur toutes ses etapes. "
            "Le backlog est vide par constat, pas par omission."
            if not frictions
            else "Une issue par probleme independant; aucun regroupement sans doublon avere."
        ),
    }


def load_frictions(path: str = WALKTHROUGH_REPORT) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("frictions", [])


def write_backlog(backlog: dict, directory: str = EVIDENCE_DIR) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "friction-triage-331.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(redaction.redact_artifact(backlog), f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return path


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Triage Partner Pilot frictions into an actionable backlog.")
    parser.add_argument("--from", dest="source", default=WALKTHROUGH_REPORT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not os.path.exists(args.source):
        print(f"No walkthrough report at {args.source}. Run: python pilot/partner_walkthrough.py --write")
        return 1
    backlog = triage(load_frictions(args.source))
    if args.write:
        backlog["written"] = write_backlog(backlog)

    if args.json:
        print(json.dumps(backlog, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Friction triage · {backlog['friction_count']} friction(s) → {backlog['issue_count']} issue(s)")
        for item in backlog["backlog"]:
            print(f"  {item['priority']} {item['category']:<14} → #{item['parent_issue']}  {item['title']}")
        print(f"  {backlog['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
