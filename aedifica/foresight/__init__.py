"""Foresight — the predictive / suggestive layer over the operational stack.

Doctrine (non-negotiable):
- The IA proposes, the architect decides. Every output is a Proposal that must
  be explicitly accepted / deferred / refused before anything mutates.
- Sourced or unknown — never invented. A prediction without enough data says
  "données insuffisantes" instead of fabricating a number.
- Operational layer stays pur-soft: Foresight is additional, never a prereq.
- Local-first: confidential content stays on the machine; cloud LLM is opt-in
  per project and excludes anything marked confidential=True.
- Everything is traced: each Proposal lists basis (named sources), confidence
  (0..1, derived not vibed), and apply_payload (what would be written).

W12.A is deterministic: duration / cost / risk / comparables / suggest.
W12.B wires the surface. W12.C adds the opt-in LLM. W12.D smartens next_step.
W12.E captures the learning loop. W12.F enforces explainability.
"""
from .engine import compute_proposals, thresholds, ForesightSummary  # noqa: F401
