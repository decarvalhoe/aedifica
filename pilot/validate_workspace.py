#!/usr/bin/env python3
"""Validate Aedifica project workspace fixtures."""
import sys

import workspace


def validate_all():
    return workspace.validate_all()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        j = item["jurisdiction"] or {}
        print(
            f"PASS? {item['path']} "
            f"({item['project_id']}; {j.get('country')}/{j.get('canton')}/{j.get('commune')}; "
            f"{item['report_count']} reports)"
        )
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} project workspace fixture(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())

