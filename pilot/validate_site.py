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


def validate_site_note(path=os.path.join(SITE_DIR, "site_note_fixture.json")):
    report = SiteReport()
    data = _load(path)
    for key in ("schema_version", "note_id", "project_id", "phase_code", "captured_at", "captured_by", "location", "summary"):
        if not _nonempty(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")
    if not isinstance(data.get("photos"), list) or not data["photos"]:
        report.add_error(path, "photos must be a non-empty list")
    if not isinstance(data.get("source_refs"), list) or not data["source_refs"]:
        report.add_error(path, "source_refs must be a non-empty list")
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
        for key in ("item_id", "title", "status", "required_evidence"):
            if not _nonempty(item.get(key)):
                report.add_error(path, f"items[].{key} must be a non-empty string")
    report.items.append({"kind": "handover", "path": os.path.relpath(path, HERE), "blocked_count": sum(1 for item in items if item.get("status") == "blocked")})
    return report


def generate_pv_and_task_register(note):
    return {
        "pv_id": f"PV-{note['note_id']}",
        "project_id": note["project_id"],
        "source_note_id": note["note_id"],
        "summary": note["summary"],
        "tasks": note.get("tasks", []),
        "source_refs": note.get("source_refs", []),
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
