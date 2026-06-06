"""W12.E — atelier benchmark capture (deterministic).

Compute the current learning state of the atelier and freeze it as an
AtelierBenchmark row. Triggered manually (POST /api/orgs/benchmark/snapshot)
or by a quarterly cron. Append-only.
"""
from __future__ import annotations

import datetime as _dt
import json
import statistics
from collections import defaultdict


def _quarter_label(now: _dt.datetime | None = None) -> str:
    n = now or _dt.datetime.now(_dt.timezone.utc)
    q = (n.month - 1) // 3 + 1
    return f"{n.year}-Q{q}"


def snapshot_atelier(session, org_id: int, *, note: str | None = None):
    """Compute + persist a benchmark row for the given org. Returns the row."""
    from ..db import models as m  # noqa: WPS433
    # Duration ratios per phase (median over the atelier's done tasks).
    tasks = (session.query(m.Task)
             .join(m.Project, m.Task.project_id == m.Project.id)
             .filter(m.Project.org_id == org_id,
                     m.Task.status == "done",
                     m.Task.estimate_hours.isnot(None),
                     m.Task.actual_hours.isnot(None)).all())
    by_phase = defaultdict(list)
    for t in tasks:
        if t.estimate_hours and t.estimate_hours > 0:
            by_phase[t.phase_code or "_"].append(t.actual_hours / t.estimate_hours)
    duration_ratios = {ph: round(statistics.median(rs), 2)
                       for ph, rs in by_phase.items() if len(rs) >= 3}
    # Cost factor (median ratio across projects with both estimate + final).
    cost_factor = None
    projs = session.query(m.Project).filter_by(org_id=org_id).all()
    pairs = []
    for p in projs:
        ci = p.cost_inputs or {}
        est = ci.get("estimate_chf") or ci.get("estimate")
        fin = ci.get("final_chf") or ci.get("actual_chf") or ci.get("actual")
        try:
            est = float(est) if est else 0.0
            fin = float(fin) if fin else 0.0
        except (TypeError, ValueError):
            est = fin = 0.0
        if est > 0 and fin > 0:
            pairs.append(fin / est)
    if len(pairs) >= 3:
        cost_factor = round(statistics.median(pairs), 2)
    row = m.AtelierBenchmark(
        org_id=org_id,
        period_label=_quarter_label(),
        n_projects=len(projs),
        n_tasks_done=len(tasks),
        duration_ratios_json=json.dumps(duration_ratios),
        cost_factor=cost_factor,
        note=note,
    )
    session.add(row); session.flush()
    return row


def latest_snapshot(session, org_id: int):
    from ..db import models as m  # noqa: WPS433
    return (session.query(m.AtelierBenchmark)
            .filter_by(org_id=org_id)
            .order_by(m.AtelierBenchmark.id.desc()).first())
