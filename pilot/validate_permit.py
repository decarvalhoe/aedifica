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
EVIDENCE_STATUSES = {"present", "missing", "pending", "not_applicable", "out_of_scope"}
PRESENT_EVIDENCE_STATUSES = {"present"}
OUT_OF_SCOPE_STATUSES = {"not_applicable", "out_of_scope"}
ACTOR_BY_CATEGORY = {
    "platform": "architect",
    "plans": "architect_or_surveyor",
    "parcel": "architect",
    "project": "architect",
    "compliance": "specialist",
    "special_authorizations": "architect_or_specialist",
    "aedifica": "aedifica",
}


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


def _validate_evidence_source_ref(ref, path, report, owner, index):
    if not isinstance(ref, dict):
        report.add_error(path, f"{owner}.source_refs[{index}] must be an object")
        return
    for key in ("source_id", "locator", "valid_as_of", "confidence"):
        if not _nonempty_string(ref.get(key)):
            report.add_error(path, f"{owner}.source_refs[{index}].{key} must be a non-empty string")


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
    mapping = map_evidence_to_items(checklist, dossier)
    missing = []
    present = []
    conditional = []
    out_of_scope = []
    groups = {}
    for item_result in mapping:
        bucket = groups.setdefault(
            item_result["category"],
            {
                "category": item_result["category"],
                "actor": item_result["actor"],
                "present": [],
                "missing": [],
                "conditional": [],
                "out_of_scope": [],
            },
        )
        bucket[item_result["status"]].append(item_result)
        if item_result["status"] == "present":
            present.append(item_result["item_id"])
        elif item_result["status"] == "missing":
            missing.append(item_result)
        elif item_result["status"] == "conditional":
            conditional.append(item_result)
        elif item_result["status"] == "out_of_scope":
            out_of_scope.append(item_result)
    return {
        "dossier_id": dossier.get("dossier_id"),
        "checklist_id": checklist.get("checklist_id"),
        "present": present,
        "missing": missing,
        "conditional": conditional,
        "out_of_scope": out_of_scope,
        "groups": list(groups.values()),
        "summary": {
            "required_blockers": len(missing),
            "present_count": len(present),
            "conditional_count": len(conditional),
            "out_of_scope_count": len(out_of_scope),
        },
    }


def evidence_records(dossier):
    records = dossier.get("evidence_records")
    return records if isinstance(records, list) else []


def evidence_by_key(dossier):
    out = {}
    for record in evidence_records(dossier):
        if not isinstance(record, dict):
            continue
        out.setdefault(record.get("key"), []).append(record)
    return out


def map_evidence_to_items(checklist, dossier):
    by_key = evidence_by_key(dossier)
    results = []
    for item in checklist.get("items", []):
        accepted = item.get("accepted_evidence", [])
        matched = [record for key in accepted for record in by_key.get(key, [])]
        present_records = [record for record in matched if record.get("status") in PRESENT_EVIDENCE_STATUSES]
        out_scope_records = [record for record in matched if record.get("status") in OUT_OF_SCOPE_STATUSES]
        if present_records:
            status = "present"
        elif out_scope_records and not item.get("required"):
            status = "out_of_scope"
        elif item.get("required"):
            status = "missing"
        else:
            status = "conditional"
        results.append(
            {
                "item_id": item["item_id"],
                "title": item["title"],
                "category": item["category"],
                "actor": ACTOR_BY_CATEGORY.get(item["category"], "architect"),
                "required": item.get("required") is True,
                "status": status,
                "missing_message": item["missing_message"],
                "accepted_evidence": accepted,
                "evidence_records": present_records or out_scope_records,
            }
        )
    return results


def render_completeness_html(report):
    def esc(value):
        import html

        return html.escape("" if value is None else str(value))

    groups = []
    for group in report["groups"]:
        rows = []
        for status in ("missing", "present", "conditional", "out_of_scope"):
            for item in group[status]:
                rows.append(
                    f"<li class='{esc(status)}'><b>{esc(status)}</b> · {esc(item['title'])}"
                    + (f"<br><small>{esc(item['missing_message'])}</small>" if status == "missing" else "")
                    + "</li>"
                )
        groups.append(f"<section><h2>{esc(group['actor'])} · {esc(group['category'])}</h2><ul>{''.join(rows)}</ul></section>")
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>{esc(report['dossier_id'])}</title></head>
<body>
  <h1>Rapport de complétude permis</h1>
  <p>Blockers requis: {esc(report['summary']['required_blockers'])}</p>
  {''.join(groups)}
</body>
</html>
"""


def _validate_evidence_record(record, path, report, index, accepted_keys):
    if not isinstance(record, dict):
        report.add_error(path, f"evidence_records[{index}] must be an object")
        return
    owner = f"evidence_records[{index}]"
    for key in ("evidence_id", "key", "kind", "title", "status"):
        if not _nonempty_string(record.get(key)):
            report.add_error(path, f"{owner}.{key} must be a non-empty string")
    if record.get("key") and record["key"] not in accepted_keys:
        report.add_error(path, f"{owner}.key {record['key']} is not accepted by checklist")
    if record.get("status") not in EVIDENCE_STATUSES:
        report.add_error(path, f"{owner}.status must be one of {sorted(EVIDENCE_STATUSES)}")
    if not (_nonempty_string(record.get("file_ref")) or _nonempty_string(record.get("external_ref"))):
        report.add_error(path, f"{owner} must include file_ref or external_ref")
    refs = record.get("source_refs")
    if not isinstance(refs, list) or not refs:
        report.add_error(path, f"{owner}.source_refs must be a non-empty list")
    else:
        for ref_index, ref in enumerate(refs):
            _validate_evidence_source_ref(ref, path, report, owner, ref_index)


def validate_demo_dossier(checklist_path, dossier_path):
    report = PermitReport()
    checklist = _load(checklist_path)
    dossier = _load(dossier_path)
    if dossier.get("checklist_id") != checklist.get("checklist_id"):
        report.add_error(dossier_path, "dossier checklist_id does not match checklist")
    accepted_keys = {key for item in checklist.get("items", []) for key in item.get("accepted_evidence", [])}
    records = dossier.get("evidence_records")
    if not isinstance(records, list):
        report.add_error(dossier_path, "evidence_records must be a list")
        records = []
    seen_records = set()
    for index, record in enumerate(records):
        evidence_id = record.get("evidence_id") if isinstance(record, dict) else None
        if evidence_id in seen_records:
            report.add_error(dossier_path, f"duplicate evidence_id {evidence_id}")
        if evidence_id:
            seen_records.add(evidence_id)
        _validate_evidence_record(record, dossier_path, report, index, accepted_keys)
    result = completeness_report(checklist, dossier)
    report.items.append(
        {
            "path": os.path.relpath(dossier_path, HERE),
            "checklist_id": dossier.get("checklist_id"),
            "missing_count": result["summary"]["required_blockers"],
            "conditional_count": result["summary"]["conditional_count"],
            "out_of_scope_count": result["summary"]["out_of_scope_count"],
            "missing": [item["item_id"] for item in result["missing"]],
            "groups": [group["category"] for group in result["groups"]],
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
