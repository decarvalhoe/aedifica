#!/usr/bin/env python3
"""Validate phase-aware constraint matrices with stdlib only.

Run:
    python pilot/validate_matrix.py
"""
from dataclasses import dataclass, field
import glob
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX_DIR = os.path.join(HERE, "constraints")
MATRIX_VERSION = "1.0"
ALLOWED_CLAIM_STATES = {"sourced", "computed", "assumption", "unknown", "conflict", "decision"}
ALLOWED_VERIFICATION = {"manual_review", "document_check", "api_check", "calculation", "adapter_check", "not_available"}
ALLOWED_RELEVANCE = {"inform", "check", "blocker", "deliverable", "handoff"}


@dataclass
class MatrixReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        rel = os.path.relpath(path, HERE)
        self.errors.append(f"{rel}: {message}")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _list_of_strings(value):
    return isinstance(value, list) and all(_nonempty_string(item) for item in value)


def _require(mapping, path, report, key, predicate, description):
    if not isinstance(mapping, dict) or key not in mapping:
        report.add_error(path, f"missing {key}")
        return None
    value = mapping[key]
    if not predicate(value):
        report.add_error(path, f"{key} must be {description}")
    return value


def _validate_source_ref(ref, path, report, row_id, index):
    if not isinstance(ref, dict):
        report.add_error(path, f"{row_id}.source_refs[{index}] must be an object")
        return
    for key in ("source_id", "locator", "valid_as_of", "confidence"):
        if not _nonempty_string(ref.get(key)):
            report.add_error(path, f"{row_id}.source_refs[{index}].{key} must be a non-empty string")


def _validate_phase_ref(ref, path, report, row_id, phase_codes, seen_codes):
    if not isinstance(ref, dict):
        report.add_error(path, f"{row_id}.phase_applicability[] must contain objects")
        return
    code = ref.get("phase_code")
    if code not in phase_codes:
        report.add_error(path, f"{row_id}.phase_applicability phase_code {code!r} is not in phase catalog")
    else:
        seen_codes.add(code)
    if ref.get("relevance") not in ALLOWED_RELEVANCE:
        report.add_error(path, f"{row_id}.phase_applicability[{code}].relevance must be one of {sorted(ALLOWED_RELEVANCE)}")
    if not _nonempty_string(ref.get("action")):
        report.add_error(path, f"{row_id}.phase_applicability[{code}].action must be a non-empty string")


def _validate_constraint(row, path, report, phase_codes, seen_codes):
    if not isinstance(row, dict):
        report.add_error(path, "constraints[] must contain objects")
        return
    row_id = row.get("constraint_id") or "<missing>"
    for key in ("constraint_id", "title", "domain", "claim_state", "owner", "verification"):
        if not _nonempty_string(row.get(key)):
            report.add_error(path, f"{row_id}.{key} must be a non-empty string")
    if row.get("claim_state") not in ALLOWED_CLAIM_STATES:
        report.add_error(path, f"{row_id}.claim_state must be one of {sorted(ALLOWED_CLAIM_STATES)}")
    if row.get("verification") not in ALLOWED_VERIFICATION:
        report.add_error(path, f"{row_id}.verification must be one of {sorted(ALLOWED_VERIFICATION)}")
    if not _list_of_strings(row.get("outputs")):
        report.add_error(path, f"{row_id}.outputs must be a list of strings")
    phase_refs = row.get("phase_applicability")
    if not isinstance(phase_refs, list) or not phase_refs:
        report.add_error(path, f"{row_id}.phase_applicability must be a non-empty list")
    else:
        for ref in phase_refs:
            _validate_phase_ref(ref, path, report, row_id, phase_codes, seen_codes)

    source_refs = row.get("source_refs")
    if row.get("claim_state") in {"sourced", "computed"}:
        if not isinstance(source_refs, list) or not source_refs:
            report.add_error(path, f"{row_id}.source_refs required for sourced/computed claims")
        else:
            for index, ref in enumerate(source_refs):
                _validate_source_ref(ref, path, report, row_id, index)
    elif source_refs is not None and not isinstance(source_refs, list):
        report.add_error(path, f"{row_id}.source_refs must be a list when present")


def validate_matrix(path):
    report = MatrixReport()
    try:
        data = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    _require(data, path, report, "matrix_version", lambda v: v == MATRIX_VERSION, f"{MATRIX_VERSION!r}")
    _require(data, path, report, "matrix_id", _nonempty_string, "a string")
    _require(data, path, report, "title", _nonempty_string, "a string")
    _require(data, path, report, "phase_model", lambda v: isinstance(v, dict), "an object")
    phases = _require(data, path, report, "phases", lambda v: isinstance(v, list) and v, "a non-empty list")
    constraints = _require(data, path, report, "constraints", lambda v: isinstance(v, list) and v, "a non-empty list")

    phase_codes = set()
    if isinstance(phases, list):
        for phase in phases:
            if not isinstance(phase, dict):
                report.add_error(path, "phases[] must contain objects")
                continue
            code = phase.get("phase_code")
            if not _nonempty_string(code):
                report.add_error(path, "phases[].phase_code must be a non-empty string")
            elif code in phase_codes:
                report.add_error(path, f"duplicate phase code {code}")
            else:
                phase_codes.add(code)
            if not _nonempty_string(phase.get("label")):
                report.add_error(path, f"phase {code}.label must be a non-empty string")

    seen_codes = set()
    if isinstance(constraints, list):
        seen_ids = set()
        for row in constraints:
            row_id = row.get("constraint_id") if isinstance(row, dict) else None
            if row_id in seen_ids:
                report.add_error(path, f"duplicate constraint_id {row_id}")
            if row_id:
                seen_ids.add(row_id)
            _validate_constraint(row, path, report, phase_codes, seen_codes)

    item = {
        "path": os.path.relpath(path, HERE),
        "matrix_id": data.get("matrix_id"),
        "phase_codes": sorted(seen_codes),
        "constraint_count": len(constraints) if isinstance(constraints, list) else 0,
    }
    report.items.append(item)
    return report


def iter_matrix_paths():
    yield from sorted(glob.glob(os.path.join(MATRIX_DIR, "*.json")))


def validate_all():
    merged = MatrixReport()
    for path in iter_matrix_paths():
        report = validate_matrix(path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append("no constraint matrices found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['constraint_count']} constraints)")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} phase-aware constraint matrix file(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
