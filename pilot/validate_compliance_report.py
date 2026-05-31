#!/usr/bin/env python3
"""Validate the phase-33 compliance workspace report (stdlib, offline).

Regression fixtures cover the complete and missing input cases. Checks: the
complete case has no legal blockers; the missing case raises legal blockers and
emits next actions for unknown inputs; legal and contractual gates stay
separated; the BIM gate is contractual, never a legal permit gate.

Run:
    python pilot/validate_compliance_report.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import compliance_report  # noqa: E402

COMPLIANCE_DIR = os.path.join(HERE, "compliance")
GATES_PATH = os.path.join(COMPLIANCE_DIR, "ch_phase33_gates.json")


@dataclass
class ComplianceReportValidation:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_all() -> ComplianceReportValidation:
    report = ComplianceReportValidation()
    gates = _load(GATES_PATH)
    complete = _load(os.path.join(COMPLIANCE_DIR, "demo_complete_inputs.json"))["inputs"]
    missing = _load(os.path.join(COMPLIANCE_DIR, "demo_missing_inputs.json"))["inputs"]

    complete_report = compliance_report.build_compliance_report(gates, complete)
    missing_report = compliance_report.build_compliance_report(gates, missing)

    if complete_report["summary"]["legal_blockers"] != 0:
        report.add_error(f"complete case should have no legal blockers, got {complete_report['summary']['legal_blockers']}")
    if missing_report["summary"]["legal_blockers"] == 0:
        report.add_error("missing case should raise at least one legal blocker")
    if not any(a["next_action"] for a in missing_report["next_actions"]):
        report.add_error("unknown gate inputs must produce next actions")

    # Legal vs contractual separation, and BIM is contractual.
    for built in (complete_report, missing_report):
        if not built["legal_contractual_separated"]:
            report.add_error("compliance report must separate legal from contractual gates")
        if any(g["category"] != "contractual" for g in built["contractual"]):
            report.add_error("contractual section must only contain contractual gates")
        bim = [g for g in built["contractual"] if g["domain"] == "bim"]
        if not bim:
            report.add_error("BIM gate must be in the contractual section, not a legal gate")
        if any(g["binding_type"] == "contractual_not_legal" for g in built["legal"]):
            report.add_error("a contractual_not_legal gate must never appear as a legal obligation")

    # Required domains are present as legal gates.
    legal_domains = {g["domain"] for g in complete_report["legal"]}
    for domain in ("energy", "fire", "accessibility", "structure"):
        if domain not in legal_domains:
            report.add_error(f"legal gate domain {domain} is missing from the report")

    report.items.append(
        {
            "complete_legal_blockers": complete_report["summary"]["legal_blockers"],
            "missing_legal_blockers": missing_report["summary"]["legal_blockers"],
            "missing_next_actions": len(missing_report["next_actions"]),
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
            f"PASS? complete blockers={item['complete_legal_blockers']} "
            f"missing blockers={item['missing_legal_blockers']} next_actions={item['missing_next_actions']}"
        )
    if report.errors:
        print("\nCompliance report validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\nphase-33 compliance workspace report validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
