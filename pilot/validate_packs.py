#!/usr/bin/env python3
"""Validate Aedifica pilot jurisdiction packs with stdlib only.

This is intentionally lightweight: it protects the current pilot contract in CI
without adding a dependency on jsonschema before the project has a package setup.

Run:
    python pilot/validate_packs.py
"""
from dataclasses import dataclass, field
from datetime import date
import glob
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
SCHEMA_VERSION = "1.0"


@dataclass
class ValidationReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        rel = os.path.relpath(path, HERE)
        self.errors.append(f"{rel}: {message}")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _is_number_or_none(value):
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool))


def _valid_iso_date(value):
    if not _is_nonempty_string(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _require(mapping, path, report, dotted_name, predicate, description):
    current = mapping
    for part in dotted_name.split("."):
        if not isinstance(current, dict) or part not in current:
            report.add_error(path, f"missing {dotted_name}")
            return None
        current = current[part]
    if not predicate(current):
        report.add_error(path, f"{dotted_name} must be {description}")
    return current


def _validate_version(data, path, report):
    schema_version = _require(
        data,
        path,
        report,
        "schema_version",
        lambda v: v == SCHEMA_VERSION,
        f"{SCHEMA_VERSION!r}",
    )
    source_version = _require(
        data,
        path,
        report,
        "source_version",
        lambda v: isinstance(v, dict),
        "an object",
    )
    if isinstance(source_version, dict):
        _require(source_version, path, report, "source_status", _is_nonempty_string, "a string")
        _require(source_version, path, report, "verified_at", _valid_iso_date, "an ISO date")
        _require(source_version, path, report, "review_due", _valid_iso_date, "an ISO date")
    return schema_version, source_version


def _validate_unit(unit, path, report, index):
    if not isinstance(unit, dict):
        report.add_error(path, f"units[{index}] must be an object")
        return
    for key in ("id", "title", "ref", "url", "scope"):
        if not _is_nonempty_string(unit.get(key)):
            report.add_error(path, f"units[{index}].{key} must be a non-empty string")
    if unit.get("confidence") not in ALLOWED_CONFIDENCE:
        report.add_error(path, f"units[{index}].confidence must be one of {sorted(ALLOWED_CONFIDENCE)}")


def _validate_registry_pack(data, path, report):
    _require(data, path, report, "level", lambda v: v in {"federal", "cantonal"}, "federal or cantonal")
    _require(data, path, report, "jurisdiction", _is_nonempty_string, "a string")
    _require(data, path, report, "description", _is_nonempty_string, "a string")
    units = _require(data, path, report, "units", lambda v: isinstance(v, list) and v, "a non-empty list")
    if isinstance(units, list):
        for index, unit in enumerate(units):
            _validate_unit(unit, path, report, index)


def _validate_zone(zone, path, report, zone_name):
    if not isinstance(zone, dict):
        report.add_error(path, f"zones[{zone_name!r}] must be an object")
        return
    for key in ("ius", "ibus", "ios", "height_corniche_m", "height_faite_m", "levels_max", "setback_min_m"):
        if not _is_number_or_none(zone.get(key)):
            report.add_error(path, f"zones[{zone_name!r}].{key} must be a number or null")
    if not _is_nonempty_string(zone.get("other")):
        report.add_error(path, f"zones[{zone_name!r}].other must be a non-empty string")
    provenance = zone.get("provenance")
    if not isinstance(provenance, dict):
        report.add_error(path, f"zones[{zone_name!r}].provenance must be an object")
        return
    for key in ("article", "url"):
        if not _is_nonempty_string(provenance.get(key)):
            report.add_error(path, f"zones[{zone_name!r}].provenance.{key} must be a non-empty string")
    if provenance.get("confidence") not in ALLOWED_CONFIDENCE:
        report.add_error(path, f"zones[{zone_name!r}].provenance.confidence must be one of {sorted(ALLOWED_CONFIDENCE)}")


def _validate_commune_pack(data, path, report):
    _require(data, path, report, "commune", _is_nonempty_string, "a string")
    _require(data, path, report, "ingested_at", _valid_iso_date, "an ISO date")
    document = _require(data, path, report, "document", lambda v: isinstance(v, dict), "an object")
    if isinstance(document, dict):
        for key in ("title", "version", "in_force", "url", "note"):
            if not _is_nonempty_string(document.get(key)):
                report.add_error(path, f"document.{key} must be a non-empty string")
    zones = _require(data, path, report, "zones", lambda v: isinstance(v, dict) and v, "a non-empty object")
    if isinstance(zones, dict):
        for zone_name, zone in zones.items():
            if not _is_nonempty_string(zone_name):
                report.add_error(path, "zone names must be non-empty strings")
            _validate_zone(zone, path, report, zone_name)


def _classify_pack(path, data):
    if os.path.basename(path) == "rpga_zones.json":
        return "commune"
    if "units" in data:
        return "registry"
    return "unknown"


def iter_pack_paths():
    yield from sorted(glob.glob(os.path.join(HERE, "registry", "*.json")))
    yield from sorted(glob.glob(os.path.join(HERE, "*", "rpga_zones.json")))


def validate_pack(path):
    report = ValidationReport()
    try:
        data = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    schema_version, source_version = _validate_version(data, path, report)
    kind = _classify_pack(path, data)
    if kind == "registry":
        _validate_registry_pack(data, path, report)
    elif kind == "commune":
        _validate_commune_pack(data, path, report)
    else:
        report.add_error(path, "cannot classify pack")

    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": kind,
            "schema_version": schema_version,
            "source_version": source_version,
        }
    )
    return report


def validate_all():
    merged = ValidationReport()
    for path in iter_pack_paths():
        report = validate_pack(path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append("no jurisdiction packs found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['kind']}, schema {item['schema_version']})")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} jurisdiction packs validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
