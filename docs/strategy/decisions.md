# Decisions Log

Lightweight ADR-style record of strategic forks the owner has settled, so the rationale is traceable
(and so the project itself practices the decisional-traceability principle it sells). Newest first.

---

## D-005 — Pitch narrative: holistic per-phase value, not voice-to-design

**Date:** 2026-05-29 · **Status:** Accepted

The story for the partner office (and any architect): *"talk to an AI that draws the building"* is seductive but
~5 % of the value; the real value is **holistic support at every SIA phase, from first document to final
handover.** Deliverable to prove it: a **per-phase value catalog** with concrete, demonstrable quick-wins →
[`phase-value-catalog.md`](phase-value-catalog.md).

## D-004 — Knowledge architecture: composable corpus + selectors; project-as-context

**Date:** 2026-05-29 · **Status:** Accepted

One **layered, versioned, shared** knowledge base (General Swiss RAG · Federal core · Canton overlay · Commune
overlay). Each project activates only `Federal + its canton + its commune` via a **selector ("regulatory
route")** — no per-project corpus rebuild. The **commune layer is capitalizable/refreshable** across projects.
**Project knowledge is context-first (repo-like) for small projects**, a dedicated RAG only for large ones
(economic gate; threshold TBD). Details → [`knowledge-architecture.md`](knowledge-architecture.md).

## D-003 — Cold-start posture: hybrid (on-demand + seed corpus)

**Date:** 2026-05-29 · **Status:** Accepted

On-demand ingestion of any commune's règlement, **plus** a robust **seed corpus** for the pilot:
**Federal + Canton de Vaud + Ville de Lausanne** (a deliberately particular commune that stress-tests the model).
Anchored on binding registries (RDPPF/ÖREB, Géoportail VD, swisstopo GeoAdmin API, fedlex).

## D-002 — Pilot jurisdiction: Vaud / Lausanne (FR first)

**Date:** 2026-05-29 · **Status:** Accepted

Go deep on **Canton de Vaud + Ville de Lausanne** first; French as the first language. Fixes the first
3-level regulatory slice and the first language pack.

## D-001 — Wedge: hybrid (regulatory/canonical spine + Archicad/BIM thread)

**Date:** 2026-05-29 · **Status:** Accepted

**Context:** a real architecture office using **Archicad/BIM** is the first design partner & pilot user.
**Decision:** lead with **canonical-first + regulatory/permit/cost intelligence** (registry-anchored, no model
required) **and** keep a live **Auto-BIM/Archicad thread** for the partner's current tools.
**Constraint (hard):** the product must stay **generalizable** — *not* Archicad-locked, *not* a mere drawing
tool; the partner office is the first user, not the product's identity.
**Consequence:** two tracks over one shared engine + jurisdiction packs (see
[`challenge-and-brainstorm.md`](challenge-and-brainstorm.md) §E); the revised MVP sequence (§F) leads with the
no-BIM regulatory wedge while the Archicad thread targets phase 32 (Auto-BIM) for demos.
