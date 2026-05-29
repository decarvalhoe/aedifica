# Per-Phase Value Catalog — What an Architect Does, and What Aedifica Does For Them

> **This is the pitch artifact.** For every step of a real Swiss mandate (corrected SIA phases), it states
> what the architect actually does, the pain, and the **concrete agentic quick-win** Aedifica can show —
> tagged by whether it needs a BIM model and how demo-able it is. Use it to walk a partner architect through
> *"at this step you do X; here is what AI can do for you here, and it saves you this."*
>
> **The message it carries:** the seductive dream — *"talk to an AI and it draws the building"* (the *stylo*,
> the voice-to-design moment) — is real but a **tiny slice**. The decisive value is **holistic support across
> every phase, from the first document to final handover.** Aedifica supports the architect's whole job; the
> drawing is the smallest part of it.

## How to read the tags

- **`[no-BIM]`** — works with no model; only documents/parcel/registers. *Demo-able to any office today.*
- **`[BIM]`** — leverages a model (Archicad/IFC/Speckle). *Directly demonstrable with the Archicad partner office.*
- **`[demo]`** — high "wow", quick to show convincingly.
- **`[VD/LSN]`** — sharpened for the Vaud / Lausanne pilot.
- Anchored on free Swiss data: RDPPF/ÖREB, Géoportail VD, swisstopo GeoAdmin API, fedlex; cost via CRB (CFC/eCCC/NPK).

> Phase codes follow the verified SIA model in [`architect-reality.md`](architect-reality.md) §3.

---

## Phase 0 / Intake — before any formal SIA phase

**Architect does:** collects the brief, the parcel, budget, constraints, existing conditions; forms a first
mental risk map. **Pain:** constraints scattered across PDFs, geoportals, emails, the commune's règlement;
nothing consolidated; the riskiest facts surface late.

| Agentic quick-win | Tags |
|---|---|
| **Parcel intake**: from a parcel № / address, pull RDPPF restrictions + zone + servitudes (RF) + DS noise + protected-site flags → one **sourced constraints sheet** | `[no-BIM][demo][VD/LSN]` |
| Auto-build the **source registry** (every fact linked to its instrument + version + date) | `[no-BIM]` |
| First **unknowns & required-decisions** list (what's missing to proceed) | `[no-BIM]` |

> **Show him:** type a Lausanne parcel № → 30 seconds later, a one-page "what constrains this land", every line
> clickable to the official source. *No model, no drawing — pure orientation value.*

## Phase 1 (11) — Définition des objectifs / feasibility

**Architect does:** clarifies objectives, feasibility, project setup. **Pain:** quick capacity studies are
manual and error-prone; early numbers drive everything downstream.

| Agentic quick-win | Tags |
|---|---|
| **Buildable-envelope calculator**: indices (IUS/IBUS/IOS) + distances + heights → max SBP, rough unit count, footprint, sourced | `[no-BIM][demo][VD/LSN]` |
| **Feasibility brief**: envelope vs program vs budget order-of-magnitude (eBKP benchmarks) | `[no-BIM]` |
| **Risk list** for this parcel/zone (what could block or shrink the project) | `[no-BIM]` |

> **Show him:** "on this parcel you can build ~X m² SBP across ~Y units, here's why" — the kind of answer that
> normally takes half a day, in seconds, with the règlement article cited.

## Phase 2 (21 feasibility · 22 mandate/competition) — Études préliminaires

**Architect does:** variants, site analysis, competition strategy (SIA 142/143), consultant setup.
**Pain:** scoring variants against rules is tedious; competition dossiers are assembly-heavy.

| Agentic quick-win | Tags |
|---|---|
| **Variant ↔ rule scoring**: each massing option scored against zone rules / indices / DS | `[no-BIM]` / `[BIM]` if massing model |
| **Competition dossier assistant** (SIA 142): checklist, required pieces, deadlines | `[no-BIM]` |
| Consultant-setup helper: which specialists this project needs + their SIA règlement | `[no-BIM]` |

## Phase 3.1 (31) — Avant-projet

**Architect does:** architectural concept, surfaces, massing, first cost estimate. **Pain:** surface/program
compliance checks and early cost are manual.

| Agentic quick-win | Tags |
|---|---|
| **Program/surface compliance** vs SIA 416 (SP, SU, SUP…) | `[no-BIM]` from schedules · `[BIM]` from model |
| **Order-of-magnitude cost** by eCCC-Bât element + benchmarks | `[no-BIM]` |
| Concept **risk report** (where the concept fights the rules) | `[no-BIM]` |

## Phase 3.2 (32) — Projet de l'ouvrage  ← **the Archicad/BIM hybrid lives here**

**Architect does:** technical coordination, material choices, BIM development with specialists.
**Pain:** BIM metadata is tedious and incomplete; coordination errors are liability. *(~21 % of fees.)*

| Agentic quick-win | Tags |
|---|---|
| **Auto-BIM in Archicad**: extract spaces, auto-fill room properties (name/number/level/area/usage), classifications | `[BIM][demo]` ← *for the partner office directly* |
| **Missing-metadata audit** + one-click fixes after approval | `[BIM]` |
| **Coordination/clash prep** + interface-responsibility map (who owns what) | `[BIM]` |
| IFC export **pre-check** (does the model carry what downstream needs) | `[BIM]` |

> **Show him (his tools):** point Aedifica at his Archicad model → it lists every space missing properties and
> fills them on approval, with a before/after log. This is the *"your dream, but useful"* demo — concrete time
> saved in the tool he already uses, while the same engine also did the no-model regulatory work above.

## Phase 3.3 (33) — Autorisation / mise à l'enquête  ← **highest-risk, highest-wow**

**Architect does:** assembles the permit dossier, faces public inquiry + oppositions. **Pain:** opposition is
the #1 schedule-killer; dossier completeness is fiddly and canton-specific. *(~2.5 % of fees, huge risk.)*

| Agentic quick-win | Tags |
|---|---|
| **Opposition / recours-risk radar**: score likelihood + likely legal grounds from neighbours, distances, gabarits, shadows, DS — *before* enquête | `[no-BIM][demo][VD/LSN]` |
| **Permit-dossier completeness** for Lausanne/VD (CAMAC), citation-backed | `[no-BIM][demo][VD/LSN]` |
| **Compliance gates**: energy (CECB/SIA 380-1), **fire AEAI** (binding), accessibility (SIA 500/LHand), seismic (SIA 261) | `[no-BIM]`/`[BIM]` |

> **Show him:** "your project has a medium opposition risk — the north setback and the shadow on parcel X are
> the likely grounds; here's the mitigation." *Nobody on the market does this.*

## Phase 4 (41) — Appel d'offres / adjudication

**Architect does:** quantities, specs, tenders, bid comparison. **Pain:** métré → soumission → comparison is
slow and standard-bound. *(~18 % of fees.)*

| Agentic quick-win | Tags |
|---|---|
| **Quantities → eCCC-Bât → NPK/CAN** draft soumissions, exported `.crbx` (IfA18) | `[BIM]` if model · `[no-BIM]` from quantities |
| **Missing/contradictory position** detection in the descriptif | `[no-BIM]` |
| **Bid comparison** + assumptions/exclusions log; integrates with Messerli/SORBA | `[no-BIM]` |

## Phase 5.1 (51) — Projet d'exécution

**Architect does:** execution drawings, details, coordination, revisions. **Pain:** drawing-set consistency
and change tracking across revisions.

| Agentic quick-win | Tags |
|---|---|
| **Drawing-set audit** (consistency, missing sheets, detail coherence) | `[BIM]` |
| **Change tracking** between model/sheet versions ("what changed since v3") | `[BIM]` |

## Phase 5.2 (52) — Exécution / chantier (direction des travaux)

**Architect does:** site management, meetings, defects, costs, schedule. **Pain:** site admin is heavy; minutes
and defects are manual. *(~29 % of fees — the biggest chunk.)*

| Agentic quick-win | Tags |
|---|---|
| **Site-report agent**: photos + notes → structured PV | `[no-BIM][demo]` |
| **Minutes → tasks** extraction with owners/deadlines | `[no-BIM][demo]` |
| **Defect tracking** + model-linked issues (BCF) | `[no-BIM]`/`[BIM]` |
| **Budget/schedule alerts** against the plan | `[no-BIM]` |

> **Show him:** drop three site photos + a voice note → a clean PV with dated, assigned action items. *Pure time
> saved, every project, no model needed.*

## Phase 5.3 (53) — Mise en service / achèvement

**Architect does:** handover, defects close-out, final docs. **Pain:** assembling a complete handover dossier.

| Agentic quick-win | Tags |
|---|---|
| **Handover-checklist** + completeness audit (warranties, as-built, manuals) | `[no-BIM]` |
| **As-built consistency** vs final model | `[BIM]` |

## Phase 6 — Exploitation

**Architect does:** (when mandated) maintenance, transformations. **Pain:** project knowledge evaporates after
handover.

| Agentic quick-win | Tags |
|---|---|
| **Project memory for operation** — queryable years later for renovation/maintenance | `[no-BIM]` |

---

## The demo shortlist (what to show first, in order)

1. **Parcel → constraints sheet** (Phase 0) — `[no-BIM]`, instant orientation, fully sourced. *(VD/Lausanne.)*
2. **Buildable-envelope** (Phase 1) — `[no-BIM]`, the "what can I build here?" wow.
3. **Opposition-risk radar** (Phase 33) — `[no-BIM]`, unique on the market, hits the #1 pain.
4. **Auto-BIM in Archicad** (Phase 32) — `[BIM]`, "your dream made useful" in *his* tool.
5. **Site-report / minutes→tasks** (Phase 52) — `[no-BIM]`, daily time-saver across every project.

> 1–3 and 5 prove the **generalizable, no-model, every-architect** story; 4 proves the **hybrid Archicad thread**
> for the partner office. Together they tell the whole message: *Aedifica supports the entire mandate — drawing
> is the smallest part.*

## The narrative spine for the pitch

```
"Parler à une IA qui dessine"   →  seductive, real, but ~5% of the value
The architect's actual job       →  intake · constraints · feasibility · coordination ·
                                    permit/opposition · tender · site · handover · memory
Aedifica                         →  a quick-win at EVERY one of those steps,
                                    sourced & logged, in your tools, generalizable to any office.
```
