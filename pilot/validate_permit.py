#!/usr/bin/env python3
"""Validate permit checklist files and produce demo missing-item reports."""
from dataclasses import dataclass, field
import glob
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
PERMIT_DIR = os.path.join(HERE, "permit")
CHECKLIST_VERSION = "1.0"
ALLOWED_CLAIM_STATES = {"sourced", "computed", "assumption", "unknown", "conflict", "decision"}


@dataclass
class PermitReport:
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


def _validate_item(item, path, report, seen_sources):
    if not isinstance(item, dict):
        report.add_error(path, "items[] must contain objects")
        return
    item_id = item.get("item_id") or "<missing>"
    for key in ("item_id", "title", "category", "claim_state", "missing_message"):
        if not _nonempty_string(item.get(key)):
            report.add_error(path, f"{item_id}.{key} must be a non-empty string")
    if not isinstance(item.get("required"), bool):
        report.add_error(path, f"{item_id}.required must be boolean")
    if item.get("claim_state") not in ALLOWED_CLAIM_STATES:
        report.add_error(path, f"{item_id}.claim_state must be one of {sorted(ALLOWED_CLAIM_STATES)}")
    if not _list_of_strings(item.get("accepted_evidence")):
        report.add_error(path, f"{item_id}.accepted_evidence must be a list of strings")
    if not _list_of_strings(item.get("source_ids")):
        report.add_error(path, f"{item_id}.source_ids must be a list of strings")
    else:
        for source_id in item["source_ids"]:
            if source_id not in seen_sources and not source_id.startswith(("MATRIX-", "VD-ENERGY", "ECA-")):
                report.add_error(path, f"{item_id}.source_ids contains unknown source {source_id}")


def validate_checklist(path):
    report = PermitReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report
    if data.get("checklist_version") != CHECKLIST_VERSION:
        report.add_error(path, f"checklist_version must be {CHECKLIST_VERSION!r}")
    for key in ("checklist_id", "title", "phase_code"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")
    if data.get("phase_code") != "33":
        report.add_error(path, "permit checklist phase_code must be 33")
    source_refs = data.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        report.add_error(path, "source_refs must be a non-empty list")
        seen_sources = set()
    else:
        seen_sources = {ref.get("source_id") for ref in source_refs if isinstance(ref, dict)}
        for index, ref in enumerate(source_refs):
            _validate_source_ref(ref, path, report, index)
    items = data.get("items")
    if not isinstance(items, list) or not items:
        report.add_error(path, "items must be a non-empty list")
    else:
        seen_items = set()
        for item in items:
            item_id = item.get("item_id") if isinstance(item, dict) else None
            if item_id in seen_items:
                report.add_error(path, f"duplicate item_id {item_id}")
            if item_id:
                seen_items.add(item_id)
            _validate_item(item, path, report, seen_sources)
    return report


def completeness_report(checklist, dossier):
    evidence = dossier.get("evidence") or {}
    missing = []
    present = []
    for item in checklist.get("items", []):
        accepted = item.get("accepted_evidence", [])
        item_present = any(bool(evidence.get(key)) for key in accepted)
        if item_present:
            present.append(item["item_id"])
        elif item.get("required"):
            missing.append(
                {
                    "item_id": item["item_id"],
                    "title": item["title"],
                    "missing_message": item["missing_message"],
                }
            )
    return {"present": present, "missing": missing}


def validate_demo_dossier(checklist_path, dossier_path):
    report = PermitReport()
    checklist = _load(checklist_path)
    dossier = _load(dossier_path)
    if dossier.get("checklist_id") != checklist.get("checklist_id"):
        report.add_error(dossier_path, "dossier checklist_id does not match checklist")
    result = completeness_report(checklist, dossier)
    report.items.append(
        {
            "path": os.path.relpath(dossier_path, HERE),
            "checklist_id": dossier.get("checklist_id"),
            "missing_count": len(result["missing"]),
            "missing": [item["item_id"] for item in result["missing"]],
        }
    )
    return report


def validate_all():
    merged = PermitReport()
    checklist_paths = sorted(glob.glob(os.path.join(PERMIT_DIR, "*checklist.json")))
    for path in checklist_paths:
        report = validate_checklist(path)
        merged.errors.extend(report.errors)
    for dossier_path in sorted(glob.glob(os.path.join(PERMIT_DIR, "demo_*dossier.json"))):
        checklist_path = os.path.join(PERMIT_DIR, "vd_camac_checklist.json")
        report = validate_demo_dossier(checklist_path, dossier_path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not checklist_paths:
        merged.errors.append("no permit checklist files found")
    if not merged.items:
        merged.errors.append("no demo permit dossier reports found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['missing_count']} missing required item(s))")
        for missing in item["missing"]:
            print(f"  missing: {missing}")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
