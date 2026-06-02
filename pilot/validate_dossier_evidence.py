#!/usr/bin/env python3
"""Validate the permit dossier evidence manifest against its schema (stdlib).

Proves the complete fixture validates, a record missing required metadata fails
with a useful message, every evidence kind maps to a known evidence category
(document ref / drawing / form / specialist note / assumption), and every record
links back to source refs.

Run:
    python pilot/validate_dossier_evidence.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import jsonschema_mini  # noqa: E402

SCHEMA_PATH = os.path.join(HERE, "schemas", "dossier-evidence.schema.json")
PERMIT_DIR = os.path.join(HERE, "permit")

# Map dossier evidence kinds to the five product evidence categories.
KIND_CATEGORY = {
    "project_document": "document_ref",
    "parcel_reference": "document_ref",
    "api_extract": "document_ref",
    "aedifica_report": "document_ref",
    "document": "document_ref",
    "drawing": "drawing",
    "platform_record": "form",
    "form": "form",
    "project_note": "specialist_note",
    "specialist_document": "specialist_note",
    "specialist_note": "specialist_note",
    "scope_decision": "assumption",
    "assumption": "assumption",
}
CATEGORIES = {"document_ref", "drawing", "form", "specialist_note", "assumption"}


@dataclass
class DossierEvidenceReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evidence_category(kind: str) -> str:
    return KIND_CATEGORY.get(kind, "other")


def validate_manifest(dossier: dict, schema: dict | None = None) -> list:
    schema = schema or _load(SCHEMA_PATH)
    return jsonschema_mini.validate(dossier, schema)


def validate_all() -> DossierEvidenceReport:
    report = DossierEvidenceReport()
    schema = _load(SCHEMA_PATH)

    complete = _load(os.path.join(PERMIT_DIR, "demo_complete_dossier.json"))
    complete_errors = validate_manifest(complete, schema)
    if complete_errors:
        report.add_error(f"complete dossier should validate: {complete_errors}")

    # Every evidence kind maps to a known category, and links to source refs.
    for record in complete.get("evidence_records", []):
        if evidence_category(record.get("kind")) not in CATEGORIES:
            report.add_error(f"evidence kind {record.get('kind')!r} has no known category")
        if not record.get("source_refs"):
            report.add_error(f"{record.get('evidence_id')} must link to source refs")

    # Missing required metadata fails with a useful, specific message.
    broken = json.loads(json.dumps(complete))
    broken["evidence_records"][0].pop("title", None)
    broken_errors = validate_manifest(broken, schema)
    if not any("title" in err for err in broken_errors):
        report.add_error("a record missing 'title' must fail with a message mentioning title")

    # A record with neither file_ref nor external_ref fails (anyOf).
    no_ref = json.loads(json.dumps(complete))
    no_ref["evidence_records"][0].pop("file_ref", None)
    no_ref["evidence_records"][0].pop("external_ref", None)
    if not validate_manifest(no_ref, schema):
        report.add_error("a record with neither file_ref nor external_ref must fail")

    report.items.append(
        {
            "dossier_id": complete.get("dossier_id"),
            "record_count": len(complete.get("evidence_records", [])),
            "categories": sorted({evidence_category(r.get("kind")) for r in complete.get("evidence_records", [])}),
        }
    )
    return report


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['dossier_id']}: {item['record_count']} records, categories {item['categories']}")
    if report.errors:
        print("\nDossier evidence validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\ndossier evidence manifest validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
