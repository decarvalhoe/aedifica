"""Workspace permit readiness report.

Combines the ACTIS-CAMAC mapping, the dossier state machine and the completeness
report into a single architect-facing readiness output, grouped by dossier
section, with missing evidence, assumptions and next actions — and visible
authority/architect-responsibility disclaimers. Unknown or unsupported evidence
never renders as ready.
"""
from __future__ import annotations

import html

import datum_html
import permit_mapping as _pm
import permit_state as _ps
import validate_permit as _vp

READY_STATES = {"ready_for_review", "architect_approved", "submitted_external"}
DISCLAIMERS = [
    "Aedifica prépare et trace le dossier; la décision de permis appartient à l'autorité compétente (VD : ACTIS/CAMAC).",
    "L'architecte reste responsable du contenu, des signatures et de la conformité du dossier déposé.",
    "« Prêt pour revue » signifie dossier complet pour dépôt, jamais permis accordé.",
]


def build_readiness(checklist: dict, dossier: dict, *, architect_approved: bool = False, submitted: bool = False) -> dict:
    completeness = _vp.completeness_report(checklist, dossier)
    results = _pm.map_actis_camac(checklist, dossier)
    summary = _pm.summarize(results)
    state = _ps.derive_state(completeness, architect_approved=architect_approved, submitted=submitted)

    groups = {}
    for result in results:
        group = groups.setdefault(
            result["category"],
            {"category": result["category"], "actor": _vp.ACTOR_BY_CATEGORY.get(result["category"], "architect"), "items": []},
        )
        group["items"].append(result)

    next_actions = [
        {"item_id": r["item_id"], "title": r["title"], "status": r["status"], "action": r["missing_message"]}
        for r in results
        if r["status"] in {"missing", "assumption"}
    ]
    ready = state in READY_STATES and summary["required_blockers"] == 0

    return {
        "dossier_id": dossier.get("dossier_id"),
        "checklist_id": checklist.get("checklist_id"),
        "state": state,
        "state_summary": _ps.state_summary(state, completeness),
        "summary": summary,
        "groups": list(groups.values()),
        "next_actions": next_actions,
        "ready_for_review": ready,
        "is_authority_decision": False,
        "disclaimers": DISCLAIMERS,
    }


def render_readiness_html(readiness: dict) -> str:
    def esc(value):
        return html.escape("" if value is None else str(value))

    summary = readiness["summary"]
    counts = summary.get("counts", {})
    state = readiness["state"]
    banner_class = "sourced" if readiness["ready_for_review"] else "assumption"
    banner_text = (
        "Dossier prêt pour revue de l'architecte"
        if readiness["ready_for_review"]
        else f"Dossier NON prêt — {summary['required_blockers']} blocker(s) requis"
    )
    chips = "".join(
        f"<span class='chip {esc(status)}'>{esc(status)} · {counts.get(status, 0)}</span> "
        for status in ("present", "missing", "assumption", "not_applicable")
    )
    group_sections = []
    for group in readiness["groups"]:
        rows = "".join(
            f"<li class='claim {esc(item['status'])}'><span class='state'>{esc(item['status'])}</span>"
            f"<b>{esc(item['title'])}</b>"
            + (f"<br><small>{esc(item['missing_message'])}</small>" if item["status"] in {"missing", "assumption"} else "")
            + f"<br><small>provenance: {esc(', '.join(item['checklist_provenance']) or '—')}</small></li>"
            for item in group["items"]
        )
        group_sections.append(f"<section><h2>{esc(group['actor'])} · {esc(group['category'])}</h2><ul>{rows}</ul></section>")
    next_rows = "".join(
        f"<li><b>{esc(item['status'])}</b> {esc(item['title'])} — {esc(item['action'])}</li>"
        for item in readiness["next_actions"]
    )
    disclaimer_rows = "".join(f"<li>{esc(d)}</li>" for d in readiness["disclaimers"])
    body = f"""
  <h1>Complétude permis · {esc(readiness['dossier_id'])}</h1>
  <p class='claim {banner_class}'><span class='state'>{esc(state)}</span> {esc(banner_text)}</p>
  <p class='chips'>{chips}</p>
  <section><h2>Disclaimers</h2><ul>{disclaimer_rows}</ul></section>
  {''.join(group_sections)}
  <section><h2>Inconnues / actions requises</h2><ul>{next_rows or '<li>Aucune action requise.</li>'}</ul></section>
"""
    return datum_html.shell(esc(readiness["dossier_id"]), "Complétude permis", body)
