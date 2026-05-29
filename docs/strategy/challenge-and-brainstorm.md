# Challenge & Brainstorm — Pressure-Testing Aedifica

> The centerpiece of this folder. It challenges the current vision and issue list at three levels, resolves
> the open strategic questions, proposes new capabilities, and lays out a generalizable engine + jurisdiction-pack
> architecture. Grounded in [`architect-reality.md`](architect-reality.md) and
> [`swiss-regulatory-stack.md`](swiss-regulatory-stack.md). Everything is a **proposal to argue with**.

---

## A. The essence, restated

Aedifica is **not** an Archicad copilot, a drawing automator, or a generic RAG chatbot. Its essence:

> A **continuously-maintained, multilingual regulatory + project-intelligence layer** that turns a parcel +
> a program + the binding Swiss registries into **sourced, phase-aware project knowledge**, carries that
> knowledge as **continuous project memory** across the whole SIA mandate, and assists the architect's
> **fiduciary, coordinative, economic, regulatory and liability** work — proposing, citing, and logging,
> with a human always accountable. Software/BIM action is a downstream, optional layer.

The Latin _aedificare_ ("to build up / edify") is the right north star: Aedifica **builds up the project's
knowledge and protects the architect**, before it ever touches geometry.

---

## B. Challenges to the vision (three levels)

### Level 1 — Framing & positioning

**B1. "Auto-BIM" is the wrong flagship for the stated target.**
The vision names *Swiss Auto-BIM* as the strong validation track and MVP2. But the target (small/mid offices)
is **not BIM-mature**: ~35 % BIM users, national market at **Stage 2/4**, construction digital-readiness **18 %**;
most work in 2D CAD + lightweight 3D. Auto-BIM presupposes a structured model they don't have.
→ **Reframe:** the entry wedge is **structure-from-unstructured** (PDF/DWG/program → structured, sourced project
knowledge) and **regulatory/permit/cost intelligence**. Auto-BIM becomes a *later* capability for the BIM-mature minority.

**B2. The vision over-indexes on the model, under-indexes on money and risk.**
The architect's existential pains are **fee erosion, permit/opposition risk, coordination liability, cost
control** — concentrated in phases **32 / 41 / 52**. Missing IFC properties is a symptom, not the disease.
→ Hook the product where money and legal risk live.

**B3. The BIM framing is factually outdated.**
"SIA 2051 / openBIM expectations" appears as a Swiss standard. **SIA 2051 is a cahier technique, withdrawn /
under revision; BIM in CH is contractual, not legal.** Keep this and a Swiss architect distrusts the product on
contact.
→ Present BIM as an *optional project convention* (SIA 102 art. 2.7). The real compliance gates are
**energy (380/1), fire (AEAI — binding cantonal law), accessibility (SIA 500/LHand), seismic (261)**.

**B4. "9 assistance layers" is comprehensive but undifferentiated.**
It reads as "do everything", with no named wedge and no stated data moat.
→ Name one wedge that compounds into a moat (see §D, §C).

### Level 2 — Strategy & architecture

**B5. The cold-start corpus problem is the real bottleneck — and it's unaddressed.**
~2,100 communes × own règlement. You cannot pre-build Switzerland.
→ **Flip feasibility:** anchor on the **binding machine-readable substrate that already exists** (RDPPF/ÖREB +
geodienste zoning + swisstopo GeoAdmin API + fedlex), and **ingest each commune's règlement on demand**
(RAG + extraction) rather than pre-modeling all rules. Make *data-acquisition strategy* a first-class workstream.

**B6. There is no generalizable-core / jurisdiction-pack separation** — which is explicitly wanted.
→ Propose a **neutral engine + pluggable jurisdiction packs** (see §E). Internationalization = add a pack.

**B7. Multilingualism is treated as localization, but it's core ontology.**
FR/DE/IT legal terms are non-cognate, and appeal *bodies/procedures* differ.
→ Canonical units must be language-neutral with localized renderings + adoption-state tracking per canton.

**B8. Trust/liability is stated as a principle but must be a hard product contract.**
The architect is legally liable; **failed coordination is an RC fault**. An AI "proposing" regulatory reads
creates liability ambiguity.
→ Define an **evidence/trust contract** (every claim sourced to an official document with article + version +
valid-as-of date, or flagged as assumption; the system is a *preparation & evidence* tool, never an authority)
and a **decisional-traceability ledger** as a *core*, because that is what actually protects the architect.

### Level 3 — Coherence

**B9.** The vision is internally consistent and well-written — its weakness is **altitude, not contradiction**:
it describes the whole elephant without committing to where to bite first or what compounds. The fixes above are
about *focus and grounding*, not rewriting the thesis.

---

## C. Challenges to the issue list

(See the line-by-line tracker in [`../review/foundations-audit.md`](../review/foundations-audit.md). Summary here.)

- **Over-weighted on tool-automation/BIM.** 5 of 21 issues (#10–14) are CAD/BIM adapters; the economic,
  regulatory and permit core is comparatively thin.
- **Whole workstreams missing:** fees/honoraires, CFC/eCCC cost, **oppositions/mise à l'enquête as a first-class
  risk object**, contracts & liability (SIA 102/118), energy (CECB/MoPEC/380-1), multilingual FR/DE/IT, the
  **generalizable-core/jurisdiction-pack architecture**, the **regulatory-corpus data-acquisition strategy**,
  business model / who-pays, competitive positioning, consultant-coordination as a workflow.
- **#21 (holistic model) is largely already done** by [`../product/holistic-assistance.md`](../product/holistic-assistance.md) — redefine or close.
- **No priority, milestones, or dependencies** — the roadmap's recommended sequence isn't reflected.
- **Auto-BIM (MVP2) is likely mis-prioritized** for the target segment (see B1).

---

## D. New proposals (capabilities to add)

Ordered by signal. Each is anchored on real, free Swiss APIs and needs **no BIM model**.

**D1. Opposition / recours-risk radar — the highest-signal, novel, defensible feature.**
Opposition is the dominant project-killer (30-day enquiry, opposition window, then recours; neighbours within
standing distance can block for months/years). Combine parcel geometry + neighbour proximity + distances aux
limites / gabarits / hauteurs + ombres portées & vues + DS noise sensitivity + zone rules + historical
opposition patterns → **score opposition probability and likely legal grounds _before_ mise à l'enquête**, with
mitigation suggestions. **Nobody does this.** It hooks straight into the #1 schedule risk.

**D2. Parcel-to-envelope — "what can I legally build here?"**
On a parcel ID: pull RDPPF restrictions + communal zone + indices (IUS/IBUS/IOS) + distances + heights + DS +
servitudes (RF) → compute the **sourced legal buildable envelope**, every number linked to its instrument.
This is the vision's "project born from constraints" made concrete and API-anchored. Seeds the project memory.

**D3. SIA fee & profitability copilot.**
Model SIA 102 (legacy CDO formula *and* 2024 H = T × h), per-phase fee weighting, and **flag _prestations
spéciales_ currently absorbed unpaid** (durability/labels, BIM, staged execution). Couple with eBKP cost
benchmarks + office history. Directly attacks fee erosion — a pain no incumbent copilot addresses.

**D4. Cost-taxonomy bridge + soumission intelligence.**
Own the mapping **eCCC-Bât ↔ NPK/CAN ↔ CFC** and the **`.crbx` / IfA18** corpus: auto-select CAN positions,
flag missing/contradictory positions, reconcile métré ↔ eBKP ↔ NPK, compare bids. **Integrate with
Messerli/SORBA/Abacus, don't replace them.** A closed, machine-readable corpus is ideal agent terrain and a
CH-specific moat few global AEC-AI players have.

**D5. Permit-readiness & dossier assembler across fragmented cantonal rails.**
Canton-correct checklist (CAMAC vs eBau vs eBaugesucheZH), completeness pre-check, citation-backed
justifications, and verification of the energy/fire/accessibility/seismic gates. The government rails only
*receive*; **nobody pre-checks completeness**.

**D6. Continuous project memory — the durable product (and the moat).**
One queryable memory spanning plans, `.crbx` tenders, CAMAC correspondence, meeting decisions, defects
(PlanRadar), model versions — surviving every phase handoff and tool silo. "What changed since v3? Which source
justifies this? What's still undecided?" This is the architect's **institutional memory**; it compounds with use.

**D7. Decisional & contractual traceability ledger.**
Every recommendation/action logged with actor, source, basis, approval, before/after. Turns coordination (the
RC-risk center) into an auditable trail. This is the trust contract (B8) made operational — and a selling point
to the architect's *insurer*.

**D8. Multilingual canonical regulatory graph.**
Rules stored language-neutral, rendered FR/DE/IT, cross-referenced to the binding source with validity dates;
tracks AIHC/MoPEC **adoption state per canton**.

**D9. (Visionary, kept honest) Model-action layer — Auto-BIM, voice-to-design, direction de travaux.**
Retained as a *downstream, opt-in* capability for BIM-mature offices and later phases. Explicitly **not** the
wedge and **not** assuming a clean model.

---

## E. The generalizable architecture — neutral engine + jurisdiction packs

This is how Aedifica is **internationalizable *and* deeply Swiss at once**: a universal engine that knows the
*shape* of an architectural project, plus a Swiss pack that holds the *content*.

```
┌─────────────────────────────────────────────────────────────┐
│  NEUTRAL ENGINE  (universal — no jurisdiction knowledge)      │
│  • Ontology: Project · Site · Parcel · Building · Space ·     │
│    Element · Actor · Constraint · Requirement · Decision ·    │
│    Evidence · Deliverable · Check · Action                    │
│  • Phase-aware lifecycle state machine (phase model = a pack) │
│  • NOMOS canonical-unit schema: provenance + temporal         │
│    validity + verification method + language-neutral body     │
│  • Two-RAG separation (project vs general)                    │
│  • Evidence/trust contract + traceability ledger              │
│  • Universal MCP/API adapter interface (tool-neutral)         │
└───────────────▲───────────────────────────────▲──────────────┘
                │ implements                     │ implements
   ┌────────────┴───────────┐        ┌───────────┴───────────────┐
   │  JURISDICTION PACK: CH  │        │  (future) PACK: UK / DE /… │
   │  • Phase pack: SIA 112/ │        │  • RIBA Plan of Work /     │
   │    102 (+2026 variant)  │        │    HOAI Leistungsphasen    │
   │  • Reg. source map:     │        │  • local registries        │
   │    federal+cantonal+    │        │  • local cost taxonomy      │
   │    communal+parcel      │        │  • local language pack      │
   │  • Connectors: fedlex,  │        └────────────────────────────┘
   │    geo.admin, 26 geo-   │
   │    portals, RDPPF, simap,│   Internationalization = author a
   │    CAMAC/eBau           │   new pack. The ENGINE never changes.
   │  • Cost pack: CFC/eCCC/ │   The Swiss pack's DEPTH is the moat;
   │    NPK/.crbx (IfA18)    │   the engine's NEUTRALITY is the scale.
   │  • Norms: 380/1,500,261,│
   │    181,118; AEAI        │
   │  • Language pack FR/DE/IT│
   │  • Adoption-state table │
   └─────────────────────────┘
```

**Design rules that follow:**
- The **phase model is a pack**, not a hardcode (SIA for CH, RIBA for UK, HOAI for DE).
- Canonical units carry **temporal validity** ("valid as of date") because Swiss rules drift constantly.
- **AEAI/cantonal-binding rules are typed differently** from contractual SIA norms in the engine.
- Adapters (Archicad/Revit/IFC/Speckle/document/admin-software) sit **behind the universal MCP/API** so the
  core never depends on one vendor.

---

## F. Proposed revised MVP sequence (to argue with)

Reordered to lead with lowest-cold-start, highest-pain, no-BIM-required value:

| # | MVP | Core capability | Why first | Maps to issues |
|---|---|---|---|---|
| **0** | Foundation | Engine ontology + NOMOS schema + jurisdiction-pack skeleton + trust contract | Everything depends on it | #6, #7, #8, #9, +new (pack arch, data strategy) |
| **1** | **Parcel & Constraints Intake** | D2 envelope + D1 risk/unknowns brief, anchored on RDPPF/geodienste/swisstopo | Immediate value *pre-design*, no model needed; seeds memory | #1, #3, #15 (sharpened) |
| **2** | **Permit-readiness & Opposition radar** | D5 + D1 (phase 33) | The #1 schedule-killer; promote *ahead* of Auto-BIM | #17 (promoted), +new |
| **3** | **Fee & Cost / Soumission copilot** | D3 + D4 (phases 32/41) | Attacks fee erosion + owns the `.crbx`/eCCC moat | #18, +new (fees, CFC) |
| **4** | **Continuous Project Memory & Coordination** | D6 + D7 across phases | The compounding moat + liability protection | #19, #21 (reframed) |
| **Later** | Model-action layer | D9 Auto-BIM, voice-to-design, DT | For BIM-mature offices; downstream | #10–14, #16, #20 |

The **bottom-up canonical-first** principle of the original vision is preserved — this sequence just makes the
*first canonical object* a sourced parcel-and-constraints context (which the docs already advocate) and defers
the model-centric work that the target segment isn't ready for.

---

## G. Open decisions for you

These are genuine forks where your call shapes the next work:

1. **Wedge confirmation** — agree to lead with *Parcel-&-Constraints Intake + Opposition/Permit* (this doc's
   recommendation) over *Auto-BIM*? Or keep Auto-BIM central for a specific reason (e.g. an Archicad-mature
   pilot office already in hand)?
2. **Pilot jurisdiction** — which canton + commune to go deep on first? (VD/Lausanne and GE are the best-documented
   geoportals; GE's SITG is the reference. This also fixes the language: FR first.)
3. **Cold-start posture** — commit to *ingest-on-demand + registry-anchored* (B5) rather than pre-building a corpus?
4. **Scope of pack-0** — build the neutral-engine/jurisdiction-pack separation now (more upfront, pays off at
   internationalization) or hardcode CH first and refactor later (faster MVP1, technical debt)?
5. **Business model** — who pays (architect seat? office subscription? per-project? insurer-subsidized given D7)?
   This influences which MVP monetizes first.

Answering 1–3 is enough to start turning this into a corrected issue set and a sharpened MVP1 spec.
