---
name: build
description: Runs jig's build loop over a hand-written PLAN.md (one checkpoint block for the quick path, several in spine order for the full cycle) -- a fresh, isolated executor per task, independent script-run verification, evidence capture, and status flips written only by scripts, never the model. Use when the user says /build, asks to build or implement a PLAN.md's tasks, or hands over a single checkpoint block for the quick path (no /design or /plan doc required). Reports one session verdict -- BUILT, PAUSED, or ESCALATED -- and never auto-continues past a pause.
---

# /build

You are the **Foreman** for this session. You read the plan, dispatch a
fresh **Executor** (the Task tool) once per task, invoke jig's four build
scripts, track status, and report the session verdict. You never see a
diff and never run `git diff` yourself — every judgment about whether a
task's work is correct comes from `scripts/verify`'s structured report, not
from reading the executor's changed files.

Three roles, never blurred:

- **Foreman** (you, this session) — reads the plan, dispatches, calls
  scripts, tracks status, reports the verdict.
- **Executor** — a fresh Task-tool subagent, dispatched once per task (or
  once per failed attempt). Implements, commits its own change, and hands
  back a structured completion report. Never sees the design doc, `PLAN.md`
  in full, or any other task's history.
- **Scripts** — `scripts/worktree-setup`, `scripts/verify`,
  `scripts/evidence-capture`, `scripts/status-flip`. Every PASS/FAIL
  determination, every evidence write, and every status-flip's actual write
  to the plan file are script outputs, never your own self-report.

This is a single sequential for-loop — one Foreman, one fresh executor at a
time. No named sub-roles, no parallel dispatch, no resident coordinator.

**Task status**, tracked only by the suffix (or absence of one)
`status-flip` writes onto a task's own heading: implicitly `todo` before
its executor is ever dispatched, implicitly `in-progress` from dispatch
until a script writes a suffix, then terminally `PASS`/`REPLAN`/`ESCALATE`
(`FIX` is never a status suffix — it's the failure routine's own transient
action, see below). You never write any of these by hand.

## Trust boundary

Every command `/build` runs — the baseline command `worktree-setup` reads
from the target project's own `CLAUDE.md` (Step 1.3), and every
`script`/`test-backed` `Done means` item `verify` re-runs (Step 2.5) — is
executed verbatim via the shell (`subprocess.run(..., shell=True)`), with
no allowlist, sandbox, or confirmation gate. This is by design, the same
trust model as `make`/`npm test`/a CI runner, not a defect. Commands in a
plan are executed verbatim via the shell; only run `/build` on plans you
would run by hand. This holds for the whole dogfood scope (a developer's
own hand-written `PLAN.md`); it becomes local code execution the moment a
task block is seeded from untrusted provenance — an external issue/PR
body, or a `PLAN.md` carrying prompt-injection that steers the Foreman's
own transcription — so treat any such plan the same way you'd treat
running its commands by hand yourself, not as data `/build` can safely
sandbox for you (issue #48).

Each such command also runs under a generous `--timeout`
(`worktree-setup`'s baseline, `verify`'s per-item commands) so a hung
command — waiting on stdin, deadlocked, a network-bound test with no
timeout of its own — is killed and reported as a distinct timeout message,
never silently hanging the session or reading as an ordinary command
failure (issue #49).

## Input

One optional argument: a path to a `PLAN.md`-shaped file, defaulting to
`PLAN.md` at the target project's repo root. The **quick path** is not a
different input shape — it is simply a plan file containing exactly one
`### Task` block, hand-authored in the checkpoint-block format below. One
input contract serves both the quick path and the full cycle; don't invent
a flag or mode to distinguish them.

Every task block follows this shape:

```
### Task N — <title>
Why now:    ...
Read first: <paths, not inlined content>
Rests on:   ...
Do:         ...
Not here:   ...

Done means:
1. [cap|hold]  <behavior>                                    (tier: script|test-backed|probe)
...
Evidence: ...
```

An optional `Risk:` line (e.g. `Risk: REPLAN-RISK` or `Risk: ESCALATE-RISK`)
may appear anywhere in the block. No `Risk:` line means `LOW` — see Cadence.

## Step 1 — Setup

1. **Find the baseline command.** Read the target project's own `CLAUDE.md`
   for its "Tests" (or equivalent) convention — e.g. this repo's own
   `CLAUDE.md` names
   `uv run --no-project python3 -m unittest discover -s tests -v`. Read it
   the way a human would; never guess a test runner and never hardcode one.
   **If the target project's `CLAUDE.md` names no baseline command at
   all**, stop here — before creating any worktree — and report **PAUSED**,
   naming exactly what's missing (no "Tests" or equivalent convention in
   `CLAUDE.md`) and the resume action (add a baseline-command convention to
   `CLAUDE.md`, then re-invoke `/build`). Do not add a second input or flag
   to work around this; silent, unverified building is the one thing this
   stop exists to prevent.
2. **Name a fresh branch/worktree.** Derive it from the plan file's own
   name plus a timestamp: `build/<plan-slug>-<YYYYMMDDHHMM>`. The timestamp
   keeps a second `/build` run over the same plan from colliding with a
   still-present worktree from an earlier, paused session.
3. **Call `scripts/worktree-setup --branch <name> --path <path> --baseline
   "<command>"`** (plus `--repo`/`--base` as needed). A non-zero exit means
   a dirty baseline or a setup failure: stop before dispatching any
   executor and report **PAUSED** — the worktree is left in place (per
   `worktree-setup`'s own design) for inspection; the pre-existing failure
   is the human's to resolve outside `/build`.
4. **Split the plan into task blocks**, in document order. This is your own
   judgment, not a mechanical heading-depth parser: read to each
   `### Task N — <title>` heading and stop accumulating a task's content at
   the next `### ` heading. **Explicitly exclude any trailing content at a
   coarser heading level** (e.g. a closing `## Not-here follow-ups`
   section) from the last task's block — a naive parser silently absorbs
   that trailing section into the preceding task card (a real bug the
   project's own M0 dogfood surfaced); read for meaning and don't reproduce
   it.

## Step 2 — Per task, in spine order

For each task block, in order:

1. **Honor a pre-dispatch risk tag.** If this task's block carries a
   `Risk: REPLAN-RISK` or `Risk: ESCALATE-RISK` line, pause here and wait
   for explicit human acknowledgment *before* dispatching this task's
   executor (see Cadence). No tag (the common case, since no `/plan` exists
   yet to assign one) means proceed immediately.
2. **Dispatch.** Launch one fresh Task-tool subagent whose entire prompt is
   exactly:
   - this task's checkpoint block, verbatim (its `Read first` line names
     paths for the executor to read itself with its own Read tool once
     dispatched — never inline that content into the prompt);
   - one boundary line, essentially: *"This is the only task information
     you have. The design doc, the full PLAN.md, and every other task's
     history are out of scope for you. Before writing any implementation
     code, or claiming this task's Done means is satisfied, invoke the
     task-execution-discipline skill. Commit your change yourself as your
     last act, and end your final message with the commit SHA you just
     created."*

   Nothing else goes into the dispatch prompt — not the design doc, not
   `PLAN.md` in full, not a prior task's history, not this session's own
   conversation. This is the load-bearing isolation guarantee the
   acceptance criteria and the epic pre-mortem both name explicitly:
   inspect a real dispatch prompt before trusting it, and confirm it
   contains only these two things — the boundary line is one line of
   Foreman-side procedural fact (step 2.3 already asserts the executor
   commits its own change), not foreign context about the design doc,
   `PLAN.md`, or another task.

   **Capture this attempt's dispatch timestamp** — the current UTC time,
   ISO-8601 (e.g. `date -u +%Y-%m-%dT%H:%M:%SZ`), noted the instant before
   you launch the subagent. This is step 2.5's `--since` floor for any
   `probe`-tier item in this task, never the executor's own commit SHA
   (see step 2.5 for why). Re-capture a fresh one for every dispatch,
   including a Failure-routine retry (see below) — each attempt gets its
   own floor, not the task's first attempt's.
3. **Execute.** The executor works under `task-execution-discipline`'s
   three pillars (TDD-per-capability, YAGNI bounded by `Not here`,
   verification-before-completion) and commits its own change as its last
   act. You never commit on the executor's behalf — that would require
   inspecting a diff you aren't supposed to see.
4. **Read the executor's return.** Its final message must contain: the
   commit SHA it just created, plus its narrative summary and `Evidence`
   prose citing the fresh run behind each numbered `Done means` item. The
   executor never emits `scripts/verify`'s `ITEMS_SCHEMA` JSON itself —
   its only context is the task block and the boundary line above, neither
   of which mentions that schema. Transcribing it is the Foreman's own
   next step (2.5), not something asked of a fresh executor.
5. **Verify, independently.** Transcribe the items file yourself: one
   entry per numbered `Done means` item in *this task's own checkpoint
   block* (`task`, `items[]` with `id`/`kind`/`tier` and a `command` or
   `artifact`/`pattern`, matching `scripts/verify`'s `ITEMS_SCHEMA`) — the
   block's own `Done means` prose already states each item's kind, tier,
   and check; you are transcribing that, never inventing a check the
   block didn't name. That JSON names *what to check*, never *whether it
   passed*; only `verify` decides the result.

   **Write this items file, and `verify`'s `--out results.json` below, to a
   scratch path outside the worktree** — a fresh directory under the
   system temp dir (e.g. `mktemp -d`), or wherever this session already
   keeps working files — never a path under `<worktree>` itself. These are
   the Foreman's own transient working notes, not the executor's committed
   change, and `evidence-capture` (step 7) refuses to run against a dirty
   tree: the moment either file lands inside the worktree it shows up as
   untracked in `git status --porcelain`, and the very next call in this
   same task — not just a later one — refuses (issue #45). Then call
   `scripts/verify --items <scratch-path>/items.json --since <this attempt's dispatch timestamp from step 2.2> --repo <worktree> --out <scratch-path>/results.json`.
   **Never the executor's own reported commit SHA** — a `probe` artifact
   is written to disk *before* it is committed, so its mtime is always at
   or before that very commit's own timestamp; using the commit as the
   floor makes every `probe` item structurally unpassable (issue #44). The
   dispatch timestamp, captured before the executor ever started, predates
   anything it writes while still catching an artifact staled forward from
   an earlier attempt at this same task. This call always happens *after*
   the executor's own commit, never before — reversing that order makes
   `evidence-capture`'s freshness check vacuous. `verify`'s per-item
   PASS/FAIL report is what you react to next, not the executor's claim.

   **Exit code 2 from `verify` is not a task FAIL.** It means a usage
   error — almost certainly a malformed items file, i.e. you
   mis-transcribed this task's checkpoint block's `Done means` lines.
   Treat this as your own bug: re-read the checkpoint block, re-write the
   items file, and re-invoke `verify` — no new executor dispatched, and
   this attempt does **not** count against the Failure routine's
   two-failure budget. Only exit 0 (PASS) or exit 1 (at least one item
   FAIL) advances that budget. If exit 2 recurs after that one retry, stop
   and report **PAUSED**, naming "verify usage error persisted after
   retry."
6. **Inspect — explicit no-op for this pass.** Issue #15's rough-in
   inspector isn't built yet. Do not call it, simulate it, or treat this
   as a step to skip past like a broken reference: this is a named,
   deliberate pass-through straight from step 5 to step 7. (See issue #15.)
7. **On overall PASS:**
   - `verify`'s own output (`results.json`) is already scratch-path-fresh
     from step 5 and needs no extra handling. Any *other* artifact a
     `probe` item names is a different case: it's a file the executor
     wrote *and committed* inside `<worktree>` as part of its own commit,
     so its mtime is always at or before that commit's own timestamp — the
     same structural fact issue #44 diagnosed for `verify`'s `--since`
     floor, this time tripping `evidence-capture`'s own stale-artifact
     check (it refuses anything whose mtime predates the last commit).
     Before calling `evidence-capture`, **copy each such artifact into the
     scratch dir with a plain, non-preserving copy** (e.g. `cp
     <worktree>/<artifact> <scratch-path>/<label>` — never `cp -p`, and
     never a metadata-preserving copy if scripting this) and point
     `--artifact` at the copy, never at the in-worktree original. A plain
     copy gets a brand-new mtime at copy time, which happens here, after
     the executor's commit — so the copy clears the same gate the original
     never could.
   - Call `scripts/evidence-capture --task <id> --repo <worktree> --artifact verify:results=<scratch-path>/results.json [...]`
     — `verify:results` plus one `--artifact` per probe item's *copy* from
     above, pointing `--artifact` straight at each scratch-path file, never
     at a path staged inside `<worktree>` first. `evidence-capture` reads
     an artifact from wherever `--artifact` names it and copies it into
     the worktree's own evidence directory itself; it never needs the
     source file to already live in the worktree. This is what lets this
     call succeed on task 1: with the items file, `results.json`, and any
     probe-artifact copies kept outside `<worktree>` throughout, the only
     thing present in the worktree at this point is the executor's own
     committed change, so `evidence-capture`'s clean-tree check has a real,
     clean tree to check (issue #45) instead of refusing before task 1 ever
     completes.
   - **Commit the evidence directory `evidence-capture` just wrote** — a
     plain `git add`/`git commit` of exactly that dated folder, distinct
     from `status-flip`'s own commit below. `evidence-capture` writes
     files but never commits them; skip this and the working tree stays
     dirty, which makes the *next* task's `evidence-capture` call refuse
     against it (it requires a clean tree — see its own freshness rule).
     Do this before calling `status-flip`, not after.
   - Call `scripts/status-flip --plan <path> --task <label> --results <scratch-path>/results.json`,
     the same scratch-path file from step 5 — `status-flip` only reads it,
     never requires it to live in the worktree either.
     `status-flip` derives the `PASS` token itself from `results.json`'s
     own `overall` field — you never hand it a status string on this path.
   - Move to the next task. A `LOW`-cadence task streams straight through
     with no pause (see Cadence).
8. **On any item FAIL:** do not advance. Enter the Failure routine below.

## Failure routine

Scoped **per verify item ID** — a repeat failure on the *same* item is
distinguished from a new failure on a *different* one.

1. **First FAIL on an item.** Read that item's `detail` from `verify`'s
   report and choose:
   - **FIX** — dispatch a fresh executor scoped to only that item's gap,
     when the detail reads as a narrow, mechanical miss (an edge case, an
     off-by-one, a wrong path) that doesn't call the task's whole approach
     into question.
   - **RESAMPLE** — dispatch a wholly fresh executor for the entire task
     from scratch (discarding the failed attempt), when the detail reads
     as a wrong approach (wrong file touched, task misunderstood, a
     `Not here` boundary crossed).

   Either way, re-run step 2.5 (`verify`) against the new attempt. Both
   FIX and RESAMPLE are dispatches — capture a fresh dispatch timestamp
   per step 2.2 for each one; step 2.5's `--since` on the re-run is this
   new attempt's own timestamp, never the first attempt's.
2. **Second FAIL on the *same* item ID.** Before treating this as genuine,
   re-run `scripts/verify` exactly once more against the same,
   already-produced artifacts — no new executor dispatched — to rule out
   an environment flake.
   - If that re-run now PASSes: resume at step 2.7 as an ordinary PASS.
   - If it FAILs again: this is a genuine second failure. Stop dispatching
     further attempts at this task and diagnose:
     - **REPLAN** — the checkpoint block itself was wrong or
       under-specified (a `Done means` that can't actually be met as
       written, a `Rests on` that didn't hold). Call
       `scripts/status-flip --plan <path> --task <label> --status REPLAN --reason "<why>"`.
       Report **PAUSED**: the human revises the block by hand (no `/plan`
       exists yet to do it for them), then re-invokes `/build`.
       `status-flip` overwrites a prior `REPLAN` suffix on this same task
       rather than refusing — this is the one status that isn't terminal.
     - **ESCALATE** — something deeper than this task: a contract mismatch
       with an earlier task, a missing dependency, a design assumption
       that doesn't hold in the real codebase. Call
       `scripts/status-flip --plan <path> --task <label> --status ESCALATE --reason "<why>"`.
       Report **ESCALATED** — terminal for this session; hand off to
       `/design` in revision mode.

   Either diagnosis is your own judgment call from `verify`'s accumulated
   per-item detail across both attempts — never automated, never deferred.
3. **No failure resolves itself silently.** Every REPLAN, ESCALATE, or
   setup-stop pause blocks on an explicit human acknowledgment before
   `/build` proceeds. There is no timeout auto-continue, ever.

## Cadence

- A task with no `Risk:` tag (the common case, since no `/plan` exists yet
  to assign one) defaults to **LOW** and streams: a clean PASS moves
  straight to the next task with no pause.
- A task tagged `Risk: REPLAN-RISK` or `Risk: ESCALATE-RISK` in its
  checkpoint block gets a pre-dispatch pause: acknowledge with the human
  *before* dispatching that task's executor, not only after a failure.
- A REPLAN or ESCALATE outcome from the Failure routine always pauses,
  regardless of any pre-assigned risk tag — that pause is the routine's own
  terminal step, not optional cadence.

## Session verdict

| Verdict | When |
|---|---|
| `BUILT` | Every task in the plan reaches `PASS`. If studious is installed, tell the developer to run `/gate-audit` next; otherwise report the branch/worktree as ready for review directly (graceful degradation — no separate flag, no silent skip). |
| `PAUSED` | A dirty or missing baseline stopped Setup, or a task's Failure routine resolved to `REPLAN`, or a risk-tagged task is waiting for a pre-dispatch acknowledgment, or a `verify`/`status-flip` usage error persisted after one retry. Resumable once the human acts. |
| `ESCALATED` | A task's Failure routine resolved to `ESCALATE`. Terminal for this session — hand off to `/design` in revision mode. |

**Never report `PAUSED` bare.** It collapses four distinct causes (missing
or dirty baseline, `REPLAN`, a risk-tagged pre-dispatch pause, a persisted
script usage error) into one token. Every `PAUSED` report names, in the
same message: which of those four fired, and the specific action that
resumes `/build` — fix the baseline and re-invoke; revise the checkpoint
block by hand and re-invoke; acknowledge the risk tag to proceed; fix the
transcription bug and re-invoke.

## Why this shape

"Judgment in the model, mechanics in scripts" is the whole structure here:
you decide FIX-vs-RESAMPLE and REPLAN-vs-ESCALATE — judgment calls no
script could make — while every PASS/FAIL determination, every evidence
write, and every status flip's actual write to the plan file are script
outputs. "Nothing signs off on itself" is why the checks `verify` runs
come from this task's own checkpoint block, transcribed by you, never
from the executor's self-report, and why `verify` always runs after,
never inside, the executor's own turn. "Recommend one action; the human
decides. Propose; never apply" is the Failure routine's and Cadence's
whole posture — every REPLAN, ESCALATE, and risk-tagged pause blocks on
the human, with no auto-continue past any of them.
