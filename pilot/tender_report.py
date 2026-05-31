"""Render a tender assumptions report from the project workspace.

Surfaces tender assumptions, quantity source refs and exclusions for architect
review, plus the permit conditions carried from project memory. It invents no
vendor pricing — it is a review surface, not automated procurement.
"""
from __future__ import annotations

import html

import datum_html
import quantity_register
import validate_memory

PRICE_KEYS = {"price", "amount", "unit_price", "total_chf", "price_chf"}


def build_tender_report(tender_log: dict, register: dict, memory: dict | None = None) -> dict:
    entries = []
    for entry in tender_log.get("entries", []):
        item = dict(entry)
        ref = item.get("quantity_source_ref")
        item["quantity_resolved"] = quantity_register.link_resolves(register, ref) if ref else None
        entries.append(item)
    assumptions = [e for e in entries if e.get("kind") in {"assumption", "allowance", "quantity_basis"}]
    exclusions = [e for e in entries if e.get("kind") == "exclusion"]
    carried = (
        validate_memory.answer_query(memory, {"intent": "conditions_for_tender_site"}) if memory else []
    )
    return {
        "log_id": tender_log.get("log_id"),
        "project_id": tender_log.get("project_id"),
        "entries": entries,
        "assumptions": assumptions,
        "exclusions": exclusions,
        "carried_conditions": [
            {"memory_id": r.get("memory_id"), "title": r.get("title"), "phase_code": r.get("phase_code")}
            for r in carried
        ],
        "no_vendor_pricing": not has_vendor_pricing({"entries": entries}),
    }


def has_vendor_pricing(report: dict) -> bool:
    for entry in report.get("entries", []):
        if any(key in entry for key in PRICE_KEYS):
            return True
    return False


def render_tender_html(report: dict) -> str:
    def esc(value):
        return html.escape("" if value is None else str(value))

    def entry_rows(entries):
        return "".join(
            f"<li><b>{esc(e.get('title'))}</b> <small>({esc(e.get('kind'))} · col. {esc(e.get('offer_comparison_column'))}"
            + (f" · quantités {esc(e['quantity_source_ref'].get('source_id'))}@{esc(e['quantity_source_ref'].get('version'))}" if e.get("quantity_source_ref") else "")
            + ")</small></li>"
            for e in entries
        )

    carried = "".join(
        f"<li>{esc(c['memory_id'])} · phase {esc(c['phase_code'])} — {esc(c['title'])}</li>"
        for c in report["carried_conditions"]
    )
    body = f"""
  <h1>Hypothèses de soumission · {esc(report['log_id'])}</h1>
  <p><small>Surface de revue pour l'architecte. Aucun prix fournisseur n'est inventé.</small></p>
  <section><h2>Hypothèses et quantités</h2><ul>{entry_rows(report['assumptions'])}</ul></section>
  <section><h2>Exclusions</h2><ul>{entry_rows(report['exclusions']) or '<li>Aucune exclusion.</li>'}</ul></section>
  <section><h2>Conditions reportées (mémoire projet)</h2><ul>{carried or '<li>Aucune condition reportée.</li>'}</ul></section>
"""
    return datum_html.shell(esc(report["log_id"]), "Soumission", body)
