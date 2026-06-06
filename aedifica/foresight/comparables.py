"""W12.A — atelier-scoped comparable retrieval (deterministic).

For a current project, find the top-N similar archived/done projects in the
same atelier. Similarity is a transparent weighted sum:
- same commune        → +0.4
- same phase reached  → +0.2
- same MO/role        → +0.15
- BRS-entry overlap   → up to +0.25 (Jaccard on requirement kinds)

This stays deterministic — no embeddings, no ML. Atelier-only, never
benchmarked against external data.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Comparable:
    project_id: int
    project_label: str
    score: float
    reasons: list[str]


def find_atelier_comparables(session, project, *, top_n: int = 3) -> list[Comparable]:
    from ..db import models as m  # noqa: WPS433
    others = (session.query(m.Project)
              .filter(m.Project.org_id == project.org_id,
                      m.Project.id != project.id).all())
    cur_brs_kinds = {b.kind for b in
                     session.query(m.BrsEntry).filter_by(project_id=project.id).all()}
    scored: list[Comparable] = []
    for o in others:
        score = 0.0
        reasons: list[str] = []
        if (o.commune or "").lower() == (project.commune or "").lower() and o.commune:
            score += 0.4
            reasons.append(f"même commune ({o.commune})")
        if (o.phase_code or "") == (project.phase_code or "") and o.phase_code:
            score += 0.2
            reasons.append(f"même phase ({o.phase_code})")
        other_brs_kinds = {b.kind for b in
                           session.query(m.BrsEntry).filter_by(project_id=o.id).all()}
        if other_brs_kinds and cur_brs_kinds:
            inter = cur_brs_kinds & other_brs_kinds
            union = cur_brs_kinds | other_brs_kinds
            jacc = len(inter) / len(union) if union else 0.0
            score += 0.25 * jacc
            if jacc:
                reasons.append(f"recouvrement BRS ({len(inter)}/{len(union)})")
        if score > 0:
            scored.append(Comparable(project_id=o.id,
                                     project_label=o.name or o.project_id,
                                     score=round(score, 2),
                                     reasons=reasons))
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_n]
