# Aedifica — Strategy & Deep-Dive

This folder is a **constructive challenge** ("esprit édifiant" — _aedificare_, to build up) of the
Aedifica foundations. It does not replace [`docs/vision.md`](../vision.md); it pressure-tests it,
re-anchors it in the real, holistic work of a Swiss architect, grounds it in fresh sourced research,
and proposes additions. Treat every claim here as a **proposal for discussion**, not a settled fact.

## The essence, in one paragraph

> Aedifica is a **continuously-maintained, multilingual, parcel-/commune-/canton-/federal-aware
> regulatory-and-project-intelligence layer** that carries a **continuous project memory** across the
> full SIA lifecycle, anchored on Switzerland's *binding machine-readable registries* (fedlex,
> geo.admin.ch, the 26 cantonal geoportals, the RDPPF/ÖREB cadastre and the registre foncier).
> It assists the architect's **fiduciary, coordinative, economic, regulatory and liability**
> responsibilities, including drawing/model assistance when the workflow calls for it. Software/BIM automation
> is a native *approved action layer*, never the whole product and never an unverified assumption. The product is
> **a neutral engine + pluggable jurisdiction packs + universal architecture API**; Switzerland
> is the first, deepest pack — which is exactly what makes the system both internationalizable *and*
> defensible.

## Why this re-framing

The original framing leads with **"Swiss Auto-BIM"** as the validation track. Fresh research says that
is the wrong flagship for the stated target (small/mid offices), for three sourced reasons:

1. **Those offices are not BIM-mature.** ~35 % are BIM users; the national market sits at **Stage 2 of 4**;
   construction's digital-readiness scored **18 %**. Most work in 2D CAD + lightweight 3D. Auto-BIM
   presupposes a structured model they do not have.
2. **BIM in Switzerland is contractual, not legal.** The cahier technique **SIA 2051 was withdrawn / put
   under revision**. Presenting BIM as a Swiss "standard/expectation" is a factual misframe.
3. **The architect's real pains are money and risk** — fee erosion, permit/opposition risk, coordination
   liability, cost control — concentrated in SIA phases **32 / 41 / 52**, not in missing IFC properties.

So the first wedge moves to **bottom-up, registry-anchored regulatory + permit + cost intelligence that needs
no BIM model**. Auto-BIM, model intelligence and controlled drawing assistance remain a native parallel product
track, scheduled after the first proof points rather than removed from scope.

## Reading order

1. [`architect-reality.md`](architect-reality.md) — what an architect *actually* does, holistically, from
   intake to handover; the corrected SIA phase model; the economic, contractual, coordination and
   liability layers a "BIM/metadata" framing misses.
2. [`swiss-regulatory-stack.md`](swiss-regulatory-stack.md) — the federal → cantonal → communal → parcel
   constraint stack; federalism as the moat; the binding data substrate to integrate; multilingual reality.
3. [`challenge-and-brainstorm.md`](challenge-and-brainstorm.md) — **the centerpiece**: challenges to the
   vision and to the issue list, the wedge debate, new feature proposals, the generalizable
   engine-plus-jurisdiction-pack architecture, and a proposed revised MVP sequence.
4. [`phase-value-catalog.md`](phase-value-catalog.md) — **the pitch artifact**: for every SIA phase, what the
   architect does and the concrete agentic quick-win to *show*, tagged no-BIM/BIM and demo-ability.
5. [`knowledge-architecture.md`](knowledge-architecture.md) — composable corpus + per-project selectors
   ("regulatory route"), capitalizable commune layer, and project-as-context vs RAG.
6. [`decisions.md`](decisions.md) — ADR-style log of settled strategic forks (wedge, pilot, cold-start, knowledge arch).
7. [`poc-lausanne-parcel.md`](poc-lausanne-parcel.md) — **real, executed proof**: binding constraints for a Lausanne parcel from free Swiss APIs (validates the MVP1 pipeline).
8. [`../specs/mvp1-parcel-constraints-intake.md`](../specs/mvp1-parcel-constraints-intake.md) — implementation-ready MVP1 spec.
9. [`../pitch/aedifica-one-pager.html`](../pitch/aedifica-one-pager.html) — the viewport-fit visual one-pager (FR) to show the partner office.
10. [`../design-system/aedifica-brand-book.html`](../design-system/aedifica-brand-book.html) — the Datum brand book: identity defense, fracture, tokens, design system and surface rules.

## Relationship to the rest of the repo

- **Corrections already spotted** (issue hygiene, missing domains, doc inconsistencies) live in
  [`../review/foundations-audit.md`](../review/foundations-audit.md) — a separate living tracker, so the
  "to-fix" list does not get lost while we think.
- The existing foundation docs ([`../vision.md`](../vision.md), [`../product/holistic-assistance.md`](../product/holistic-assistance.md),
  [`../research/`](../research/), [`../architecture/`](../architecture/), [`../nomos/nomos-archi.md`](../nomos/nomos-archi.md),
  [`../mvp-roadmap.md`](../mvp-roadmap.md)) remain the baseline this folder challenges.

_Status: brainstorm for discussion. Last updated 2026-05-29._
