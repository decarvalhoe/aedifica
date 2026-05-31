#!/usr/bin/env python3
"""Offline smoke test for the pilot — pure logic, no network.

Run:  python pilot/selfcheck.py   (exit 0 = all pass)
Covers: OEREB parser on an inline fixture, envelope math from the ingested rulesets,
zone signal-matching, winter-shadow calc, and the selector composition.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oereb              # noqa: E402
import selector          # noqa: E402
import opposition_radar as radar  # noqa: E402
import mvp1_demo as demo  # noqa: E402
import validate_packs    # noqa: E402
import validate_matrix   # noqa: E402
import validate_permit   # noqa: E402
import validate_compliance  # noqa: E402
import validate_research  # noqa: E402
import validate_memory  # noqa: E402
import validate_cost    # noqa: E402
import model_bridge_demo  # noqa: E402
import trust             # noqa: E402

_n = _fail = 0


def check(name, cond):
    global _n, _fail
    _n += 1
    ok = bool(cond)
    if not ok:
        _fail += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")


def load(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return json.load(f)


print("OEREB parser (inline fixture)")
fixture = {"Item": {
    "ConcernedTheme": [{"Code": "ch.Nutzungsplanung", "Text": [{"Language": 1, "Text": "Plans d'affectation"}]}],
    "NotConcernedTheme": [{"Code": "ch.BelasteteStandorte", "Text": [{"Language": 1, "Text": "Sites pollués"}]}],
    "RealEstate": {
        "Number": "99", "EGRID": "CH000000000000", "MunicipalityName": "TestVille", "LandRegistryArea": "500",
        "Type": {"Text": [{"Language": 1, "Text": "Bien-fonds"}]},
        "RestrictionOnLandownership": [
            {"Theme": {"Code": "ch.Nutzungsplanung"}, "LegendText": [{"Language": 1, "Text": "Zone test 15 LAT"}],
             "PartInPercent": 100, "LegalProvisions": [
                {"Title": "Loi test", "OfficialNumber": [{"Language": 1, "Text": "RS 700"}], "TextAtWeb": [{"Language": 1, "Text": "http://x"}]},
                {"Title": "Plan communal", "OfficialNumber": [{"Language": 1, "Text": "12345"}], "TextAtWeb": [{"Language": 1, "Text": "http://p"}]}]},
            {"Theme": {"Code": "ch.Laermempfindlichkeitsstufen"}, "LegendText": [{"Language": 1, "Text": "Degré de sensibilité II"}], "PartInPercent": 100},
        ]}}}
p = oereb.parse(fixture)
check("zone", p["zone"] == "Zone test 15 LAT")
check("noise DS", p["noise_ds"] == "Degré de sensibilité II")
check("area", p["area_m2"] == "500")
check("commune", p["commune"] == "TestVille")
check("law (RS 700) detected", any(law["number"] == "RS 700" for law in p["laws"]))
check("plan (numeric) not counted as law", all(law["number"] != "12345" for law in p["laws"]))
check("not-concerned label", "Sites pollués" in p["not_concerned"])
check("_text handles int Language & plain str", oereb._text([{"Language": 1, "Text": "x"}]) == "x" and oereb._text("y") == "y")

print("Envelope math (ingested rulesets)")
laus = load("lausanne", "rpga_zones.json")
pully = load("pully", "rpga_zones.json")
check("Lausanne faible densité IUS = 0.5", laus["zones"]["Zone mixte de faible densité"]["ius"] == 0.5)
check("Lausanne utilité publique IUS = 2.0", laus["zones"]["Zone d'utilité publique"]["ius"] == 2.0)
check("Lausanne Centre historique has no index", laus["zones"]["Centre historique"]["ius"] is None)
check("Pully moyenne densité IOS = 0.2", pully["zones"]["Zone d'habitation à moyenne densité"]["ios"] == 0.2)
check("SBP calc 1000 m² × IUS 0.5 = 500", round(1000 * laus["zones"]["Zone mixte de faible densité"]["ius"]) == 500)
check("emprise calc 1673 m² × IOS 0.2 = 335", round(1673 * pully["zones"]["Zone d'habitation à moyenne densité"]["ios"]) == 335)

print("Zone signal-matching (harmonized OEREB label -> communal zone)")
nm, zp, how = demo.match_zone(pully, {"zone": "Zone d'habitation de moyenne densité 15 LAT", "parcel": "x"})
check("Pully moyenne matched (not faible)", nm == "Zone d'habitation à moyenne densité")
check("match flagged keyword", how == "keyword")
nm2, _, _ = demo.match_zone(laus, {"zone": "Zone d'habitation de forte densité 15 LAT", "parcel": "x"})
check("Lausanne forte matched", nm2 == "Zone mixte de forte densité")

print("Shadow + selector")
s = radar.winter_shadow_len(15)
check("winter shadow ~41 m for 15 m", 38 < s < 45)
communes = selector.list_communes()
check("selector discovers Lausanne + Pully", "Lausanne" in communes and "Pully" in communes)
r = selector.route("CH", "VD", "Lausanne")
check("route = 3 active layers", len(r["active"]) == 3)

print("Jurisdiction pack contract")
report = validate_packs.validate_all()
check("all jurisdiction packs validate", not report.errors)
check("schema version declared", all(item["schema_version"] == "1.0" for item in report.items))
check("source version metadata declared", all(item["source_version"] for item in report.items))

print("Output trust contract")
footer = trust.render_footer("fr")
check("trust footer marks output non-authoritative", "jamais une autorité" in footer)
check("known provenance tags include api/RPGA/calc/unknown", {"api", "RPGA", "calc", "unknown"}.issubset(trust.PROVENANCE_TAGS))

print("Phase-aware constraint matrix")
matrix_report = validate_matrix.validate_all()
check("all constraint matrices validate", not matrix_report.errors)
check("pilot matrix includes authorization phase", any("33" in item["phase_codes"] for item in matrix_report.items))
check("pilot matrix includes downstream phases", any({"41", "52"}.issubset(set(item["phase_codes"])) for item in matrix_report.items))

print("Permit dossier completeness")
permit_report = validate_permit.validate_all()
check("permit checklist validates", not permit_report.errors)
check("demo dossier reports missing items", any(item["missing_count"] > 0 for item in permit_report.items))

print("Phase 33 compliance gates")
compliance_report = validate_compliance.validate_all()
check("compliance gates validate", not compliance_report.errors)
check("compliance gates distinguish legal from contractual", any(item["has_contractual_not_legal"] for item in compliance_report.items))

print("Research backbone")
research_report = validate_research.validate_all()
phase_items = [item for item in research_report.items if item["kind"] == "phase_matrix"]
source_items = [item for item in research_report.items if item["kind"] == "source_registry"]
knowledge_items = [item for item in research_report.items if item["kind"] == "project_knowledge_regime"]
workflow_items = [item for item in research_report.items if item["kind"] == "workflow_track_specs"]
adapter_items = [item for item in research_report.items if item["kind"] == "adapter_capability_matrix"]
check("research assets validate", not research_report.errors)
check(
    "phase lifecycle covers required phases",
    any(validate_research.REQUIRED_PHASES.issubset(set(item["phase_codes"])) for item in phase_items),
)
check(
    "source registry covers required tiers",
    any(validate_research.REQUIRED_SOURCE_TIERS.issubset(set(item["tiers"])) for item in source_items),
)
check(
    "project knowledge defaults to context-first",
    any(item["default_regime"] == "context_first" for item in knowledge_items),
)
check(
    "project knowledge defines escalation regimes",
    any(validate_research.REQUIRED_KNOWLEDGE_REGIMES.issubset(set(item["regimes"])) for item in knowledge_items),
)
check(
    "workflow track specs cover remaining tracks",
    any(validate_research.REQUIRED_WORKFLOW_TRACKS.issubset(set(item["tracks"])) for item in workflow_items),
)
check(
    "adapter matrix covers target adapters",
    any(validate_research.REQUIRED_ADAPTERS.issubset(set(item["adapters"])) for item in adapter_items),
)

print("Project memory")
memory_report = validate_memory.validate_all()
check("project memory validates", not memory_report.errors)
check(
    "project memory answers demo queries",
    all(item["answered_queries"] == item["query_count"] for item in memory_report.items),
)
check(
    "project memory spans permit-to-site phases",
    any({"0", "31", "33", "41", "52"}.issubset(set(item["phase_codes"])) for item in memory_report.items),
)

print("Cost and model bridge")
cost_report = validate_cost.validate_all()
mutating_plan = model_bridge_demo.build_bridge_plan("archicad_json", "set_room_usage_property")
check("cost assets validate", not cost_report.errors)
check("cost assets include fee sample and taxonomy bridge", {item["kind"] for item in cost_report.items} == {"fee_sample", "quantity_bridge"})
check("model bridge dry-run protects mutating actions", mutating_plan["mutating"] and mutating_plan["dry_run_required"] and mutating_plan["approval_required"])

print("-" * 48)
print(f"{_n - _fail}/{_n} checks passed" + ("" if not _fail else f"  ({_fail} FAILED)"))
sys.exit(1 if _fail else 0)
