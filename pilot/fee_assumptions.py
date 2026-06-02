"""Productized SIA 102 fee assumption form and object.

Exposes mandate size, phase, hours, rate and special-prestation assumptions as an
editable object that round-trips through the cost validator. Renders explicit
assumptions and exclusions and marks them human-review-required. Never hardcodes
paid SIA coefficients — office-provided factors and assumptions are logged.
"""
from __future__ import annotations

import html
import json
import os
import tempfile

import datum_html
import validate_cost

MANDATE_SIZES = {"small", "medium", "large"}
SIA_SOURCE_REF = {
    "source_id": "SIA-102-2020",
    "title": "SIA 102:2020",
    "url": "https://shop.sia.ch/normenwerk/architekt/102_2020_f/F/Product/",
    "valid_as_of": "2026-05-31",
    "usage": "metadata only; paid tables/factors must be supplied by the office",
}


def build_fee_object(
    mandate_size: str,
    phase_code: str,
    estimated_hours: float,
    hourly_rate_chf: float,
    target_margin_percent: float,
    special_prestations: list,
    absorbed_prestations: list,
    assumptions: list,
    exclusions: list,
    project_type: str = "small_housing_transformation",
) -> dict:
    estimated_fee = round(estimated_hours * hourly_rate_chf, 2)
    return {
        "schema_version": "1.0",
        "sample_id": f"SIA102-FEE-{mandate_size}".upper(),
        "title": "SIA 102 fee assumption object",
        "mandate_size": mandate_size,
        "human_review_required": True,
        "source_refs": [dict(SIA_SOURCE_REF)],
        "method_contract": {
            "supported_methods": ["hourly_model_H_equals_T_times_h"],
            "default_method": "hourly_model_H_equals_T_times_h",
            "rule": "Aedifica must not hardcode paid SIA coefficients; it accepts office-provided factors and logs assumptions.",
        },
        "sample_mandate": {
            "project_type": project_type,
            "mandate_size": mandate_size,
            "phase_code": phase_code,
            "estimated_hours": estimated_hours,
            "hourly_rate_chf": hourly_rate_chf,
            "estimated_fee_chf": estimated_fee,
            "target_margin_percent": target_margin_percent,
            "assumptions": assumptions,
            "exclusions": exclusions,
            "special_prestations": special_prestations,
            "absorbed_prestations": absorbed_prestations,
        },
    }


def round_trip(fee_object: dict) -> list:
    """Serialize, reload and validate the fee object. Returns validation errors."""
    reloaded = json.loads(json.dumps(fee_object, ensure_ascii=False))
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "fee.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(reloaded, f, ensure_ascii=False)
        report = validate_cost.validate_fee_sample(path)
    return report.errors


def render_fee_html(fee_object: dict) -> str:
    def esc(value):
        return html.escape("" if value is None else str(value))

    cockpit = validate_cost.profitability_cockpit(fee_object)
    mandate = fee_object["sample_mandate"]
    assumptions = "".join(
        f"<li class='assumption'><span class='state'>revue requise</span> {esc(item)}</li>"
        for item in mandate.get("assumptions", [])
    )
    exclusions = "".join(f"<li>{esc(item)}</li>" for item in mandate.get("exclusions", []))
    specials = "".join(
        f"<li>{esc(item['title'])} <small>({esc(item['pricing_status'])}, {esc(item['estimated_hours'])} h)</small></li>"
        for item in mandate.get("special_prestations", [])
    )
    body = f"""
  <h1>Honoraires SIA 102 · {esc(fee_object.get('mandate_size'))} · phase {esc(mandate.get('phase_code'))}</h1>
  <p><span class="chip computed">Honoraire estimé</span> CHF {esc(cockpit['estimated_fee_chf'])} · {esc(mandate.get('estimated_hours'))} h × CHF {esc(mandate.get('hourly_rate_chf'))} · marge cible {esc(mandate.get('target_margin_percent'))}%</p>
  <p><small>{esc(fee_object['method_contract']['rule'])}</small></p>
  <section><h2>Hypothèses (revue humaine requise)</h2><ul>{assumptions}</ul></section>
  <section><h2>Exclusions</h2><ul>{exclusions or '<li>Aucune exclusion déclarée.</li>'}</ul></section>
  <section><h2>Prestations spéciales</h2><ul>{specials}</ul></section>
"""
    return datum_html.shell(esc(fee_object.get("sample_id")), "Honoraires / coûts", body)
