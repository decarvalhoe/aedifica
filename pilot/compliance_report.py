"""Phase-33 compliance gates as a workspace report.

Evaluates the energy / fire / accessibility / structure / BIM gates against the
project's known evidence inputs and renders them with a strict separation between
**legal obligations** (binding law / technical norms by reference) and
**contractual BIM conventions** (never a legal permit gate). Unknown gate inputs
produce a required next action instead of a silent pass.
"""
from __future__ import annotations

import html

import datum_html

LEGAL_BINDING_TYPES = {"binding_law", "binding_law_when_applicable", "technical_norm_by_reference"}
GATE_STATUSES = {"satisfied", "unknown", "action_required", "not_applicable"}


def evaluate_gate(gate: dict, inputs: dict) -> dict:
    keys = gate.get("required_evidence", [])
    evidence_status = {key: inputs.get(key, "unknown") for key in keys}
    values = list(evidence_status.values())
    if keys and all(value == "present" for value in values):
        status = "satisfied"
    elif any(value == "unknown" for value in values):
        status = "unknown"
    elif values and all(value == "not_applicable" for value in values):
        status = "not_applicable"
    else:
        status = "action_required"

    category = "contractual" if gate.get("binding_type") == "contractual_not_legal" else "legal"
    next_action = None
    if status == "unknown":
        unknown_keys = [key for key, value in evidence_status.items() if value == "unknown"]
        next_action = f"Clarifier l'évidence requise: {', '.join(unknown_keys)}."
    elif status == "action_required":
        missing_keys = [key for key, value in evidence_status.items() if value not in {"present", "not_applicable"}]
        next_action = f"Compléter l'évidence: {', '.join(missing_keys) or 'évidence requise'}."

    return {
        "gate_id": gate.get("gate_id"),
        "title": gate.get("title"),
        "domain": gate.get("domain"),
        "binding_type": gate.get("binding_type"),
        "category": category,
        "blocking": gate.get("blocking") is True,
        "status": status,
        "evidence_status": evidence_status,
        "next_action": next_action,
        "legal_basis": gate.get("legal_basis"),
    }


def build_compliance_report(gates_doc: dict, inputs: dict) -> dict:
    results = [evaluate_gate(gate, inputs) for gate in gates_doc.get("gates", [])]
    legal = [r for r in results if r["category"] == "legal"]
    contractual = [r for r in results if r["category"] == "contractual"]
    legal_blockers = [r for r in legal if r["blocking"] and r["status"] in {"action_required", "unknown"}]
    next_actions = [
        {"gate_id": r["gate_id"], "title": r["title"], "category": r["category"], "next_action": r["next_action"]}
        for r in results
        if r["next_action"]
    ]
    return {
        "gates_id": gates_doc.get("gates_id"),
        "phase_code": gates_doc.get("phase_code"),
        "legal": legal,
        "contractual": contractual,
        "next_actions": next_actions,
        "legal_contractual_separated": True,
        "summary": {
            "legal_gates": len(legal),
            "contractual_gates": len(contractual),
            "legal_blockers": len(legal_blockers),
            "unknown": sum(1 for r in results if r["status"] == "unknown"),
            "satisfied": sum(1 for r in results if r["status"] == "satisfied"),
        },
    }


def render_compliance_html(report: dict) -> str:
    def esc(value):
        return html.escape("" if value is None else str(value))

    def render_section(title, results, note):
        rows = "".join(
            f"<li class='claim {esc(r['status'])}'><span class='state'>{esc(r['status'])}</span>"
            f"<b>{esc(r['title'])}</b> <small>({esc(r['domain'])} · {esc(r['binding_type'])})</small>"
            + (f"<br><small>action: {esc(r['next_action'])}</small>" if r["next_action"] else "")
            + "</li>"
            for r in results
        )
        return f"<section><h2>{esc(title)}</h2><p><small>{esc(note)}</small></p><ul>{rows}</ul></section>"

    summary = report["summary"]
    body = f"""
  <h1>Gates de conformité · phase {esc(report['phase_code'])}</h1>
  <p class='chips'>
    <span class='chip sourced'>satisfied · {summary['satisfied']}</span>
    <span class='chip unknown'>unknown · {summary['unknown']}</span>
    <span class='chip assumption'>legal blockers · {summary['legal_blockers']}</span>
  </p>
  {render_section('Obligations légales', report['legal'], 'Lois liantes et normes techniques par renvoi (énergie, incendie, accessibilité, structure).')}
  {render_section('Conventions contractuelles (BIM)', report['contractual'], 'Conventions de projet — jamais une exigence légale de permis.')}
"""
    return datum_html.shell(esc(report["gates_id"]), "Gates conformité", body)
