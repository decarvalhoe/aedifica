#!/usr/bin/env python3
"""Validate the privacy redaction pass (stdlib only, offline).

Loads a fixture with sensitive fields, runs the redaction pass and checks that
the shareable artifact carries no client name, email, phone or local path, while
structural/validation fields (ids, claim states, source ids, hashes) survive.

Run:
    python pilot/validate_redaction.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import redaction  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "sensitive_artifact_fixture.json")


@dataclass
class RedactionReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_all() -> RedactionReport:
    report = RedactionReport()
    original = _load(FIXTURE)

    before = redaction.find_sensitive(original)
    if not before:
        report.add_error("fixture should contain sensitive data to redact")

    redacted = redaction.redact_artifact(original)
    after = redaction.find_sensitive(redacted)
    if after:
        report.add_error(f"redacted artifact still leaks sensitive data: {after}")

    # Structural/validation fields must survive.
    if redacted.get("report_id") != original.get("report_id"):
        report.add_error("redaction must preserve report_id")
    if redacted.get("content_sha256") != original.get("content_sha256"):
        report.add_error("redaction must preserve content hashes")
    claim_states = {claim.get("state") for claim in redacted.get("claims", [])}
    if not {"sourced", "unknown"}.issubset(claim_states):
        report.add_error("redaction must preserve claim states")
    if redacted.get("source_refs", [{}])[0].get("source_id") != "VD-OEREB":
        report.add_error("redaction must preserve source ids")

    # Original must not be mutated by the pass.
    if redaction.find_sensitive(original) != before:
        report.add_error("redaction must not mutate the original artifact")

    summary = redaction.redaction_report(original, redacted)
    report.items.append(
        {
            "fixture": os.path.basename(FIXTURE),
            "sensitive_before": len(summary["sensitive_before"]),
            "sensitive_after": len(summary["sensitive_after"]),
            "preserved_keys": summary["preserved_keys_present"],
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
        print(
            f"PASS? {item['fixture']}: {item['sensitive_before']} sensitive -> "
            f"{item['sensitive_after']} after redaction"
        )
    if report.errors:
        print("\nRedaction validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\nprivacy redaction pass validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
