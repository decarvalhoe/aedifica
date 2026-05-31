# Aedifica Agent Demo Realignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebaseline Aedifica so the first MVP wave proves the full ArchiOS scope with a visible agent-to-architecture-software demo.

**Architecture:** Keep the neutral engine, jurisdiction packs, trust contract and project memory as the spine. Add an early `R1A` release that exercises the universal adapter lifecycle through an Archicad-shaped fixture and later live Archicad JSON calls. Documentation, code fixtures, selfcheck coverage and GitHub issues all point to the same sequence.

**Tech Stack:** Markdown planning docs, Python stdlib pilot, GitHub CLI issues/milestones, existing offline CI validators.

---

### Task 1: Product Decision And MVP Spec

**Files:**
- Create: `docs/specs/mvp1a-agent-to-architecture-software-demo.md`
- Modify: `docs/strategy/decisions.md`

- [x] **Step 1: Record the product decision**

Add a new accepted decision stating that `R1A Agent-To-Software Demo` moves before workspace productization.

- [x] **Step 2: Write the R1A spec**

Define goals, inputs, outputs, demo flow, safety gates, live/fallback behavior and acceptance criteria.

- [x] **Step 3: Link the spec from roadmap and overview**

Ensure the spec is discoverable from `README.md`, `docs/overview.md` and planning docs.

### Task 2: Roadmap And Backlog Rebaseline

**Files:**
- Modify: `README.md`
- Modify: `docs/overview.md`
- Modify: `docs/mvp-roadmap.md`
- Modify: `docs/planning/software-development-plan.md`
- Modify: `docs/planning/software-roadmap.md`
- Modify: `docs/planning/epics-and-backlog.md`
- Modify: `docs/planning/development-checklists.md`
- Modify: `docs/planning/README.md`

- [x] **Step 1: Insert R1A/R1B release sequence**

Use `R1A Agent-To-Software Demo` for the first spectacular proof and `R1B Project Workspace` for the existing project-workspace productization.

- [x] **Step 2: Add new epics**

Add epics `AED-E14` to `AED-E23` covering product doctrine, demo, CLI orchestrator, adapter action contract, Archicad live bridge, design intent generation, diff/approval, ledger evidence, partner validation and later adapter expansion.

- [x] **Step 3: Add issue-ready tasks**

Add granular issues `AED-052` onward with priority, milestone, labels and done criteria.

### Task 3: Offline Agent-To-Software Demo Contract

**Files:**
- Create: `pilot/model/design_intent_fixture.json`
- Modify: `pilot/model_bridge_demo.py`
- Modify: `pilot/demo_run.py`
- Modify: `pilot/selfcheck.py`

- [x] **Step 1: Add structured design intent fixture**

Create an architect-intent fixture with property updates and an annotation item tied to a selected Archicad-shaped model snapshot.

- [x] **Step 2: Add dry-run and diff helpers**

Extend the model bridge with intent loading, dry-run item planning, before/after summaries and a partner-demo object.

- [x] **Step 3: Surface the demo in the CLI path**

Make `python pilot/demo_run.py` print the number of model bridge actions and whether they are blocked.

- [x] **Step 4: Add selfcheck coverage**

Check that design intent loads, dry-run plans property updates, the diff includes before/after text and the partner demo stays fixture-safe.

### Task 4: GitHub Issue Wave

**Files:**
- GitHub repository: `decarvalhoe/aedifica`

- [x] **Step 1: Create or update labels**

Ensure `demo` exists and reuse existing `product`, `adapter`, `backend`, `frontend`, `docs`, `validation`, `security`, `architecture`, `P0`, `P1`, `P2`, `P3`.

- [x] **Step 2: Create milestones**

Create `R1A Agent-To-Software Demo` and update existing release milestone descriptions when needed.

- [x] **Step 3: Open issues**

Open granular issues from the rebaselined backlog.

- [x] **Step 4: Close locally completed issues**

For issues covered by this change, add a comment with delivered files and verification evidence, then close them.

### Task 5: Verification And Publishing

**Files:**
- Local repository and GitHub branch

- [ ] **Step 1: Run offline verification**

Run:

```powershell
python pilot/selfcheck.py
python tests/contracts/run_contracts.py
```

Expected: both exit `0`.

- [ ] **Step 2: Review diff**

Run:

```powershell
git diff --stat
git diff -- README.md docs pilot tests
```

Expected: only intentional docs and pilot files changed, plus existing unrelated `.gitignore` remains unstaged unless intentionally included.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add README.md docs pilot tests
git commit -m "feat: rebaseline agent-to-software demo"
git push
```

Expected: branch push succeeds.
