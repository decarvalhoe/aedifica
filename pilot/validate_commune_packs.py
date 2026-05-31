#!/usr/bin/env python3
"""Regression tests for the ingested commune packs (Lausanne + Pully).

Turns the two commune packs into regressions instead of manual examples: it
fails — naming the affected commune and zone — if a required zone field, a known
index value, a provenance/source ref or the ingestion note disappears.

Run:
    python pilot/validate_commune_packs.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# Known anchors: a change here is a real regression that must be reviewed.
ANCHORS = {
    "Lausanne": {
        "pack": os.path.join("lausanne", "rpga_zones.json"),
        "ingestion_doc": os.path.join("lausanne", "INGESTION.md"),
        "zones": {
            "Zone mixte de faible densité": {"ius": 0.5},
            "Zone d'utilité publique": {"ius": 2.0},
            "Centre historique": {"ius": None},
        },
    },
    "Pully": {
        "pack": os.path.join("pully", "rpga_zones.json"),
        "ingestion_doc": os.path.join("pully", "INGESTION.md"),
        "zones": {
            "Zone d'habitation à moyenne densité": {"ios": 0.2},
        },
    },
}


@dataclass
class CommunePackReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check_zone(commune: str, zone_name: str, zone: dict, expected: dict, report: CommunePackReport) -> None:
    label = f"{commune}/{zone_name}"
    if zone is None:
        report.add_error(f"{label}: zone is missing from the pack")
        return
    for index_key, value in expected.items():
        if index_key not in zone:
            report.add_error(f"{label}: required field '{index_key}' disappeared")
        elif zone.get(index_key) != value:
            report.add_error(f"{label}: {index_key} changed from {value!r} to {zone.get(index_key)!r}")
    provenance = zone.get("provenance")
    if not isinstance(provenance, dict):
        report.add_error(f"{label}: provenance/source ref missing")
        return
    for key in ("article", "url", "confidence"):
        if not provenance.get(key):
            report.add_error(f"{label}: provenance.{key} (source ref) missing")


def validate_all() -> CommunePackReport:
    report = CommunePackReport()
    for commune, spec in ANCHORS.items():
        pack_path = os.path.join(HERE, spec["pack"])
        if not os.path.exists(pack_path):
            report.add_error(f"{commune}: pack file {spec['pack']} is missing")
            continue
        pack = _load(pack_path)
        if pack.get("commune") != commune:
            report.add_error(f"{commune}: pack commune field is {pack.get('commune')!r}")
        document = pack.get("document", {})
        if not document.get("note"):
            report.add_error(f"{commune}: ingestion note (document.note) disappeared")
        if not pack.get("ingested_at"):
            report.add_error(f"{commune}: ingested_at disappeared")
        if not os.path.exists(os.path.join(HERE, spec["ingestion_doc"])):
            report.add_error(f"{commune}: ingestion doc {spec['ingestion_doc']} is missing")
        zones = pack.get("zones", {})
        for zone_name, expected in spec["zones"].items():
            _check_zone(commune, zone_name, zones.get(zone_name), expected, report)
        report.items.append({"commune": commune, "zone_count": len(zones), "anchors": len(spec["zones"])})
    return report


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['commune']}: {item['zone_count']} zones, {item['anchors']} anchors")
    if report.errors:
        print("\nCommune pack regression errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\ncommune pack regressions validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
