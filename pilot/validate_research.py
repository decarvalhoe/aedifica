#!/usr/bin/env python3
"""Validate research backbone assets with stdlib only.

Run:
    python pilot/validate_research.py
"""
from dataclasses import dataclass, field
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = os.path.join(HERE, "research")
PHASE_MATRIX_PATH = os.path.join(RESEARCH_DIR, "swiss_phase_lifecycle_matrix.json")
SOURCE_REGISTRY_PATH = os.path.join(RESEARCH_DIR, "pilot_source_registry.json")
KNOWLEDGE_REGIME_PATH = os.path.join(RESEARCH_DIR, "project_knowledge_regime.json")
SCHEMA_VERSION = "1.0"
REQUIRED_PHASES = {"0", "1", "2", "31", "32", "33", "41", "51", "52", "53", "61-63"}
REQUIRED_SIZE_VARIANTS = {"small", "medium", "large"}
REQUIRED_SOURCE_TIERS = {"federal", "cantonal", "communal", "parcel", "sia", "office", "project"}
REQUIRED_KNOWLEDGE_REGIMES = {"context_first", "hybrid_index", "project_rag_db"}
REQUIRED_PHASE_FIELDS = {
    "phase_code",
    "phase_label",
    "purpose",
    "activities",
    "actors",
    "decisions",
    "deliverables",
    "risks",
    "source_inputs",
    "aedifica_outputs",
    "size_variants",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "tier",
    "kind",
    "title",
    "owner",
    "uri",
    "version",
    "ingestion_status",
    "valid_as_of",
    "review_due",
    "priority",
    "nomos_unit_types",
    "used_for_phases",
    "allowed_use",
    "confidence",
}


@dataclass
class ResearchReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path, message):
        self.errors.append(f"{os.path.relpath(path, HERE)}: {message}")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _nonempty_list(value):
    return isinstance(value, list) and bool(value)


def _list_of_strings(value):
    return _nonempty_list(value) and all(_nonempty_string(item) for item in value)


def _require_keys(mapping, path, report, owner, required_keys):
    if not isinstance(mapping, dict):
        report.add_error(path, f"{owner} must be an object")
        return
    for key in sorted(required_keys):
        if key not in mapping:
            report.add_error(path, f"{owner}.{key} is required")


def validate_phase_matrix(path=PHASE_MATRIX_PATH):
    report = ResearchReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    if data.get("schema_version") != SCHEMA_VERSION:
        report.add_error(path, f"schema_version must be {SCHEMA_VERSION!r}")
    for key in ("matrix_id", "title"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")
    if not isinstance(data.get("source_model"), dict):
        report.add_error(path, "source_model must be an object")
    if not isinstance(data.get("project_size_model"), dict):
        report.add_error(path, "project_size_model must be an object")

    phases = data.get("phases")
    if not isinstance(phases, list) or not phases:
        report.add_error(path, "phases must be a non-empty list")
        phases = []

    phase_codes = []
    all_have_size_variants = True
    for index, phase in enumerate(phases):
        owner = f"phases[{index}]"
        _require_keys(phase, path, report, owner, REQUIRED_PHASE_FIELDS)
        if not isinstance(phase, dict):
            continue
        code = phase.get("phase_code")
        if not _nonempty_string(code):
            report.add_error(path, f"{owner}.phase_code must be a non-empty string")
        else:
            phase_codes.append(code)
        for key in ("activities", "actors", "decisions", "deliverables", "risks", "source_inputs", "aedifica_outputs"):
            if not _list_of_strings(phase.get(key)):
                report.add_error(path, f"{owner}.{key} must be a non-empty list of strings")
        variants = phase.get("size_variants")
        if not isinstance(variants, dict):
            report.add_error(path, f"{owner}.size_variants must be an object")
            all_have_size_variants = False
        else:
            missing = REQUIRED_SIZE_VARIANTS - set(variants)
            if missing:
                report.add_error(path, f"{owner}.size_variants missing {sorted(missing)}")
                all_have_size_variants = False
            for variant_key, variant in variants.items():
                if variant_key not in REQUIRED_SIZE_VARIANTS:
                    report.add_error(path, f"{owner}.size_variants has unexpected key {variant_key!r}")
                if not isinstance(variant, dict):
                    report.add_error(path, f"{owner}.size_variants.{variant_key} must be an object")
                    all_have_size_variants = False
                    continue
                if not _nonempty_string(variant.get("focus")):
                    report.add_error(path, f"{owner}.size_variants.{variant_key}.focus must be a non-empty string")
                    all_have_size_variants = False
                for list_key in ("extra_deliverables", "risk_bias"):
                    if not _list_of_strings(variant.get(list_key)):
                        report.add_error(path, f"{owner}.size_variants.{variant_key}.{list_key} must be a non-empty list")
                        all_have_size_variants = False

    duplicates = sorted({code for code in phase_codes if phase_codes.count(code) > 1})
    for code in duplicates:
        report.add_error(path, f"duplicate phase_code {code}")
    missing_phases = REQUIRED_PHASES - set(phase_codes)
    if missing_phases:
        report.add_error(path, f"missing required phases {sorted(missing_phases)}")

    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "phase_matrix",
            "phase_codes": sorted(set(phase_codes)),
            "phase_count": len(phases),
            "all_have_size_variants": all_have_size_variants,
        }
    )
    return report


def validate_source_registry(path=SOURCE_REGISTRY_PATH):
    report = ResearchReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    if data.get("schema_version") != SCHEMA_VERSION:
        report.add_error(path, f"schema_version must be {SCHEMA_VERSION!r}")
    for key in ("registry_id", "title"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")

    declared_tiers = data.get("source_tiers")
    if set(declared_tiers or []) != REQUIRED_SOURCE_TIERS:
        report.add_error(path, f"source_tiers must be exactly {sorted(REQUIRED_SOURCE_TIERS)}")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        report.add_error(path, "sources must be a non-empty list")
        sources = []

    seen_ids = set()
    seen_tiers = set()
    for index, source in enumerate(sources):
        owner = f"sources[{index}]"
        _require_keys(source, path, report, owner, REQUIRED_SOURCE_FIELDS)
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        if source_id in seen_ids:
            report.add_error(path, f"duplicate source_id {source_id}")
        if _nonempty_string(source_id):
            seen_ids.add(source_id)
        tier = source.get("tier")
        if tier not in REQUIRED_SOURCE_TIERS:
            report.add_error(path, f"{owner}.tier must be one of {sorted(REQUIRED_SOURCE_TIERS)}")
        else:
            seen_tiers.add(tier)
        for key in ("source_id", "kind", "title", "owner", "uri", "version", "ingestion_status", "valid_as_of", "review_due", "priority", "allowed_use", "confidence"):
            if not _nonempty_string(source.get(key)):
                report.add_error(path, f"{owner}.{key} must be a non-empty string")
        for key in ("nomos_unit_types", "used_for_phases"):
            if not _list_of_strings(source.get(key)):
                report.add_error(path, f"{owner}.{key} must be a non-empty list of strings")

    missing_tiers = REQUIRED_SOURCE_TIERS - seen_tiers
    if missing_tiers:
        report.add_error(path, f"missing source tiers {sorted(missing_tiers)}")

    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "source_registry",
            "source_count": len(sources),
            "tiers": sorted(seen_tiers),
        }
    )
    return report


def _positive_numbers(mapping, path, report, owner):
    if not isinstance(mapping, dict) or not mapping:
        report.add_error(path, f"{owner} must be a non-empty object")
        return
    for key, value in mapping.items():
        if not isinstance(value, (int, float)) or value <= 0:
            report.add_error(path, f"{owner}.{key} must be a positive number")


def validate_project_knowledge_regime(path=KNOWLEDGE_REGIME_PATH):
    report = ResearchReport()
    try:
        data = _load(path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(path, f"cannot load JSON: {exc}")
        return report

    if data.get("schema_version") != SCHEMA_VERSION:
        report.add_error(path, f"schema_version must be {SCHEMA_VERSION!r}")
    if data.get("default_regime") != "context_first":
        report.add_error(path, "default_regime must be 'context_first'")
    for key in ("regime_id", "title"):
        if not _nonempty_string(data.get(key)):
            report.add_error(path, f"{key} must be a non-empty string")

    regimes = data.get("regimes")
    if not isinstance(regimes, dict):
        report.add_error(path, "regimes must be an object")
        regimes = {}
    missing_regimes = REQUIRED_KNOWLEDGE_REGIMES - set(regimes)
    if missing_regimes:
        report.add_error(path, f"missing knowledge regimes {sorted(missing_regimes)}")
    for name, regime in regimes.items():
        owner = f"regimes.{name}"
        if name not in REQUIRED_KNOWLEDGE_REGIMES:
            report.add_error(path, f"unexpected regime {name!r}")
        if not isinstance(regime, dict):
            report.add_error(path, f"{owner} must be an object")
            continue
        for key in ("description", "storage", "retrieval", "economics"):
            if not _nonempty_string(regime.get(key)):
                report.add_error(path, f"{owner}.{key} must be a non-empty string")
        if not _list_of_strings(regime.get("default_for")):
            report.add_error(path, f"{owner}.default_for must be a non-empty list of strings")
        if name == "context_first":
            _positive_numbers(regime.get("maximum_guideline"), path, report, f"{owner}.maximum_guideline")
        else:
            _positive_numbers(regime.get("minimum_triggers"), path, report, f"{owner}.minimum_triggers")

    rules = data.get("graduation_rules")
    if not isinstance(rules, list) or not rules:
        report.add_error(path, "graduation_rules must be a non-empty list")
        rules = []
    seen_rules = set()
    for index, rule in enumerate(rules):
        owner = f"graduation_rules[{index}]"
        if not isinstance(rule, dict):
            report.add_error(path, f"{owner} must be an object")
            continue
        rule_id = rule.get("rule_id")
        if rule_id in seen_rules:
            report.add_error(path, f"duplicate graduation rule {rule_id}")
        if _nonempty_string(rule_id):
            seen_rules.add(rule_id)
        target = rule.get("target_regime")
        if target not in REQUIRED_KNOWLEDGE_REGIMES and target != "all":
            report.add_error(path, f"{owner}.target_regime must be a known regime or 'all'")
        for key in ("rule_id", "condition", "rationale"):
            if not _nonempty_string(rule.get(key)):
                report.add_error(path, f"{owner}.{key} must be a non-empty string")
    for required_rule in ("DEFAULT-SMALL-CONTEXT", "TWO-RAG-TRIGGERS", "NEVER-MIX-SILENTLY"):
        if required_rule not in seen_rules:
            report.add_error(path, f"missing graduation rule {required_rule}")

    if not _list_of_strings(data.get("review_gates")):
        report.add_error(path, "review_gates must be a non-empty list of strings")
    if not _list_of_strings(data.get("open_metrics_to_collect")):
        report.add_error(path, "open_metrics_to_collect must be a non-empty list of strings")

    report.items.append(
        {
            "path": os.path.relpath(path, HERE),
            "kind": "project_knowledge_regime",
            "default_regime": data.get("default_regime"),
            "regimes": sorted(set(regimes)),
            "rule_count": len(rules),
        }
    )
    return report


def validate_all():
    merged = ResearchReport()
    for validator in (validate_phase_matrix, validate_source_registry, validate_project_knowledge_regime):
        report = validator()
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    return merged


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    report = validate_all()
    for item in report.items:
        if item["kind"] == "phase_matrix":
            print(f"PASS? {item['path']} ({item['phase_count']} phases)")
        elif item["kind"] == "source_registry":
            print(f"PASS? {item['path']} ({item['source_count']} sources; tiers: {', '.join(item['tiers'])})")
        elif item["kind"] == "project_knowledge_regime":
            print(
                f"PASS? {item['path']} "
                f"(default: {item['default_regime']}; regimes: {', '.join(item['regimes'])})"
            )
    if report.errors:
        print("\nValidation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print(f"\n{len(report.items)} research asset(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
