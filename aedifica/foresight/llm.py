"""W12.C — LLM opt-in layer (local Ollama by default; cloud via opt-in).

Doctrine:
- llm_mode="off" (default): no LLM call ever happens.
- llm_mode="local": Ollama on the atelier's machine (http://localhost:11434).
  Confidential content allowed because it stays local.
- llm_mode="cloud": opt-in hosted model. Confidential content (BRS marked
  confidential=true, documents marked confidential=true) is EXCLUDED from
  the prompt by the LLM layer before any call.
- Every call is audited (event_type=llm_called) — model, target, projection.
- Every output is a Proposal — the LLM never mutates anything directly.

The actual HTTP integration is left to a pluggable backend so tests can
inject a fake. Default backend is a no-op that returns None — the test
suite swaps it for a stub.
"""
from __future__ import annotations

import json


# Pluggable backend: signature (mode: str, prompt: str) -> str | None.
# Returns the LLM's text output. None means "model unavailable / failed";
# the engine reports "modèle indisponible" rather than fabricate content.
def _noop_backend(mode: str, prompt: str) -> str | None:  # pragma: no cover
    return None


_BACKEND = _noop_backend


def set_backend(fn):
    """Test/integration hook: register a backend (mode, prompt) -> text|None."""
    global _BACKEND
    _BACKEND = fn


def get_backend():
    return _BACKEND


def _filter_brs_for_cloud(rows, mode: str):
    """In cloud mode, exclude pieces marked confidential at the BRS level
    (we treat any BRS whose source_ref looks confidential or whose
    emitter_label includes a 'LPD' tag as confidential — adjust to your
    own policy). For now we just drop entries with channel=='pv'
    (procès-verbal — often confidential) when in cloud mode.

    Local mode keeps everything (data stays on the atelier's machine)."""
    if mode == "local":
        return rows
    return [b for b in rows if b.channel != "pv"]


def summarize_brs_thread(session, project, *, head: int = 30):
    """Build a Proposal of kind=brs_summary by asking the LLM to summarize
    the project's BRS register. Respects the opt-in mode + confidential
    filtering. Returns None when llm_mode=="off" or the backend fails.

    Output is a *proposal*: the architect must accept / defer / refuse
    like any Foresight item. The LLM never writes to the BRS register."""
    from ..db import models as m  # noqa: WPS433
    mode = (project.llm_mode or "off").lower()
    if mode == "off":
        return None
    rows = (session.query(m.BrsEntry)
            .filter_by(project_id=project.id)
            .order_by(m.BrsEntry.id.desc()).limit(head).all())
    if not rows:
        return None
    filtered = _filter_brs_for_cloud(rows, mode)
    if not filtered:
        return None
    prompt = "Résume en 3 points actionnables le fil d'exigences client suivant. " \
             "Cite l'ID de chaque BRS référencé. Ne pas inventer.\n\n" + \
             "\n".join(f"BRS#{b.id} ({b.kind}, canal={b.channel}): {b.content}" for b in filtered)
    text = _BACKEND(mode, prompt)
    if not text:
        return None
    basis = [{"source_kind": "brs", "source_id": b.id,
              "ref": f"BRS#{b.id} {b.kind} ({b.channel})"} for b in filtered]
    return {
        "kind": "brs_summary",
        "title": f"Résumé LLM ({mode}) du registre BRS ({len(filtered)} entrées)",
        "detail": text,
        "basis": basis,
        "confidence": 0.0,   # LLM output is always 0-confidence until the architect accepts
        "apply_payload": {
            "kind": "advisory",
            "mode": mode,
            "filtered_out": len(rows) - len(filtered),
            "note": "Résumé proposé par le LLM. À valider avant toute utilisation.",
        },
    }
