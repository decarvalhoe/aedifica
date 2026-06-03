"""Project memory queries + per-phase next-step orchestration (the north-star Q&A).

Answers, over the persisted project data (claims + ledger + sources), the
questions the architect asks: what is still unknown, what was decided, what
changed, which source justifies this — and composes a sourced "next step per
phase". Never invents; marks unknowns; never an authority decision.
"""
from __future__ import annotations

from ..db import models as m
from ..ingestion import service as ingestion
from . import reports

DECISION_EVENTS = {"approval", "adapter_execution", "decision"}


def unknowns(session, project) -> list:
    rows = (
        session.query(m.Claim)
        .filter(m.Claim.project_id == project.id, m.Claim.state.in_(["unknown", "assumption"]))
        .all()
    )
    return [
        {"claim_id": c.claim_id, "title": c.title, "state": c.state, "next_action": c.next_action, "source_refs": c.source_refs}
        for c in rows
    ]


def _ledger(session, project):
    return session.query(m.LedgerEntry).filter_by(project_id=project.id).order_by(m.LedgerEntry.id).all()


def decisions(session, project) -> list:
    return [
        {"ledger_id": e.ledger_id, "event_type": e.event_type, "summary": e.summary, "phase_code": e.phase_code,
         "approval_scope": e.approval.scope if e.approval else None}
        for e in _ledger(session, project)
        if e.event_type in DECISION_EVENTS
    ]


def changes(session, project) -> list:
    return [
        {"ledger_id": e.ledger_id, "event_type": e.event_type, "summary": e.summary, "phase_code": e.phase_code, "mutating": e.mutating}
        for e in _ledger(session, project)
    ]


def source(session, project, source_id: str) -> dict:
    claims = [
        {"claim_id": c.claim_id, "title": c.title, "state": c.state}
        for c in session.query(m.Claim).filter_by(project_id=project.id).all()
        if any((ref or {}).get("source_id") == source_id for ref in (c.source_refs or []))
    ]
    sources = [
        {"source_id": s.source_id, "title": s.title, "kind": s.kind, "valid_as_of": s.valid_as_of}
        for s in session.query(m.Source).filter_by(project_id=project.id, source_id=source_id).all()
    ]
    return {"source_id": source_id, "claims": claims, "sources": sources}


def next_step(session, project, phase: str | None = None) -> dict:
    steps = []
    for c in unknowns(session, project):
        steps.append({"kind": "resolve_unknown", "phase": project.phase_code, "state": "unknown", "title": c["title"], "action": c["next_action"], "source_refs": c["source_refs"]})

    permit = reports.permit_view(project)
    for group in permit["groups"]:
        for item in group["items"]:
            if item["status"] == "missing":
                steps.append({"kind": "permit_blocker", "phase": "33", "state": "missing", "title": item["title"], "action": item.get("missing_message")})

    compliance = reports.compliance_view(project)
    for gate in compliance["legal"]:
        if gate["status"] in {"unknown", "action_required"}:
            steps.append({"kind": "compliance", "phase": "33", "state": "unknown", "title": gate["title"], "action": gate.get("next_action")})

    support = ingestion.support_state(session, project.commune, project.canton)
    if not support["usable"]:
        steps.append({"kind": "commune", "phase": project.phase_code, "state": "unknown", "title": f"Commune {project.commune} non supportée", "action": "Ingérer le règlement communal avant de fiabiliser l'enveloppe."})

    if phase:
        steps = [s for s in steps if s.get("phase") == phase]
    return {
        "project_id": project.project_id,
        "phase": phase,
        "claims_prediction": False,
        "note": "Recommandations sourcées; jamais une décision d'autorité.",
        "steps": steps,
    }
