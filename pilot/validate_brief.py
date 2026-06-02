#!/usr/bin/env python3
"""Validate the project-scoped constraint brief object (stdlib only, offline).

Generates the Lausanne fixture brief from the project manifest without network
and checks the durable contract: it validates against the brief schema, stays
JSON-serializable for report rendering, preserves sourced/computed/unknown
states, and keeps its source refs resolvable.

Run:
    python pilot/validate_brief.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import domain  # noqa: E402
import evidence_store  # noqa: E402
import jsonschema_mini  # noqa: E402
import workspace  # noqa: E402

ALLOWED_STATES = {"sourced", "computed", "assumption", "unknown", "conflict", "decision"}

SCHEMA_PATH = os.path.join(HERE, "schemas", "constraint-brief.schema.json")
DEMO_PROJECT = os.path.join(HERE, "projects", "demo_lausanne_palud")


@dataclass
class BriefValidationReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_brief(brief: dict, schema: dict | None = None) -> list:
    return jsonschema_mini.validate(brief, schema or _load_schema())


def validate_all(project_dir: str = DEMO_PROJECT) -> BriefValidationReport:
    report = BriefValidationReport()
    schema = _load_schema()

    brief = workspace.generate_offline_parcel_brief(project_dir)

    # 1. Serializable for report rendering.
    try:
        serialized = json.dumps(brief, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        report.add_error(f"brief is not JSON-serializable: {exc}")
        serialized = "{}"

    # 2. Schema contract.
    schema_errors = validate_brief(brief, schema)
    for err in schema_errors:
        report.add_error(f"brief schema: {err}")

    # 3. Trust states preserved. The historic-centre demo parcel has no numeric
    # index, so it legitimately yields sourced + unknown (no computed envelope).
    # We still prove the computed path is preserved end-to-end for indexed zones.
    states = {claim.get("state") for claim in brief.get("claims", [])}
    if not states.issubset(ALLOWED_STATES):
        report.add_error(f"brief has unknown claim states: {sorted(states - ALLOWED_STATES)}")
    if not {"sourced", "unknown"}.issubset(states):
        report.add_error(f"brief must preserve sourced and unknown states, got {sorted(states)}")
    indexed_envelope = domain.calculate_envelope(1000, {"ius": 0.5})
    computed_claims = workspace._envelope_claims(indexed_envelope, brief.get("source_refs", []))
    if not any(claim.get("state") == "computed" for claim in computed_claims):
        report.add_error("brief envelope must preserve the computed state for indexed zones")

    # 4. Source refs resolve to the project store.
    unresolved = evidence_store.unresolved_source_refs(project_dir, brief.get("source_refs", []))
    if unresolved:
        report.add_error(f"brief source refs do not resolve: {unresolved}")

    report.items.append(
        {
            "project_id": brief.get("project_id"),
            "brief_id": brief.get("brief_id"),
            "claim_states": sorted(states),
            "serialized_bytes": len(serialized),
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
        print(f"PASS? {item['brief_id']} states={item['claim_states']}")
    if report.errors:
        print("\nBrief validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\nproject-scoped constraint brief validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
