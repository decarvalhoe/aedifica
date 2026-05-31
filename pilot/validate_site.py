#!/usr/bin/env python3
"""Validate site/handover fixtures and render site reports."""
from dataclasses import dataclass, field
import json
import os
import sys

import datum_html


HERE = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(HERE, "site")


@dataclass
class SiteReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        self.errors.append(f"{os.path.relpath(path, HERE)}: {message}")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


HANDOVER_STATUSES = {"open", "closed", "blocked"}


def site_note_contract_errors(note: dict) -> list:
    """Return errors for the site note intake contract (date/author/location required)."""
    errors = []
    for key in ("note_id", "project_id", "phase_code", "captured_at", "captured_by", "location", "summary", "raw_notes"):
        if not _nonempty(note.get(key)):
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(note.get("participants"), list) or not note["participants"]:
        errors.append("participants must be a non-empty list")
    if not isinstance(note.get("decisions"), list):
        errors.append("decisions must be a list")
    if not isinstance(note.get("photos"), list) or not note["photos"]:
        errors.append("photos must be a non-empty list")
    if not isinstance(note.get("source_refs"), list) or not note["source_refs"]:
        errors.append("source_refs must be a non-empty list")
    if not isinstance(note.get("evidence_refs"), list) or not note["evidence_refs"]:
        errors.append("evidence_refs must be a non-empty list")
    return errors


def validate_site_note(path=os.path.join(SITE_DIR, "site_note_fixture.json")):
    report = SiteReport()
    data = _load(path)
    if data.get("schema_version") != "1.0":
        report.add_error(path, "schema_version must be '1.0'")
    for message in site_note_contract_errors(data):
        report.add_error(path, message)
    report.items.append({"kind": "site_note", "path": os.path.relpath(path, HERE), "task_count": len(data.get("tasks", []))})
    return report


def validate_defects(path=os.path.join(SITE_DIR, "defect_register_fixture.json")):
    report = SiteReport()
    data = _load(path)
    defects = data.get("defects")
    if not isinstance(defects, list) or not defects:
        report.add_error(path, "defects must be a non-empty list")
        defects = []
    for defect in defects:
        for key in ("defect_id", "title", "severity", "status", "responsible_party", "target_resolution"):
            if not _nonempty(defect.get(key)):
                report.add_error(path, f"defects[].{key} must be a non-empty string")
        if not isinstance(defect.get("evidence_refs"), list) or not defect.get("evidence_refs"):
            report.add_error(path, f"defects[{defect.get('defect_id')}].evidence_refs must be a non-empty list")
    report.items.append({"kind": "defects", "path": os.path.relpath(path, HERE), "defect_count": len(defects)})
    return report


def validate_handover(path=os.path.join(SITE_DIR, "handover_checklist.json")):
    report = SiteReport()
    data = _load(path)
    items = data.get("items")
    if not isinstance(items, list) or not items:
        report.add_error(path, "items must be a non-empty list")
        items = []
    for item in items:
        for key in ("item_id", "title", "status", "required_evidence", "responsible_party", "due_at"):
            if not _nonempty(item.get(key)):
                report.add_error(path, f"items[].{key} must be a non-empty string")
        if item.get("status") not in HANDOVER_STATUSES:
            report.add_error(path, f"items[{item.get('item_id')}].status must be one of {sorted(HANDOVER_STATUSES)}")
        if not isinstance(item.get("evidence_refs"), list) or not item.get("evidence_refs"):
            report.add_error(path, f"items[{item.get('item_id')}].evidence_refs must be a non-empty list")
    report.items.append(
        {
            "kind": "handover",
            "path": os.path.relpath(path, HERE),
            "blocked_count": sum(1 for item in items if item.get("status") == "blocked"),
            "statuses": sorted({item.get("status") for item in items}),
        }
    )
    return report


def _normalize_task(task: dict) -> dict:
    """Ensure each task carries owner / status / deadline or an explicit unknown."""
    return {
        "task_id": task.get("task_id"),
        "title": task.get("title"),
        "owner": task.get("owner") or task.get("assignee") or "unknown",
        "status": task.get("status") or "unknown",
        "deadline": task.get("deadline") or task.get("due_at") or "unknown",
    }


def generate_pv_and_task_register(note):
    tasks = [_normalize_task(task) for task in note.get("tasks", [])]
    return {
        "pv_id": f"PV-{note['note_id']}",
        "project_id": note["project_id"],
        "source_note_id": note["note_id"],
        "summary": note["summary"],
        "participants": note.get("participants", []),
        "decisions": note.get("decisions", []),
        "tasks": tasks,
        "source_refs": note.get("source_refs", []),
        "evidence_refs": note.get("evidence_refs", []),
    }


def pv_memory_records(pv: dict, note: dict) -> list:
    """Build project-memory records (decisions + tasks) linking back to the source note evidence."""
    evidence_refs = note.get("evidence_refs", [])
    records = []
    for decision in pv.get("decisions", []):
        records.append(
            {
                "memory_id": f"MEM-SITE-DEC-{decision.get('decision_id')}",
                "record_type": "decision",
                "phase_code": note.get("phase_code", "52"),
                "title": decision.get("title"),
                "summary": f"Site decision from {pv['pv_id']}.",
                "claim_state": "decision",
                "status": decision.get("status", "open"),
                "source_refs": note.get("source_refs", []),
                "evidence_refs": evidence_refs,
                "links": [pv["source_note_id"]],
            }
        )
    for task in pv.get("tasks", []):
        records.append(
            {
                "memory_id": f"MEM-SITE-TASK-{task.get('task_id')}",
                "record_type": "site_issue",
                "phase_code": note.get("phase_code", "52"),
                "title": task.get("title"),
                "summary": f"Task owner={task.get('owner')} deadline={task.get('deadline')} from {pv['pv_id']}.",
                "claim_state": "sourced",
                "status": task.get("status", "open"),
                "source_refs": note.get("source_refs", []),
                "evidence_refs": evidence_refs,
                "links": [pv["source_note_id"]],
            }
        )
    return records


def write_pv_memory(memory: dict, pv: dict, note: dict) -> dict:
    """Append PV decision/task records into a project memory object (idempotent by memory_id)."""
    new_records = pv_memory_records(pv, note)
    new_ids = {record["memory_id"] for record in new_records}
    kept = [record for record in memory.get("records", []) if record.get("memory_id") not in new_ids]
    memory["records"] = kept + new_records
    return memory


def carryover_to_handover_check(condition: dict, item_id: str) -> dict:
    """Create a handover checklist item from a permit/tender carryover condition."""
    return {
        "item_id": item_id,
        "title": f"Carryover: {condition.get('title')}",
        "status": "blocked",
        "responsible_party": "Architecte",
        "due_at": "unknown",
        "required_evidence": f"carryover://{condition.get('memory_id')}",
        "evidence_refs": condition.get("evidence_refs", [{"evidence_id": condition.get("memory_id"), "kind": "carryover", "file_ref": f"memory://{condition.get('memory_id')}"}]),
        "links": [condition.get("memory_id")],
    }


def render_handover_html(checklist, defects):
    defect_rows = "".join(f"<li class='{d['status']}'><span class='state {d['status']}'>{d['status']}</span> {d['title']} · {d['responsible_party']}</li>" for d in defects.get("defects", []))
    item_rows = "".join(f"<li class='{i['status']}'><span class='state {i['status']}'>{i['status']}</span> {i['title']}</li>" for i in checklist.get("items", []))
    body = f"""
  <h1>Handover checklist</h1>
  <section><h2>Items</h2><ul>{item_rows}</ul></section>
  <section><h2>Defects</h2><ul>{defect_rows}</ul></section>
"""
    return datum_html.shell("Handover checklist", "Chantier / remise", body)


def validate_all():
    merged = SiteReport()
    for validator in (validate_site_note, validate_defects, validate_handover):
        report = validator()
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    return merged


def main():
    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['kind']})")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
