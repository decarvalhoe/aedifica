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


def _empty_dossier(project) -> dict:
    """A valid-but-empty permit dossier for a project with nothing submitted yet."""
    return {
        "dossier_id": f"{project.project_id}-DOSSIER",
        "checklist_id": "PERMIT-VD-CAMAC-BASELINE",
        "project_context": {"country": project.country, "canton_or_region": project.canton, "commune": project.commune, "phase_code": project.phase_code},
        "evidence_records": [],
    }


def permit_view(project) -> dict:
    import permit_readiness  # noqa: E402

    checklist = _load("permit", "vd_camac_checklist.json")
    dossier = project.permit_dossier or _empty_dossier(project)
    r = permit_readiness.build_readiness(checklist, dossier)
    return {
        "dossier_id": r["dossier_id"],
        "state": r["state"],
        "ready_for_review": r["ready_for_review"],
        "summary": r["summary"],
        "disclaimers": r["disclaimers"],
        "data_basis": "project" if project.permit_dossier else "empty",
        "groups": [
            {
                "actor": g["actor"],
                "category": g["category"],
                "items": [
                    {"item_id": i["item_id"], "title": i["title"], "status": i["status"], "missing_message": i.get("missing_message")}
                    for i in g["items"]
                ],
            }
            for g in r["groups"]
        ],
    }


def submit_permit_piece(project, item_id: str, present: bool) -> None:
    """Mark a permit checklist item as submitted (present) or withdrawn, in the
    project's own dossier. Real per-project submission — no global fixture."""
    checklist = _load("permit", "vd_camac_checklist.json")
    item = next((it for it in checklist["items"] if it["item_id"] == item_id), None)
    if item is None:
        raise ValueError(f"unknown checklist item {item_id}")
    key = (item.get("accepted_evidence") or [item_id])[0]
    dossier = dict(project.permit_dossier or _empty_dossier(project))
    records = [r for r in dossier.get("evidence_records", []) if r.get("key") != key]
    if present:
        records.append({
            "evidence_id": f"EVID-{key.upper()}",
            "key": key,
            "kind": "app_submission",
            "title": item["title"],
            "status": "present",
            "source_refs": [{"source_id": "APP-SUBMISSION", "locator": "Déposé dans l'application", "valid_as_of": "2026-06-03", "confidence": "declared"}],
        })
    dossier["evidence_records"] = records
    project.permit_dossier = dossier  # reassign so SQLAlchemy flags the JSON column dirty


# W21-4 — claim titles that touch what neighbors actually oppose (heights,
# limits, shadows, parking, heritage…). Lowercase, accent-insensitive matching.
NEIGHBOR_SENSITIVE = (
    "hauteur", "gabarit", "distance", "limite", "ombr", "voisin", "vue",
    "stationnement", "parking", "bruit", "patrimoine", "densit", "ius",
    "ibus", "alignement", "implantation",
)
# Compliance domains a neighbor can weaponize at the enquête publique.
NEIGHBOR_DOMAINS = {"neighbor", "shadow", "visibility", "alignment", "heritage"}


def _fold(text: str) -> str:
    import unicodedata

    return "".join(c for c in unicodedata.normalize("NFD", (text or "").lower()) if unicodedata.category(c) != "Mn")


def doc_basis(project) -> dict:
    basis = {"canonical": 0, "indicative": 0, "refused": 0, "pending": 0}
    for doc in project.documents:
        basis[doc.validation_level] = basis.get(doc.validation_level, 0) + 1
    return basis


def opposition_points(project) -> list[dict]:
    """Targeted, mechanical attention points — never an invented severity.

    Each point is derived from something verifiable in the dossier (a claim in
    conflict, an unsourced neighbor-sensitive claim, a neighbor-facing
    compliance gate left open, the canonical coverage of the pieces) and
    carries its basis. This is the Etienne redress of the generic score:
    « au lieu de élevé/modéré, dire attention précisément à CE point ».
    """
    points: list[dict] = []
    claims = list(project.claims)

    for c in claims:
        if c.state == "conflict":
            points.append({
                "kind": "conflit_avere",
                "focus": f"Friction avérée · {c.title}",
                "why": "Deux bases se contredisent sur ce point — un opposant l'exploitera tel quel à l'enquête.",
                "action": c.next_action or "Arbitrer le conflit et tracer la décision (Mémoire).",
                "basis": [{"kind": "claim", "ref": c.claim_id, "title": c.title, "state": c.state, "sources": c.source_refs or []}],
            })
    for c in claims:
        if c.state in ("unknown", "assumption") and any(k in _fold(c.title) for k in NEIGHBOR_SENSITIVE):
            points.append({
                "kind": "base_non_sourcee",
                "focus": f"Point sensible voisinage non sourcé · {c.title}",
                "why": "Valeur non adossée à une source officielle sur un motif d'opposition classique — attaquable à l'enquête.",
                "action": c.next_action or "Sourcer (règlement communal / RDPPF) puis valider la pièce en canonique.",
                "basis": [{"kind": "claim", "ref": c.claim_id, "title": c.title, "state": c.state, "sources": c.source_refs or []}],
            })

    if project.compliance_inputs:
        cv = compliance_view(project)
        for gate in (cv.get("legal") or []) + (cv.get("contractual") or []):
            if gate.get("status") == "action_required" and gate.get("domain") in NEIGHBOR_DOMAINS:
                points.append({
                    "kind": "conformite_voisinage",
                    "focus": f"Gate voisinage ouvert · {gate.get('title')}",
                    "why": "Exigence côté voisins non satisfaite — motif d'opposition recevable tant que le gate reste ouvert.",
                    "action": gate.get("next_action") or "Lever le gate dans Conformité.",
                    "basis": [{"kind": "compliance_gate", "ref": gate.get("domain"), "title": gate.get("title"), "binding_type": gate.get("binding_type")}],
                })

    basis = doc_basis(project)
    if claims and basis["canonical"] == 0:
        points.append({
            "kind": "couverture_canonique",
            "focus": "Aucune pièce canonique au dossier",
            "why": "L'analyse repose uniquement sur des pièces non validées — fragile face à une opposition documentée.",
            "action": "Valider les pièces de référence (canonique) dans Documents & sources.",
            "basis": [{"kind": "documents", "ref": "validation_levels", "counts": basis}],
        })
    if basis["refused"] > 0:
        points.append({
            "kind": "piece_refusee",
            "focus": f"{basis['refused']} pièce(s) refusée(s) encore au dossier",
            "why": "Une pièce écartée par l'architecte maître reste référencée — source d'ambiguïté exploitable.",
            "action": "Purger ou re-valider ces pièces (Documents & sources).",
            "basis": [{"kind": "documents", "ref": "validation_levels", "counts": basis}],
        })
    return points


def opposition_view(project) -> dict:
    import opposition_radar as radar  # noqa: E402

    # W21-4 — the targeted layer is computed from the live dossier in BOTH
    # branches: it exists (or honestly doesn't) independently of the legacy
    # generic radar.
    points = opposition_points(project)
    basis = doc_basis(project)

    risks = project.brief_risks
    if not risks:
        return {
            "overall": None, "score": None, "claims_prediction": False, "data_basis": "empty",
            "disclaimer": "Aucune analyse de parcelle pour ce projet — lancez une recherche d'adresse dans Terrain & zonage.",
            "signals": [],
            "points": points,
            "doc_basis": basis,
        }
    model = radar.evidence_model(risks)
    return {
        "overall": risks.get("overall"),
        "score": risks.get("score"),
        "claims_prediction": False,
        "data_basis": "project",
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
        "points": points,
        "doc_basis": basis,
    }


def compliance_view(project) -> dict:
    import compliance_report  # noqa: E402

    gates = _load("compliance", "ch_phase33_gates.json")
    inputs = project.compliance_inputs or {}
    r = compliance_report.build_compliance_report(gates, inputs)

    def _gate(g):
        return {"title": g["title"], "domain": g["domain"], "status": g["status"], "binding_type": g["binding_type"], "next_action": g.get("next_action")}

    return {
        "phase_code": r["phase_code"],
        "summary": r["summary"],
        "data_basis": "project" if project.compliance_inputs else "empty",
        "legal": [_gate(g) for g in r["legal"]],
        "contractual": [_gate(g) for g in r["contractual"]],
    }


def cost_view(project) -> dict:
    import validate_cost  # noqa: E402

    ci = project.cost_inputs
    if not ci:
        return {"data_basis": "empty", "cockpit": None, "tender_assumptions": [], "quantity_rows": []}
    return {
        "data_basis": "project",
        "cockpit": validate_cost.profitability_cockpit(ci["fee"]),
        "tender_assumptions": ci.get("tender", []),
        "quantity_rows": ci.get("bridge", []),
    }


def site_view(project) -> dict:
    si = project.site_inputs
    if not si:
        return {"data_basis": "empty", "handover": [], "defects": [],
                "summary": {"handover_blocked": 0, "handover_open": 0, "handover_closed": 0, "defects_open": 0}}
    items = si.get("handover", [])
    dlist = si.get("defects", [])
    return {
        "data_basis": "project",
        "handover": items,
        "defects": dlist,
        "summary": {
            "handover_blocked": sum(1 for i in items if i.get("status") == "blocked"),
            "handover_open": sum(1 for i in items if i.get("status") == "open"),
            "handover_closed": sum(1 for i in items if i.get("status") == "closed"),
            "defects_open": sum(1 for d in dlist if d.get("status") not in ("closed", "resolved")),
        },
    }


def seed_reference_reports(project) -> None:
    """Seed the demo/reference project with the demo dossier, inputs, cost & site.

    Real projects start empty (nothing submitted); only the explicit reference
    project carries this demo submission so the surfaces have something to show.
    """
    project.permit_dossier = _load("permit", "demo_missing_dossier.json")
    project.compliance_inputs = _load("compliance", "demo_missing_inputs.json")["inputs"]
    project.cost_inputs = {
        "fee": _load("cost", "sia102_fee_sample.json"),
        "tender": _load("cost", "tender_assumptions_log.json").get("entries", []),
        "bridge": _load("cost", "quantity_taxonomy_bridge.json").get("quantity_rows", []),
    }
    project.site_inputs = {
        "handover": _load("site", "handover_checklist.json").get("items", []),
        "defects": _load("site", "defect_register_fixture.json").get("defects", []),
    }
