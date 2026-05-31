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
TENDER_LOG_PATH = os.path.join(COST_DIR, "tender_assumptions_log.json")


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
    if sample.get("hourly_rate_chf", 0) <= 0:
        report.add_error(path, "sample_mandate.hourly_rate_chf must be positive")
    if sample.get("target_margin_percent", 0) <= 0:
        report.add_error(path, "sample_mandate.target_margin_percent must be positive")
    special = sample.get("special_prestations")
    if not isinstance(special, list) or not special:
        report.add_error(path, "special_prestations must be a non-empty list")
    else:
        for item in special:
            for key in ("prestation_id", "title", "pricing_status"):
                if not _nonempty_string(item.get(key)):
                    report.add_error(path, f"special_prestations missing {key}")
            if item.get("estimated_hours", 0) <= 0:
                report.add_error(path, "special_prestations estimated_hours must be positive")
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
            "target_margin_percent": sample.get("target_margin_percent"),
            "absorbed_count": len(flags or []),
            "special_count": len(special or []),
        }
    )
    return report


def profitability_cockpit(fee_data):
    sample = fee_data["sample_mandate"]
    absorbed_hours = sum(item["estimated_hours"] for item in sample.get("absorbed_prestations", []))
    absorbed_cost = round(absorbed_hours * sample["hourly_rate_chf"], 2)
    target_margin = sample["target_margin_percent"]
    estimated_fee = sample["estimated_fee_chf"]
    risk = "high" if absorbed_cost > estimated_fee * 0.15 else "medium" if absorbed_cost else "low"
    return {
        "estimated_fee_chf": estimated_fee,
        "estimated_hours": sample["estimated_hours"],
        "hourly_rate_chf": sample["hourly_rate_chf"],
        "target_margin_percent": target_margin,
        "absorbed_hours": absorbed_hours,
        "absorbed_cost_chf": absorbed_cost,
        "margin_risk": risk,
        "absorbed_tasks": sample.get("absorbed_prestations", []),
        "special_prestations": sample.get("special_prestations", []),
        "assumptions": sample.get("assumptions", []),
    }


def render_profitability_html(cockpit):
    absorbed = "".join(f"<li>{item['title']} ({item['estimated_hours']} h)</li>" for item in cockpit["absorbed_tasks"])
    assumptions = "".join(f"<li>{item}</li>" for item in cockpit["assumptions"])
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Profitability cockpit</title></head>
<body>
  <h1>Profitability cockpit</h1>
  <p>Estimated fee: CHF {cockpit['estimated_fee_chf']} · Target margin: {cockpit['target_margin_percent']}%</p>
  <p>Absorbed cost: CHF {cockpit['absorbed_cost_chf']} · Risk: {cockpit['margin_risk']}</p>
  <h2>Absorbed tasks</h2><ul>{absorbed}</ul>
  <h2>Assumptions</h2><ul>{assumptions}</ul>
</body>
</html>
"""


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
    if len(rows) < 3:
        report.add_error(path, "quantity_rows must contain multiple sample mappings")
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


def validate_tender_log(path=TENDER_LOG_PATH):
    report = CostReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report
    for key in ("schema_version", "log_id", "project_id", "phase_code"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        report.add_error(path, "entries must be a non-empty list")
        entries = []
    for entry in entries:
        for key in ("assumption_id", "kind", "title", "status", "source_ref", "offer_comparison_column"):
            if not _nonempty_string(entry.get(key)):
                report.add_error(path, f"tender assumption entry missing {key}")
    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "tender_assumptions",
            "entry_count": len(entries),
            "carry_count": sum(1 for entry in entries if entry.get("status") == "carry_to_offer_comparison"),
        }
    )
    return report


def validate_all():
    merged = CostReport()
    for validator in (validate_fee_sample, validate_bridge, validate_tender_log):
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
                f"{item['absorbed_count']} absorbed flags; {item['special_count']} special prestations)"
            )
        elif item["kind"] == "quantity_bridge":
            print(f"PASS? {item['path']} ({item['quantity_count']} rows; CRBX entries: {', '.join(item['crbx_entries'])})")
        else:
            print(f"PASS? {item['path']} ({item['entry_count']} tender assumptions; {item['carry_count']} carried)")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} cost asset(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
