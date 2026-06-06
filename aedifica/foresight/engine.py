"""W12.A — Foresight engine.

Compose the per-rule generators (duration / cost / risk) + retrieval
(comparables) into a single, deterministic pass that returns Proposal dicts
ready to persist. Compute a freshness timestamp and a summary.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass

from .comparables import find_atelier_comparables
from .cost import propose_cost_factor
from .duration import propose_duration_adjustments
from .risk import propose_risks


@dataclass
class ForesightSummary:
    predictions: int
    risks: int
    suggestions: int
    confidence_avg: float
    comparables: list  # list of Comparable dataclasses
    freshness: _dt.datetime


def _persist(session, project, proposals: list[dict]) -> list:
    """Replace the project's *pending* proposals with the freshly computed set.
    Accepted/refused/deferred proposals are NEVER touched — they're the user's
    decision history."""
    from ..db import models as m  # noqa: WPS433
    # Drop only PENDING proposals — the others form the architect's audit trail.
    (session.query(m.Proposal)
            .filter_by(project_id=project.id, decision="pending")
            .delete(synchronize_session=False))
    saved = []
    for p in proposals:
        row = m.Proposal(
            project_id=project.id,
            kind=p["kind"],
            title=p["title"],
            detail=p["detail"],
            basis_json=json.dumps(p["basis"], ensure_ascii=False),
            confidence=float(p.get("confidence", 0.0)),
            apply_payload_json=(json.dumps(p["apply_payload"], ensure_ascii=False)
                                if p.get("apply_payload") is not None else None),
            decision="pending",
        )
        session.add(row); saved.append(row)
    session.flush()
    return saved


def thresholds(session, project) -> dict:
    """W14.A — explain the minimum-data thresholds per rule so the architect
    knows exactly what's missing when no proposal fires.

    "Pas assez de comparables" is not a useful empty-state — "il faut 5 tâches
    closes en phase 32, vous en avez 2" is."""
    from ..db import models as m  # noqa: WPS433
    from collections import defaultdict
    # duration_adjust: 5 done tasks per phase, with both estimate AND actual.
    done_tasks = (session.query(m.Task)
                  .join(m.Project, m.Task.project_id == m.Project.id)
                  .filter(m.Project.org_id == project.org_id,
                          m.Task.status == "done",
                          m.Task.estimate_hours.isnot(None),
                          m.Task.actual_hours.isnot(None)).all())
    by_phase = defaultdict(int)
    for t in done_tasks:
        by_phase[t.phase_code or "_"] += 1
    duration_by_phase = {ph: {"have": n, "need": 5, "ready": n >= 5}
                          for ph, n in by_phase.items()}
    # cost_factor: 3 archived projects with both estimate and final cost.
    pairs = 0
    for p in session.query(m.Project).filter_by(org_id=project.org_id).all():
        ci = p.cost_inputs or {}
        est = ci.get("estimate_chf") or ci.get("estimate")
        fin = ci.get("final_chf") or ci.get("actual_chf") or ci.get("actual")
        try:
            if est and fin and float(est) > 0 and float(fin) > 0:
                pairs += 1
        except (TypeError, ValueError):
            pass
    return {
        "duration_adjust": {
            "rule": "Médiane atelier réel/estimé par phase",
            "need_per_phase": 5,
            "samples_by_phase": duration_by_phase,
            "explanation": "Pour chaque tâche ouverte, il faut au moins 5 tâches "
                           "closes de la même phase avec heures estimées ET réelles "
                           "renseignées avant qu'une recommandation d'estimation "
                           "puisse émerger.",
        },
        "cost_factor": {
            "rule": "Coefficient atelier final/SIA",
            "have": pairs,
            "need": 3,
            "ready": pairs >= 3,
            "explanation": "Il faut au moins 3 projets clos avec coût final ET "
                           "estimation SIA renseignés dans cost_inputs avant qu'un "
                           "coefficient atelier puisse être proposé.",
        },
        "risk_alert": {
            "rule": "Règles déterministes cross-surface",
            "explanation": "Fire automatiquement quand un signal sourcé matche "
                           "(BRS après dépôt, cascade overdue, surcharge hebdo, "
                           "friction récurrente, règlement à l'étude).",
        },
    }


def compute_proposals(session, project) -> tuple[list, ForesightSummary]:
    """Run all deterministic Foresight rules and persist the pending proposals.

    Returns (rows, summary). Never raises on individual rule failure — the
    safety doctrine is "silent skip on missing data" rather than mask the
    other rules behind one broken signal."""
    all_props: list[dict] = []

    def _run(gen):
        try:
            for p in gen:
                all_props.append(p)
        except Exception:  # pragma: no cover — defensive: never block other rules
            pass

    _run(propose_duration_adjustments(session, project))
    _run(propose_cost_factor(session, project))
    _run(propose_risks(session, project))

    rows = _persist(session, project, all_props)
    comps = find_atelier_comparables(session, project)
    n_pred = sum(1 for p in all_props if p["kind"] in ("duration_adjust", "cost_factor"))
    n_risk = sum(1 for p in all_props if p["kind"] == "risk_alert")
    n_sugg = sum(1 for p in all_props if p["kind"] in ("reuse_brs", "reuse_checklist", "rebalance"))
    conf = (sum(p.get("confidence", 0.0) for p in all_props) / len(all_props)
            if all_props else 0.0)
    summary = ForesightSummary(
        predictions=n_pred,
        risks=n_risk,
        suggestions=n_sugg,
        confidence_avg=round(conf, 2),
        comparables=comps,
        freshness=_dt.datetime.now(_dt.timezone.utc),
    )
    return rows, summary
