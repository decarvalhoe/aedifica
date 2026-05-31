#!/usr/bin/env python3
"""Validate the project manifest v1 JSON schema and its fixtures (stdlib only).

This protects the manifest contract in CI: the schema must declare version 1.0,
the valid fixture must pass, and the invalid fixtures (missing project_id, phase
or regulatory route) must fail with a useful, specific error.

Run:
    python pilot/validate_manifest.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import jsonschema_mini  # noqa: E402

SCHEMA_VERSION = "1.0"
SCHEMA_PATH = os.path.join(HERE, "schemas", "project-manifest.schema.json")
FIXTURES_DIR = os.path.join(HERE, "schemas", "fixtures")

# fixture file -> expectation. ``mention`` must appear in at least one error.
EXPECTATIONS = {
    "project_manifest_valid.json": {"valid": True},
    "project_manifest_invalid_missing_id.json": {"valid": False, "mention": "project_id"},
    "project_manifest_invalid_missing_phase.json": {"valid": False, "mention": "phase_code"},
    "project_manifest_invalid_missing_route.json": {"valid": False, "mention": "regulatory_route"},
}


@dataclass
class ManifestValidationReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schema() -> dict:
    return _load_json(SCHEMA_PATH)


def validate_manifest(manifest: dict, schema: dict | None = None) -> list:
    """Return a list of schema-violation strings (empty == valid)."""
    return jsonschema_mini.validate(manifest, schema or load_schema())


def validate_all() -> ManifestValidationReport:
    report = ManifestValidationReport()
    try:
        schema = load_schema()
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(f"cannot load manifest schema: {exc}")
        return report

    if schema.get("$schema") != "http://json-schema.org/draft-07/schema#":
        report.add_error("manifest schema must declare the draft-07 $schema")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != SCHEMA_VERSION:
        report.add_error(f"manifest schema must pin schema_version const to {SCHEMA_VERSION!r}")

    for filename, expectation in EXPECTATIONS.items():
        path = os.path.join(FIXTURES_DIR, filename)
        if not os.path.exists(path):
            report.add_error(f"missing manifest fixture {filename}")
            continue
        manifest = _load_json(path)
        errors = validate_manifest(manifest, schema)
        if expectation["valid"] and errors:
            report.add_error(f"{filename} should be valid but failed: {errors}")
        if not expectation["valid"]:
            if not errors:
                report.add_error(f"{filename} should be rejected but passed validation")
            elif not any(expectation["mention"] in err for err in errors):
                report.add_error(
                    f"{filename} rejected but no error mentioned {expectation['mention']!r}: {errors}"
                )
        report.items.append(
            {
                "fixture": filename,
                "expected_valid": expectation["valid"],
                "error_count": len(errors),
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
        verdict = "valid" if item["expected_valid"] else f"rejected ({item['error_count']} errors)"
        print(f"PASS? {item['fixture']} -> {verdict}")
    if report.errors:
        print("\nManifest validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} manifest fixtures validated against schema {SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
