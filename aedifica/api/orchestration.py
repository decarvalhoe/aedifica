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


SIA_PHASE_ORDER = ("11", "21", "22", "31", "32", "33", "41", "51", "52", "53", "61")


def _phase_window(project_phase: str | None, look_ahead: int = 1) -> set[str]:
    """W11.A coherence: the *prochain pas* surface only makes sense if it tracks
    the project's actual phase. Return the set of phase codes that count as
    "now" — the current phase + the next ``look_ahead`` upcoming ones. When the
    project isn't started yet (``phase_code`` empty or "0"), show only the
    first SIA sub-phase as the immediate next step."""
    code = (project_phase or "").strip()
    if not code or code == "0":
        return {SIA_PHASE_ORDER[0]}
    try:
        idx = SIA_PHASE_ORDER.index(code)
    except ValueError:
        return {SIA_PHASE_ORDER[0]}
    return set(SIA_PHASE_ORDER[idx: idx + 1 + look_ahead])


def next_step(session, project, phase: str | None = None) -> dict:
    """W11.A: return next steps grounded in the project's current SIA phase.
    Three buckets are walked: unresolved unknowns (any phase), missing permit
    items (phase 33), unknown compliance gates (phase 33), then the actual
    SIA *checklist* — the per-actor steps the workspace seeded — which is the
    authoritative source of "what's next per phase". By default only the
    current + next phases are returned (anything later is pushed to
    ``upcoming``)."""
    window = _phase_window(project.phase_code) if not phase else {phase}
    # Fallback phase for steps that have no natural phase tied to them (project-wide
    # unknowns, the commune-not-supported warning…). Anchor them to the project's
    # current phase, or to the first SIA sub-phase if not started yet.
    here = project.phase_code if project.phase_code and project.phase_code != "0" else SIA_PHASE_ORDER[0]

    raw_steps = []
    for c in unknowns(session, project):
        raw_steps.append({"kind": "resolve_unknown", "phase": here,
                          "state": "unknown", "title": c["title"], "action": c["next_action"],
                          "source_refs": c["source_refs"]})

    permit = reports.permit_view(project)
    for group in permit["groups"]:
        for item in group["items"]:
            if item["status"] == "missing":
                raw_steps.append({"kind": "permit_blocker", "phase": "33", "state": "missing",
                                  "title": item["title"], "action": item.get("missing_message")})

    compliance = reports.compliance_view(project)
    for gate in compliance["legal"]:
        if gate["status"] in {"unknown", "action_required"}:
            raw_steps.append({"kind": "compliance", "phase": "33", "state": "unknown",
                              "title": gate["title"], "action": gate.get("next_action")})

    support = ingestion.support_state(session, project.commune, project.canton)
    if not support["usable"]:
        raw_steps.append({"kind": "commune", "phase": here,
                          "state": "unknown",
                          "title": f"Commune {project.commune} non supportée",
                          "action": "Ingérer le règlement communal avant de fiabiliser l'enveloppe."})

    # Checklist — the actual SIA per-actor steps this project carries (W10).
    # Surface unfinished items, tagged by their responsible actor.
    cl = session.query(m.ChecklistItem).filter_by(project_id=project.id).order_by(m.ChecklistItem.order_index).all()
    for it in cl:
        if it.status != "todo":
            continue
        raw_steps.append({"kind": "checklist", "phase": it.phase_code, "state": "todo",
                          "title": it.title, "actor": it.actor,
                          "is_retroactive": bool(it.is_retroactive),
                          "action": ("Étape rétroactive à reconstituer." if it.is_retroactive
                                     else "Avancer cette étape dans la phase courante.")})

    steps = [s for s in raw_steps if s.get("phase") in window]
    upcoming = [s for s in raw_steps if s.get("phase") not in window]
    return {
        "project_id": project.project_id,
        "phase": phase or project.phase_code or "",
        "window": sorted(window),
        "claims_prediction": False,
        "note": "Recommandations sourcées; jamais une décision d'autorité.",
        "steps": steps,
        "upcoming": upcoming,
    }
