# ADR-0001: Neutral Engine And Jurisdiction Packs

Date: 2026-05-29

Status: Accepted

## Context

Aedifica must serve Swiss architects first without becoming a Vaud-only, Lausanne-only, or Archicad-only tool.
The pilot already proves a concrete regulatory route:

```text
project parcel -> commune/canton -> Federal core + canton overlay + commune overlay
```

The same product also needs to support later BIM/model adapters, permit dossiers, cost workflows, project
memory, and construction-management tasks. These capabilities should share one evidence and decision contract.

## Decision

Aedifica is split into:

1. A tool- and jurisdiction-neutral engine.
2. Jurisdiction packs that provide phase models, source registries, regulatory layers, terms, and localized
   renderings.
3. Adapters that inspect or mutate external systems only through explicit, logged commands.

The first jurisdiction pack is `CH`, with `VD` and commune overlays in the pilot. The SIA phase model is part
of the Swiss pack, not hardcoded into the engine.

## Engine Responsibilities

The neutral engine owns:

- canonical-unit schema and validation;
- regulatory route selection;
- project knowledge regime selection: context-first for small projects, RAG/DB for large projects;
- claim provenance and trust contract;
- decision and action ledger;
- conflict detection between active sources;
- adapter command lifecycle: inspect, dry-run, approve, execute, verify, log.

The engine does not own:

- Swiss-specific legal source lists;
- SIA phase labels;
- Archicad/Revit/IFC command details;
- commune-specific zoning semantics;
- localized legal wording.

## Jurisdiction Pack Responsibilities

A jurisdiction pack provides:

- phase model, such as SIA phases for Switzerland;
- source registries, including legal instruments and update cadence;
- regulatory layers, such as federal, canton, and commune packs;
- canonical term mappings across languages;
- output disclaimers and risk language appropriate to the jurisdiction;
- adapter-specific constraints only when imposed by local practice or law.

The active pack route is selected at query time. Inactive packs must not leak into project claims.

## Interface Sketch

```text
ProjectContext
  project_id
  parcel_ref
  country
  canton_or_region
  commune
  phase
  knowledge_regime

RegulatoryRoute
  active_layers[]
  inactive_layers[]
  selected_at
  selected_by

CanonicalQuery
  project_context
  intent
  required_unit_types[]
  source_filters

ClaimEnvelope
  claim
  claim_type
  confidence
  source_refs[]
  assumptions[]
  conflicts[]
  valid_as_of

AdapterCommand
  command_id
  adapter
  operation
  target_refs[]
  dry_run_required
  approval_required
  evidence_before[]
  evidence_after[]
```

## Adapter Lifecycle

Every mutating command follows this sequence:

```text
intent -> inspect -> dry-run plan -> evidence snapshot -> human approval -> execute -> verify -> ledger entry
```

Commands that cannot produce a dry-run plan are read-only until a project owner explicitly approves a
one-off exception. The exception itself must be logged.

## Consequences

- Adding another Swiss commune is a data-pack task, not an engine rewrite.
- Adding another country is a new jurisdiction-pack family, not a fork.
- Adding Archicad, IFC, Revit, or document workflows is an adapter task behind the same command lifecycle.
- Output quality depends on source freshness and provenance, so every pack needs version metadata and review
  cadence.

## Non-Goals

- No automatic legal authority. Aedifica prepares evidence; the architect decides.
- No direct model mutation from natural language.
- No per-project regulatory corpus rebuild when a shared pack already exists.
- No Archicad-specific core abstractions.
