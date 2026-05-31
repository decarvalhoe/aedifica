"""Project workspace contract for the first Aedifica software slice.

The pilot started as standalone scripts. The workspace contract gives the next
software wave a durable project folder with a manifest, evidence, reports and
memory records while staying stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import html
import json
import os
import re

import artifacts
import claims
import domain
import opposition_radar as radar
import parcel_intake
import selector
import trust


HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(HERE, "projects")
WORKSPACE_VERSION = "1.0"
PROJECT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,63}$")
REQUIRED_DIRS = ("sources", "evidence", "reports", "memory")
REQUIRED_TRUST_STATES = {"sourced", "computed", "assumption", "unknown"}
ALLOWED_PHASES = {"0", "1", "2", "31", "32", "33", "41", "51", "52", "53", "61-63"}
ALLOWED_ROUTE_LEVELS = {"federal", "cantonal", "communal"}


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


def _valid_iso_datetime(value) -> bool:
    if not _nonempty_string(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _source_ref(source_id: str, locator: str, valid_as_of: str, confidence: str = "high") -> dict:
    return {
        "source_id": source_id,
        "locator": locator,
        "valid_as_of": valid_as_of,
        "confidence": confidence,
    }


def _load_source_manifest(project_dir: str) -> dict:
    path = os.path.join(project_dir, "sources", "source_manifest.json")
    if not os.path.exists(path):
        return {"schema_version": WORKSPACE_VERSION, "sources": []}
    return _load_json(path)


def _validate_route_layer(layer: dict, path: str, report: WorkspaceValidationReport, prefix: str, active: bool) -> None:
    if not isinstance(layer, dict):
        report.add_error(path, f"{prefix} must contain objects")
        return
    layer_id = layer.get("layer_id") or "<missing>"
    for key in ("layer_id", "jurisdiction", "state", "evaluated_at"):
        if not _nonempty_string(layer.get(key)):
            report.add_error(path, f"{prefix}.{layer_id}.{key} must be a non-empty string")
    if layer.get("level") not in ALLOWED_ROUTE_LEVELS:
        report.add_error(path, f"{prefix}.{layer_id}.level must be one of {sorted(ALLOWED_ROUTE_LEVELS)}")
    if not _valid_iso_datetime(layer.get("evaluated_at")):
        report.add_error(path, f"{prefix}.{layer_id}.evaluated_at must be an ISO datetime")
    if active:
        if layer.get("state") != "active":
            report.add_error(path, f"{prefix}.{layer_id}.state must be active")
        if not _valid_iso_datetime(layer.get("selected_at")):
            report.add_error(path, f"{prefix}.{layer_id}.selected_at must be an ISO datetime")
    else:
        if layer.get("state") != "inactive":
            report.add_error(path, f"{prefix}.{layer_id}.state must be inactive")
        if not _nonempty_string(layer.get("inactive_reason")):
            report.add_error(path, f"{prefix}.{layer_id}.inactive_reason must be a non-empty string")
    source_version = layer.get("source_version")
    if not isinstance(source_version, dict):
        report.add_error(path, f"{prefix}.{layer_id}.source_version must be an object")
        return
    for key in ("source_status", "verified_at", "review_due"):
        if not _nonempty_string(source_version.get(key)):
            report.add_error(path, f"{prefix}.{layer_id}.source_version.{key} must be a non-empty string")


def _validate_regulatory_route(manifest: dict, manifest_path: str, report: WorkspaceValidationReport) -> None:
    route_obj = manifest.get("regulatory_route")
    if not isinstance(route_obj, dict):
        report.add_error(manifest_path, "regulatory_route must be an object")
        return
    if route_obj.get("schema_version") != WORKSPACE_VERSION:
        report.add_error(manifest_path, f"regulatory_route.schema_version must be {WORKSPACE_VERSION!r}")
    for key in ("route_id", "country", "canton", "commune", "selected_at", "evaluated_at"):
        if not _nonempty_string(route_obj.get(key)):
            report.add_error(manifest_path, f"regulatory_route.{key} must be a non-empty string")
    for key in ("selected_at", "evaluated_at"):
        if not _valid_iso_datetime(route_obj.get(key)):
            report.add_error(manifest_path, f"regulatory_route.{key} must be an ISO datetime")
    active_layers = route_obj.get("active_layers")
    inactive_layers = route_obj.get("inactive_layers")
    if not isinstance(active_layers, list) or not active_layers:
        report.add_error(manifest_path, "regulatory_route.active_layers must be a non-empty list")
        active_layers = []
    if not isinstance(inactive_layers, list):
        report.add_error(manifest_path, "regulatory_route.inactive_layers must be a list")
        inactive_layers = []
    for index, layer in enumerate(active_layers):
        _validate_route_layer(layer, manifest_path, report, f"regulatory_route.active_layers[{index}]", True)
    for index, layer in enumerate(inactive_layers):
        _validate_route_layer(layer, manifest_path, report, f"regulatory_route.inactive_layers[{index}]", False)
    if not isinstance(route_obj.get("freshness_warnings", []), list):
        report.add_error(manifest_path, "regulatory_route.freshness_warnings must be a list")


def project_manifest_path(project_dir: str) -> str:
    return os.path.join(project_dir, "project.json")


def report_index_path(project_dir: str) -> str:
    return os.path.join(project_dir, "reports", "report_index.json")


def report_memory_path(project_dir: str) -> str:
    return os.path.join(project_dir, "memory", "report_memory.json")


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
    _validate_regulatory_route(manifest, manifest_path, report)

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
                if not artifacts.is_sha256(item.get("content_sha256")):
                    report.add_error(index_path, f"{report_id}.content_sha256 must be a SHA-256 hex digest")
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
    report_path = os.path.join(project_dir, entry["path"])
    if os.path.exists(report_path):
        entry["content_sha256"] = artifacts.sha256_file(report_path)
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
    _record_generated_report_memory(project_dir, entry)
    return entry


def _record_generated_report_memory(project_dir: str, report_entry: dict) -> None:
    manifest = _load_json(project_manifest_path(project_dir)) if os.path.exists(project_manifest_path(project_dir)) else {}
    memory_path = report_memory_path(project_dir)
    if os.path.exists(memory_path):
        memory = _load_json(memory_path)
    else:
        memory = {
            "schema_version": WORKSPACE_VERSION,
            "memory_id": f"MEMORY-{manifest.get('project_id', 'PROJECT')}-REPORTS",
            "project_id": manifest.get("project_id"),
            "records": [],
        }
    record = {
        "memory_id": f"MEM-REPORT-{report_entry['report_id']}",
        "record_type": "report_generation",
        "phase_code": manifest.get("phase_code", "0"),
        "title": f"Generated {report_entry['kind']} report",
        "summary": f"Generated {report_entry['path']} with stable SHA-256 hash.",
        "claim_state": "evidence",
        "status": "active",
        "generated_at": report_entry["generated_at"],
        "source_refs": report_entry["source_refs"],
        "evidence_refs": [
            {
                "evidence_id": report_entry["report_id"],
                "kind": report_entry["kind"],
                "file_ref": f"project://{report_entry['path']}",
                "sha256": report_entry.get("content_sha256"),
            }
        ],
        "content_sha256": report_entry.get("content_sha256"),
    }
    records = [item for item in memory.get("records", []) if item.get("memory_id") != record["memory_id"]]
    records.append(record)
    memory["schema_version"] = WORKSPACE_VERSION
    memory["records"] = records
    _write_json(memory_path, memory)


def _constraint_claims(oereb_record: dict, source_ref: dict) -> list[dict]:
    alignment_value = ", ".join(oereb_record.get("alignments") or [])
    constraints = [
        claims.make_claim(
            "CLAIM-OEREB-ZONE",
            "Zone d'affectation",
            "sourced",
            oereb_record.get("zone"),
            confidence="high",
            source_refs=[source_ref],
        ),
        claims.make_claim(
            "CLAIM-OEREB-NOISE",
            "Degré de sensibilité au bruit",
            "sourced",
            oereb_record.get("noise_ds"),
            confidence="high",
            source_refs=[source_ref],
        ),
    ]
    if alignment_value:
        constraints.append(
            claims.make_claim(
                "CLAIM-OEREB-ALIGNMENTS",
                "Alignements / limites des constructions",
                "sourced",
                alignment_value,
                confidence="high",
                source_refs=[source_ref],
            )
        )
    else:
        constraints.append(
            claims.unknown_claim(
                "CLAIM-OEREB-ALIGNMENTS",
                "Alignements / limites des constructions",
                "Verifier la couche RDPPF/OEREB et le plan communal avant depot.",
            )
        )
    return constraints


def _envelope_claims(envelope: dict, source_refs: list[dict]) -> list[dict]:
    computed_refs = source_refs or []
    out = []
    if envelope.get("max_sbp_m2") is not None:
        out.append(
            claims.make_claim(
                "CLAIM-ENVELOPE-SBP",
                "Surface de plancher maximale",
                "computed",
                envelope["max_sbp_m2"],
                confidence="medium",
                source_refs=computed_refs,
                formula="surface_parcelle_m2 * indice_IUS_ou_IBUS",
                inputs={"area_m2": envelope.get("area_m2"), "index_value": envelope.get("index_value")},
            )
        )
    else:
        out.append(
            claims.unknown_claim(
                "CLAIM-ENVELOPE-SBP",
                "Surface de plancher maximale",
                "Aucun IUS/IBUS numerique n'est disponible; verifier le gabarit communal et le contexte bati.",
            )
        )
    if envelope.get("max_footprint_m2") is not None:
        out.append(
            claims.make_claim(
                "CLAIM-ENVELOPE-FOOTPRINT",
                "Emprise au sol maximale",
                "computed",
                envelope["max_footprint_m2"],
                confidence="medium",
                source_refs=computed_refs,
                formula="surface_parcelle_m2 * IOS",
                inputs={"area_m2": envelope.get("area_m2"), "ios": envelope.get("ios")},
            )
        )
    else:
        out.append(
            claims.unknown_claim(
                "CLAIM-ENVELOPE-FOOTPRINT",
                "Emprise au sol maximale",
                "Aucun IOS numerique n'est disponible; verifier les distances, longueurs et gabarits applicables.",
            )
        )
    for key, title, action in (
        ("height_corniche_m", "Hauteur a la corniche", "Verifier la regle de hauteur dans le reglement communal."),
        ("height_faite_m", "Hauteur au faite", "Verifier la regle de hauteur dans le reglement communal."),
        ("levels_max", "Nombre de niveaux maximal", "Verifier niveaux, combles et attiques dans le reglement communal."),
        ("setback_min_m", "Distance minimale aux limites", "Verifier limites, mitoyennete et alignements avant esquisse."),
    ):
        if envelope.get(key) is not None:
            out.append(
                claims.make_claim(
                    f"CLAIM-ENVELOPE-{key.upper()}",
                    title,
                    "sourced",
                    envelope[key],
                    confidence="medium",
                    source_refs=computed_refs,
                )
            )
        else:
            out.append(claims.unknown_claim(f"CLAIM-ENVELOPE-{key.upper()}", title, action))
    return out


def _residual_unknowns(claims_list: list[dict]) -> list[dict]:
    unknowns = [
        {
            "claim_id": claim["claim_id"],
            "topic": claim["title"],
            "state": claim["state"],
            "next_action": claim.get("next_action") or claim.get("required_human_check"),
        }
        for claim in claims_list
        if claim.get("state") in {"unknown", "assumption", "conflict"}
    ]
    unknowns.append(
        {
            "topic": "Servitudes du registre foncier",
            "state": "unknown",
            "next_action": "Consulter l'extrait du registre foncier et les servitudes avant toute decision.",
        }
    )
    return unknowns


def render_brief_html(brief: dict) -> str:
    claims.validate_claims(brief.get("claims") or [])
    title = html.escape(brief.get("brief_id", "Aedifica brief"))
    route = brief.get("regulatory_route") or {}
    warnings = brief.get("freshness_warnings") or []
    risks = brief.get("risks") or {}
    source_registry = brief.get("source_registry") or {}

    def esc(value):
        return html.escape("" if value is None else str(value))

    def render_claim(claim):
        value = "Inconnu" if claim.get("value") is None else esc(claim.get("value"))
        meta = []
        if claim.get("formula"):
            meta.append(f"formule: {esc(claim['formula'])}")
        if claim.get("next_action"):
            meta.append(f"action: {esc(claim['next_action'])}")
        return (
            f"<li class='claim {esc(claim['state'])}'>"
            f"<span class='state'>{esc(claim['state'])}</span>"
            f"<b>{esc(claim['title'])}</b><br><span>{value}</span>"
            + (f"<small>{' · '.join(meta)}</small>" if meta else "")
            + "</li>"
        )

    source_rows = "".join(
        f"<li><b>{esc(src.get('source_id'))}</b> — {esc(src.get('title'))} ({esc(src.get('valid_as_of'))})</li>"
        for src in source_registry.get("sources", [])
    )
    active_layers = "".join(
        f"<li>{esc(layer.get('layer_id'))} · {esc(layer.get('source_version_id'))}</li>"
        for layer in route.get("active_layers", [])
    )
    warning_rows = "".join(f"<li>{esc(w.get('layer_id'))}: {esc(w.get('message'))}</li>" for w in warnings)
    risk_rows = "".join(
        f"<li><b>{esc(item.get('level'))}</b> {esc(item.get('ground'))}: {esc(item.get('basis'))}</li>"
        for item in risks.get("grounds", [])
    )
    unknown_rows = "".join(
        f"<li>{esc(item.get('topic'))}: {esc(item.get('next_action'))}</li>"
        for item in brief.get("residual_unknowns", [])
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #17202a; line-height: 1.35; }}
    h1, h2 {{ margin: 0 0 10px; }}
    section {{ border-top: 1px solid #d9dee7; padding-top: 16px; margin-top: 18px; }}
    ul {{ padding-left: 18px; }}
    .claim {{ margin: 9px 0; }}
    .state {{ display: inline-block; min-width: 86px; font-size: 12px; text-transform: uppercase; color: #4f5b67; }}
    .unknown .state, .assumption .state, .conflict .state {{ color: #9a5b00; font-weight: bold; }}
    small {{ display: block; color: #5d6975; margin-top: 2px; }}
    footer {{ white-space: pre-line; color: #4f5b67; margin-top: 24px; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>{esc(brief.get('project_summary', {}).get('name'))} · {esc(brief.get('generated_at'))}</p>
  <section><h2>Route réglementaire</h2><ul>{active_layers}</ul>{'<h3>Avertissements</h3><ul>' + warning_rows + '</ul>' if warning_rows else ''}</section>
  <section><h2>Sources</h2><ul>{source_rows}</ul></section>
  <section><h2>Parcelle</h2><ul>{''.join(render_claim(c) for c in brief.get('constraints', []))}</ul></section>
  <section><h2>Enveloppe</h2><ul>{''.join(render_claim(c) for c in brief.get('envelope_claims', []))}</ul></section>
  <section><h2>Risques indicatifs</h2><p>Global: {esc(risks.get('overall'))} ({esc(risks.get('score'))})</p><ul>{risk_rows or '<li>Aucun facteur saillant dans le fixture.</li>'}</ul></section>
  <section><h2>Inconnues résiduelles</h2><ul>{unknown_rows}</ul></section>
  <footer>{esc(brief.get('trust_footer'))}</footer>
</body>
</html>
"""


def write_brief_html_report(project_dir: str, brief: dict) -> dict:
    report_rel = f"reports/{brief['brief_id'].lower()}.html"
    report_path = os.path.join(project_dir, report_rel)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(render_brief_html(brief))
    return record_report(project_dir, f"{brief['brief_id']}-HTML", "parcel_brief_html", report_rel, brief["source_refs"], brief["trust_footer"])


def generate_offline_parcel_brief(project_dir: str, write_report: bool = False) -> dict:
    manifest = _load_json(project_manifest_path(project_dir))
    parcel_context = parcel_intake.from_project_fixture(project_dir)
    source_registry = _load_source_manifest(project_dir)
    route_obj = manifest.get("regulatory_route")
    if not isinstance(route_obj, dict):
        jurisdiction = manifest.get("jurisdiction") or {}
        route_obj = selector.regulatory_route(
            jurisdiction.get("country", "CH"),
            jurisdiction.get("canton", "VD"),
            jurisdiction.get("commune", "Lausanne"),
        )
    freshness_warnings = selector.pack_freshness_warnings(route_obj)
    oereb_record = parcel_context["oereb_record"]
    area = parcel_context["area_m2"]

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
    source_refs_by_id = {item["source_id"]: item for item in source_refs}
    constraint_claims = _constraint_claims(oereb_record, source_refs_by_id["VD-OEREB"])
    zone_claim = (
        claims.make_claim(
            "CLAIM-COMMUNAL-ZONE",
            "Zone communale retenue",
            "sourced",
            zone_name,
            confidence=provenance.get("confidence", "medium") if provenance else "medium",
            source_refs=[source_refs_by_id["COMMUNE-RPGA"]],
        )
        if zone_name and "COMMUNE-RPGA" in source_refs_by_id
        else claims.unknown_claim(
            "CLAIM-COMMUNAL-ZONE",
            "Zone communale retenue",
            "Cartographier la zone OEREB vers un pack communal vérifié avant de calculer l'enveloppe.",
        )
    )
    envelope = domain.calculate_envelope(area, zone_params)
    envelope_claims = _envelope_claims(envelope, source_refs)
    all_claims = constraint_claims + [zone_claim] + envelope_claims
    claims.validate_claims(all_claims)
    risks = radar.score(oereb_record, None, None, area)
    residual_unknowns = _residual_unknowns(all_claims)

    brief = {
        "schema_version": WORKSPACE_VERSION,
        "brief_id": f"BRIEF-{manifest['project_id']}-PARCEL",
        "project_id": manifest["project_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_summary": {
            "project_id": manifest["project_id"],
            "name": manifest.get("name"),
            "phase_code": manifest.get("phase_code"),
            "knowledge_regime": manifest.get("knowledge_regime"),
            "jurisdiction": manifest.get("jurisdiction"),
        },
        "claim_state_summary": sorted({claim["state"] for claim in all_claims}),
        "source_refs": source_refs,
        "evidence_refs": parcel_context.get("evidence_refs", []),
        "source_registry": source_registry,
        "parcel_context": {key: value for key, value in parcel_context.items() if key != "oereb_record"},
        "regulatory_route": route_obj,
        "freshness_warnings": freshness_warnings,
        "parcel": {
            "egrid": oereb_record.get("egrid"),
            "number": oereb_record.get("parcel"),
            "commune": oereb_record.get("commune"),
            "area_m2": area,
        },
        "constraints": constraint_claims,
        "communal_zone": {
            "name": zone_name,
            "match_method": match_method,
            "claim_state": "sourced" if zone_name else "unknown",
        },
        "envelope": envelope,
        "envelope_claims": envelope_claims,
        "claims": all_claims,
        "risks": risks,
        "residual_unknowns": residual_unknowns,
        "unknowns": [item["next_action"] for item in residual_unknowns if item.get("next_action")],
        "trust_footer": trust.render_footer(manifest.get("trust_contract", {}).get("language", "fr")),
    }
    if write_report:
        report_rel = f"reports/{brief['brief_id'].lower()}.json"
        _write_json(os.path.join(project_dir, report_rel), brief)
        record_report(project_dir, brief["brief_id"], "parcel_brief", report_rel, source_refs, brief["trust_footer"])
        write_brief_html_report(project_dir, brief)
    return brief
