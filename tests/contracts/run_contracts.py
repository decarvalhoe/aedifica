#!/usr/bin/env python3
"""Run stdlib contract validators used by CI and release checks."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PILOT = os.path.join(ROOT, "pilot")
sys.path.insert(0, PILOT)

import validate_compliance  # noqa: E402
import validate_cost  # noqa: E402
import validate_ledger  # noqa: E402
import validate_manifest  # noqa: E402
import validate_matrix  # noqa: E402
import validate_memory  # noqa: E402
import validate_packs  # noqa: E402
import validate_permit  # noqa: E402
import validate_research  # noqa: E402
import validate_site  # noqa: E402
import validate_workspace  # noqa: E402


VALIDATORS = [
    validate_packs.validate_all,
    validate_manifest.validate_all,
    validate_matrix.validate_all,
    validate_permit.validate_all,
    validate_compliance.validate_all,
    validate_research.validate_all,
    validate_memory.validate_all,
    validate_ledger.validate_all,
    validate_workspace.validate_all,
    validate_cost.validate_all,
    validate_site.validate_all,
]


def main():
    errors = []
    for validator in VALIDATORS:
        report = validator()
        errors.extend(getattr(report, "errors", []))
    if errors:
        print("Contract failures:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"{len(VALIDATORS)} contract validator(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
