"""Pilotage helpers — deterministic estimates, cross-project collision, SIA fees.

No LLM here: predictions are historical averages and the fee calc is the published
SIA model. This matches the partner's framing — most of the pilotage layer is "pur
soft"; the predictive lever is learning durations from the atelier's own history.
"""
from __future__ import annotations

import datetime as _dt

# SIA ordinary-fee weighting across phases 31..53 (~100%), cf. architect-reality.md §4.
FEE_PHASE_WEIGHTS = {"31": 0.09, "32": 0.21, "33": 0.025, "41": 0.18, "51": 0.16, "52": 0.29, "53": 0.045}
# Indicative % of CFC2 by project type (SIA practice — the atelier tunes these).
DEFAULT_FEE_PCT = {"villa": 0.13, "logement": 0.12, "renovation": 0.15, "amenagement": 0.16, "autre": 0.13}


def fee_estimate(cfc2: float, project_type: str = "autre", hourly_rate: float | None = None,
                 hours: float | None = None) -> dict:
    """Honoraire via the two SIA methods: % of the CFC2 cost, and H = T × h."""
    pct = DEFAULT_FEE_PCT.get(project_type, DEFAULT_FEE_PCT["autre"])
    by_cost = round(cfc2 * pct) if cfc2 else None
    by_time = round(hourly_rate * hours) if (hourly_rate and hours) else None
    base = by_cost or by_time
    by_phase = {ph: round(base * w) for ph, w in FEE_PHASE_WEIGHTS.items()} if base else {}
    return {
        "cfc2": cfc2, "project_type": project_type, "percentage": pct,
        "by_cost_method": by_cost, "by_time_method": by_time,
        "hourly_rate": hourly_rate, "hours": hours,
        "recommended": base, "by_phase": by_phase,
    }


def _kw(title: str) -> set:
    return {w for w in (title or "").lower().split() if len(w) > 3}


def predict_hours(title: str, history: list[dict]) -> dict:
    """Predict a task's hours from the atelier's completed tasks (actual_hours).
    Prefers tasks sharing keywords; falls back to the global average."""
    done = [h for h in history if h.get("actual_hours")]
    if not done:
        return {"prediction": None, "basis": "no_history", "samples": 0}
    words = _kw(title)
    similar = [h for h in done if words & _kw(h.get("title", ""))]
    pool = similar or done
    avg = sum(h["actual_hours"] for h in pool) / len(pool)
    return {"prediction": round(avg, 1), "basis": "similar" if similar else "global_average", "samples": len(pool)}


def _iso_week(date_str: str | None):
    try:
        y, w, _ = _dt.date.fromisoformat(date_str).isocalendar()
        return f"{y}-W{w:02d}"
    except Exception:
        return None


def collisions(tasks: list[dict], weekly_capacity: float = 40.0) -> dict:
    """Sum estimated hours of open tasks by ISO week of their deadline; flag weeks over
    capacity. This is the cross-project overload Etienne can't see in a flat agenda."""
    load: dict = {}
    for t in tasks:
        if t.get("status") == "done":
            continue
        wk = _iso_week(t.get("due_date"))
        if not wk:
            continue
        load[wk] = load.get(wk, 0.0) + float(t.get("estimate_hours") or 0)
    overloaded = sorted(
        [{"week": w, "hours": round(h, 1), "over": round(h - weekly_capacity, 1)} for w, h in load.items() if h > weekly_capacity],
        key=lambda x: x["week"],
    )
    return {"weekly_capacity": weekly_capacity, "by_week": {w: round(h, 1) for w, h in sorted(load.items())}, "overloaded": overloaded}
