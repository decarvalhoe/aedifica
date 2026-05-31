"""Map the Vaud/ACTIS-CAMAC checklist to project evidence.

Connects each checklist requirement to the dossier evidence entries and returns a
status of ``present``, ``missing``, ``assumption`` (matched but still pending
human confirmation) or ``not_applicable``. Every requirement keeps both its
checklist provenance (source_ids) and the evidence provenance (source_refs).
"""
from __future__ import annotations

import validate_permit as _vp

PRESENT_STATUSES = {"present"}
PENDING_STATUSES = {"pending"}
NOT_APPLICABLE_STATUSES = {"not_applicable", "out_of_scope"}
RESULT_STATUSES = {"present", "missing", "assumption", "not_applicable"}


def map_actis_camac(checklist: dict, dossier: dict) -> list:
    by_key = _vp.evidence_by_key(dossier)
    results = []
    for item in checklist.get("items", []):
        accepted = item.get("accepted_evidence", [])
        matched = [record for key in accepted for record in by_key.get(key, [])]
        present = [r for r in matched if r.get("status") in PRESENT_STATUSES]
        pending = [r for r in matched if r.get("status") in PENDING_STATUSES]
        not_applicable = [r for r in matched if r.get("status") in NOT_APPLICABLE_STATUSES]
        if present:
            status = "present"
        elif pending:
            status = "assumption"
        elif not_applicable:
            status = "not_applicable"
        elif item.get("required"):
            status = "missing"
        else:
            status = "not_applicable"
        evidence = present or pending or not_applicable
        results.append(
            {
                "item_id": item["item_id"],
                "title": item["title"],
                "category": item["category"],
                "required": item.get("required") is True,
                "status": status,
                "missing_message": item.get("missing_message"),
                "checklist_provenance": list(item.get("source_ids", [])),
                "evidence_provenance": [ref for record in evidence for ref in record.get("source_refs", [])],
            }
        )
    return results


def summarize(results: list) -> dict:
    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    missing = [r["item_id"] for r in results if r["status"] == "missing"]
    return {
        "counts": counts,
        "missing": missing,
        "required_blockers": len(missing),
        "assumptions": [r["item_id"] for r in results if r["status"] == "assumption"],
        "not_applicable": [r["item_id"] for r in results if r["status"] == "not_applicable"],
    }
