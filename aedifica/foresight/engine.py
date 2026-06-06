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
