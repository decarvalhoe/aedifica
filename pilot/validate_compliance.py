#!/usr/bin/env python3
"""Validate phase-33 compliance gate checklists."""
from dataclasses import dataclass, field
import glob
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
COMPLIANCE_DIR = os.path.join(HERE, "compliance")
GATES_VERSION = "1.0"
ALLOWED_BINDING_TYPES = {
    "binding_law",
    "binding_law_when_applicable",
    "technical_norm_by_reference",
    "contractual_not_legal",
}
REQUIRED_DOMAINS = {"energy", "fire", "accessibility", "structure"}


@dataclass
class ComplianceReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        self.errors.append(f"{os.path.relpath(path, HERE)}: {message}")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _list_of_strings(value):
    return isinstance(value, list) and all(_nonempty_string(item) for item in value)


def _validate_source_ref(ref, path, report, index):
    if not isinstance(ref, dict):
        report.add_error(path, f"source_refs[{index}] must be an object")
        return
    for key in ("source_id", "title", "url", "locator", "valid_as_of", "confidence"):
        if not _nonempty_string(ref.get(key)):
            report.add_error(path, f"source_refs[{index}].{key} must be a non-empty string")


def _validate_gate(gate, path, report, source_ids):
    if not isinstance(gate, dict):
        report.add_error(path, "gates[] must contain objects")
        return
    gate_id = gate.get("gate_id") or "<missing>"
    for key in ("gate_id", "title", "domain", "binding_type", "legal_basis", "phase_code", "notes"):
        if not _nonempty_string(gate.get(key)):
            report.add_error(path, f"{gate_id}.{key} must be a non-empty string")
    if gate.get("binding_type") not in ALLOWED_BINDING_TYPES:
        report.add_error(path, f"{gate_id}.binding_type must be one of {sorted(ALLOWED_BINDING_TYPES)}")
    if not isinstance(gate.get("blocking"), bool):
        report.add_error(path, f"{gate_id}.blocking must be boolean")
    if not _list_of_strings(gate.get("required_evidence")):
        report.add_error(path, f"{gate_id}.required_evidence must be a list of strings")
    if not _list_of_strings(gate.get("source_ids")):
        report.add_error(path, f"{gate_id}.source_ids must be a list of strings")
    else:
        for source_id in gate["source_ids"]:
            if source_id not in source_ids:
                report.add_error(path, f"{gate_id}.source_ids contains unknown source {source_id}")


def validate_gates(path):
    report = ComplianceReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report
    if data.get("gates_version") != GATES_VERSION:
        report.add_error(path, f"gates_version must be {GATES_VERSION!r}")
    for key in ("gates_id", "title", "phase_code"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")
    source_refs = data.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        report.add_error(path, "source_refs must be a non-empty list")
        source_ids = set()
    else:
        source_ids = {ref.get("source_id") for ref in source_refs if isinstance(ref, dict)}
        for index, ref in enumerate(source_refs):
            _validate_source_ref(ref, path, report, index)
    gates = data.get("gates")
    domains = set()
    has_contractual_not_legal = False
    if not isinstance(gates, list) or not gates:
        report.add_error(path, "gates must be a non-empty list")
    else:
        seen = set()
        for gate in gates:
            gate_id = gate.get("gate_id") if isinstance(gate, dict) else None
            if gate_id in seen:
                report.add_error(path, f"duplicate gate_id {gate_id}")
            if gate_id:
                seen.add(gate_id)
            if isinstance(gate, dict):
                domains.add(gate.get("domain"))
                if gate.get("binding_type") == "contractual_not_legal":
                    has_contractual_not_legal = True
            _validate_gate(gate, path, report, source_ids)
    missing_domains = REQUIRED_DOMAINS - domains
    if missing_domains:
        report.add_error(path, f"missing required gate domains {sorted(missing_domains)}")
    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "gate_count": len(gates) if isinstance(gates, list) else 0,
            "domains": sorted(domain for domain in domains if domain),
            "has_contractual_not_legal": has_contractual_not_legal,
        }
    )
    return report


def validate_all():
    merged = ComplianceReport()
    for path in sorted(glob.glob(os.path.join(COMPLIANCE_DIR, "*gates.json"))):
        report = validate_gates(path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append("no compliance gate files found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['gate_count']} gates: {', '.join(item['domains'])})")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
