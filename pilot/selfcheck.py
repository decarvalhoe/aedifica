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
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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
import ledger  # noqa: E402
import ledger_writer  # noqa: E402
import approval  # noqa: E402
import validate_cost    # noqa: E402
import validate_site    # noqa: E402
import validate_workspace  # noqa: E402
import validate_manifest  # noqa: E402
import validate_evidence_store  # noqa: E402
import validate_brief  # noqa: E402
import validate_redaction  # noqa: E402
import validate_freshness  # noqa: E402
import validate_commune_packs  # noqa: E402
import seed_commune  # noqa: E402
import permit_state  # noqa: E402
import validate_dossier_evidence  # noqa: E402
import permit_mapping  # noqa: E402
import permit_readiness  # noqa: E402
import validate_compliance_report  # noqa: E402
import compliance_report as compliance_report_mod  # noqa: E402
import redaction  # noqa: E402
import evidence_store  # noqa: E402
import project_cli  # noqa: E402
import route_service  # noqa: E402
import r1b_demo  # noqa: E402
import workspace_api  # noqa: E402
import workspace_ui  # noqa: E402
import urllib.request  # noqa: E402
import model_bridge_demo  # noqa: E402
import adapter_snapshots   # noqa: E402
import workspace          # noqa: E402
import trust             # noqa: E402

sys.path.insert(0, os.path.dirname(HERE))
import aedifica           # noqa: E402

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
opposition_evidence = radar.evidence_model(opposition)
check(
    "opposition evidence model supports heritage/noise/neighbor/shadow/visibility",
    {"heritage", "noise", "neighbor", "shadow", "visibility"}.issubset(set(opposition_evidence["supported_categories"])),
)
check("opposition report does not claim prediction", opposition_report["claims_prediction"] is False and bool(opposition_report["disclaimer"]))
check("opposition signals carry evidence category and missing evidence fields", all("evidence_category" in sig and "missing_evidence" in sig for sig in opposition["signals"]))
check(
    "opposition missing evidence stays visible as unknown/assumption",
    all(sig["evidence_state"] in {"unknown", "assumption"} for sig in opposition["signals"] if sig.get("missing_evidence")),
)
_opp_full = radar.score(
    {"commune": "Lausanne", "zone": "Centre historique 15 LAT", "parcel": "10072", "egrid": "CH915772367853", "noise_ds": "Degré de sensibilité II", "alignments": ["Limite des constructions"], "valid_as_of": "2026-05-29", "area_m2": 1000, "concerned_themes": ["site construit protégé"]},
    None, None, 1000, project_height_m=20,
)
check(
    "opposition model can categorize heritage/noise/neighbor/shadow/visibility together",
    {"heritage", "noise", "neighbor", "shadow", "visibility"}.issubset(set(radar.evidence_model(_opp_full)["categories"])),
)
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
check("trust footer marks output non-authoritative", "Pas une autorité" in footer)
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

print("Dossier evidence manifest")
dossier_evidence_report = validate_dossier_evidence.validate_all()
check("dossier evidence manifest validates", not dossier_evidence_report.errors)
check(
    "dossier evidence spans document/form/specialist/assumption categories",
    {"document_ref", "form", "specialist_note", "assumption"}.issubset(set(dossier_evidence_report.items[0]["categories"])),
)

print("Permit dossier state machine")
_permit_checklist = load("permit", "vd_camac_checklist.json")
_complete_dossier = load("permit", "demo_complete_dossier.json")
_missing_dossier = load("permit", "demo_missing_dossier.json")
_cr_complete = validate_permit.completeness_report(_permit_checklist, _complete_dossier)
_cr_missing = validate_permit.completeness_report(_permit_checklist, _missing_dossier)
check("permit state derives ready_for_review for a complete dossier", permit_state.derive_state(_cr_complete) == "ready_for_review")
check("permit state derives missing_evidence for a missing dossier", permit_state.derive_state(_cr_missing) == "missing_evidence")
check("permit state rejects an invalid transition", not permit_state.is_valid_transition("draft", "submitted_external"))
try:
    permit_state.transition("draft", "submitted_external")
    _permit_bad_transition = False
except permit_state.PermitStateError:
    _permit_bad_transition = True
check("permit state machine raises on invalid transition", _permit_bad_transition)
check("permit state is never an authority decision", permit_state.state_summary("ready_for_review")["is_authority_decision"] is False)

print("ACTIS-CAMAC mapping + permit readiness")
_map_complete = permit_mapping.map_actis_camac(_permit_checklist, _complete_dossier)
_sum_complete = permit_mapping.summarize(_map_complete)
_map_missing = permit_mapping.map_actis_camac(_permit_checklist, _missing_dossier)
_sum_missing = permit_mapping.summarize(_map_missing)
check("ACTIS-CAMAC mapping reports no false blockers for a complete dossier", _sum_complete["required_blockers"] == 0)
check("ACTIS-CAMAC mapping reports known missing items for a missing dossier", len(_sum_missing["missing"]) > 0)
check("mapping statuses stay within present/missing/assumption/not_applicable", all(r["status"] in permit_mapping.RESULT_STATUSES for r in _map_complete + _map_missing))
check("every checklist requirement keeps source/checklist provenance", all(r["checklist_provenance"] for r in _map_complete))
_syn_ck = {"items": [{"item_id": "X", "title": "X", "category": "project", "missing_message": "do X", "required": True, "accepted_evidence": ["k"], "source_ids": ["S"]}]}
_syn_do = {"evidence_records": [{"evidence_id": "E", "key": "k", "kind": "form", "title": "t", "status": "pending", "source_refs": [{"source_id": "S"}]}]}
check("matched-but-pending evidence maps to assumption", permit_mapping.map_actis_camac(_syn_ck, _syn_do)[0]["status"] == "assumption")
_ready_complete = permit_readiness.build_readiness(_permit_checklist, _complete_dossier)
_ready_missing = permit_readiness.build_readiness(_permit_checklist, _missing_dossier)
check("permit readiness is ready for a complete dossier", _ready_complete["ready_for_review"] is True)
check("permit readiness is never ready with required blockers", _ready_missing["ready_for_review"] is False)
check("permit readiness is never an authority decision", _ready_complete["is_authority_decision"] is False)
_ready_html = permit_readiness.render_readiness_html(_ready_missing)
check("permit readiness report groups blockers and shows disclaimers", "Disclaimers" in _ready_html and "NON prêt" in _ready_html)

print("Phase 33 compliance gates")
compliance_report = validate_compliance.validate_all()
check("compliance gates validate", not compliance_report.errors)
check("compliance gates distinguish legal from contractual", any(item["has_contractual_not_legal"] for item in compliance_report.items))

print("Phase 33 compliance workspace report")
compliance_report_validation = validate_compliance_report.validate_all()
check("phase-33 compliance workspace report validates", not compliance_report_validation.errors)
_gates_doc = load("compliance", "ch_phase33_gates.json")
_complete_inputs = load("compliance", "demo_complete_inputs.json")["inputs"]
_missing_inputs = load("compliance", "demo_missing_inputs.json")["inputs"]
_complete_compliance = compliance_report_mod.build_compliance_report(_gates_doc, _complete_inputs)
_missing_compliance = compliance_report_mod.build_compliance_report(_gates_doc, _missing_inputs)
check("compliance report separates legal from contractual BIM gates", _complete_compliance["legal_contractual_separated"] and any(g["domain"] == "bim" for g in _complete_compliance["contractual"]))
check("complete compliance inputs produce no legal blockers", _complete_compliance["summary"]["legal_blockers"] == 0)
check("unknown compliance inputs produce legal blockers and next actions", _missing_compliance["summary"]["legal_blockers"] > 0 and _missing_compliance["next_actions"])
check("compliance report renders legal and contractual sections", "Obligations légales" in compliance_report_mod.render_compliance_html(_missing_compliance) and "Conventions contractuelles" in compliance_report_mod.render_compliance_html(_missing_compliance))

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
_open_decisions = {r["memory_id"] for r in validate_memory.answer_query(demo_memory, {"intent": "open_decisions"})}
check("memory returns known open decisions", "MEM-DEC-31-OPEN" in _open_decisions)
check("resolved decisions disappear from the open-decisions query", "MEM-DEC-31-001" not in _open_decisions)
check("memory returns unknown claims needing review", {r["memory_id"] for r in validate_memory.answer_query(demo_memory, {"intent": "unknown_claims"})} == {"MEM-UNK-32-ENVELOPE"})
_open_questions = validate_memory.open_questions(demo_memory)
check(
    "open-questions view is UI-stable with provenance refs",
    bool(_open_questions["open_decisions"]) and all(item["source_refs"] and item["evidence_refs"] for item in _open_questions["open_decisions"]),
)

print("Durable ledger writer + approval scopes")
with tempfile.TemporaryDirectory() as tmp:
    _pd = os.path.join(tmp, "proj")
    os.makedirs(_pd)
    _actor = {"name": "Architecte", "role": "architect"}
    _rep = {"report_id": "BRIEF-LED", "kind": "parcel_brief", "path": "reports/b.json", "source_refs": [{"source_id": "VD-OEREB", "locator": "x", "valid_as_of": "2026-05-29", "confidence": "high"}], "content_sha256": "a" * 64}
    ledger_writer.write_ledger_entry(_pd, ledger_writer.report_generation_entry("P", "33", _rep, _actor, "LED-A"))
    ledger_writer.write_ledger_entry(_pd, ledger_writer.report_generation_entry("P", "33", _rep, _actor, "LED-B"))
    _led = ledger_writer.read_ledger(_pd)
    check("durable ledger writer appends, not overwrites", len(_led["entries"]) == 2)
    try:
        ledger.validate_ledger(_led)
        _led_valid = True
    except ledger.LedgerValidationError:
        _led_valid = False
    check("written ledger validates offline", _led_valid)
    check("report generation entry links back to the report", _led["entries"][0]["inputs"]["report_id"] == "BRIEF-LED")
_rep_appr = approval.make_approval("Arch", "report_review", "reviewed")
_dry_appr = approval.make_approval("Arch", "adapter_dry_run", "ok")
_exec_appr = approval.make_approval("Arch", "adapter_execution", "ok")
check("report approval cannot authorize an adapter mutation", not approval.authorizes(_rep_appr, "adapter_execution"))
check("adapter dry-run approval cannot authorize execution", not approval.authorizes(_dry_appr, "adapter_execution"))
check("adapter execution approval also covers dry-run", approval.authorizes(_exec_appr, "adapter_dry_run"))
_scope_ok, _scope_msg = approval.check_scope(_dry_appr, "adapter_execution")
check("failed scope check renders a clear message", (not _scope_ok) and "does NOT authorize" in _scope_msg)

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
check(
    "R1B report separates the five trust states",
    "Synthèse par état de confiance" in html_report
    and all(f"chip {state}" in html_report for state in ("sourced", "computed", "assumption", "unknown", "conflict")),
)
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
        "R1B report claims survive in memory",
        {"sourced", "unknown"}.issubset({record["claim_state"] for record in claim_memory["records"]}),
    )
    first_report = report_index["reports"][0]
    first_hash = first_report["content_sha256"]
    with open(os.path.join(tmp_project, first_report["path"]), "a", encoding="utf-8") as f:
        f.write("<!-- mutated for hash test -->")
    mutated_entry = workspace.record_report(
        tmp_project,
        first_report["report_id"],
        first_report["kind"],
        first_report["path"],
        first_report["source_refs"],
    )
    with open(os.path.join(tmp_project, "reports", "report_index.json"), encoding="utf-8") as f:
        index_after = json.load(f)
    check("report hash changes when report content changes", mutated_entry["content_sha256"] != first_hash)
    check("re-recording a report does not duplicate its index entry", len(index_after["reports"]) == len(report_index["reports"]))

print("Project manifest schema (v1)")
manifest_report = validate_manifest.validate_all()
check("manifest schema and fixtures validate", not manifest_report.errors)
manifest_schema = validate_manifest.load_schema()
check("manifest schema pins version 1.0", manifest_schema["properties"]["schema_version"]["const"] == "1.0")
demo_manifest = load("projects", "demo_lausanne_palud", "project.json")
check("real demo manifest satisfies the schema", not validate_manifest.validate_manifest(demo_manifest, manifest_schema))
check(
    "manifest schema rejects a manifest missing project_id",
    any("project_id" in err for err in validate_manifest.validate_manifest({"schema_version": "1.0"}, manifest_schema)),
)

print("Privacy redaction pass")
redaction_report = validate_redaction.validate_all()
check("privacy redaction pass validates", not redaction_report.errors)
_sensitive = {"client_name": "Famille Test", "notes": "mail test@example.ch tel +41 79 123 45 67"}
_redacted = redaction.redact_artifact(_sensitive)
check("redaction removes sensitive fields and patterns", not redaction.find_sensitive(_redacted))
check("redaction does not mutate the original artifact", redaction.find_sensitive(_sensitive))

print("Datum workspace surfaces")
_demo_project = os.path.join(HERE, "projects", "demo_lausanne_palud")
shell_html = workspace_ui.render_workspace_shell(_demo_project)
check("workspace shell loads the fixture project", "DEMO-LAUSANNE-PALUD" in shell_html and "Prochaines vérifications" in shell_html)
check("workspace shell leads with the working surface, no marketing page", "datum-surface" in shell_html and "slide__body" in shell_html)
intake_html = workspace_ui.render_parcel_intake(_demo_project)
check("parcel intake renders address/EGRID/parcel state", "EGRID" in intake_html and "CH915772367853" in intake_html and 'name="address"' in intake_html)
synthetic_brief = {
    "claims": [
        claims.make_claim("UI-S", "Sourced thing", "sourced", "Zone X", source_refs=[{"source_id": "VD-OEREB"}]),
        claims.make_claim("UI-C", "Computed thing", "computed", 42, formula="a*b", source_refs=[{"source_id": "VD-OEREB"}]),
        claims.make_claim("UI-A", "Assumed thing", "assumption", "peut-être", required_human_check="Confirmer aupres de architecte responsable"),
        claims.unknown_claim("UI-U", "Unknown thing", "Verifier le reglement communal"),
    ]
}
claim_html = workspace_ui.render_claim_review(synthetic_brief)
check(
    "claim review renders sourced/computed/assumption/unknown states",
    all(f"{state} · 1" in claim_html for state in ("sourced", "computed", "assumption", "unknown")),
)
check("claim review shows the next action for unknown claims", "Verifier le reglement communal" in claim_html)
check("claim review shows an explicit human-review status for assumptions", "Confirmer aupres de architecte responsable" in claim_html)
with tempfile.TemporaryDirectory() as tmp:
    written = workspace_ui.write_surfaces(tmp)
    check("workspace surfaces writer emits the three screens", set(written) == {"app_shell.html", "project_intake.html", "claim_review.html"})

print("Local workspace HTTP API")
with tempfile.TemporaryDirectory() as tmp:
    status_health, _ = workspace_api.route_request("GET", "/api/health", None, tmp)
    check("API health endpoint returns ok", status_health == 200)
    status_create, created_payload = workspace_api.route_request(
        "POST", "/api/projects", {"project_id": "API-SELFCHECK-1", "name": "API selfcheck"}, tmp
    )
    check("API creates a project with structured payload", status_create == 201 and "created" in created_payload)
    status_missing, missing_payload = workspace_api.route_request("POST", "/api/projects", {}, tmp)
    check("API returns structured 400 for missing fields", status_missing == 400 and missing_payload["error"]["code"] == "MISSING_FIELDS")
    status_404, _ = workspace_api.route_request("GET", "/api/projects/NOPE", None, tmp)
    check("API returns 404 for unknown project", status_404 == 404)
    # brief endpoint against a copy of the offline fixture
    shutil.copytree(os.path.join(HERE, "projects", "demo_lausanne_palud"), os.path.join(tmp, "demo_lausanne_palud"))
    status_brief, brief_payload = workspace_api.route_request("POST", "/api/projects/DEMO-LAUSANNE-PALUD/brief", {}, tmp)
    check("API generates a brief from an offline fixture", status_brief == 200 and brief_payload["unknowns_count"] > 0)
    # live socket smoke
    api_server = workspace_api.serve("127.0.0.1", 0, tmp)
    api_thread = threading.Thread(target=api_server.serve_forever, daemon=True)
    api_thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{api_server.server_port}/api/health", timeout=5) as resp:
            live_health = json.loads(resp.read().decode("utf-8"))
    finally:
        api_server.shutdown()
        api_server.server_close()
    check("API answers a live HTTP health request", live_health.get("status") == "ok")

print("R1B end-to-end demo")
with tempfile.TemporaryDirectory() as tmp:
    r1b_summary = r1b_demo.build_r1b_demo(tmp)
    check("R1B demo runs offline in fixture mode", r1b_summary["fixture_mode"] is True)
    check("R1B demo names project, route and reports", r1b_summary["project_id"] == "DEMO-LAUSANNE-PALUD" and r1b_summary["report_count"] == 2)
    check("R1B demo reports unknowns and evidence counts", r1b_summary["unknowns_count"] > 0 and r1b_summary["evidence_count"] >= 1)
    r1b_text = r1b_demo.render_summary(r1b_summary)
    check("R1B demo summary marks offline fixture mode", "OFFLINE FIXTURE MODE" in r1b_text)

print("Next-commune seed workflow")
seed_pack = seed_commune.build_seed_pack("Vevey", "VD")
check("seed commune is created without fabricated legal values", seed_pack["status"] == "seed" and seed_pack["zones"] == {})
check("seed commune carries no numeric indices", all(z == {} for z in seed_pack["zones"].values()))
seed_checklist = seed_commune.build_ingestion_checklist("Vevey", "VD")
check("seed checklist names source authority and missing items", "Commune de Vevey" in seed_checklist and "Required inputs" in seed_checklist)
check("seeded commune stays unsupported (no zero values)", route_service.commune_support_state("Vevey")["state"] == "unsupported")
with tempfile.TemporaryDirectory() as tmp:
    seeded = seed_commune.seed_commune("Vevey", "VD", tmp)
    seeded_files = set(os.listdir(os.path.dirname(seeded["pack_path"])))
    check("seed writes a .seed scaffold but no active rpga_zones.json", "rpga_zones.seed.json" in seeded_files and "rpga_zones.json" not in seeded_files)

print("Commune pack regressions")
commune_pack_report = validate_commune_packs.validate_all()
check("commune pack regressions validate (Lausanne + Pully)", not commune_pack_report.errors)
check("commune pack regression covers both communes", {item["commune"] for item in commune_pack_report.items} == {"Lausanne", "Pully"})
_broken_zone = {"ius": 0.9}
_broken_report = validate_commune_packs.CommunePackReport()
validate_commune_packs._check_zone("Lausanne", "Zone mixte de faible densité", _broken_zone, {"ius": 0.5}, _broken_report)
check("commune regression names the affected commune and zone on change", any("Lausanne/Zone mixte de faible densité" in e for e in _broken_report.errors))

print("Pack freshness gate")
freshness_report = validate_freshness.validate_all()
check("pack freshness gate validates", not freshness_report.errors)
_fresh_route = selector.regulatory_route("CH", "VD", "Lausanne")
_expired = json.loads(json.dumps(_fresh_route))
_expired["active_layers"][0]["source_version"]["review_due"] = "2000-01-01"
check(
    "freshness gate flags expired packs and stale sources",
    any(w["code"] == "pack_review_overdue" for w in selector.report_freshness_warnings(_expired, [{"source_id": "S", "valid_as_of": "2000-01-01"}], today="2026-05-31")),
)

print("Regulatory route service")
laus_route = route_service.select_route("CH", "VD", "Lausanne")
pully_route = route_service.select_route("CH", "VD", "Pully")
check("route service resolves Lausanne with 3 active layers", laus_route["supported"] and len(laus_route["active_layers"]) == 3)
check("route service resolves Pully with 3 active layers", pully_route["supported"] and len(pully_route["active_layers"]) == 3)
check("route service exposes pack versions and warnings", isinstance(laus_route["pack_versions"], list) and isinstance(laus_route["freshness_warnings"], list))
unsupported_route = route_service.select_route("CH", "GE", "Genève")
check(
    "unsupported commune returns a structured unsupported state",
    unsupported_route["support_state"] == "unsupported" and unsupported_route["unsupported"]["state"] == "unsupported",
)
check("route service still exposes the federal layer for unsupported commune", len(unsupported_route["active_layers"]) >= 1)
check("selector CLI route() still composes active layers", len(selector.route("CH", "VD", "Lausanne")["active"]) == 3)

print("Project-scoped constraint brief")
brief_report = validate_brief.validate_all()
check("project-scoped constraint brief validates against schema", not brief_report.errors)
check(
    "brief object bundles constraints, envelope, risks and unknowns",
    brief_report.items and brief_report.items[0]["serialized_bytes"] > 0,
)

print("Source and evidence store")
evidence_store_report = validate_evidence_store.validate_all()
check("evidence store writer validates", not evidence_store_report.errors)
demo_project_dir = os.path.join(HERE, "projects", "demo_lausanne_palud")
demo_brief = workspace.generate_offline_parcel_brief(demo_project_dir)
check(
    "brief source_refs resolve to the project source store",
    not evidence_store.unresolved_source_refs(demo_project_dir, demo_brief["source_refs"]),
)
check(
    "report locators never leak a local path",
    not any(evidence_store.looks_like_local_path(ref.get("locator")) for ref in demo_brief["source_refs"]),
)

print("Create/open project CLI")
with tempfile.TemporaryDirectory() as tmp:
    created = project_cli.create_project(
        root=tmp,
        project_id="SELFCHECK-CLI-001",
        name="Selfcheck CLI project",
        commune="Lausanne",
        phase_code="31",
    )
    check("create writes a valid workspace", not workspace.validate_project(created["project_dir"]).errors)
    opened = project_cli.open_project(created["project_dir"])
    check("open reports project id, route and phase", opened["project_id"] == "SELFCHECK-CLI-001" and opened["phase_code"] == "31")
    check("open lists the three active route layers", len(opened["active_layers"]) == 3)
    summary_text = project_cli.render_open_summary(opened)
    check("open summary renders route and artifacts", "Route" in summary_text and "Artifacts" in summary_text)
    try:
        project_cli.open_project(os.path.join(tmp, "missing-project"))
        cli_structured_error = False
    except project_cli.ProjectCLIError as exc:
        cli_structured_error = exc.to_dict()["code"] == "PROJECT_NOT_FOUND"
    check("open fails with a structured error for a bad folder", cli_structured_error)

print("Aedifica product package")
check("aedifica package declares a version", isinstance(aedifica.__version__, str) and aedifica.__version__)
check("aedifica re-exports domain service", aedifica.domain.calculate_envelope is domain.calculate_envelope)
pkg_env = aedifica.domain.calculate_envelope(1000, {"ius": 0.5})
check("aedifica domain service computes through package namespace", pkg_env["max_sbp_m2"] == 500)
check("aedifica re-exports claim envelope", aedifica.claims.make_claim is claims.make_claim)
check("aedifica re-exports route service", aedifica.route.regulatory_route is selector.regulatory_route)
check(
    "aedifica re-exports workspace brief generator",
    aedifica.workspace.generate_offline_parcel_brief is workspace.generate_offline_parcel_brief,
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
design_intent = model_bridge_demo.load_design_intent()
intent_dry_run = model_bridge_demo.dry_run_design_intent(design_intent, selection, ledger_data)
intent_diff = model_bridge_demo.render_before_after_diff(intent_dry_run)
unsupported_intent = json.loads(json.dumps(design_intent))
unsupported_intent["items"].append({"item_id": "ITEM-UNSUPPORTED-001", "kind": "teleport_wall", "basis": {"confidence": "low"}})
unsupported_dry_run = model_bridge_demo.dry_run_design_intent(unsupported_intent, selection, ledger_data)
agent_demo = model_bridge_demo.build_agent_demo(os.path.join(HERE, "memory", "demo_project_ledger.json"))


class DemoArchicadHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        if payload.get("command") == "GetProductInfo":
            response = {"result": {"productInfo": {"name": "Archicad", "version": "DEMO", "buildNumber": "1"}}}
        else:
            response = {
                "result": {
                    "source_model_version": "ARCHICAD-LIVE-DEMO",
                    "source_model_ref": "http://localhost/demo",
                    "selected_elements": selection["selected_elements"],
                }
            }
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


server = HTTPServer(("127.0.0.1", 0), DemoArchicadHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
endpoint = f"http://127.0.0.1:{server.server_port}"
try:
    live_product = model_bridge_demo.live_product_info(endpoint)
    live_selection = model_bridge_demo.live_selected_elements(endpoint)
finally:
    server.shutdown()
    server.server_close()

ifc_snapshot = adapter_snapshots.inspect_ifc_snapshot()
speckle_snapshot = adapter_snapshots.inspect_speckle_snapshot()
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
check("model bridge loads structured design intent", design_intent["intent_id"].startswith("INTENT-") and len(design_intent["items"]) == 3)
check("model bridge dry-runs generated intent items", intent_dry_run["action_count"] == 3 and intent_dry_run["unsupported_count"] == 0)
check("model bridge renders before/after diff", "Before/After" in intent_diff and "AC-SPACE-101.RoomUsage" in intent_diff)
check("model bridge refuses unsupported intent actions", unsupported_dry_run["unsupported_count"] == 1)
check("agent demo preserves fixture safety", agent_demo["fixture_mode"] and agent_demo["dry_run"]["dry_run"])
check("model bridge probes live product info endpoint", live_product["running"] and live_product["product_info"]["name"] == "Archicad")
check("model bridge normalizes live selected elements", live_selection["source_model_version"] == "ARCHICAD-LIVE-DEMO" and len(live_selection["selected_elements"]) == 2)
check("IFC snapshot baseline exposes spaces and property sets", ifc_snapshot["adapter_id"] == "ifc_ifcopenshell" and ifc_snapshot["spaces"] and ifc_snapshot["property_sets"])
check("Speckle snapshot baseline exposes spaces and property sets", speckle_snapshot["adapter_id"] == "speckle" and speckle_snapshot["spaces"] and speckle_snapshot["property_sets"])

print("Site and handover")
site_report = validate_site.validate_all()
site_note = load("site", "site_note_fixture.json")
defects = load("site", "defect_register_fixture.json")
handover = load("site", "handover_checklist.json")
pv = validate_site.generate_pv_and_task_register(site_note)
handover_html = validate_site.render_handover_html(handover, defects)
check("site assets validate", not site_report.errors)
check("site note generates PV and task register", pv["tasks"] and pv["source_note_id"] == site_note["note_id"])
check("defect register fixture has open defects", any(d["status"] in {"open", "pending_review"} for d in defects["defects"]))
check("handover checklist renders blocked defects", "Handover checklist" in handover_html and "blocked" in handover_html)

print("UI, demo and release hygiene")
check("app shell screens exist", all(os.path.exists(os.path.join(HERE, "ui", name)) for name in ("app_shell.html", "project_intake.html", "claim_review.html", "adapter_approval.html")))
demo_pack = load("demo", "fixture_pack_manifest.json")
check("demo fixture pack lists commands and fixtures", bool(demo_pack["fixtures"]) and "python pilot/demo_run.py" in demo_pack["demo_commands"])
check("dedicated agent software demo CLI exists", os.path.exists(os.path.join(HERE, "agent_software_demo.py")))
check("contract test directory exists", os.path.exists(os.path.join(os.path.dirname(HERE), "tests", "contracts", "run_contracts.py")))
check("offline/network test split is documented", os.path.exists(os.path.join(os.path.dirname(HERE), "tests", "offline", "README.md")) and os.path.exists(os.path.join(os.path.dirname(HERE), "tests", "network", "README.md")))
check("privacy and release checklists exist", os.path.exists(os.path.join(os.path.dirname(HERE), "docs", "security", "project-data-privacy-checklist.md")) and os.path.exists(os.path.join(os.path.dirname(HERE), "docs", "release", "release-checklist.md")))

print("-" * 48)
print(f"{_n - _fail}/{_n} checks passed" + ("" if not _fail else f"  ({_fail} FAILED)"))
sys.exit(1 if _fail else 0)
