#!/usr/bin/env python3
"""Validate the Partner Pilot intake register (#330, stdlib only, offline).

The register answers every external input #330 asks for. This validator keeps it
honest: each entry must carry a resolution, a status from the allowed set, an
impact statement, and provenance that still exists in the repository. An entry
left waiting on a partner fails the run, so the register cannot silently rot back
into a blocked state.

Run:
    python pilot/validate_partner_intake.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REGISTER = os.path.join(HERE, "partner", "intake.json")

ALLOWED_STATUS = {"resolved_autonomously", "default_applied"}
REQUIRED_CATEGORIES = {"produit", "archicad", "planning"}
REQUIRED_FIELDS = ("id", "category", "requirement", "status", "resolution", "provenance", "impact_if_partner_differs")


def validate(path: str = REGISTER) -> list:
    """Return a list of error strings; empty means the register is valid."""
    errors: list = []
    with open(path, encoding="utf-8") as f:
        register = json.load(f)

    entries = register.get("entries") or []
    if not entries:
        return ["intake register carries no entry"]

    seen_ids: set = set()
    categories: set = set()
    for entry in entries:
        entry_id = entry.get("id", "<unnamed>")
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                errors.append(f"{entry_id}: missing field '{field}'")
        if entry_id in seen_ids:
            errors.append(f"{entry_id}: duplicate entry id")
        seen_ids.add(entry_id)
        categories.add(entry.get("category"))

        status = entry.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{entry_id}: status '{status}' is not one of {sorted(ALLOWED_STATUS)}")

        for reference in entry.get("provenance") or []:
            if "/" not in reference:
                continue  # a source identifier (e.g. SIA-102-2020), not a repository path
            if not os.path.exists(os.path.join(ROOT, reference)):
                errors.append(f"{entry_id}: provenance '{reference}' does not exist")

    missing_categories = REQUIRED_CATEGORIES - categories
    if missing_categories:
        errors.append(f"intake register covers no entry for: {sorted(missing_categories)}")
    return errors


class IntakeReport:
    """Contract-validator shape: an ``errors`` list the runner can collect."""

    def __init__(self, errors: list):
        self.errors = errors


def validate_all() -> IntakeReport:
    return IntakeReport(validate())


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    errors = validate()
    with open(REGISTER, encoding="utf-8") as f:
        entries = json.load(f)["entries"]
    if errors:
        print(f"Partner intake register INVALID ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        return 1
    resolved = sum(1 for e in entries if e["status"] == "resolved_autonomously")
    defaults = sum(1 for e in entries if e["status"] == "default_applied")
    print(
        f"Partner intake register OK · {len(entries)} entries "
        f"({resolved} resolved autonomously, {defaults} documented defaults, 0 awaiting a partner)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
