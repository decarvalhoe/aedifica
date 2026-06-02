#!/usr/bin/env python3
"""Validate project memory fixtures and answer provenance-backed demo queries."""
from dataclasses import dataclass, field
import glob
import json
import os
import sys

import ledger


HERE = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(HERE, "memory")
MEMORY_VERSION = "1.0"
REQUIRED_RECORD_TYPES = {
    "source_evidence",
    "decision",
    "model_version",
    "change",
    "authority_correspondence",
    "handoff",
    "site_issue",
}
OPEN_STATUSES = {"open", "pending_human_review"}


@dataclass
class MemoryReport:
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


def _validate_source_refs(path, report, record):
    refs = record.get("source_refs")
    record_id = record.get("memory_id") or "<missing>"
    if not isinstance(refs, list) or not refs:
        report.add_error(path, f"{record_id}.source_refs must be a non-empty list")
        return
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            report.add_error(path, f"{record_id}.source_refs[{index}] must be an object")
            continue
        for key in ("source_id", "locator", "valid_as_of", "confidence"):
            if not _nonempty_string(ref.get(key)):
                report.add_error(path, f"{record_id}.source_refs[{index}].{key} must be a non-empty string")


def _validate_evidence_refs(path, report, record):
    refs = record.get("evidence_refs")
    record_id = record.get("memory_id") or "<missing>"
    if not isinstance(refs, list) or not refs:
        report.add_error(path, f"{record_id}.evidence_refs must be a non-empty list")
        return
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            report.add_error(path, f"{record_id}.evidence_refs[{index}] must be an object")
            continue
        for key in ("evidence_id", "kind", "file_ref"):
            if not _nonempty_string(ref.get(key)):
                report.add_error(path, f"{record_id}.evidence_refs[{index}].{key} must be a non-empty string")


def answer_query(memory, query):
    records = memory.get("records", [])
    intent = query.get("intent")
    params = query.get("parameters") or {}
    if intent == "changes_since_version":
        version = params.get("version")
        return [record for record in records if record.get("record_type") == "change" and record.get("from_version") == version]
    if intent == "source_for_claim":
        source_id = params.get("source_id")
        return [
            record
            for record in records
            if any(ref.get("source_id") == source_id for ref in record.get("source_refs", []) if isinstance(ref, dict))
        ]
    if intent == "open_items_by_phase":
        phase_code = params.get("phase_code")
        return [
            record
            for record in records
            if record.get("phase_code") == phase_code and record.get("status") in OPEN_STATUSES
        ]
    if intent == "open_decisions":
        return [
            record
            for record in records
            if record.get("record_type") == "decision" and record.get("status") in OPEN_STATUSES
        ]
    if intent == "unknown_claims":
        return [
            record
            for record in records
            if record.get("claim_state") == "unknown" and record.get("status") in OPEN_STATUSES
        ]
    if intent == "assumptions_needing_review":
        return [
            record
            for record in records
            if record.get("claim_state") == "assumption" and record.get("status") == "pending_human_review"
        ]
    if intent == "changed_sources":
        return [
            record
            for record in records
            if record.get("record_type") == "change" and record.get("status") in OPEN_STATUSES
        ]
    if intent in {"open_blockers_before_permit", "conditions_for_tender_site", "changes_since_report"}:
        return ledger.carryover(memory, intent)
    return []


def open_questions(memory: dict) -> dict:
    """UI-stable view of what is still undecided/unknown, with provenance refs."""

    def project(record):
        return {
            "memory_id": record.get("memory_id"),
            "phase_code": record.get("phase_code"),
            "title": record.get("title"),
            "summary": record.get("summary"),
            "status": record.get("status"),
            "source_refs": record.get("source_refs", []),
            "evidence_refs": record.get("evidence_refs", []),
        }

    return {
        "open_decisions": [project(r) for r in answer_query(memory, {"intent": "open_decisions"})],
        "unknown_claims": [project(r) for r in answer_query(memory, {"intent": "unknown_claims"})],
        "assumptions_needing_review": [project(r) for r in answer_query(memory, {"intent": "assumptions_needing_review"})],
        "changed_sources": [project(r) for r in answer_query(memory, {"intent": "changed_sources"})],
    }


def validate_memory(path):
    report = MemoryReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    if data.get("schema_version") != MEMORY_VERSION:
        report.add_error(path, f"schema_version must be {MEMORY_VERSION!r}")
    for key in ("memory_id", "project_id", "title", "knowledge_regime"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")

    records = data.get("records")
    if not isinstance(records, list) or not records:
        report.add_error(path, "records must be a non-empty list")
        records = []

    seen_records = set()
    record_types = set()
    phase_codes = set()
    for record in records:
        if not isinstance(record, dict):
            report.add_error(path, "records[] must contain objects")
            continue
        record_id = record.get("memory_id")
        if record_id in seen_records:
            report.add_error(path, f"duplicate memory_id {record_id}")
        if _nonempty_string(record_id):
            seen_records.add(record_id)
        for key in ("memory_id", "record_type", "phase_code", "title", "summary", "claim_state", "status"):
            if not _nonempty_string(record.get(key)):
                report.add_error(path, f"{record_id or '<missing>'}.{key} must be a non-empty string")
        record_type = record.get("record_type")
        if record_type:
            record_types.add(record_type)
        phase_code = record.get("phase_code")
        if phase_code:
            phase_codes.add(phase_code)
        _validate_source_refs(path, report, record)
        _validate_evidence_refs(path, report, record)
        if "links" in record and not _list_of_strings(record.get("links")):
            report.add_error(path, f"{record_id}.links must be a list of strings")

    missing_types = REQUIRED_RECORD_TYPES - record_types
    if missing_types:
        report.add_error(path, f"missing record types {sorted(missing_types)}")

    queries = data.get("queries")
    if not isinstance(queries, list) or not queries:
        report.add_error(path, "queries must be a non-empty list")
        queries = []

    answered = 0
    for query in queries:
        if not isinstance(query, dict):
            report.add_error(path, "queries[] must contain objects")
            continue
        query_id = query.get("query_id") or "<missing>"
        for key in ("query_id", "question", "intent"):
            if not _nonempty_string(query.get(key)):
                report.add_error(path, f"{query_id}.{key} must be a non-empty string")
        expected = query.get("expected_record_ids")
        if not _list_of_strings(expected):
            report.add_error(path, f"{query_id}.expected_record_ids must be a non-empty list of strings")
            continue
        actual_ids = {record.get("memory_id") for record in answer_query(data, query)}
        missing_expected = set(expected) - actual_ids
        if missing_expected:
            report.add_error(path, f"{query_id} did not return expected records {sorted(missing_expected)}")
        else:
            answered += 1

    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "memory_id": data.get("memory_id"),
            "record_count": len(records),
            "query_count": len(queries),
            "answered_queries": answered,
            "phase_codes": sorted(phase_codes),
            "record_types": sorted(record_types),
        }
    )
    return report


def iter_memory_paths():
    for path in sorted(glob.glob(os.path.join(MEMORY_DIR, "*.json"))):
        if "ledger" in os.path.basename(path):
            continue
        yield path


def validate_all():
    merged = MemoryReport()
    for path in iter_memory_paths():
        report = validate_memory(path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append("no project memory files found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        print(
            f"PASS? {item['path']} "
            f"({item['record_count']} records; {item['answered_queries']}/{item['query_count']} queries)"
        )
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} project memory fixture(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
