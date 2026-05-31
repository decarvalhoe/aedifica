"""Project workspace contract for the first Aedifica software slice.

The pilot started as standalone scripts. The workspace contract gives the next
software wave a durable project folder with a manifest, evidence, reports and
memory records while staying stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import re

import domain
import trust


HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(HERE, "projects")
WORKSPACE_VERSION = "1.0"
PROJECT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,63}$")
REQUIRED_DIRS = ("sources", "evidence", "reports", "memory")
REQUIRED_TRUST_STATES = {"sourced", "computed", "assumption", "unknown"}
ALLOWED_PHASES = {"0", "1", "2", "31", "32", "33", "41", "51", "52", "53", "61-63"}


@dataclass
class WorkspaceValidationReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, path: str, message: str) -> None:
        self.errors.append(f"{os.path.relpath(path, HERE)}: {message}")


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _source_ref(source_id: str, locator: str, valid_as_of: str, confidence: str = "high") -> dict:
    return {
        "source_id": source_id,
        "locator": locator,
        "valid_as_of": valid_as_of,
        "confidence": confidence,
    }


def project_manifest_path(project_dir: str) -> str:
    return os.path.join(project_dir, "project.json")


def report_index_path(project_dir: str) -> str:
    return os.path.join(project_dir, "reports", "report_index.json")


def iter_project_dirs(root: str = PROJECTS_DIR):
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isdir(path) and os.path.exists(project_manifest_path(path)):
            yield path


def validate_project(project_dir: str) -> WorkspaceValidationReport:
    report = WorkspaceValidationReport()
    manifest_path = project_manifest_path(project_dir)
    if not os.path.isdir(project_dir):
        report.add_error(project_dir, "project directory does not exist")
        return report
    if not os.path.exists(manifest_path):
        report.add_error(project_dir, "missing project.json")
        return report

    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        report.add_error(manifest_path, f"cannot load project.json: {exc}")
        return report

    if manifest.get("schema_version") != WORKSPACE_VERSION:
        report.add_error(manifest_path, f"schema_version must be {WORKSPACE_VERSION!r}")
    project_id = manifest.get("project_id")
    if not _nonempty_string(project_id) or not PROJECT_ID_RE.match(project_id):
        report.add_error(manifest_path, "project_id must be 3-64 chars: A-Z, 0-9, _ or -")
    if not _nonempty_string(manifest.get("name")):
        report.add_error(manifest_path, "name must be a non-empty string")
    phase_code = manifest.get("phase_code")
    if phase_code not in ALLOWED_PHASES:
        report.add_error(manifest_path, f"phase_code must be one of {sorted(ALLOWED_PHASES)}")

    jurisdiction = manifest.get("jurisdiction")
    if not isinstance(jurisdiction, dict):
        report.add_error(manifest_path, "jurisdiction must be an object")
        jurisdiction = {}
    for key in ("country", "canton", "commune"):
        if not _nonempty_string(jurisdiction.get(key)):
            report.add_error(manifest_path, f"jurisdiction.{key} must be a non-empty string")

    trust_contract = manifest.get("trust_contract")
    if not isinstance(trust_contract, dict):
        report.add_error(manifest_path, "trust_contract must be an object")
        trust_contract = {}
    if not _nonempty_string(trust_contract.get("language")):
        report.add_error(manifest_path, "trust_contract.language must be a non-empty string")
    if trust_contract.get("footer_required") is not True:
        report.add_error(manifest_path, "trust_contract.footer_required must be true")
    states = set(trust_contract.get("required_claim_states") or [])
    if not REQUIRED_TRUST_STATES.issubset(states):
        report.add_error(manifest_path, "trust_contract.required_claim_states misses required states")

    for dirname in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(project_dir, dirname)):
            report.add_error(project_dir, f"missing directory {dirname}/")

    index_path = report_index_path(project_dir)
    report_count = 0
    if os.path.exists(index_path):
        try:
            index = _load_json(index_path)
        except (OSError, json.JSONDecodeError) as exc:
            report.add_error(index_path, f"cannot load report index: {exc}")
            index = {}
        reports = index.get("reports") if isinstance(index, dict) else None
        if not isinstance(reports, list):
            report.add_error(index_path, "reports must be a list")
        else:
            report_count = len(reports)
            for item in reports:
                if not isinstance(item, dict):
                    report.add_error(index_path, "reports[] must contain objects")
                    continue
                report_id = item.get("report_id") or "<missing>"
                for key in ("report_id", "kind", "generated_at", "path", "trust_footer"):
                    if not _nonempty_string(item.get(key)):
                        report.add_error(index_path, f"{report_id}.{key} must be a non-empty string")
                if not isinstance(item.get("source_refs"), list) or not item["source_refs"]:
                    report.add_error(index_path, f"{report_id}.source_refs must be a non-empty list")

    report.items.append(
        {
            "path": os.path.relpath(project_dir, HERE),
            "project_id": project_id,
            "phase_code": phase_code,
            "jurisdiction": jurisdiction,
            "report_count": report_count,
        }
    )
    return report


def validate_all(root: str = PROJECTS_DIR) -> WorkspaceValidationReport:
    merged = WorkspaceValidationReport()
    for project_dir in iter_project_dirs(root):
        report = validate_project(project_dir)
        merged.items.extend(report.items)
        merged.errors.extend(report.errors)
    if not merged.items:
        merged.errors.append(f"{os.path.relpath(root, HERE)}: no project workspaces found")
    return merged


def create_project_workspace(root: str, manifest: dict) -> str:
    project_id = manifest["project_id"]
    project_dir = os.path.join(root, project_id.lower())
    for dirname in REQUIRED_DIRS:
        os.makedirs(os.path.join(project_dir, dirname), exist_ok=True)
    _write_json(project_manifest_path(project_dir), manifest)
    if not os.path.exists(report_index_path(project_dir)):
        _write_json(report_index_path(project_dir), {"schema_version": WORKSPACE_VERSION, "reports": []})
    return project_dir


def record_report(
    project_dir: str,
    report_id: str,
    kind: str,
    relative_path: str,
    source_refs: list,
    trust_footer: str | None = None,
    generated_at: str | None = None,
) -> dict:
    if not source_refs:
        raise ValueError("source_refs must be non-empty")
    footer = trust_footer or trust.render_footer("fr")
    entry = {
        "report_id": report_id,
        "kind": kind,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "path": relative_path.replace("\\", "/"),
        "source_refs": source_refs,
        "trust_footer": footer,
    }
    index_path = report_index_path(project_dir)
    if os.path.exists(index_path):
        index = _load_json(index_path)
    else:
        index = {"schema_version": WORKSPACE_VERSION, "reports": []}
    reports = [item for item in index.get("reports", []) if item.get("report_id") != report_id]
    reports.append(entry)
    index["schema_version"] = WORKSPACE_VERSION
    index["reports"] = reports
    _write_json(index_path, index)
    return entry


def generate_offline_parcel_brief(project_dir: str, write_report: bool = False) -> dict:
    manifest = _load_json(project_manifest_path(project_dir))
    evidence_rel = manifest.get("parcel", {}).get("oereb_parsed_evidence")
    if not evidence_rel:
        raise ValueError("project parcel.oereb_parsed_evidence is required for offline brief generation")
    evidence_path = os.path.join(project_dir, evidence_rel)
    oereb_record = _load_json(evidence_path)
    area = oereb_record.get("area_m2")
    try:
        area = float(area)
    except (TypeError, ValueError):
        area = None

    commune = manifest["jurisdiction"]["commune"]
    rpga = domain.load_commune_ruleset(commune)
    zone_name, zone_params, match_method = domain.match_communal_zone(
        rpga,
        {"zone": oereb_record.get("zone"), "parcel": oereb_record.get("parcel")},
    )
    zone_params = zone_params or {}
    source_refs = [
        _source_ref("VD-OEREB", f"EGRID {oereb_record.get('egrid')}", oereb_record.get("valid_as_of", "2026-05-29")),
    ]
    provenance = zone_params.get("provenance") or {}
    if provenance:
        source_refs.append(
            _source_ref(
                "COMMUNE-RPGA",
                provenance.get("article", "communal ruleset"),
                oereb_record.get("valid_as_of", "2026-05-29"),
                provenance.get("confidence", "medium"),
            )
        )

    brief = {
        "schema_version": WORKSPACE_VERSION,
        "brief_id": f"BRIEF-{manifest['project_id']}-PARCEL",
        "project_id": manifest["project_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_state_summary": ["sourced", "computed", "unknown"],
        "source_refs": source_refs,
        "parcel": {
            "egrid": oereb_record.get("egrid"),
            "number": oereb_record.get("parcel"),
            "commune": oereb_record.get("commune"),
            "area_m2": area,
        },
        "constraints": [
            {"claim": f"Zone d'affectation: {oereb_record.get('zone')}", "claim_state": "sourced"},
            {"claim": f"Degré de sensibilité au bruit: {oereb_record.get('noise_ds')}", "claim_state": "sourced"},
            {"claim": f"Alignements: {', '.join(oereb_record.get('alignments') or [])}", "claim_state": "sourced"},
        ],
        "communal_zone": {
            "name": zone_name,
            "match_method": match_method,
            "claim_state": "sourced" if zone_name else "unknown",
        },
        "envelope": domain.calculate_envelope(area, zone_params),
        "unknowns": [
            "Servitudes du registre foncier à vérifier manuellement.",
            "Toute valeur non exposée par API doit rester liée au règlement communal ingéré.",
        ],
        "trust_footer": trust.render_footer(manifest.get("trust_contract", {}).get("language", "fr")),
    }
    if write_report:
        report_rel = f"reports/{brief['brief_id'].lower()}.json"
        _write_json(os.path.join(project_dir, report_rel), brief)
        record_report(project_dir, brief["brief_id"], "parcel_brief", report_rel, source_refs, brief["trust_footer"])
    return brief
