---
name: aedifica-design
description: Use this skill to generate well-branded interfaces and assets for AEDIFICA — the Datum design system (radical Swiss, architectonic, evidence-backed) for architecture-office project intelligence. Covers design guidelines, color, type, fonts, the proprietary Æ mark and icon sprite, the eight epistemic states, components, and the A4 report — for production or throwaway prototypes/mocks.
user-invocable: true
---

Read the `README.md` file within this skill, then explore the other available files. The navigable system lives in `design_system/` — start at `design_system/index.html`; the canonical tokens are in `colors_and_type.css`; the machine-readable inventory is `design_system/design-system-manifest.json`.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out (`assets/logo-aedifica-horizontal.svg` & lockups, `assets/functional-icons.svg`, the `fonts/`) and create static HTML files that link `colors_and_type.css`. If working on production code, copy assets and read the rules here to become an expert in designing with this brand.

Non-negotiables when you generate anything AEDIFICA:
- **Type lock** — Space Grotesk Light (300) for display + the ÆDIFICA wordmark (Æ ligature 400), Space Grotesk 400/500/600 for UI/body/titles, IBM Plex Mono for evidence annotations only. **IBM Plex Sans is forbidden.** No third sans, no external icon library.
- **Trust states are first-class** — every claim/signal/field carries one of the six: sourced (green), computed (slate), assumption (ochre), unknown (dashed grey), conflict (red), decision (ink-filled). Render color **and** label — never color alone. The datum-red accent (`#C0392B`) is the active reference line, used sparingly, never as a state.
- **Posture** — keep the disclaimer "Préparation sourcée par AEDIFICA. Pas une autorité." AEDIFICA prepares sourced evidence; it is not a legal authority and not a generic AI assistant. Name unknowns; never claim conformity as fact.
- **Visual** — ink on warm paper, square corners, hairline/datum-line structure, controlled density. No gradient, blob, glassmorphism, neumorphism, drop-shadow magic, or authority/magic posture.
- Mark any demo data `DEMO`. Never invent values — read `colors_and_type.css`.

If the user invokes this skill without other guidance, ask what they want to build or design, ask a few focused questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.
