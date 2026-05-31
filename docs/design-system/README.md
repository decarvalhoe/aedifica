# AEDIFICA Datum Design System

Status: local product copy, re-aligned from the corrected Claude Design brand book export on 2026-05-31.

## Source

Canonical visual direction: **02A Datum**.

Claude Design source project:

`https://claude.ai/design/p/3fb655a4-b665-49d0-b428-20b220cadcf1`

Corrected brand book source:

`https://claude.ai/design/p/d3d361b0-a9a7-4219-a7fb-d87cba4135a1`

Validated identity source referenced by the manifest:

`0b56b66b`

The committed [`aedifica-brand-book.html`](aedifica-brand-book.html) is the canonical brand book artifact. It replaces the previous repo-authored interpretation and should be treated as the visual source of truth for identity, editorial posture, component tone, and Datum layout language.

## Included Files

- `colors_and_type.css`: token and type source of truth.
- `aedifica-datum-ui.css`: small product-surface layer for repo HTML pages.
- `aedifica-brand-book.html`: canonical offline Claude Design brand book export.
- `design-system-manifest.json`: machine-readable design system contract.
- `assets/`: logo lockups, favicon and proprietary functional icon sprite.
- `fonts/`: self-hosted Space Grotesk and IBM Plex Mono files.

## Product Guardrail

This design system defines AEDIFICA's visual language. It does **not** define the product scope. The product remains the full ArchiOS Suisse scope described in [`../product/scope-realignment.md`](../product/scope-realignment.md): bottom-up canonical project intelligence plus top-down architectural assistance through a multi-software API.

## Surface Constraint

AEDIFICA product and presentation surfaces are **viewport-fit by default**. If a surface needs more material than one viewport can hold, split it into states, slides, chapters, tabs or a PDF/export template instead of extending the page. The brand book itself is a slide deck: the slide is the surface; the deck navigation is only a reading aid.

## Key Decisions

- Wordmark: typographic `AEDIFICA` / `ÆDIFICA`, Space Grotesk Light with the validated red datum fracture line.
- Accent: Datum red `#C0392B`, used as an active reference line, not as a trust state.
- Trust states: `sourced`, `computed`, `assumption`, `unknown`, `conflict`, `decision`.
- Icons: proprietary SVG sprite only; no external icon library dependency.
- Typography: Space Grotesk for display/UI, IBM Plex Mono for evidence annotations.
- Brand book hierarchy: the corrected deck is canonical; repo one-pagers and pilot screens are downstream derivations, never identity references.
