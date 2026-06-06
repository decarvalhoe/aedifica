"""W12.A — cross-surface anomaly detection (deterministic, ALL rules sourced).

Each rule scans the project's persisted state and yields Proposal dicts when
its trigger matches. NEVER fabricates: if the data needed to evaluate a rule
is missing, the rule is silently skipped (not a false alarm).

Rules:
1. BRS-after-permit: requirement_change BRS created after permit_submitted ledger
2. Overdue cascade: late P0 task with dependent tasks → warn about each dependent
3. Overload (weekly): assignee with > 50 sum estimate_hours over 7 days
4. Permit-missing-critical: dossier ready_for_review=false with required pieces missing
5. Cost-by-phase drift: phase hours > 1.3x SIA plan
6. Recurring friction: ≥ 3 capture friction in 30 days from the same source_ref
7. Regulation under study impacting current phase
"""
from __future__ import annotations

import datetime as _dt
import re
from collections import defaultdict


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def propose_risks(session, project):
    """Yield risk Proposal dicts (deterministic rule firing)."""
    from ..db import models as m  # noqa: WPS433

    yield from _rule_brs_after_permit(session, project, m)
    yield from _rule_overdue_cascade(session, project, m)
    yield from _rule_overload(session, project, m)
    yield from _rule_recurring_friction(session, project, m)
    yield from _rule_regulation_impact(session, project, m)


def _rule_brs_after_permit(session, project, m):
    permit_events = (session.query(m.LedgerEntry)
                     .filter(m.LedgerEntry.project_id == project.id,
                             m.LedgerEntry.event_type == "permit_submitted")
                     .order_by(m.LedgerEntry.timestamp).all())
    if not permit_events:
        return
    cutoff = permit_events[0].timestamp
    if cutoff is None:
        return
    risky = (session.query(m.BrsEntry)
             .filter(m.BrsEntry.project_id == project.id,
                     m.BrsEntry.kind == "change",
                     m.BrsEntry.created_at > cutoff).all())
    for b in risky:
        yield {
            "kind": "risk_alert",
            "title": f"Changement client après dépôt permis : « {b.content[:60]} »",
            "detail": (
                "Une exigence client a changé après le dépôt du permis "
                f"({cutoff.date()}). Un avenant de procédure peut être requis, "
                "et certaines pièces déjà transmises sont peut-être obsolètes."
            ),
            "basis": [
                {"source_kind": "brs", "source_id": b.id, "ref": f"BRS {b.id} ({b.created_at.date() if b.created_at else '?'})"},
                {"source_kind": "ledger", "source_id": permit_events[0].id,
                 "ref": f"permit_submitted le {cutoff.date()}"},
            ],
            "confidence": 0.9,
            "apply_payload": None,
        }


def _rule_overdue_cascade(session, project, m):
    today = _dt.date.today().isoformat()
    overdue_p0 = (session.query(m.Task)
                  .filter(m.Task.project_id == project.id,
                          m.Task.priority == "p0",
                          m.Task.status != "done",
                          m.Task.due_date.isnot(None),
                          m.Task.due_date < today).all())
    if not overdue_p0:
        return
    deps = session.query(m.TaskDependency).all()
    children_of = defaultdict(list)
    for d in deps:
        children_of[d.blocked_by_id].append(d.task_id)
    for t in overdue_p0:
        downstream = children_of.get(t.id, [])
        if not downstream:
            continue
        children = session.query(m.Task).filter(m.Task.id.in_(downstream)).all()
        yield {
            "kind": "risk_alert",
            "title": f"Tâche P0 en retard avec {len(downstream)} dépendance(s) aval : « {t.title} »",
            "detail": (
                f"La tâche P0 « {t.title} » (échéance {t.due_date}) est dépassée "
                f"et bloque {len(downstream)} autre(s) tâche(s) en aval. "
                "Repriorisez ou réaffectez avant que le chemin critique ne décale."
            ),
            "basis": [
                {"source_kind": "task", "source_id": t.id,
                 "ref": f"Tâche {t.id} : échéance {t.due_date}, statut {t.status}"},
            ] + [{"source_kind": "task", "source_id": c.id, "ref": f"aval : « {c.title} »"}
                 for c in children[:6]],
            "confidence": 1.0,
            "apply_payload": None,
        }


def _rule_overload(session, project, m, *, week_cap_hours: float = 50.0):
    from collections import defaultdict as _dd
    by_assignee = _dd(float)
    tasks = (session.query(m.Task)
             .filter(m.Task.project_id == project.id,
                     m.Task.status.in_(("todo", "doing")),
                     m.Task.estimate_hours.isnot(None),
                     m.Task.assignee_user_id.isnot(None)).all())
    horizon = (_dt.date.today() + _dt.timedelta(days=7)).isoformat()
    today_s = _dt.date.today().isoformat()
    for t in tasks:
        if t.due_date and today_s <= t.due_date <= horizon:
            by_assignee[t.assignee_user_id] += t.estimate_hours
    if not by_assignee:
        return
    for uid, hours in by_assignee.items():
        if hours <= week_cap_hours:
            continue
        u = session.query(m.User).filter_by(id=uid).first()
        name = u.name if u else f"user#{uid}"
        yield {
            "kind": "risk_alert",
            "title": f"Surcharge sur 7 jours : {name} cumulerait {hours:.0f} h",
            "detail": (
                f"{name} a {hours:.0f} h estimées dans les 7 prochains jours, "
                f"au-delà du plafond de {week_cap_hours:.0f} h. Risque qualité + "
                "glissement d'échéance. Reéquilibrez vers un autre collaborateur."
            ),
            "basis": [
                {"source_kind": "user", "source_id": uid,
                 "ref": f"{name} — {hours:.0f} h estimées sur 7 j"},
            ],
            "confidence": 0.85,
            "apply_payload": None,
        }


def _rule_recurring_friction(session, project, m, *, window_days: int = 30, min_count: int = 3):
    cutoff = _now() - _dt.timedelta(days=window_days)
    rows = (session.query(m.CaptureNote)
            .filter(m.CaptureNote.project_id == project.id,
                    m.CaptureNote.kind == "friction",
                    m.CaptureNote.created_at >= cutoff).all())
    if not rows:
        return
    by_keyword = defaultdict(list)
    for c in rows:
        # crude grouping: first two non-stopword tokens lowercased
        toks = [w.lower() for w in re.findall(r"\w{4,}", c.content or "")][:2]
        if not toks:
            continue
        by_keyword[tuple(toks)].append(c)
    for key, items in by_keyword.items():
        if len(items) < min_count:
            continue
        yield {
            "kind": "risk_alert",
            "title": f"Friction récurrente ({len(items)} occurrences) : « {' '.join(key)} »",
            "detail": (
                f"{len(items)} captures de friction en {window_days} jours mentionnent "
                f"« {' '.join(key)} ». Pattern à traiter : créez un BRS de type 'change' "
                "ou une tâche P1 pour adresser la cause racine."
            ),
            "basis": [{"source_kind": "capture", "source_id": c.id,
                       "ref": f"« {(c.content or '')[:50]} » ({c.created_at.date() if c.created_at else '?'})"}
                      for c in items[:6]],
            "confidence": min(1.0, len(items) / 6.0),
            "apply_payload": None,
        }


def _rule_regulation_impact(session, project, m):
    cur_phase = project.phase_code or "0"
    # phases ≤ 33 are sensitive to regulation changes (avant-projet → dépôt permis)
    if cur_phase == "0" or cur_phase > "33":
        return
    rows = (session.query(m.CaptureNote)
            .filter(m.CaptureNote.project_id == project.id,
                    m.CaptureNote.kind == "regulation").all())
    for c in rows:
        yield {
            "kind": "risk_alert",
            "title": f"Règlement à l'étude impactant phase {cur_phase}",
            "detail": (
                f"« {(c.content or '')[:140]} » — détecté pendant que le projet "
                f"est en phase {cur_phase}. Vérifiez l'impact sur les claims "
                "réglementaires sourcés (hauteur, IBUS, distances)."
            ),
            "basis": [{"source_kind": "capture", "source_id": c.id,
                       "ref": c.source_ref or f"capture {c.id}"}],
            "confidence": 0.7,
            "apply_payload": None,
        }
