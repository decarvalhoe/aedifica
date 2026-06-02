#!/usr/bin/env python3
"""Validate Aedifica demo ledger files."""
from dataclasses import dataclass, field
import glob
import json
import os
import sys

import ledger


HERE = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(HERE, "memory")


@dataclass
class LedgerReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_file(path):
    report = LedgerReport()
    try:
        data = _load(path)
        ledger.validate_ledger(data)
    except (OSError, json.JSONDecodeError, ledger.LedgerValidationError) as exc:
        report.errors.append(f"{os.path.relpath(path, HERE)}: {exc}")
        return report
    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "ledger_id": data.get("ledger_id"),
            "entry_count": len(data.get("entries", [])),
            "event_types": sorted({entry.get("event_type") for entry in data.get("entries", [])}),
        }
    )
    return report


def validate_all():
    merged = LedgerReport()
    for path in sorted(glob.glob(os.path.join(MEMORY_DIR, "*ledger*.json"))):
        report = validate_file(path)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append("no ledger files found")
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['path']} ({item['entry_count']} entries; {', '.join(item['event_types'])})")
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
