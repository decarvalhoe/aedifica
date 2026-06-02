# Commune Support Policy

Aedifica separates project routing from commune pack availability. The route
can resolve a project as `CH + canton + commune` before every local rule has
been ingested, but the trust state must show what is usable today.

## Support States

| State | Meaning | Product Behavior |
|---|---|---|
| `supported` | Pack is ingested, validated, source-versioned and inside its review window. | Regulatory claims may render as `sourced` when they carry source refs. |
| `seed` | Pack exists as a pilot or seed pack but needs partner-office review before production reliance. | Render claims as `sourced` only for checked fixture/demo scope; otherwise add a human check. |
| `on_demand` | Commune has no pack yet, but can be ingested for a project. | Create the route with the commune marked missing, keep envelope claims `unknown`, and open an ingestion task. |
| `unsupported` | Source access, language, rights or project risk makes ingestion unavailable for now. | Refuse sourced regulatory claims and show the required external authority/specialist check. |

## Current Pilot Coverage

| Commune | State | Notes |
|---|---|---|
| Lausanne | `seed` | Official RPGA pack ingested for MVP1 and fixture validation. Production use still needs architect verification. |
| Pully | `seed` | Second-commune pack proving the selector handles a different rule style. |
| Other communes | `on_demand` | Route can be created, but the commune layer is missing until an ingestion checklist is completed. |

## Trust Rules

- A missing commune pack never becomes a zero value.
- Expired `review_due` creates a warning, not a crash.
- A regulatory claim without current source refs remains `unknown` or requires a human check.
- Unsupported communes are product-scoped refusals, not engine errors.
