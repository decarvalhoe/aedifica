# The Swiss Regulatory Stack — Federal / Cantonal / Communal / Parcel

> Purpose: make the "Swiss context" concrete and operational. The three-level constraint stack (plus the
> parcel level) is simultaneously the **core complexity** and the **strongest moat**. This doc names the
> actual instruments, says where the *binding machine-readable data* lives, and explains the multilingual
> reality. Sources at the end.

## Mental model: inverted subsidiarity

A Swiss building project is constrained by a strict legal hierarchy, but with a twist crucial to product
design: **the Confederation only sets _framework_ law (LAT/RPG); the operational substance lives at
cantonal and communal level.** So you cannot model "Swiss building rules" centrally — the rules that
actually decide what you may build are dispersed across **26 cantons and ~2,100 communes, in 4 languages**.

```
Federal     →  framework only (LAT/RPG, environment, energy frame, accessibility, fire concordat)
Cantonal    →  permit procedure, energy law, most binding construction rules   (26 variants)
Communal    →  the land-use plan + building regulation that fix what THIS parcel allows  (~2,100 variants)
Parcel      →  public-law restrictions (RDPPF/ÖREB) + private rights (registre foncier, servitudes)
```

## Level 1 — Federal (frame)

Permits are essentially never federal (exceptions: rail, national roads, military, aviation). Federal law
sets minimums, harmonisation mandates and protected inventories.

| Instrument | Abbr. (FR/DE) | Constrains | Volatility |
|---|---|---|---|
| Loi sur l'aménagement du territoire + ord. | **LAT/RPG**, **OAT/RPV** | Building vs non-building zones; densification (LAT 1); LAT 2 in progress | Med-high (actively moving) |
| Protection nature/paysage + inventories | **LPN/NHG**, **ISOS**, **IFP/BLN** | Demolition/alteration in protected built fabric & landscapes | Low |
| Protection de l'environnement + EIE | **LPE/USG**, **OEIE/UVPV** | Which projects need an environmental impact study (rides inside the permit) | Medium |
| Protection contre le bruit | **OPB/LSV** | Noise limit values; assigns **degrés de sensibilité DS I–IV** per zone | Med-high |
| Égalité handicap | **LHand/BehiG** | Accessibility (technically via **SIA 500**) | Low |
| Loi CO₂ | — | Building-sector decarbonisation → feeds cantonal energy law | High |
| Fire protection | **AEAI/VKF** | Fire norm + directives; **binding in all cantons via the AIET concordat** | High (2015; 2026 revision) |

**Federal data spine:** `fedlex.admin.ch` (consolidated law, the legal source of truth), `map.geo.admin.ch`
(national geoportal; ISOS, IFP, hazards), **swisstopo GeoAdmin API** (`api3.geo.admin.ch` — free,
programmable parcel/address/layer queries), ARE / BAFU / BAK.

## Level 2 — Cantonal (the operational core)

Each canton has its own construction law, its own MoPEC-derived energy law, its own permit procedure with a
mandatory **public inquiry (mise à l'enquête / öffentliche Auflage)** and an **opposition → recours** chain,
and **its own geoportal**. Worked examples:

| Canton | Construction law | Procedure / appeal body | Geoportal |
|---|---|---|---|
| **Vaud** | **LATC** + RLATC | enquête 30 j (FAO), opposition → recours to **CDAP** | Géoportail VD (geo.vd.ch) |
| **Genève** | **LCI** (+ RCI), **LaLAT**, LaLPE | ordinary 60 j / accelerated **APA** 30 j → **TAPI** | **SITG** (sitg.ge.ch) |
| **Zürich** | **PBG** (mandates communal **BZO**) | Baugesuch → Auflage → **Rekurs** to Baurekursgericht | GIS-ZH (maps.zh.ch) |

**Cross-cantonal harmonisation — and its trap:**
- **AIHC / IVHB** harmonises ~30 measurement definitions (heights, distances, indices) — but adoption is
  **canton-by-canton, partial, with reservations and different transposition dates**.
- **MoPEC / MuKEn** is a *template* energy law cantons copy unevenly; **CECB / GEAK** is the energy label,
  with variable legal mandate per canton.

> **Never assume the harmonised definition applies.** A correct system must track **adoption state per
> canton**. Partial harmonisation creates an *illusion* of uniformity that is itself a correctness hazard.

## Level 3 — Communal (~2,100 variants — highest density of project-deciding numbers)

The commune adopts the binding **land-use plan + building regulation** that fix what a given parcel allows.

- **Plan d'affectation / PGA** (_Nutzungsplan_; carried in the **BZO** in ZH) → each parcel's **zone**.
- **Règlement communal des constructions** (_Baureglement_ / BZO) → per-zone rules. ⚠️ "RCCZ" is *not* a
  universal label; the naming varies by canton — treat it as a **category**, not a fixed acronym.
- **Plan de quartier / PPA** (_Quartierplan / Gestaltungsplan_) → detailed plan overriding ordinary rules.

Project-deciding indices (harmonised *in name* by AIHC where adopted): **IUS / IBUS** (floor-area ratios,
_AZ/aBGF_), **indice d'occupation IOS** (footprint, _Überbauungsziffer_), **indice de masse** (_BMZ_),
**distances aux limites** (_Grenzabstände_), **hauteurs / gabarits** (_Gebäude-/Firsthöhe_), and the
**degré de sensibilité au bruit DS I–IV** assigned per zone under OPB.

Where it lives: the commune (greffe / Bauamt), surfaced through the **cantonal geoportal** and, for the
*binding* restrictions, the **RDPPF/ÖREB cadastre**. Volatility: **very high in count, low individually** —
something is always changing across 2,100 communes, and plans are mid-revision under LAT 1 + AIHC.

## Level 4 — Parcel / property

The rights and restrictions attached to the specific parcel, split between public and private law:

| Instrument | Nature | Constrains | Where |
|---|---|---|---|
| **Registre foncier (RF / _Grundbuch_)** | Private-law register | Ownership, **servitudes**, mortgages, mentions | Cantonal RF offices (not fully open; extracts on legitimate interest) |
| **Servitudes** | Private real rights | Rights-of-way, building/height/distance restrictions — **can override what zoning allows** | RF + plan de servitude (mensuration officielle) |
| **Droits de voisinage (art. 684 ss CC)** | Civil-law duty | Avoid excess harming neighbours (noise, light deprivation…) | CC + cantonal application + Federal Court case-law |
| **Cadastre RDPPF / ÖREB** | Public-law register | The **authoritative** view of ≥17 themes of public restriction per parcel (zone, DS noise, alignments, polluted sites, forest, groundwater…) | swisstopo strategy, cantonal publication (SITG, Géoportail VD, GIS-ZH); `cadastre.ch` |
| **Mensuration officielle (MO / AV)** | Legal-grade survey | Legally binding parcel boundaries; geometric base for RF + RDPPF | géomètre officiel; cantonal cadastral offices |

> **The RDPPF/ÖREB cadastre is the single most valuable real-time integration target** — it consolidates the
> *binding public-law layer* per parcel and is event-driven (changes on mutations, new servitudes, new noise
> plans, new contaminated-site entries).

## The multilingual reality is ontology, not translation

Legal terms are **non-cognate** across FR/DE/IT, and even the *bodies and procedures* differ:

| Concept | FR | DE | Note |
|---|---|---|---|
| Permit | autorisation / permis de construire | **Baubewilligung** | — |
| Public inquiry | mise à l'enquête publique | **öffentliche Auflage** | — |
| Objection → appeal | **opposition → recours** | **Einsprache → Rekurs** | appeal *bodies* differ (CDAP/TAPI vs Baurekursgericht) |
| Land-use plan | plan d'affectation / PPA | **Nutzungsplan / Gestaltungsplan** | — |
| Floor-area index | IUS / IBUS | **AZ / aBGF** | same concept, different letters + historically different measurement |
| Public-restrictions cadastre | RDPPF | **ÖREB-Kataster** | (IT: catasto RDPP) |

Canonical units must therefore be **language-neutral**, with FR/DE/IT renderings and explicit links to the
binding source — not a localisation afterthought.

## Why this fragmentation is the moat (not just a burden)

1. **Irreducible local knowledge.** Correctness requires knowing, per commune: which law version × which
   AIHC-transposed definitions × which DS map × which live RDPPF themes. No generic/foreign tool shortcuts
   this; it is *earned data + maintained mappings*, not algorithm.
2. **Multilingual legal-semantic graph.** Mapping FR/DE/IT terms to one canonical ontology is hard,
   defensible, and compounds with every canton/commune added.
3. **High-volatility maintenance = recurring value.** Constant asynchronous change (LAT 2, OPB, AEAI 2026,
   CO₂ law, MoPEC rollout, ~2,100 communal plan revisions) makes a *continuously-updated* system a
   subscription-grade necessity, not a one-off.
4. **Anchor on binding registries.** Whoever robustly integrates **fedlex + geo.admin.ch + the 26 cantonal
   geoportals + RDPPF/registre foncier** owns a data spine competitors must rebuild from scratch.
5. **Trust & switching cost.** In a liability-sensitive domain, architects/authorities trust the tool that
   is demonstrably *current and canton-correct*. That trust + the maintained corpus is the durable defence.

> **Thesis:** *The Swiss construction stack is not one system but ~2,100 overlapping ones across 3 sovereignty
> levels and 4 languages, only partially harmonised (AIHC, MoPEC) and constantly drifting — so the defensible
> product is a continuously-maintained, multilingual, canton-and-commune-aware ontology bolted onto the
> binding registries.* This is also exactly why a **neutral engine + jurisdiction packs** design wins (see
> [`challenge-and-brainstorm.md`](challenge-and-brainstorm.md) §E).

## Sources

- LAT/RPG: <https://www.are.admin.ch/fr/lat> · OPB/LSV: <https://www.fedlex.admin.ch/eli/cc/1987/338_338_338/fr> · LHand+SIA 500: <https://architecturesansobstacles.ch/normes_et_publications/norme-sia-500-constructions-sans-obstacles/> · AEAI 2015: <https://www.bsvonline.ch/fr/prescriptions-de-protection-incendie/prescriptions-2015>
- AIHC/IVHB: <https://www.bpuk.ch/fr/dtap/concordats/aihc> · MoPEC (EnDK): <https://www.endk.ch/fr/politique-energetique/mopec> · CECB/GEAK: <https://www.cecb.ch/>
- VD LATC: <https://www.lexfind.ch/tolv/97689/fr> · GE LCI: <https://silgeneve.ch/legis/data/rsg_l5_05.htm> · ZH PBG: <https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung/zhlex-ls/erlass-700_1-1975_09_07-1976_04_01-107.html>
- Geoportals: SITG <https://sitg.ge.ch> · Géoportail VD <https://www.geo.vd.ch> · GIS-ZH <https://maps.zh.ch>
- swisstopo GeoAdmin API: <https://api3.geo.admin.ch/services/sdiservices.html> · geodienste zoning: <https://www.geodienste.ch/services/npl_nutzungsplanung?locale=fr> · RDPPF dataset: <https://opendata.swiss/en/dataset/rdppf-zones-daffectation-primaires>
- Cadastre RDPPF / registre foncier / mensuration: <https://www.cadastre.ch/fr/cadastre-rdppf> · <https://www.cadastre.ch/fr/registre-foncier-suisse> · droit de voisinage art. 684 CC: <https://juriup.ch/terme-juridique/troubles-du-voisinage-en-suisse-bruit-odeurs-et-regles-cc/>
