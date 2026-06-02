"""Engine report projections for the web app (permit / opposition / compliance).

These read the engine + pilot fixtures and return JSON-ready dicts. They are
demo-fixture-backed today; per-project dossier/inputs wiring comes as projects
accumulate real evidence.
"""
from __future__ import annotations

import json
import os

from aedifica import _bootstrap  # noqa: F401  (pilot engine on sys.path)

PILOT = _bootstrap.PILOT_DIR
DEMO_DIR = os.path.join(PILOT, "projects", "demo_lausanne_palud")


def _load(*parts) -> dict:
    with open(os.path.join(PILOT, *parts), encoding="utf-8") as f:
        return json.load(f)


def permit_view() -> dict:
    import permit_readiness  # noqa: E402

    checklist = _load("permit", "vd_camac_checklist.json")
    dossier = _load("permit", "demo_missing_dossier.json")
    r = permit_readiness.build_readiness(checklist, dossier)
    return {
        "dossier_id": r["dossier_id"],
        "state": r["state"],
        "ready_for_review": r["ready_for_review"],
        "summary": r["summary"],
        "disclaimers": r["disclaimers"],
        "groups": [
            {
                "actor": g["actor"],
                "category": g["category"],
                "items": [
                    {"title": i["title"], "status": i["status"], "missing_message": i.get("missing_message")}
                    for i in g["items"]
                ],
            }
            for g in r["groups"]
        ],
    }


def opposition_view() -> dict:
    import opposition_radar as radar  # noqa: E402
    import workspace  # noqa: E402

    brief = workspace.generate_offline_parcel_brief(DEMO_DIR)
    risks = brief["risks"]
    model = radar.evidence_model(risks)
    return {
        "overall": risks.get("overall"),
        "score": risks.get("score"),
        "claims_prediction": False,
        "disclaimer": model["disclaimer"],
        "signals": [
            {
                "ground": s.get("ground"),
                "category": s.get("evidence_category"),
                "level": s.get("level"),
                "basis": s.get("basis"),
                "mitigation": s.get("mitigation"),
                "evidence_state": s.get("evidence_state"),
                "confidence": s.get("confidence"),
            }
            for s in risks.get("signals", [])
        ],
    }


def compliance_view() -> dict:
    import compliance_report  # noqa: E402

    gates = _load("compliance", "ch_phase33_gates.json")
    inputs = _load("compliance", "demo_missing_inputs.json")["inputs"]
    r = compliance_report.build_compliance_report(gates, inputs)

    def _gate(g):
        return {"title": g["title"], "domain": g["domain"], "status": g["status"], "binding_type": g["binding_type"], "next_action": g.get("next_action")}

    return {
        "phase_code": r["phase_code"],
        "summary": r["summary"],
        "legal": [_gate(g) for g in r["legal"]],
        "contractual": [_gate(g) for g in r["contractual"]],
    }
