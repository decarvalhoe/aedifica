# W19-06 - Aedifica feedback to NOMOS core

Status: design note for NOMOS CKM epic #481, especially CKM-03 Canon Promotion
and CKM-08 cite-or-abstain trust tiers.

## Purpose

Aedifica already carries two product-level trust mechanics that should be promoted
back into NOMOS core as conceptual input, not as code coupling:

- document curation by the liable architect, via
  `Document.validation_level: pending -> canonical -> indicative -> refused`;
- user-facing claim trust states, via
  `Claim.state: sourced | computed | assumption | unknown | conflict | decision`.

This note defines how those mechanics should inform NOMOS Canon Promotion and
trust-tier design while preserving the W19 rule: Aedifica consumes versioned
NOMOS artifacts only, never NOMOS implementation code.

## Aedifica mechanics worth promoting

### Document validation level

In Aedifica, a project document is not just an uploaded file. It is a source under
curation by the architect responsible for the project. The existing states are:

| Aedifica state | Product meaning | NOMOS core analogue |
| --- | --- | --- |
| `pending` | Submitted or captured, not yet relied on. | `pending_review` promotion candidate. |
| `canonical` | Accepted by the architect as project canon. | Approved canon promotion inside a governed scope. |
| `indicative` | Useful context, but not authoritative enough for reliance. | Non-certified or advisory corpus member. |
| `refused` | Explicitly rejected for reliance. | Rejected or archived promotion candidate. |

The important contribution is the separation between official authority and
project authority. A `canonical` project document can be reliable inside its
project or atelier scope without being an official public source.

### Six claim trust states

Aedifica renders every user-facing claim as one of six states:

| Aedifica state | Contract |
| --- | --- |
| `sourced` | Directly supported by source references. Regulatory sourced claims must have `source_refs`. |
| `computed` | Derived from sourced inputs and a formula. |
| `assumption` | Useful but explicitly unproven; requires human check. |
| `unknown` | Missing or inaccessible information; cite-or-abstain should abstain. |
| `conflict` | Sources disagree or scope is ambiguous; escalation required. |
| `decision` | Human-approved project choice with actor, timestamp, and basis. |

This is a better primitive than a single confidence score. It describes why a
statement can or cannot be used, and it gives the UI and retrieval layer a stable
way to decide whether to answer, abstain, or ask for human validation.

## Proposed mapping to NOMOS facets and tiers

NOMOS should keep `trust_tier` and `provenance` distinct.

| NOMOS field | Recommended values | Rule |
| --- | --- | --- |
| `trust_tier` | `certified`, `indicative`, `unverified` | How reliance-safe the atom is in its declared scope. |
| `provenance` | `official`, `metier_bible`, `user_promoted` | Where the authority claim comes from. |
| `confidentiality` | `public`, `org`, `project`, `confidential` | Who may retrieve or quote it. |
| `validation_level` | `pending`, `canonical`, `indicative`, `refused` | Promotion lifecycle before an atom enters active canon. |

Critical rule: `official` and `user_promoted` must never be collapsed. A user
promoted source may become canonical for a project or atelier, but citations must
still say that its provenance is `user_promoted`, not `official`.

## Canon Promotion implications for CKM-03

Canon Promotion should model a governed promotion request:

1. A user submits or selects a source.
2. The source is faceted with nature, discipline, activity, scope, provenance,
   confidentiality, and applicability metadata.
3. Rights are checked for the target scope.
4. A validator accepts it as `canonical`, downgrades it to `indicative`, leaves it
   `pending`, or marks it `refused`.
5. The resulting atom carries both its validation level and provenance.
6. If confidential, retrieval is restricted to the project or organization silo.

Aedifica's `validated_by`, `validated_at`, `confidential`, document versions, and
access grants are product evidence that this lifecycle is useful before NOMOS
formalizes it.

## Cite-or-abstain implications for CKM-08

Cite-or-abstain should use trust state as a gate, not just as decoration:

| Claim state | Retrieval/generation behavior |
| --- | --- |
| `sourced` | May answer, with citations. |
| `computed` | May answer, with formula and input citations. |
| `decision` | May report as a human decision, not as external authority. |
| `assumption` | Must label as assumption and ask for verification. |
| `unknown` | Must abstain and name the missing source/data. |
| `conflict` | Must abstain or escalate with conflicting citations. |

This makes refusal measurable: a correct assistant is not only one that cites
when it answers, but one that abstains when the active corpus is not entailment
safe.

## Boundary for Aedifica W19

This note does not introduce a runtime dependency from Aedifica to NOMOS. The
boundary remains:

- Aedifica receives versioned NOMOS bundle artifacts.
- NOMOS core may adopt these concepts in CKM-03 and CKM-08.
- Aedifica may later map bundle facets into local nullable fields, behind feature
  flags, without requiring NOMOS source code.

This keeps both products alive: Aedifica continues to ship with its existing
trust contract, and NOMOS gets concrete product feedback for its core promotion
and trust-tier model.
