# Later Track Spec — Tender And Quantity Workflows

Issue: #18

## Goal

Support phase `41` by turning quantities, cost taxonomy and project assumptions into structured tender packages,
offer comparisons, and memory records.

## Inputs

- Project context and phase `41` objectives.
- Quantity source: BIM/model extraction, schedule, spreadsheet, manual register.
- Cost/tender structure: CFC, eCCC, NPK/CAN, office structure, or future `.crbx`/IfA18 bridge.
- Office templates and project assumptions.
- Offers, exclusions and clarifications from contractors.

## Pipeline

1. Collect and version quantities.
2. Map quantities to the selected cost/tender taxonomy.
3. Draft position descriptions or tender sections.
4. Mark assumptions, exclusions and missing measurements.
5. Compare offers on normalized scope.
6. Push assumptions, decisions and unresolved items into project memory.

## Outputs

- Quantity register.
- Taxonomy mapping table.
- Draft tender descriptions.
- Offer comparison matrix.
- Assumptions and exclusions log.
- Decision/memory records for selected offers and open risks.

## Boundaries

- Aedifica does not certify quantities.
- Export to `.crbx`/IfA18 is a later adapter target, not required for the first spec.
- The architect/economist validates quantities, scope and adjudication logic.

## Success Criteria

- Quantities remain linked to source/version.
- Tender descriptions expose assumptions instead of hiding them.
- Offer comparison distinguishes price differences from scope differences.
- Decisions and exclusions survive into later phases.
