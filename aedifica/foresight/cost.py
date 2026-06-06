"""W12.A — atelier-complexity coefficient for SIA 102 estimates (deterministic).

The SIA 102 method is already implemented in `aedifica.api.actions.estimate`.
Foresight only proposes a *factor*: a ratio derived from the atelier's
archived projects (status='archived' with a real cost on file vs SIA estimate).

Doctrine: we never overwrite the SIA 102 base — we *propose* multiplying it
by a confidence-weighted factor that the architect accepts/refuses.
"""
from __future__ import annotations

import statistics


def _cost_pair(p) -> tuple[float, float] | None:
    """Extract (estimate_chf, final_chf) from a project's cost_inputs JSON if present.
    Returns None if either side is missing — we never fabricate a missing actual."""
    ci = p.cost_inputs or {}
    est = ci.get("estimate_chf") or ci.get("estimate")
    fin = ci.get("final_chf") or ci.get("actual_chf") or ci.get("actual")
    if not est or not fin:
        return None
    try:
        est = float(est); fin = float(fin)
    except (TypeError, ValueError):
        return None
    if est <= 0 or fin <= 0:
        return None
    return est, fin


def propose_cost_factor(session, project, *, min_archived: int = 3):
    from ..db import models as m  # noqa: WPS433
    others = (session.query(m.Project)
              .filter(m.Project.org_id == project.org_id,
                      m.Project.id != project.id).all())
    pairs: list[tuple[m.Project, float]] = []
    for p in others:
        cp = _cost_pair(p)
        if not cp:
            continue
        est, fin = cp
        pairs.append((p, fin / est))
    if len(pairs) < min_archived:
        return
    ratios = [r for _, r in pairs]
    factor = round(statistics.median(ratios), 2)
    if abs(factor - 1.0) < 0.05:
        return  # within noise — don't propose
    direction = "majorer" if factor > 1.0 else "minorer"
    yield {
        "kind": "cost_factor",
        "title": f"{direction.capitalize()} l'estimation SIA 102 d'un coefficient atelier de {factor}×",
        "detail": (
            f"L'atelier a {len(pairs)} projets clos avec un ratio médian "
            f"coût-final / estimation SIA de {factor}. Cela suggère que vos "
            f"projets {direction} systématiquement la base SIA."
        ),
        "basis": [{"source_kind": "project", "source_id": p.id,
                   "ref": f"{p.name or p.project_id} : ratio réel/estimé = ×{r:.2f}"}
                  for p, r in pairs[:8]],
        "confidence": round(min(1.0, len(pairs) / 8.0), 2),
        "apply_payload": {
            "kind": "advisory",
            "factor": factor,
            "note": "À appliquer côté Coûts comme coefficient d'atelier sur la base SIA 102.",
        },
    }
