# Aedifica Development Checklists

Status: delivery operating lists for the next software-development wave.

## Board Lists

Use these lists for GitHub Projects, a simple Kanban board, or manual triage.

| List | Entry rule | Exit rule |
|---|---|---|
| Inbox | Idea, bug, source update, partner feedback or research note. | Classified into epic, priority and milestone. |
| Needs Spec | Work is real but acceptance criteria are not clear. | Spec has scope, non-goals, fixtures and done criteria. |
| Ready | Small enough to implement and not blocked. | Engineer starts a branch or worktree. |
| In Progress | Active implementation. | PR opened or work handed back with blocker. |
| Review | Code/docs changed and need review. | Review findings resolved or accepted. |
| Validate | Local and CI verification pending. | Required commands and demo fixture pass. |
| Demo | Product slice ready for owner/partner review. | Feedback captured as issues or release approved. |
| Done | Shipped and documented. | No further action unless regression appears. |

## Issue Triage Checklist

- [ ] Is this Aedifica-specific, not another project?
- [ ] Does it map to an epic in [`epics-and-backlog.md`](epics-and-backlog.md)?
- [ ] Is the user value tied to a SIA phase or cross-phase memory need?
- [ ] Is the jurisdiction route clear: country, canton, commune, parcel?
- [ ] Does it need official sources, project files, office templates, model data or all of these?
- [ ] Does it require a new schema, fixture or validator?
- [ ] Does it touch a mutating adapter action?
- [ ] Does it have labels, priority, milestone and dependencies?

## Definition Of Ready

An issue is ready for implementation when:

- [ ] scope and non-goals are explicit;
- [ ] acceptance criteria are testable;
- [ ] source authority is defined for regulatory claims;
- [ ] fixture data exists or the issue includes creating it;
- [ ] dependencies are linked;
- [ ] expected files/modules are named;
- [ ] validation commands are listed;
- [ ] privacy or licensing constraints are noted.

## Definition Of Done

An issue is done when:

- [ ] implementation or document change is merged or ready to merge;
- [ ] validator/fixture coverage exists for new contracts;
- [ ] `python pilot/selfcheck.py` still passes when pilot contracts are touched;
- [ ] generated reports preserve trust states and source refs;
- [ ] docs are updated when behavior, contracts or limits change;
- [ ] GitHub issue is commented with delivered files and validation evidence;
- [ ] known residual limits are written down instead of hidden.

## Regulatory Claim Checklist

Before rendering a regulatory claim to a user:

- [ ] `claim_state` is one of `sourced`, `computed`, `assumption`, `unknown`, `conflict`, `decision`;
- [ ] `sourced` claims include source title/ref, locator, valid-as-of date and confidence;
- [ ] `computed` claims include formula and source refs for each input;
- [ ] `assumption` claims include the human check required;
- [ ] `unknown` claims include the missing source or next action;
- [ ] conflicts are not flattened into one answer;
- [ ] report footer says Aedifica is preparation/evidence, not an authority.

## Adapter Action Checklist

Before any adapter mutates a model, file, dossier or external system:

- [ ] adapter capabilities were checked for the target operation;
- [ ] current project phase and context were resolved;
- [ ] source/evidence before-state was captured;
- [ ] dry-run plan was produced;
- [ ] user-visible diff or preview exists;
- [ ] human approval was recorded in the ledger;
- [ ] execution result was verified;
- [ ] before/after evidence was saved;
- [ ] failure leaves the project in a known state.

## Release Checklist

Before calling a release ready:

- [ ] release goal matches one roadmap milestone;
- [ ] all P0 issues in the milestone are closed or explicitly deferred;
- [ ] local validation commands pass;
- [ ] GitHub Actions passes on the target branch;
- [ ] one offline demo fixture works without network access;
- [ ] one live-source demo has been run or explicitly marked unavailable;
- [ ] generated report includes known limits and trust footer;
- [ ] README or overview links to the new capability;
- [ ] partner-demo script is updated if the release changes the story.

## Partner Demo Checklist

- [ ] Start with the no-BIM value: parcel, constraints, envelope, unknowns.
- [ ] Show source links and trust states before any "AI" language.
- [ ] Show where the architect approves or decides.
- [ ] Show one phase handoff: permit blocker, tender assumption or site condition.
- [ ] If showing Archicad, present it as an adapter thread, not the product identity.
- [ ] End with the next real office workflow to validate.

## Documentation Maintenance Checklist

- [ ] If a source URL changes, update the source registry and affected docs.
- [ ] If a schema changes, update fixture, validator and human-readable contract.
- [ ] If a roadmap item ships, update roadmap status and issue list.
- [ ] If a strategic decision changes, add a new entry to `docs/strategy/decisions.md`.
- [ ] If a limitation is discovered, add it near the relevant spec instead of burying it in chat.
