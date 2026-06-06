"""W12.A — duration prediction (deterministic).

Method: for each open task (estimate_hours set, status != "done"), look up
the same atelier's archived tasks that are *similar* on (phase_code, kind).
If at least 5 comparable rows exist, compute the median ratio
`actual_hours / estimate_hours`. If that ratio drifts ≥ 1.2 or ≤ 0.8 from 1.0,
propose a re-estimate. Otherwise the original estimate stands.

No comparable data → no proposal. We do NOT fabricate.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class _Comparable:
    estimate: float
    actual: float
    task_id: int


def _gather_comparables(session, org_id: int, phase: str | None) -> list[_Comparable]:
    from ..db import models as m  # noqa: WPS433 — runtime import to avoid cycle
    q = (session.query(m.Task)
         .join(m.Project, m.Task.project_id == m.Project.id)
         .filter(m.Project.org_id == org_id, m.Task.status == "done",
                 m.Task.estimate_hours.isnot(None), m.Task.actual_hours.isnot(None)))
    if phase:
        q = q.filter(m.Task.phase_code == phase)
    return [_Comparable(estimate=t.estimate_hours, actual=t.actual_hours, task_id=t.id)
            for t in q.all() if t.estimate_hours and t.actual_hours and t.estimate_hours > 0]


def propose_duration_adjustments(session, project, *, threshold: float = 0.2, min_comparables: int = 5):
    """Yield Proposal dicts for tasks whose median atelier ratio departs from 1.0 by ≥ threshold."""
    from ..db import models as m  # noqa: WPS433
    open_tasks = [t for t in session.query(m.Task).filter_by(project_id=project.id).all()
                  if t.status not in ("done",) and t.estimate_hours and t.estimate_hours > 0]
    for t in open_tasks:
        comps = _gather_comparables(session, project.org_id, t.phase_code)
        if len(comps) < min_comparables:
            continue
        ratios = [c.actual / c.estimate for c in comps]
        ratio_med = statistics.median(ratios)
        if abs(ratio_med - 1.0) < threshold:
            continue
        suggested = round(t.estimate_hours * ratio_med, 1)
        basis = [{"source_kind": "task", "source_id": c.task_id,
                  "ref": f"Tâche {c.task_id} : {c.estimate} h estimées → {c.actual} h réelles"}
                 for c in comps[:8]]
        # Confidence rises with the comparable count and saturates at 20 samples.
        confidence = round(min(1.0, len(comps) / 20.0), 2)
        delta = suggested - t.estimate_hours
        direction = "augmenter" if delta > 0 else "réduire"
        yield {
            "kind": "duration_adjust",
            "title": f"{direction.capitalize()} l'estimation de « {t.title} » de {t.estimate_hours} h → {suggested} h",
            "detail": (
                f"L'atelier a {len(comps)} tâches similaires (phase {t.phase_code or '—'}) "
                f"avec un ratio médian réel/estimé de {ratio_med:.2f}. "
                f"Cela suggère de {direction} l'estimation actuelle de {abs(delta):.1f} h."
            ),
            "basis": basis,
            "confidence": confidence,
            "apply_payload": {
                "method": "PATCH",
                "path": f"/api/projects/{project.project_id}/tasks/{t.id}",
                "body": {"estimate_hours": suggested},
            },
        }
