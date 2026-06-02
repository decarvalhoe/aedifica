# Direction alignment check — product layer vs the ArchiOS north star

> Status: **point-in-time synthesis, 2026-06-02. No docs or code changed by this
> note** — it exists to decide the next move. Yardsticks: `vision.md`,
> `product/scope-realignment.md`, `strategy/decisions.md` (D-001…D-006).

## 1 · The north star (faithful restatement)

Aedifica = **ArchiOS Suisse**, an *agentic operating layer* across the full SIA
process (intake → design → permit → tender → execution → handover), built on **two
inseparable movements** (`vision.md` §Two-Movement Architecture):

1. **Bottom-up canonical-first** — sources → traceable canonical units (NOMOS) +
   durable **project memory**; every claim sourced or explicitly unknown.
2. **Top-down agentic orchestration** — agents reason over that memory, answer the
   architect's questions, propose the next step, and **act through a universal
   multi-software API** (`inspect_project`, `update_bim_properties`,
   `run_model_check`, `export_ifc`, …) under **dry-run → approval → ledger**.

Confirmed steers that bound scope:
- **D-001** hybrid wedge: regulatory/canonical spine **+** a live Archicad/BIM
  thread; must stay **generalizable** (partner office ≠ product identity).
- **D-005** the value is **holistic per-phase support**, not voice-to-design (~5%).
- **D-006** the real risk is **sequencing**: keeping the agent→software proof late
  makes the product *"feel like reports first."* The loop `agent → API/adapter →
  model/drawing intent → dry-run diff → approval → ledger` must lead.
- **Scope guardrails** (`scope-realignment.md`, verbatim intent): do **not** reduce
  Aedifica to (a) the UI surfaces, (b) regulatory reports, or (c) drawing
  automation. Keep **neutral engine + project memory + universal action API** as
  the stable center.

## 2 · What exists today (inventory)

| Layer | Built | Nature |
|---|---|---|
| **Engine (stdlib, `pilot/` + `aedifica/`)** | 43-issue wave: OEREB/route/claims/envelope, permit readiness, opposition evidence, phase-33 gates, **project memory + ledger + scoped approvals**, **adapter capability/transaction/export contracts + Archicad harness + replay server + adapter-evidence→ledger**, cost/tender, site/handover. 261 offline checks. | Contracts + fixtures (both movements represented). |
| **Cockpit** | Datum demo web app: live parcel lookup, permis, opposition, **and an agent→Archicad dry-run tab**. | Communication artifact. |
| **Product layer (W1/W3)** | SQL model + Alembic, repositories, **FastAPI**, **Next.js** workspace (parcelle/permis/opposition/conformité), multi-tenant auth, **on-demand commune ingestion**, live parcel pipeline, Docker/Postgres/GHCR. | Runtime substrate + surfaces. |

## 3 · Guardrail & two-movement check (honest)

| North-star element | Engine | **Product runtime** | Verdict |
|---|---|---|---|
| Bottom-up canonical + memory | ✅ strong | partial (projects/sources/claims persisted; memory queries not exposed) | 🟢 on track |
| **Top-down agentic orchestration** ("what next" per phase) | 🟡 demos only | ❌ absent | 🟠 missing in product |
| **Universal multi-software action API** (inspect/generate/check/export/**mutate**; dry-run→approval→ledger) | ✅ as contracts (E28+E27) | ❌ **not exposed at all** | 🔴 the gap |
| Don't reduce to UI surfaces | — | the workspace *is* the product surface | ⚠️ framing risk |
| Don't reduce to regulatory reports | — | product = parcelle/permis/opposition/conformité + CRUD | ⚠️ that's all it does |
| Neutral engine + memory + **universal API** as center | ✅ engine neutral | product centers the **regulatory workspace**, not the action API | ⚠️ center shifted |
| Adapter action = professional work (dry-run/approval/ledger) | ✅ | ❌ not in runtime | 🔴 |

## 4 · The drift, named

The W1/W3 sprint built an **excellent, vision-consistent substrate** (persistence,
API, web, deploy, multi-tenant, on-demand communes). But the **product framing
slid**: `ADR-0002` states *"the product = a deployed multi-tenant web app,"* and
the only things the product runtime exposes are the **bottom-up regulatory wedge**
(parcel/permit/opposition/compliance reports + CRUD). The **top-down half of the
architecture — the universal multi-software action loop (D-006's lead proof) and
the agentic per-phase "next step" + memory queries — is present as engine
contracts but absent from the product.**

That is precisely the failure mode `scope-realignment.md` and **D-006** warn
against: the product *"feels like reports first,"* reads as a *regulatory
workspace SaaS*, and the universal-action-API center is under-exposed. The wedge
is correct; treating it as the whole product is the drift.

## 5 · Correction options (your call)

- **A — Reframe (words, ~free).** Re-anchor `ADR-0002` + `overview.md`: the product
  is the **ArchiOS layer** (engine + memory + **universal action API** + agents);
  web/SQL/Docker are the **delivery substrate**, not the definition. No code change.
- **B — Re-balance the roadmap (the real fix).** Make the next product wave expose,
  in the runtime, the half that's missing:
  - the **action loop** over the API/UI — adapter capability discovery → dry-run
    diff → scoped approval → ledger (productize E28 + E27 = the R1A proof);
  - **project-memory queries** in the product — open decisions, what-changed,
    which-source-justifies-this (productize E27/AED-105);
  - a first **agentic "next step per SIA phase"** orchestrator (the North-Star
    question-answering).
  Keep the regulatory workspace as **one surface**, not the center. (The cockpit's
  agent→Archicad tab is the natural first action-loop surface to pull into product.)
- **C — Sequence consciously (accept the lean, document it).** Keep the regulatory
  workspace as the partner-pilot wedge (W2); explicitly **defer** action-loop
  productization to the wave right after partner validation; record it as a
  *sequencing* choice, not a scope redefinition. Risk: contradicts D-006's intent
  for longer (looks regulatory-only to the skeptical partner).

## 6 · Recommendation (mine, not imposed)

**A now + B next.** Reframe the two docs immediately (cheap, stops the narrative
drift), then make the **next product wave the action loop + memory + a per-phase
"next step"** rather than more CRUD/surfaces — because that half *is* the north
star and D-006's lead promise. Hold C only if partner go-to-market forces it, and
then say so explicitly.

## 7 · What this note did **not** do

No strategy/ADR/overview/code changes. Awaiting your decision on §5.
