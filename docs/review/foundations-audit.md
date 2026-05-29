# Foundations Audit — Findings & Corrections

> **Living document.** It collects, in one place, everything spotted as "to fix / to decide"
> while auditing the Aedifica foundations, so nothing gets lost before we act on the issues.
> It is intentionally separate from the deep strategy/brainstorm work (see
> [`docs/strategy/`](../strategy/)). Add to it; mark items resolved with a date; do not delete.

**Last updated:** 2026-05-29
**Scope of audit:** the 11 foundation docs + the 21 GitHub issues, as of commit `fa7a7b8`.

## Status legend

- `OPEN` — spotted, not yet acted on.
- `DECIDE` — needs a human/product decision before it can be corrected.
- `DONE` — corrected (add date + commit/PR).

---

## A. Backlog & issue hygiene

| # | Finding | Suggested correction | Status |
|---|---|---|---|
| A1 | The 21 issues are a **flat list with no priority labels** (no P0–P3). The MVP roadmap defines a recommended sequence, but nothing on the issues reflects it. | Add priority labels and order by the critical path (see A3). | OPEN |
| A2 | **No milestones.** MVP0→MVP4 exist in docs but not as GitHub milestones, so progress can't be tracked against the roadmap. | Create milestones `MVP0 Foundation`…`MVP4 Direction Travaux` + `Later tracks`; assign issues. | OPEN |
| A3 | **Inter-issue dependencies are undeclared.** Real critical path: `#1, #3 → #6 → #8 → #15` and `#12 → #11/#13 → #16`. A reader can't see what blocks what. | Declare dependencies (task lists / "blocked by" notes) and surface the first wave (`#1, #3, #6`). | OPEN |
| A4 | **Issue #21 (holistic assistance model) is largely already realized** by [`holistic-assistance.md`](../product/holistic-assistance.md). | Redefine #21 as "formalize/validate the holistic model against the deep-dive" or close it. | DECIDE |
| A5 | Issues mirror the backlog **1:1 but with wording drift** (e.g. #5 backlog says "logiciels suisses/romands" → issue says "outils suisses"; #12 wording expanded). | Decide whether the backlog file or GitHub is the source of truth; reconcile once. | DECIDE |

## B. Repository hygiene

| # | Finding | Suggested correction | Status |
|---|---|---|---|
| B1 | **No `LICENSE`.** Concept docs are unlicensed; ambiguous for any future contributor/code. | Choose and add a license (or an explicit "all rights reserved" notice for now). | DECIDE |
| B2 | **No `CONTRIBUTING.md`, issue/PR templates, `CODEOWNERS`.** The repo is meant to receive code and structured issues. | Add `.github/` templates + a short CONTRIBUTING once the workflow is set. | OPEN |
| B3 | **No language policy.** Vision docs are in English; backlog/issues are in French. | Decide a convention (proposal: English for durable docs/code to support internationalization; French OK for issues/discussion). | DECIDE |
| B4 | **No technical-stack decision record.** `#6` (NOMOS schema), `#7` (RAG), `#12` (API/MCP) will all stall without one. | ADR added for the neutral engine + jurisdiction-pack split; storage/RAG implementation choices remain future work. | DONE 2026-05-29 (`docs/architecture/adr-0001-neutral-engine-and-jurisdiction-packs.md`) |

## C. Documentation consistency

| # | Finding | Suggested correction | Status |
|---|---|---|---|
| C1 | [`sources.md`](../research/sources.md) uses some **generic/placeholder URLs** (e.g. `shop.sia.ch` root, a `testshop` link) — yet the file's own rule asks every source to be classified by jurisdiction, phase, reliability, version. | Replace with precise, citable sources; add the jurisdiction/phase/version/allowed-use columns the file itself prescribes. | OPEN |
| C2 | **SIA phase codes are imprecise** across docs (e.g. "31 preliminary project", "3.2 Project", phase 4 split in three). Verified canonical numbering now exists. | Reconcile everything to the verified table in [`../strategy/architect-reality.md`](../strategy/architect-reality.md) §3 (incl. the SIA 102:2024/2026 Phase-0 + 41/42 variant). | OPEN |
| C3 | The phase-agentic matrix already names a concrete next step ("Issue #1 should turn this into a more exhaustive Swiss phase matrix") — **good**, but it isn't linked from issue #1. | Cross-link the doc and the issue. | OPEN |
| C4 | **BIM framing is factually outdated.** Docs cite "SIA 2051 / openBIM expectations" as a Swiss standard, but **SIA 2051 is a cahier technique, withdrawn / under revision**; BIM in CH is **contractual, not legal**. | Re-frame BIM as an optional project convention (SIA 102 art. 2.7); move real compliance weight to energy/fire (AEAI = binding)/accessibility/seismic. See [`../strategy/architect-reality.md`](../strategy/architect-reality.md) §5. | OPEN |
| C5 | Docs lead with **"Swiss Auto-BIM"** as the validation track, but the target small/mid offices are **not BIM-mature** (~35 % BIM, market Stage 2/4, 18 % digital readiness). | Re-prioritize toward registry-anchored, no-BIM-required intelligence. See [`../strategy/challenge-and-brainstorm.md`](../strategy/challenge-and-brainstorm.md) §B1, §F. | OPEN |

## D. Coverage gaps — domains the foundations under-weight

These are whole areas of the *real* architect's job that are thin or absent in the current
vision/issues. Each is a candidate new issue (to be confirmed by the deep-dive).

| # | Missing domain | Why it matters (Swiss reality) | Status |
|---|---|---|---|
| D1 | **Fees / honoraires (SIA)** | Fee erosion & profitability are an existential pain; the product touches money only via "tendering". | OPEN |
| D2 | **Cost classification CFC / eCCC-Bât (eBKP)** | Devis, soumissions, adjudication all run on CFC/eCCC; barely referenced. | OPEN |
| D3 | **Oppositions & mise à l'enquête publique** | The single biggest schedule risk in CH permitting; not modeled as a first-class risk object. | OPEN |
| D4 | **Contracts & liability (SIA 102/118, RC, garanties)** | The architect is legally liable; an AI proposing regulatory reads needs a crisp trust/disclaimer stance. | OPEN |
| D5 | **Energy / sustainability (CECB/GEAK, MoPEC/MuKEn, SIA 380/1, Minergie)** | Mandatory cantonal energy compliance; currently absent. | OPEN |
| D6 | **Multilingualism FR/DE/IT** | Canonical rules must be language-neutral with localized renderings; not addressed. | OPEN |
| D7 | **Generalizable core vs Swiss "jurisdiction pack" architecture** | Captured in ADR-0001: neutral engine, jurisdiction packs, SIA phase model as pack data, adapters behind a shared lifecycle. | DONE 2026-05-29 |
| D8 | **Regulatory-corpus data-acquisition strategy** | ~2100 communes each with their own RCCZ/PGA — the real bottleneck for NOMOS; no strategy issue. | OPEN |
| D9 | **Business model / "who pays" & pricing** | Determines which wedge to build first; absent. | OPEN |
| D10 | **Competitive landscape** | Messerli/Sorba/Abacus, Archilyse, PlanRadar, CRB/NPK, etc. — no positioning issue. | OPEN |
| D11 | **Consultant coordination as a workflow** | Architect = coordinator of civil/MEP/géomètre/etc.; treated only implicitly. | OPEN |

## E. Strategic open questions (resolved in the deep-dive)

- **E1 — The wedge.** Most *defensible* first product (NOMOS constraints/project memory) vs most *measurable* first value (Auto-BIM) vs most *economically painful* (fees/cost/oppositions). Which wedge first?
- **E2 — Target/feature fit.** Small/mid offices are the stated target but are often *not* BIM-mature; does leading with "Auto-BIM" (MVP2) fit them?
- **E3 — Cold start.** Pre-build a CH regulatory corpus vs ingest each commune's documents on demand (RAG + extraction)? This changes feasibility entirely.
- **E4 — Trust contract.** How to be useful on regulation without assuming the architect's legal liability.

## Change log

- 2026-05-29 — Initial audit created from foundation review (commit `fa7a7b8`).
- 2026-05-29 — Added C4 (BIM framing outdated / SIA 2051 withdrawn) and C5 (Auto-BIM vs target BIM-maturity) after fresh sourced research; linked C2 to the verified SIA phase table. See [`../strategy/`](../strategy/).
- 2026-05-29 — Added ADR-0001, NOMOS schema v0, and trust ledger contract; marked B4 and D7 done.
