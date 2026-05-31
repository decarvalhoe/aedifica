#!/usr/bin/env python3
"""Run the offline Aedifica demo path from the fixture pack."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import workspace  # noqa: E402
import validate_permit  # noqa: E402
import opposition_radar  # noqa: E402


HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    project_dir = os.path.join(HERE, "projects", "demo_lausanne_palud")
    brief = workspace.generate_offline_parcel_brief(project_dir)
    checklist = validate_permit._load(os.path.join(HERE, "permit", "vd_camac_checklist.json"))
    dossier = validate_permit._load(os.path.join(HERE, "permit", "demo_complete_dossier.json"))
    permit = validate_permit.completeness_report(checklist, dossier)
    risk = opposition_radar.report(brief["risks"])
    print(f"Brief: {brief['brief_id']} ({len(brief['claims'])} claims)")
    print(f"Permit blockers: {permit['summary']['required_blockers']}")
    print(f"Opposition risk: {risk['summary']['overall']} ({risk['summary']['signal_count']} signals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
