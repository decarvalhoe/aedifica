# AEDIFICA — Datum Design System

The official, navigable design system for **AEDIFICA** — an independent Swiss B2B product brand for architecture offices. AEDIFICA delivers **sourced project intelligence**: parcel constraints, permit readiness, opposition risk, decision memory, evidence, and A4 reports.

> **Préparation sourcée par AEDIFICA. Pas une autorité.**

AEDIFICA is **not a legal authority** and **not a generic AI assistant**. It prepares evidence; it does not rule.

This repository is the **source of truth** for the validated direction **02A — Datum**: radical Swiss, architectonic, post-classical, evidence-backed. It is a formal system, not a collection of mockups. Downstream surfaces (landing, dashboard, intake, opposition radar, decision ledger, A4 report, sales one-pager) are **derived examples**, never the source.

---

## Status

| | |
|---|---|
| Version | **v4** |
| Date | **2026-05-31** |
| Direction | **02A — Datum** (validated) |
| Type lock | Space Grotesk + IBM Plex Mono |
| Icons | Proprietary sprite — **no external library** |
| Runtime | None — static HTML + CSS |

---

## Sources & context

- **This pack formalizes the VALIDATED direction.** The visual foundation — the ÆDIFICA wordmark, datum-red accent, the six trust states, the proprietary icon sprite and the token layer — is the validated 02A Datum DA (source of truth: project `0b56b66b`). This pack does not re-invent it; logo and icon artwork were copied from that source. Do not deviate.
- **The current POC/MVP did not inform this direction.** It only told us which surfaces ship. Its visual language must not leak into Datum.
- **Parent context** — AEDIFICA is a sibling brand to *Réalisons* (Yan Haltey Brands Sàrl, Lausanne). The Réalisons design system lives in a separate Claude Design project and is **neumorphic, calm, brand-pure** — a deliberately different world. Do not borrow from it. Datum is sharp, flat, architectural.
- **Fonts** — Space Grotesk and IBM Plex Mono are sourced from the Google Fonts OFL repository and self-hosted in `fonts/`. Swap for licensed masters if your team holds them.

The navigable system pages are the primary reference: open `design_system/index.html`.

---

## Index — what's in this folder

| Path | What |
|---|---|
| `README.md` | You are here. Context, content fundamentals, visual foundations, iconography, index. |
| `SKILL.md` | Agent-Skills compatible manifest — invoke the system from Claude Code or another agent. |
| `colors_and_type.css` | **Canonical token layer.** Color, type, spacing, radii, grid, elevation, motion + base type classes. Drop-in. |
| `design_system/index.html` | Official hub — status, principles, order of use, ready-for-generation surfaces. |
| `design_system/foundations.html` | All tokens. |
| `design_system/typography.html` | Type lock, specimens, setting rules. |
| `design_system/color-states.html` | Core / neutral + the six trust states. |
| `design_system/logo.html` | ÆDIFICA wordmark, lockups, datum + fracture, clearspace, do/don't, outlining note. |
| `design_system/iconography.html` | Proprietary sprite, state squares, datum marks. |
| `design_system/components.html` | Buttons, fields, tabs, KPI, claim card, evidence row, chips, report card, ledger, table, async states. |
| `design_system/report-a4.html` | A4 report rules: print, margins, sources, unknowns, conclusions, non-authority posture. |
| `design_system/data-contract.html` | The real schema + a DEMO fixture. |
| `design_system/accessibility-qa.html` | Contrast, focus, keyboard, print + responsive QA, export checklist. |
| `design_system/implementation.html` | Recipes, naming, React handoff, file inventory, skill prompt. |
| `design_system/design-system-manifest.json` | Machine-readable inventory (v4). |
| `design_system/ds.css` · `ds.js` | Doc chrome + injected header/nav/disclaimer. |
| `assets/` | Æ mark (+ duotone), proprietary icon sprite. **Use these — never redraw.** |
| `fonts/` | Space Grotesk (variable) · IBM Plex Mono (regular/medium). |
| `preview/` | Specimen cards for the Design System tab. |

---

## 1. Product context — who and what

AEDIFICA serves **architecture offices** under deadline. The product gathers and **sources** the information that precedes a permit dossier, and presents it with explicit provenance. The seven authorised surfaces:

1. **Landing — produit.** Public proposition: sourced intelligence, non-authority posture.
2. **Dashboard — portefeuille.** Office portfolio of projects, parcels and readiness.
3. **Intake flow.** Stepped opening of a project: parcel, programme, constraints.
4. **Opposition radar.** Opposition-risk signals with provenance and confidence.
5. **Decision ledger.** Append-only decision memory.
6. **Report preview — A4.** Print-ready dossier with sources, unknowns and sourced conclusions.
7. **Sales one-pager.** Single sheet: what AEDIFICA prepares, how it is sourced, what it never claims.

The most important object across all of them is the **claim** and its **state** — see §2 and Color & States.

---

## 2. CONTENT FUNDAMENTALS — voice, tone, copy

AEDIFICA writes like a precise technical office that respects its reader's expertise. Calm, factual, exact. The content is evidence, not persuasion.

### Voice traits

Precise · factual · sober · architectural · Swiss-romand in convention. Confident about *method*, never about *outcome*.

### Posture and pronouns

- **Vouvoiement.** The reader is a professional; address them as one.
- **Prepare, never rule.** Never state conformity, approval or legal outcome as fact. AEDIFICA prepares sourced evidence; the decision and conformity rest with the competent authority.
- **Name the unknown.** If a value is not sourced, say so. Gaps are surfaced, never hidden.

### The provenance reflex — *every claim carries a state*

This is the spine of the brand. No statement appears without one of the six trust states:
`sourced · computed · assumption · unknown · conflict · decision`.
The copy mirrors the state: a sourced claim cites its reference; an assumption says “présumé, à confirmer”; an unknown is flagged for human verification.

### The mandatory claim

Every surface and every report carries:

> **Préparation sourcée par AEDIFICA. Pas une autorité.**

### Vocabulary

| ✅ Use | ❌ Avoid |
|---|---|
| sourcé, évidence, provenance | garanti, approuvé, conforme (as fact) |
| préparation, dossier, parcelle | autorité, décision finale (as ours) |
| hypothèse, inconnue, à confirmer | magique, intelligent, révolutionnaire |
| contrainte, recul, indice, faîte | game changer, disruptif |

### Editorial typography

- Swiss formats: `CHF 1'200.00` · `18.05.2026` · `12 m` · `0.6` · `15 %`.
- References and IDs always in IBM Plex Mono: `AED-2026-0042`, `RPGA art. 19 al. 2`.
- Sentence case for content. UPPERCASE only for mono eyebrows and labels.
- **No emoji.** No decorative unicode beyond the middle dot `·` as a separator.

### CTAs — calm, precise

| ✅ | ❌ |
|---|---|
| Ouvrir le projet · Voir le détail | Booster · Foncer |
| Voir la source · Exporter A4 | Découvrir la magie |
| Marquer comme hypothèse | — |

---

## 3. VISUAL FOUNDATIONS — the look and feel

### Backgrounds

Always `--paper` (`#F2F0EA`) — a **warm drafting-paper off-white**. Never pure white, never pure black. **No gradient, no blob, no glassmorphism, no neumorphism, no grain, no texture, no background image full-bleed.** The page is a measured drawing; structure comes from **datum lines and grids**, not from fills or shadows.

### The datum signature

Strong hairlines (`--hairline-strong` = ink) act as **datum lines** — the reference rules that structure a page like an architectural drawing. Sections are separated by rules, not cards-on-cards. Corner ticks (`.datum-frame`) frame key blocks. Numbered sections (`§ 01.2`) run in the left gutter.

### Color vibe

Two inks on warm paper, plus one **datum red** accent (`#C0392B`) — the active reference line, used sparingly and never as a state. Provenance color is **reserved for the six trust states**: sourced is green (`#1F7A44`), conflict is red (`#C1122C`), decision is ink-filled, unknown is dashed. Color never carries meaning alone — always with a label.

### Type

Two families, locked. **Space Grotesk** — Light 300 for display and the wordmark; 400/500 for UI and body. **IBM Plex Mono** — annotations only (refs, IDs, coordinates, source lines, eyebrows). **IBM Plex Sans is forbidden.** No third sans, no Inter/Roboto/Arial. Display tracking is negative (−0.02em); never italicise the display weight.

### Borders, radii, cards

- Borders are **hairlines** (`--hairline` `#D6D2C8`) or **datum lines** (ink). No borderless floating surfaces.
- **Corners are square.** `--r-0: 0` for cards, panels, the report sheet; `--r-1: 3px` for buttons/inputs, `--r-2: 4px` for report cards. No 8/12/20px radii.
- Cards are **flat**: `--sheet` background, 1px hairline, square corners, no shadow at rest, **no top-accent stripe, no left-color bar** (except the ledger item, whose left rule is a deliberate, documented exception in the decision hue).

### Elevation & shadow

Minimal. Hairlines do the work. Shadow appears **only** for overlays (`--elev-popover`, `--elev-overlay`). No Material drop shadows, no shadow under text, no glow.

### Animation

Precise and mechanical. `--ease-datum` = `cubic-bezier(.2,0,0,1)`, durations 120–260ms. Hover changes background/border, not transform. **No bounce, no spring, no parallax.** Always honour `prefers-reduced-motion`.

### Hover & pressed states

- **Hover** — background shifts to `--paper-2`, or fill darkens one step (ink → n-700, trust → trust-ink). Never opacity fades.
- **Focus-visible** — always `outline: 2px solid var(--accent)` with `outline-offset: 2px`. Never removed without replacement.

### Layout rules

- Page margins are symmetric: 64px desktop, collapsing to 24px under 760px.
- 12-column grid, 24px gutter, content max 1280px, reading measure ≤ 68ch.
- Everything snaps to the 8px module.

### What this system AVOIDS

Gradient backgrounds · blobs · glassmorphism · neumorphism · Material shadows · rounded SaaS cards · colored left-border accent cards · emoji icons · magic/authority posture · invented numbers · purple-to-blue AI hero backdrops · IBM Plex Sans · any external icon library.

---

## 4. ICONOGRAPHY

AEDIFICA ships **one proprietary sprite** — `assets/functional-icons.svg`. Geometric, drawn on a 24px grid with a 1.5px stroke, square caps and miter joins to match the datum drawing language. Icons inherit `currentColor`.

### What we have

- **Logo** — the ÆDIFICA typographic wordmark (Space Grotesk Light, Æ ligature 400) on a red datum line with a controlled fracture. Lockups: `assets/logo-aedifica-horizontal.svg` (primary), `-reverse.svg`, `-stacked.svg`, `-monogram.svg`, `favicon.svg`. Never redraw; outline the wordmark for production.
- **Functional sprite** — `assets/functional-icons.svg`, used via `<svg><use href="assets/functional-icons.svg#ic-parcel"/></svg>`. The validated set is ic-intake/claims/evidence/decisions/report/export/source/warning/check; the file extends it in the same style.
- **Trust-state marks** — the six trust states as `.ds-ts` chips and square markers (unknown dashed, decision ink-filled). See `design_system/color-states.html`.

### Rules

- Outline family only — never mix outline and filled glyphs.
- Sizes: 16–18 inline · 22–24 controls · 26+ surface headers.
- **No emoji. No unicode-as-icon.**
- **Aucune bibliothèque externe** — never link or bundle a third-party icon set or icon-package dependency. Add new glyphs to the sprite on the same grid and stroke.

---

## Quick start

```html
<link rel="stylesheet" href="colors_and_type.css">
<body style="background:var(--paper); color:var(--fg-1); font-family:var(--font-ui)">
  <p class="ds-eyebrow">Le portefeuille</p>
  <h1 class="ds-display-1">Parcelle 4412</h1>
  <span class="chip" style="color:var(--st-sourced);background:var(--st-sourced-bg);border-color:var(--st-sourced-line)">Sourced</span>
  <svg class="i"><use href="assets/functional-icons.svg#ic-parcel"/></svg>
</body>
```

---

## Caveats & known gaps

- The **logo + icon artwork** are copied from the validated source project (`0b56b66b`); this pack formalizes that DA rather than re-inventing it.
- The **baseline tagline** (“INTELLIGENCE PROJET · SOURCÉE”) is **not validated** — to be defined; it has been removed from all artwork here.
- **Fonts** are OFL builds from Google Fonts; substitute licensed masters if required, and **outline the wordmark** for production artwork.
- No photography library — AEDIFICA's surfaces are data-led; use placeholders, not invented imagery.
- The seven surfaces are **derived examples**; this system, not those screens, is the source of truth.

---

## License

Brand, mark, tokens © 2026. Private. Do not redistribute.
