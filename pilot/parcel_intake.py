"""Parcel intake normalization for project fixtures, EGRIDs and addresses."""
from __future__ import annotations

import json
import os

import artifacts
import domain
import mvp1_demo
import oereb


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _project_context(project_dir: str) -> tuple[dict, dict, str, str]:
    manifest = _load_json(os.path.join(project_dir, "project.json"))
    evidence_rel = manifest.get("parcel", {}).get("oereb_parsed_evidence")
    if not evidence_rel:
        raise ValueError("project parcel.oereb_parsed_evidence is required")
    evidence_path = os.path.join(project_dir, evidence_rel)
    return manifest, _load_json(evidence_path), evidence_rel.replace("\\", "/"), evidence_path


def from_project_fixture(project_dir: str) -> dict:
    manifest, record, evidence_rel, evidence_path = _project_context(project_dir)
    return {
        "input_type": "parcel_fixture",
        "query": manifest.get("parcel", {}).get("egrid"),
        "project_id": manifest.get("project_id"),
        "egrid": record.get("egrid"),
        "parcel_number": record.get("parcel"),
        "commune": record.get("commune"),
        "area_m2": _number_or_none(record.get("area_m2")),
        "oereb_record": record,
        "source_refs": [
            {
                "source_id": "VD-OEREB",
                "locator": f"EGRID {record.get('egrid')}",
                "valid_as_of": record.get("valid_as_of", "2026-05-29"),
                "confidence": "high",
            }
        ],
        "evidence_refs": [
            {
                "evidence_id": f"EVID-OEREB-{record.get('egrid')}",
                "kind": "api_extract",
                "file_ref": f"project://{evidence_rel}",
                "sha256": artifacts.sha256_file(evidence_path),
            }
        ],
    }


def normalize_parcel_input(query: str | None = None, project_dir: str | None = None) -> dict:
    """Return a normalized parcel context.

    `project_dir` is offline and fixture-backed. A query starting with `CH` is
    treated as an EGRID. Other queries are resolved as addresses through the
    existing live geoadmin/OEREB functions.
    """
    if project_dir:
        return from_project_fixture(project_dir)
    if not query:
        raise ValueError("query or project_dir is required")
    if query[:2] == "CH" and query[2:].isdigit():
        record = oereb.get(query)
        return _context_from_record("egrid", query, record, None)

    geocoded = mvp1_demo.geocode(query)
    if not geocoded:
        raise ValueError(f"Address not found: {query}")
    e, n, _ = geocoded
    parcel = mvp1_demo.identify_parcel(e, n)
    if not parcel:
        raise ValueError(f"No parcel found for address: {query}")
    record = oereb.get(parcel["egrid"])
    area = domain.polygon_area_m2(parcel.get("rings"))
    return _context_from_record("address", query, record, area, coordinates={"e": e, "n": n})


def _context_from_record(input_type: str, query: str, record: dict, area_m2, coordinates: dict | None = None) -> dict:
    return {
        "input_type": input_type,
        "query": query,
        "egrid": record.get("egrid"),
        "parcel_number": record.get("parcel"),
        "commune": record.get("commune"),
        "area_m2": _number_or_none(record.get("area_m2")) or _number_or_none(area_m2),
        "coordinates": coordinates,
        "oereb_record": record,
        "source_refs": [
            {
                "source_id": "VD-OEREB",
                "locator": f"EGRID {record.get('egrid')}",
                "valid_as_of": record.get("valid_as_of", "live"),
                "confidence": "high",
            }
        ],
    }


def _number_or_none(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
