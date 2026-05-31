#!/usr/bin/env python3
"""Offline smoke test for the pilot — pure logic, no network.

Run:  python pilot/selfcheck.py   (exit 0 = all pass)
Covers: OEREB parser on an inline fixture, envelope math from the ingested rulesets,
zone signal-matching, winter-shadow calc, and the selector composition.
"""
import json
import os
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import artifacts          # noqa: E402
import oereb              # noqa: E402
import claims             # noqa: E402
import domain             # noqa: E402
import parcel_intake      # noqa: E402
import selector          # noqa: E402
import opposition_radar as radar  # noqa: E402
import mvp1_demo as demo  # noqa: E402
import validate_packs    # noqa: E402
import validate_matrix   # noqa: E402
import validate_permit   # noqa: E402
import validate_compliance  # noqa: E402
import validate_research  # noqa: E402
import validate_memory  # noqa: E402
import validate_ledger  # noqa: E402
import validate_cost    # noqa: E402
import validate_workspace  # noqa: E402
import model_bridge_demo  # noqa: E402
import workspace          # noqa: E402
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
check("domain OEREB parser wrapper", domain.parse_oereb_extract(fixture)["zone"] == "Zone test 15 LAT")

print("Envelope math (ingested rulesets)")
laus = load("lausanne", "rpga_zones.json")
pully = load("pully", "rpga_zones.json")
check("Lausanne faible densité IUS = 0.5", laus["zones"]["Zone mixte de faible densité"]["ius"] == 0.5)
check("Lausanne utilité publique IUS = 2.0", laus["zones"]["Zone d'utilité publique"]["ius"] == 2.0)
check("Lausanne Centre historique has no index", laus["zones"]["Centre historique"]["ius"] is None)
check("Pully moyenne densité IOS = 0.2", pully["zones"]["Zone d'habitation à moyenne densité"]["ios"] == 0.2)
check("SBP calc 1000 m² × IUS 0.5 = 500", round(1000 * laus["zones"]["Zone mixte de faible densité"]["ius"]) == 500)
check("emprise calc 1673 m² × IOS 0.2 = 335", round(1673 * pully["zones"]["Zone d'habitation à moyenne densité"]["ios"]) == 335)
env = domain.calculate_envelope(1000, laus["zones"]["Zone mixte de faible densité"])
check("domain envelope service computes SBP", env["max_sbp_m2"] == 500)

print("Zone signal-matching (harmonized OEREB label -> communal zone)")
nm, zp, how = demo.match_zone(pully, {"zone": "Zone d'habitation de moyenne densité 15 LAT", "parcel": "x"})
check("Pully moyenne matched (not faible)", nm == "Zone d'habitation à moyenne densité")
check("match flagged keyword", how == "keyword")
nm2, _, _ = demo.match_zone(laus, {"zone": "Zone d'habitation de forte densité 15 LAT", "parcel": "x"})
check("Lausanne forte matched", nm2 == "Zone mixte de forte densité")
try:
    domain.load_commune_ruleset("Commune Inconnue", required=True)
    missing_pack_error = None
except domain.AedificaDomainError as exc:
    missing_pack_error = exc.to_dict()
check("domain errors are structured", missing_pack_error["code"] == "MISSING_PACK")

print("Shadow + selector")
s = radar.winter_shadow_len(15)
check("winter shadow ~41 m for 15 m", 38 < s < 45)
opposition = radar.score(p, None, None, None)
check("opposition signals are normalized", all({"signal_id", "source_refs", "confidence", "affected", "mitigation"}.issubset(sig) for sig in opposition["signals"]))
check("offline neighbour geometry is unknown, not asserted", any(sig["signal_id"] == "OPP-NEIGHBOURS-UNKNOWN" and sig["evidence_state"] == "unknown" for sig in opposition["signals"]))
opposition_report = radar.report(opposition)
opposition_html = radar.render_report_html(opposition_report)
check("opposition report renders checks and confidence", "Contrôles requis" in opposition_html and "confiance" in opposition_html)
communes = selector.list_communes()
check("selector discovers Lausanne + Pully", "Lausanne" in communes and "Pully" in communes)
r = selector.route("CH", "VD", "Lausanne")
check("route = 3 active layers", len(r["active"]) == 3)
check("route object carries active/inactive layers", len(r["active_layers"]) == 3 and len(r["inactive_layers"]) >= 1)
check(
    "route layers carry source versions",
    all(layer.get("source_version", {}).get("review_due") for layer in r["active_layers"] + r["inactive_layers"]),
)
stale_route = json.loads(json.dumps(r))
stale_route["active_layers"][0]["source_version"]["review_due"] = "2000-01-01"
stale_warnings = selector.pack_freshness_warnings(stale_route, today="2026-05-31")
check("expired pack review produces a warning", any(w["code"] == "pack_review_overdue" for w in stale_warnings))

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
check("complete permit fixture has zero required blockers", any(item["missing_count"] == 0 for item in permit_report.items))
check("permit report keeps conditional gates visible", any(item["conditional_count"] + item["out_of_scope_count"] > 0 for item in permit_report.items))
permit_checklist = load("permit", "vd_camac_checklist.json")
permit_complete = load("permit", "demo_complete_dossier.json")
permit_rendered = validate_permit.render_completeness_html(validate_permit.completeness_report(permit_checklist, permit_complete))
check("permit completeness report renders actor/category groups", "architect" in permit_rendered and "specialist" in permit_rendered)

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
practice_items = [item for item in research_report.items if item["kind"] == "practice_workflows"]
business_items = [item for item in research_report.items if item["kind"] == "business_positioning"]
graph_items = [item for item in research_report.items if item["kind"] == "multilingual_graph"]
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
check(
    "practice workflows cover competitions and site tools",
    any(validate_research.REQUIRED_PRACTICE_PACKS.issubset(set(item["packs"])) for item in practice_items),
)
check(
    "business positioning covers competitive categories",
    any(validate_research.REQUIRED_BUSINESS_CATEGORIES.issubset(set(item["categories"])) for item in business_items),
)
check(
    "multilingual graph covers FR/DE/IT",
    any(validate_research.REQUIRED_GRAPH_LANGUAGES.issubset(set(item["languages"])) for item in graph_items),
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
ledger_report = validate_ledger.validate_all()
check("project ledger validates", not ledger_report.errors)
check("ledger covers approvals, dry-runs and report generations", any({"approval", "adapter_dry_run", "report_generation"}.issubset(set(item["event_types"])) for item in ledger_report.items))
demo_memory = load("memory", "demo_project_memory.json")
check("carryover query returns permit blockers", len(validate_memory.answer_query(demo_memory, {"intent": "open_blockers_before_permit"})) == 2)
check("carryover query returns tender/site conditions", len(validate_memory.answer_query(demo_memory, {"intent": "conditions_for_tender_site"})) == 2)

print("Project workspace")
workspace_report = validate_workspace.validate_all()
check("project workspace validates", not workspace_report.errors)
check(
    "demo workspace is Vaud/Lausanne context-first",
    any(
        item["project_id"] == "DEMO-LAUSANNE-PALUD"
        and item["jurisdiction"].get("canton") == "VD"
        and item["jurisdiction"].get("commune") == "Lausanne"
        for item in workspace_report.items
    ),
)
parcel_ctx = parcel_intake.from_project_fixture(os.path.join(HERE, "projects", "demo_lausanne_palud"))
check("parcel intake normalizes fixture", parcel_ctx["input_type"] == "parcel_fixture" and parcel_ctx["egrid"] == "CH915772367853")
check("parcel fixture evidence is hashed", artifacts.is_sha256(parcel_ctx["evidence_refs"][0]["sha256"]))
brief = workspace.generate_offline_parcel_brief(os.path.join(HERE, "projects", "demo_lausanne_palud"))
check("offline workspace brief has source refs", bool(brief["source_refs"]))
check("offline workspace brief has evidence hashes", artifacts.is_sha256(brief["evidence_refs"][0]["sha256"]))
check("offline workspace brief has source registry", bool(brief["source_registry"]["sources"]))
check("offline workspace brief has project summary", brief["project_summary"]["project_id"] == "DEMO-LAUSANNE-PALUD")
check("offline workspace brief includes regulatory route", len(brief["regulatory_route"]["active_layers"]) == 3)
check("offline workspace brief exposes freshness warnings", isinstance(brief["freshness_warnings"], list))
check("offline workspace brief includes risks", "overall" in brief["risks"] and "grounds" in brief["risks"])
check("claim envelope validates", not any(claim.get("state") == "sourced" and not claim.get("source_refs") for claim in brief["claims"]))
html_report = workspace.render_brief_html(brief)
check("HTML brief renders trust states", "Inconnues résiduelles" in html_report and "class='claim unknown'" in html_report)
bad_brief = json.loads(json.dumps(brief))
bad_brief["claims"][0]["source_refs"] = []
try:
    workspace.render_brief_html(bad_brief)
    refused_bad_claim = False
except claims.ClaimValidationError:
    refused_bad_claim = True
check("HTML renderer refuses unsourced regulatory facts", refused_bad_claim)
check("offline workspace brief keeps unknowns visible", bool(brief["unknowns"]))
with tempfile.TemporaryDirectory() as tmp:
    tmp_project = os.path.join(tmp, "demo_lausanne_palud")
    shutil.copytree(os.path.join(HERE, "projects", "demo_lausanne_palud"), tmp_project)
    workspace.generate_offline_parcel_brief(tmp_project, write_report=True)
    tmp_report = workspace.validate_project(tmp_project)
    with open(os.path.join(tmp_project, "reports", "report_index.json"), encoding="utf-8") as f:
        report_index = json.load(f)
    with open(workspace.report_memory_path(tmp_project), encoding="utf-8") as f:
        report_memory = json.load(f)
    with open(os.path.join(tmp_project, "memory", "r1_report_memory.json"), encoding="utf-8") as f:
        claim_memory = json.load(f)
    check("offline workspace brief writes report metadata", tmp_report.items[0]["report_count"] == 2 and not tmp_report.errors)
    check("generated reports carry hashes", all(artifacts.is_sha256(item.get("content_sha256")) for item in report_index["reports"]))
    check(
        "generated report hashes enter memory records",
        all(
            artifacts.is_sha256(record.get("content_sha256"))
            and artifacts.is_sha256(record["evidence_refs"][0].get("sha256"))
            for record in report_memory["records"]
        ),
    )
    check(
        "R1 report claims survive in memory",
        {"sourced", "unknown"}.issubset({record["claim_state"] for record in claim_memory["records"]}),
    )

print("Cost and model bridge")
cost_report = validate_cost.validate_all()
fee_data = load("cost", "sia102_fee_sample.json")
cockpit = validate_cost.profitability_cockpit(fee_data)
cockpit_html = validate_cost.render_profitability_html(cockpit)
bridge_data = load("cost", "quantity_taxonomy_bridge.json")
mutating_plan = model_bridge_demo.build_bridge_plan("archicad_json", "set_room_usage_property")
bridge_health = model_bridge_demo.health_check("archicad_json")
selection = model_bridge_demo.inspect_selected_elements()
metadata_audit = model_bridge_demo.missing_metadata_audit(selection)
dry_run_blocked = model_bridge_demo.dry_run_property_update("AC-SPACE-101", "RoomUsage", "office")
ledger_data = load("memory", "demo_project_ledger.json")
dry_run_approved = model_bridge_demo.dry_run_property_update("AC-SPACE-101", "RoomUsage", "office", ledger_data)
check("cost assets validate", not cost_report.errors)
check("cost assets include fee sample, taxonomy bridge and tender log", {item["kind"] for item in cost_report.items} == {"fee_sample", "quantity_bridge", "tender_assumptions"})
check("profitability cockpit renders fee risk and assumptions", "Estimated fee" in cockpit_html and cockpit["absorbed_cost_chf"] > 0)
check("taxonomy bridge preserves multiple rows", len(bridge_data["quantity_rows"]) >= 3)
check("tender assumptions carry to offer comparison", any(item["kind"] == "tender_assumptions" and item["carry_count"] >= 2 for item in cost_report.items))
check("model bridge dry-run protects mutating actions", mutating_plan["mutating"] and mutating_plan["dry_run_required"] and mutating_plan["approval_required"])
check("model bridge health reports capabilities", "selection" in bridge_health["read_capabilities"] and "set_properties" in bridge_health["write_capabilities"])
check("model bridge inspects selected elements", selection["source_model_version"] and selection["selected_elements"][0]["element_id"])
check("model bridge audits missing metadata", metadata_audit["missing_count"] >= 1 and metadata_audit["missing"][0]["proposed_fix"])
check("model bridge blocks property update without approval", dry_run_blocked["blocked"] and dry_run_blocked["required_approval"])
check("model bridge allows dry-run once ledger approval exists", not dry_run_approved["blocked"])

print("-" * 48)
print(f"{_n - _fail}/{_n} checks passed" + ("" if not _fail else f"  ({_fail} FAILED)"))
sys.exit(1 if _fail else 0)
