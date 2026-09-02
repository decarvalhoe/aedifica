# Partner Pilot Kit — live Archicad session

> Status: **prepared playbook, ready to run.** One self-contained procedure for a
> confident first joint session with the partner architect, on their **real
> Archicad model**, doing **clear, safe, pre-rehearsed actions**.
>
> It consolidates and supersedes the scattered notes
> ([`partner-agent-demo-protocol.md`](partner-agent-demo-protocol.md),
> [`../architecture/archicad-json-live-setup.md`](../architecture/archicad-json-live-setup.md),
> [`../security/partner-data-redaction.md`](../security/partner-data-redaction.md)).

## 0 · What this is (and is not)

- **Goal:** prove the loop *on the partner's real model* — `inspect → missing-data
  audit → dry-run diff → approval boundary` — and decide the next workflow to
  validate. Closes the acceptance side of **#105 / #115**.
- **Session 1 is READ-ONLY.** The current live connector inspects the model but does
  not execute a write against Archicad. Mutation is a later, separately scoped pilot.
- **The Archicad session stays local.** The harness runs on the partner's machine;
  only a manually reviewed, redacted transcript may be shared afterwards.

## 1 · Status of the foundation (verified)

| Piece | State |
|---|---|
| Live Archicad JSON connection (`product info`, `selected elements`) | ✅ built (stdlib `urllib`), runs **`mode=live`** — verified against the replay server |
| Non-mutating harness (`inspect → audit → dry-run`, redacted) | ✅ `pilot/archicad_harness.py` |
| Seat-free stand-in (rehearse without Archicad) | ✅ `pilot/replay_server.py` |
| Approval boundary (simulation blocked without a scoped approval) | ✅ engine + product |
| Read-only inspection **inside the product UI** | ✅ built in #190; requires a backend that can reach the endpoint |
| Live mutation from the product | ⏳ not implemented; out of scope for session 1 |

The read-only path is ready for partner validation. Its invariants are proven
against the official-shaped bridge by `pilot/partner_preflight.py` — `mode=live`, a
real `before` value, `mutated=false`, an unchanged model on re-read and a redacted
transcript — which is what closed the acceptance side of #105 and #115. A real seat
changes the values measured, not the protocol: see
[partner-pilot-autonomous.md](partner-pilot-autonomous.md).

### Runtime topology

The endpoint is contacted by the **FastAPI backend**, not directly by the browser.
The hosted Fly backend therefore cannot reach `127.0.0.1:19723` on the partner's
computer. Use the local CLI harness for session 1, or run the Aedifica API locally if
the product UI must exercise the connector. The hosted demo remains the environment
for the separate product field test in #312.

## 2 · Roles

- **You (facilitator):** drive the procedure, narrate the loop, capture decisions.
- **Partner (architect):** runs Archicad, selects elements, judges usefulness, owns the data.
- **Aedifica:** the tool — proposes, shows the diff, never acts without approval.

## 3 · The partner brings

- A real Archicad project they are comfortable showing (or a representative copy).
- Archicad **JSON interface enabled** (Graphisoft JSON/Python interface), default
  port range **19723–19743**.
- 30–45 min, screenshare or in person, on **their** machine.

## 4 · Pre-flight (run *in advance*, not in the session)

Do this a day before, on the partner's machine (screenshare is fine). It must end green.

```bash
# 0) (no Archicad needed) rehearse the exact commands against the stand-in:
python pilot/replay_server.py --port 8077        # terminal A
python pilot/archicad_harness.py --endpoint http://127.0.0.1:8077   # terminal B
#    expect: "Archicad harness OK · mode=live · missing metadata=N · mutated=False"

# 1) with Archicad OPEN and a model loaded, point at the real bridge:
python pilot/archicad_harness.py --endpoint http://127.0.0.1:19723 --no-fallback
```

**Green** = `mode=live` and `mutated=False`. **Red** → fix with the table in §A and
re-run. `--no-fallback` makes a non-ready bridge fail loudly instead of silently
using fixtures (so pre-flight can't pass on a false positive).

## 5 · Run-of-show (the session)

Each step: **the partner does X → we run Y → look at Z → go / abort**. A replay run
can keep the demonstration moving after a failure, but it does not satisfy the live
acceptance criteria for #105 or #115.

| # | Joint action | Command / step | Observe | Gate |
|---|---|---|---|---|
| 1 | Connect | `archicad_harness --endpoint …:19723 --json` | `product_info.running=true`, real version | live ok → continue; else fixture fallback |
| 2 | Partner **selects one zone/space** in Archicad | same harness run | `selection.count ≥ 1`, normalized elements | empty → "select a zone and rerun" |
| 3 | See what the model lacks | (same run) `missing_metadata_audit` | `missing_count` + which properties | partner confirms it's real/manual today |
| 4 | **Dry-run** a property update (e.g. `RoomUsage → office`) | (same run) `dry_run` | **before/after diff**, `mutating=false` | partner judges the diff clear enough to approve |
| 5 | The **safety boundary** | (narrate) the traced simulation stays blocked without a scoped approval | nothing changed in the model | partner accepts the boundary as necessary |

The four questions to ask while doing it (from the original protocol): does the
inspection match your manual work? is the diff clear enough to approve? is fixture
mode acceptable as a local proof? which workflow next — room data, annotations,
exports, sheets, or quantities?

## 6 · Data & privacy (state this out loud)

- The harness and bridge run **locally**; no model payload is sent to the hosted demo.
- The harness returns a **redacted** transcript (`pilot/redaction.py`) — no client
  names / paths should appear in the shareable copy. Review it manually because the
  redaction pass is a safety net, not a guarantee.
- Session 1 does **not** write to the model.
- Get a one-line verbal **consent** to run read-only inspection before step 1.

## 7 · Success criteria

- The architect can **restate the loop**: context → model → proposed items → diff → approval.
- They name **at least one task** this saves time on.
- They **accept the approval boundary** as protection, not friction.
- They **agree on the next workflow** to validate on a real model.
- They do **not** read the product as Archicad-only.

## 8 · Capture log (fill live)

```
Date / partner / role / Archicad version / JSON bridge port:
Model shown / phase / sensitivity limits:
Step 1 connect:      live? ___   notes:
Step 2 selection:    count ___   "matches manual?" quote:
Step 3 audit:        missing ___ partner reaction:
Step 4 dry-run diff: clear to approve? ___ quote:
Step 5 boundary:     accepted? ___
Next workflow chosen: room data | annotations | exports | sheets | quantities
Blockers / data constraints:
Decision: go to live-mutation pilot?  yes / no — because:
```

## 9 · After the session

- Turn the capture log into issue updates on **#105** (verify live dry-run) and
  **#115** (first model audit); record blockers/missing action types as new issues
  under the W2 epic **#171**.
- If "go": open a new, narrowly scoped issue for a reversible live-mutation pilot.
  #190 already delivered read-only inspection in the product; it did not implement
  external mutation.

## A · Troubleshooting (consolidated)

| Symptom | Fix |
|---|---|
| `endpoint unavailable` | Archicad not running / JSON interface off → enable it, confirm the port (19723–19743) |
| `API.GetProductInfo` fails | wrong port or interface disabled → scan the range, re-enable |
| `selection.count = 0` | partner must select ≥1 zone/space and rerun |
| harness "OK" but `mode=fixture_fallback` | endpoint didn't answer; add `--no-fallback` to see the real error |
| capability missing for an action | mark the planned item unsupported; pick another workflow |
| any uncertainty about data | stay read-only; the replay server reproduces the whole loop with zero client data |

## B · Running the pilot without a partner

The whole protocol is executable without a seat or a scheduled session — see
[partner-pilot-autonomous.md](partner-pilot-autonomous.md). The commands are the
same ones used here, with `--endpoint` pointed at the replay stand-in, and they
emit the redacted evidence consumed by #330, #105, #115, #312 and #331 into
`docs/validation/evidence/`. Use the joint session above when you want the
architect's judgement; use the autonomous run whenever you want the invariants
re-proven.
