# Multilingual Regulatory Graph

Issue: #34  
Structured file: `pilot/research/multilingual_regulatory_graph.json`

## Contract

Rules are stored language-neutral and rendered in FR/DE/IT.

Each canonical term must include:

- `canonical_key`;
- domain;
- `renderings.fr`, `renderings.de`, `renderings.it`;
- source refs with validity dates;
- adoption state: authority, canton, instrument, status, valid-as-of, review due.

## Why This Matters

Swiss legal terms are not always cognates:

- `opposition` / `Einsprache` / `opposizione`;
- `recours` / `Rekurs` or `Beschwerde` depending context;
- `indice d'utilisation du sol` / `Ausnützungsziffer` / `indice di sfruttamento`.

The graph must keep one canonical concept while rendering the local legal vocabulary.

## Adoption State

AIHC/IVHB and MoPEC/MuKEn-style concepts must be tracked per canton and instrument. Aedifica cannot assume
that a harmonized model is adopted identically everywhere.

The pilot file starts with VD examples and requires explicit `adoption_state_to_verify_per_canton` when the
state is not yet fully ingested.
