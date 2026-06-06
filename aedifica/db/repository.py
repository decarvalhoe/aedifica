"""Persistence repositories — bridge the stdlib engine output to the SQL store.

The engine (``aedifica.workspace`` / pilot) produces dict-shaped briefs, claims,
reports and ledger entries. These repositories map them to ORM rows so a project
round-trips through the DB with identical trust states. The trust invariant is
enforced by the model layer at flush.
"""
from __future__ import annotations

from . import models as m


def get_or_create_org(session, name: str = "Default Org") -> m.Org:
    org = session.query(m.Org).filter_by(name=name).first()
    if org is None:
        org = m.Org(name=name)
        session.add(org)
        session.flush()
    return org


def create_project(
    session,
    org_id: int,
    project_id: str,
    name: str,
    commune: str,
    country: str = "CH",
    canton: str = "VD",
    phase_code: str = "0",
    knowledge_regime: str = "context_first",
) -> m.Project:
    project = m.Project(
        org_id=org_id,
        project_id=project_id,
        name=name,
        commune=commune,
        country=country,
        canton=canton,
        phase_code=phase_code,
        knowledge_regime=knowledge_regime,
    )
    session.add(project)
    session.flush()
    return project


def save_brief(session, project: m.Project, brief: dict) -> dict:
    """Persist the engine brief (sources, evidence, claims, route) for a project."""
    seen_sources = set()
    for ref in brief.get("source_refs", []):
        sid = ref.get("source_id")
        if not sid or sid in seen_sources:
            continue
        seen_sources.add(sid)
        session.add(
            m.Source(
                project_id=project.id,
                source_id=sid,
                title=ref.get("title", sid),
                kind=ref.get("kind", "brief_source"),
                locator=ref.get("locator"),
                valid_as_of=ref.get("valid_as_of"),
            )
        )
    for ev in brief.get("evidence_refs", []):
        session.add(
            m.Evidence(
                project_id=project.id,
                evidence_id=ev.get("evidence_id"),
                kind=ev.get("kind"),
                file_ref=ev.get("file_ref"),
                sha256=ev.get("sha256"),
                valid_as_of=ev.get("valid_as_of"),
            )
        )
    for c in brief.get("claims", []):
        session.add(
            m.Claim(
                project_id=project.id,
                claim_id=c["claim_id"],
                title=c["title"],
                claim_type=c.get("claim_type", "regulatory"),
                state=c["state"],
                value=c.get("value"),
                confidence=c.get("confidence", "medium"),
                formula=c.get("formula"),
                next_action=c.get("next_action"),
                source_refs=c.get("source_refs", []),
            )
        )
    route = brief.get("regulatory_route") or {}
    if route.get("route_id"):
        session.add(
            m.RegulatoryRoute(
                project_id=project.id,
                route_id=route["route_id"],
                country=route.get("country", project.country),
                canton=route.get("canton", project.canton),
                commune=route.get("commune", project.commune),
                selected_at=str(route.get("selected_at", "")),
                active_pack_ids=[layer.get("layer_id") for layer in route.get("active_layers", [])],
            )
        )
    project.brief_risks = brief.get("risks")  # per-project opposition input (AED-211)
    session.flush()
    return {
        "claims": len(brief.get("claims", [])),
        "sources": len(seen_sources),
        "evidence": len(brief.get("evidence_refs", [])),
    }


def save_report(session, project: m.Project, report_entry: dict) -> m.Report:
    report = m.Report(
        project_id=project.id,
        report_id=report_entry["report_id"],
        kind=report_entry.get("kind", "report"),
        path=report_entry.get("path", ""),
        content_sha256=report_entry.get("content_sha256"),
        source_refs=report_entry.get("source_refs", []),
    )
    session.add(report)
    session.flush()
    return report


def save_ledger_entry(session, project: m.Project, entry: dict) -> m.LedgerEntry:
    actor = entry.get("actor", {})
    led = m.LedgerEntry(
        project_id=project.id,
        ledger_id=entry["ledger_id"],
        event_type=entry["event_type"],
        summary=entry.get("summary", ""),
        actor_name=actor.get("name", "unknown"),
        actor_role=actor.get("role", "unknown"),
        phase_code=entry.get("phase", {}).get("phase_code", "0"),
        mutating=bool(entry.get("mutating")),
        content_sha256=entry.get("content_sha256"),
    )
    approval = entry.get("approval")
    if approval:
        led.approval = m.Approval(
            approved_by=approval.get("approved_by", ""),
            scope=approval.get("scope", ""),
            basis=approval.get("basis", ""),
            approved_at=str(approval.get("approved_at", "")),
        )
    session.add(led)
    session.flush()
    return led


def claims_for(session, project: m.Project) -> list[dict]:
    rows = session.query(m.Claim).filter_by(project_id=project.id).all()
    return [
        {
            "claim_id": c.claim_id,
            "title": c.title,
            "state": c.state,
            "value": c.value,
            "confidence": c.confidence,
            "source_refs": c.source_refs,
        }
        for c in rows
    ]


def project_summary(session, project: m.Project) -> dict:
    return {
        "project_id": project.project_id,
        "name": project.name,
        "phase_code": project.phase_code,
        "jurisdiction": {"country": project.country, "canton": project.canton, "commune": project.commune},
        "claims": session.query(m.Claim).filter_by(project_id=project.id).count(),
        "sources": session.query(m.Source).filter_by(project_id=project.id).count(),
        "evidence": session.query(m.Evidence).filter_by(project_id=project.id).count(),
        "reports": session.query(m.Report).filter_by(project_id=project.id).count(),
        "ledger_entries": session.query(m.LedgerEntry).filter_by(project_id=project.id).count(),
        # W15.B: surface the LLM mode so the Settings UI can show its current
        # state per project without an extra fetch.
        "llm_mode": getattr(project, "llm_mode", "off") or "off",
    }
