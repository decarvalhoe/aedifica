#!/usr/bin/env python3
"""Validate cost/fee fixtures and demonstrate an in-memory CRBX-style round-trip."""
from dataclasses import dataclass, field
from io import BytesIO
import json
import os
import sys
import zipfile


HERE = os.path.dirname(os.path.abspath(__file__))
COST_DIR = os.path.join(HERE, "cost")
FEE_PATH = os.path.join(COST_DIR, "sia102_fee_sample.json")
BRIDGE_PATH = os.path.join(COST_DIR, "quantity_taxonomy_bridge.json")


@dataclass
class CostReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        self.errors.append(f"{os.path.relpath(path, HERE)}: {message}")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_fee_sample(path=FEE_PATH):
    report = CostReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report
    sample = data.get("sample_mandate") or {}
    if sample.get("estimated_hours", 0) <= 0:
        report.add_error(path, "sample_mandate.estimated_hours must be positive")
    if sample.get("estimated_fee_chf", 0) <= 0:
        report.add_error(path, "sample_mandate.estimated_fee_chf must be positive")
    flags = sample.get("absorbed_prestations")
    if not isinstance(flags, list) or not flags:
        report.add_error(path, "absorbed_prestations must be a non-empty list")
    else:
        for flag in flags:
            if not _nonempty_string(flag.get("flag_id")) or flag.get("estimated_hours", 0) <= 0:
                report.add_error(path, "absorbed prestations need flag_id and positive estimated_hours")
    methods = (data.get("method_contract") or {}).get("supported_methods")
    if not isinstance(methods, list) or "hourly_model_H_equals_T_times_h" not in methods:
        report.add_error(path, "method_contract must include H = T x h model")
    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "fee_sample",
            "estimated_hours": sample.get("estimated_hours"),
            "estimated_fee_chf": sample.get("estimated_fee_chf"),
            "absorbed_count": len(flags or []),
        }
    )
    return report


def build_crbx_bytes(bridge):
    payload = {
        "bridge_id": bridge["bridge_id"],
        "quantity_rows": bridge["quantity_rows"],
        "source_refs": bridge["source_refs"],
    }
    manifest = {
        "package_type": "crbx_demo",
        "bridge_id": bridge["bridge_id"],
        "entries": ["exchange.e1s"],
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("exchange.e1s", json.dumps(payload, ensure_ascii=False, indent=2))
    return buffer.getvalue()


def parse_crbx_bytes(data):
    with zipfile.ZipFile(BytesIO(data), "r") as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        exchange = json.loads(zf.read("exchange.e1s").decode("utf-8"))
    return names, manifest, exchange


def validate_bridge(path=BRIDGE_PATH):
    report = CostReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report
    rows = data.get("quantity_rows")
    if not isinstance(rows, list) or not rows:
        report.add_error(path, "quantity_rows must be a non-empty list")
        rows = []
    for row in rows:
        for key in ("row_id", "eccc_code", "cfc_code", "npk_draft"):
            if key not in row:
                report.add_error(path, f"quantity row missing {key}")
    names, manifest, exchange = parse_crbx_bytes(build_crbx_bytes(data))
    required = set((data.get("crbx_round_trip_contract") or {}).get("required_entries") or [])
    if not required.issubset(names):
        report.add_error(path, f"crbx package missing entries {sorted(required - names)}")
    if manifest.get("bridge_id") != data.get("bridge_id"):
        report.add_error(path, "manifest bridge_id was not preserved")
    if [row.get("row_id") for row in exchange.get("quantity_rows", [])] != [row.get("row_id") for row in rows]:
        report.add_error(path, "quantity row IDs were not preserved in round-trip")
    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "quantity_bridge",
            "quantity_count": len(rows),
            "crbx_entries": sorted(names),
        }
    )
    return report


def validate_all():
    merged = CostReport()
    for validator in (validate_fee_sample, validate_bridge):
        report = validator()
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        if item["kind"] == "fee_sample":
            print(
                f"PASS? {item['path']} "
                f"({item['estimated_hours']} h; CHF {item['estimated_fee_chf']}; "
                f"{item['absorbed_count']} absorbed flags)"
            )
        else:
            print(f"PASS? {item['path']} ({item['quantity_count']} rows; CRBX entries: {', '.join(item['crbx_entries'])})")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} cost asset(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
