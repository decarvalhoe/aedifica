#!/usr/bin/env python3
"""Validate adapter capability manifests against the schema (stdlib, offline).

Each manifest validates; the Archicad/IFC/Speckle baselines exist; required but
unsupported capabilities are reported (not silently passed); and the schema can
represent the future Revit/Rhino/SketchUp/AutoCAD/BricsCAD/Vectorworks adapters.

Run:
    python pilot/validate_adapter_capability.py
"""
from dataclasses import dataclass, field
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import adapter_capability as cap  # noqa: E402

EXPECTED_ADAPTERS = {"archicad_json", "ifc_ifcopenshell", "speckle"}
FUTURE_FAMILIES = {"revit", "rhino", "sketchup", "autocad", "bricscad", "vectorworks"}


@dataclass
class AdapterCapabilityReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def validate_all() -> AdapterCapabilityReport:
    report = AdapterCapabilityReport()
    schema = cap.load_schema()
    manifests = cap.all_manifests()

    found = set()
    for manifest in manifests:
        adapter_id = manifest.get("adapter_id", "<unknown>")
        found.add(adapter_id)
        errors = cap.validate_manifest(manifest, schema)
        for err in errors:
            report.add_error(f"{adapter_id}: {err}")

    missing_adapters = EXPECTED_ADAPTERS - found
    if missing_adapters:
        report.add_error(f"missing adapter manifests: {sorted(missing_adapters)}")

    # Unknown/unsupported required capability is reported, not silently passed.
    try:
        ifc = cap.load_manifest("ifc_ifcopenshell")
        if not cap.missing_capabilities(ifc, {"write": ["set_properties"]}):
            report.add_error("IFC adapter should report write:set_properties as unsupported")
        archicad = cap.load_manifest("archicad_json")
        if cap.missing_capabilities(archicad, {"write": ["set_properties"], "transaction": True}):
            report.add_error("Archicad adapter should support set_properties + transactions")
    except cap.AdapterCapabilityError as exc:
        report.add_error(str(exc))

    # Schema can represent future adapter families.
    family_enum = set(schema["properties"]["family"]["enum"])
    if not FUTURE_FAMILIES.issubset(family_enum):
        report.add_error(f"schema family enum cannot represent {sorted(FUTURE_FAMILIES - family_enum)}")

    report.items.append({"adapters": sorted(found), "count": len(manifests)})
    return report


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['count']} adapter manifests: {', '.join(item['adapters'])}")
    if report.errors:
        print("\nAdapter capability validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\nadapter capability manifests validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
