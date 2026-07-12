# Design: The /build SKILL.md (dispatch loop, failure routine, cadence, verdicts)

## Problem & persona

Primary persona, verbatim from `PRODUCT.md`:

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

That persona's problem today: `skills/build/SKILL.md` is still the M1 stub
("Do not invoke for actual build work yet; there is no behavior behind this
file"). The mechanics that make `/build` trustworthy already exist —
`scripts/worktree-setup`, `scripts/verify`, `scripts/evidence-capture`
(story `build-scripts`, merged into `epic/m4-build-core` at `62387bc`) and
the shared discipline text (`skills/task-execution-discipline/SKILL.md`,
story `discipline-skill`) — but nothing yet calls them in sequence. Without
an orchestration layer, the persona still has no `/build` to invoke at all:
the scripts are correct in isolation but inert, and the discipline skill has
no for-loop to be dispatched into. Issue #14 splits `/build`'s three roles
across two stories — Scripts (done) and Foreman/Executor dispatch (this
story). This doc covers exactly the second half: the dispatch loop, the
failure routine, cadence, and the session verdict — the prose
`skills/build/SKILL.md` needs to replace its stub with.

This is also the concrete unlock for the epic goal: "dogfood the quick path
(single task block → `/build` → `/gate-audit`) before `/design`/`/plan`
exist." `/plan` (M3) doesn't exist, so there is no `plan-lint`-generated,
machine-validated `PLAN.md` to consume — only a hand-written one, in the
same checkpoint-block shape this project's own M0 dogfood produced and
hand-validated (`PLAN-viva-unified-session.md`, branch
`docs/m0-paper-dogfood`). This story's job is to make that hand-written
artifact buildable today, not to wait for `/plan` to exist first.

Without this story: the three merged scripts sit unused, the discipline
skill never gets dispatched into a fresh executor's context, and the
persona is back to "ad hoc prompting" — exactly the alternative
`PRODUCT.md` says jig exists to replace.

## Proposed design

Two things change behavior. `skills/build/SKILL.md` — its stub frontmatter
description and body are replaced with the Foreman's real orchestration
procedure. And `scripts/status-flip` — one new script, this story's own
addition, the mechanical status-flip writer `docs/design/build-scripts.md`'s
Open questions left unresolved ("where 'status flips' actually lands") and
asked this doc to make a call on; see "Status-flip persistence" below for
why a script, not the model, performs that write. The three already-built
scripts (`worktree-setup`, `verify`, `evidence-capture`) are called, not
modified, by this story. Nothing under
`skills/task-execution-discipline/` changes (it's read, not edited).

What follows is the shape of that procedure — behavior-level, matching
`docs/design/build-scripts.md`'s own convention of leaving literal
prompt/flag wording to the build phase, since exact SKILL.md prose is an
implementation decision, not a design-review question per
`reference/design-doc-contract.md`'s non-requirements section.

### Roles, restated for this half

- **Foreman** — the main `/build` session (the model invoking the skill).
  Reads the plan, dispatches, invokes the four scripts, tracks status,
  reports the verdict. Per issue #14: **never sees a diff** — it inspects
  outcomes only through `verify`'s and `evidence-capture`'s structured
  output, never by reading the executor's changed files or running
  `git diff` itself.
- **Executor** — a fresh subagent (Claude Code's Task tool) dispatched once
  per task. Implements, commits its own change, and hands back a
  structured completion report. Never sees the design doc, `PLAN.md` in
  full, or any other task's history.
- **Scripts** — three of the four are already built (`worktree-setup`,
  `verify`, `evidence-capture`; story `build-scripts`); this story adds a
  fourth, `status-flip` (see "Status-flip persistence"), and is the first
  real caller of all four.

### Input contract

`/build` takes one optional argument: a path to a `PLAN.md`-shaped file,
defaulting to `PLAN.md` at the target project's repo root if omitted. The
**quick path** (`PRODUCT.md` critical user journey 2) is not a different
input shape — it is simply a `PLAN.md` containing exactly one `### Task`
block, authored by hand in the same checkpoint-block format the M0 dogfood
validated (`Why now` / `Read first` / `Rests on` / `Do` / `Not here` /
`Done means` (numbered `cap`/`hold` items, each tagged with a verification
tier) / `Evidence`). One input contract serves both critical user journey 1
(full cycle, once `/plan` exists) and journey 2 (quick path, today) — no
separate flag or mode is needed to distinguish them.

### Step 1 — Setup

The Foreman:

1. Reads the target project's own `CLAUDE.md` "Tests" (or equivalent)
   convention to find its baseline verification command — e.g. this very
   repo's own `CLAUDE.md` names
   `uv run --no-project python3 -m unittest discover -s tests -v`. This
   resolves `docs/design/build-scripts.md`'s open question ("how the
   target project's baseline verification command reaches
   `worktree-setup`"): the Foreman reads it from that project's `CLAUDE.md`
   the same way a human would, rather than `worktree-setup` guessing or
   hardcoding one project's test runner. **If the target project's
   `CLAUDE.md` names no baseline command** (no "Tests" section or
   equivalent — the realistic state for `PRODUCT.md`'s secondary persona,
   who per that document's own admission may have no other jacquardlabs
   tooling or convention installed at all), the Foreman does not guess one
   or silently proceed with no baseline check: it stops before any
   worktree is created and reports **PAUSED**, naming the missing
   convention explicitly and the action that resolves it: add a "Tests" (or
   equivalent) baseline-command convention to the target project's
   `CLAUDE.md`, then re-invoke `/build`. No second input or flag is added
   to satisfy this case (the Input contract above stays a single optional
   plan-path argument) — silent unverified building is the one failure
   mode "Standalone-capable" (graceful, never silent, degradation) rules
   out here, not a reason to widen `/build`'s own input shape.
2. Derives a branch/worktree name from the plan file's own name plus a
   timestamp, e.g. `build/<plan-slug>-<YYYYMMDDHHMM>` — timestamped so a
   second `/build` run over the same `PLAN.md` (a resample after a paused
   session, say) doesn't collide with the first run's still-present
   worktree. (`worktree-setup` fails loudly, not silently, on a genuine
   collision — this naming choice exists to make a **deliberate** rebuild
   distinguishable from an accidental name clash.)
3. Calls `scripts/worktree-setup --branch <name> --path <path> --baseline
   "<command>"`. A non-zero exit (dirty baseline or a setup failure) stops
   the session before any executor is dispatched. Session verdict:
   **PAUSED** — the pre-existing failure is the human's to resolve outside
   `/build`; the worktree is left in place (per `worktree-setup`'s own
   design) for inspection.
4. On a clean baseline, reads the plan file and splits it into ordered task
   blocks. Splitting is the Foreman's own judgment, not a mechanical
   heading-depth parser: it reads to each `### Task N — <title>` heading in
   document order (spine order) and stops accumulating a task's content at
   the next `### ` heading of the same level, explicitly excluding trailing
   material at a coarser heading level (e.g. `## Not-here follow-ups`) from
   any task's block. This is a deliberate difference from a future
   mechanical `plan-lint`: the M0 friction report (`FRICTION-REPORT.md`,
   finding 6) documents a real bug in naive heading-depth splitting — a
   coarser trailing heading gets silently absorbed into the last task card.
   A model reading the whole document for meaning does not have to
   reproduce that bug; this doc calls it out explicitly precisely because
   `/build` is taking on a piece of parsing responsibility `/plan`/
   `plan-lint` hasn't shipped yet (see Out of scope).

### Step 2 — Per task, in spine order

For each task block:

1. **Dispatch.** The Foreman dispatches one fresh executor (Task tool)
   whose entire prompt is: the task's checkpoint block verbatim (which
   itself names `Read first` pointers as paths, not inlined content — the
   executor reads those files itself, with its own Read tool, once
   dispatched inside the worktree) plus one explicit boundary/trigger line:
   this is the only task information the executor receives; the design
   doc, `PLAN.md` in full, and every other task's history are out of scope
   for it; before writing implementation code or claiming `Done means` is
   satisfied, it must invoke `task-execution-discipline`. That last clause
   is a deliberate belt-and-suspenders choice over relying solely on the
   skill's model-invoked auto-trigger — see Alternatives considered.
   Nothing else goes into the dispatch prompt. This is the acceptance
   criteria's central claim ("exactly the task block + Read-first contents
   + task-execution-discipline — not the design doc, not other tasks'
   history") and the epic pre-mortem's risk #2 ("a naive dispatch
   implementation could leak the calling session's broader context") —
   satisfying it is this step's whole purpose.
2. **Execute.** The executor works under `task-execution-discipline`'s
   three pillars (TDD-per-capability, YAGNI bounded by `Not here`,
   verification-before-completion) and commits its own change as its last
   act — the Foreman never commits on the executor's behalf, since that
   would require the Foreman to inspect (or blindly stage) a diff it isn't
   supposed to see.
3. **Executor return contract.** The executor's final message must
   contain: the commit SHA it just created, plus its narrative summary and
   `Evidence` prose citing the fresh run behind each numbered `Done means`
   item. The executor never emits `scripts/verify`'s documented
   `ITEMS_SCHEMA` JSON itself — its only context is the task's checkpoint
   block plus Step 1's dispatch boundary line, neither of which mentions
   that schema. Transcribing it is the Foreman's own next step (Step 4,
   below), not something asked of a fresh executor.
4. **Verify (independent, Foreman-run).** The Foreman transcribes the
   items file itself: one entry per numbered `Done means` item in this
   task's own checkpoint block (`task`, `items[]` with `id`/`kind`/`tier`
   and either a `command` or an `artifact`/`pattern`, matching
   `scripts/verify`'s documented `ITEMS_SCHEMA`) — the block's own
   `Done means` prose already states each item's kind, tier, and check;
   the Foreman is transcribing that, never inventing a check the block
   didn't name. That JSON names *what to check*, never *whether it
   passed*; only `verify` decides the result. The Foreman then calls
   `scripts/verify --items <file> --since <the executor's reported commit
   SHA> --out <results.json>`. This call always happens *after* the
   executor's commit, never before — the ordering that keeps
   `evidence-capture`'s freshness check non-vacuous
   (`docs/design/build-scripts.md` risk #1: "a naive `now >=
   last-commit` check is vacuous whenever the task's own work is still
   uncommitted at capture time"). `verify`'s per-item PASS/FAIL report,
   not the executor's claim, is what the rest of this loop reacts to.
   **Exit code 2 is not a FAIL.** `verify` exits 2 for a usage error — most
   likely a malformed items JSON, meaning the Foreman mis-transcribed this
   task's checkpoint block's `Done means` lines rather than the task
   genuinely failing anything. The Foreman treats this as its own bug: it
   re-reads the checkpoint block, re-writes the items file, and re-invokes
   `verify`, without dispatching a new executor and without counting the
   attempt against the Failure routine's two-failure budget. Only an exit 0
   (PASS) or exit 1 (at least one item FAIL) advances that budget; a
   repeated exit 2 after one honest retry is a Foreman-side defect serious
   enough to pause the session outright (**PAUSED**, naming "verify usage
   error persisted after retry" as the cause) rather than silently loop.
5. **Inspect (load-bearing only).** Explicit no-op stub for this pass —
   issue #15's inspector isn't built yet. `/build` does not call it, does
   not simulate it, and does not skip a step that looks like a broken
   reference: this stage is a named, deliberate pass-through directly from
   Step 4 to Step 6, with a one-line comment in `SKILL.md` pointing at
   issue #15. (Epic pre-mortem risk #4, addressed directly.)
6. **On overall PASS:** the Foreman calls `scripts/evidence-capture --task
   <id> --artifact verify:results=<results.json> [...]` for `verify`'s and
   any probe artifacts, then calls `scripts/status-flip` to write the
   task's terminal status back into the plan file itself — see
   "Status-flip persistence," below — and moves to the next task, streaming
   without a pause (see Cadence) unless the task carries an explicit risk
   tag.
7. **On any item FAIL:** enters the Failure routine, below, instead of
   advancing.

### Status-flip persistence

`docs/design/build-scripts.md`'s Open questions flagged this explicitly
("where 'status flips' actually lands... a fast-follow to this story,
folded into `build-skill`'s foreman state, or a story not yet filed") and
asked this doc to make a call. The call: **no new file or persistence
format — but a new script performs the write.** `DESIGN.md`'s Vocabulary
table already commits `/build` task status to being "flipped by scripts
only, never the model" (line 40 — of that line's four-member enum,
`status-flip` writes three of them as heading suffixes, `PASS`/`REPLAN`/
`ESCALATE`; `FIX` is a transient failure-routine action, a fresh
scoped-executor dispatch per Failure routine step 1, never a status-flip
call or a heading suffix in its own right), and `PRODUCT.md`'s "Judgment in
the model, mechanics in scripts" principle names "status flips" by name as a
script concern. An earlier draft of this section had the Foreman edit the
plan file's own heading directly with its own tools — that draft shipped
behavior contradicting both of those unchanged, ratified statements, and
left nothing to catch a mis-transcription (heading says `PASS`, `verify`'s
own `results.json` says `FAIL`). This revision closes that gap by adding
`scripts/status-flip`, a fourth script this story builds alongside
`SKILL.md`:

- **Interface**: `scripts/status-flip --plan <path> --task <label> --results
  <results.json>` (the PASS path), or `--plan <path> --task <label> --status
  REPLAN|ESCALATE --reason "<text>"` (the failure-routine path, no
  `--results` — there is no script verdict to bind against a Foreman
  judgment call). Locates the single `### Task <label>` heading in `<path>`,
  refuses (exit 2) if it finds zero or more than one match. **Idempotency —
  "a status flips exactly once" — governs `PASS` and `ESCALATE` only.** A
  heading that already carries either of those two suffixes refuses any
  further status-flip call outright, since both close the task out for
  this session (`PASS` advances to the next task; `ESCALATE` ends the
  session per the Revision loop). `REPLAN` is deliberately not in that set:
  it is the Failure routine's and Session verdicts' own resumable,
  PAUSED-not-closed state (Failure routine, step 2, below; Session
  verdicts, below — "Resumable once the human acts"), so a heading already
  carrying a `REPLAN` suffix does **not** refuse. status-flip overwrites it
  in place with whatever the retried attempt actually earns next — a later
  `PASS`, a repeat `REPLAN` if the human's revision still doesn't hold, or
  an `ESCALATE` — the same append-and-commit mechanics either way. This is
  the doc's explicit reconciliation of the two claims that would otherwise
  collide: "a status flips exactly once" and "`REPLAN` is a resumable state
  `/build` revisits once the human acts." Without this carve-out, the
  human's ordinary resume action — revise the checkpoint block by hand,
  re-invoke `/build` (Failure routine step 2) — would dead-end: the retried
  task's own eventual `PASS` would hit the pre-existing `REPLAN` suffix,
  status-flip would refuse (exit 2), the Foreman would treat that as a
  usage error per Step 2.4's policy, retry once, hit the same refusal, and
  pause the session with a misleading "status-flip usage error persisted
  after retry" — for a task that in fact passed. Appends the suffix, writes
  the file, and creates the commit itself — a fixed, script-authored
  message, distinct from the executor's own implementation commit and from
  any commit the Foreman makes elsewhere.
- **The PASS path is where the integrity check lives, by construction, not
  as a bolted-on extra check.** Given `--results`, the script reads that
  file's own `overall` field and derives the token itself (`PASS` iff
  `overall == "PASS"`); it never accepts a status string the Foreman
  supplies for this path. The Foreman cannot mis-transcribe a FAIL as a
  PASS here, because the Foreman never gets to state the PASS token at
  all — only to hand the script the same `results.json` path it already
  wrote in Step 2.4. If `--results` doesn't parse, has no `overall` field,
  or `overall != "PASS"`, the script refuses (exit 2) rather than writing
  anything, which the Foreman treats the same way it treats any other
  `status-flip` usage error: a bug in its own invocation, not a task
  verdict.
- **The REPLAN/ESCALATE path is still the Foreman's judgment**, per the
  Failure routine below and this doc's own Principle-alignment section —
  no script could make that call. What moves to the script here is only
  the *mechanical write*: once the Foreman has decided REPLAN or ESCALATE,
  it hands that decided token to `status-flip`, which performs the same
  heading-edit-and-commit mechanics as the PASS path — subject to the
  REPLAN-is-overwritable carve-out above (`ESCALATE`, like `PASS`, still
  flips exactly once; only `REPLAN` is resumable). The model still never
  edits the plan file's bytes or runs `git commit` on it directly.
- The plan file remains the single source of truth for a task's status —
  unchanged from the original call — and still needs no new format, no new
  ledger, and stays git-diffable in the same history `/gate-audit` already
  reads. Only *who performs the edit* changed, not *what* gets recorded or
  *where*.

This is deliberately narrower than "a plan the loop can amend under its own
failure pressure," which `PRODUCT.md`'s "What we're NOT building" rules out.
Nothing — not the Foreman, not `status-flip` — ever rewrites a checkpoint
block's `Do`/`Not here`/`Done means` content; the only thing `status-flip`
ever writes is a status suffix on a task's own heading — terminal
(flips-exactly-once) for `PASS`/`ESCALATE`, resumable and overwritable for
`REPLAN` (see Interface, above) — driven by either `verify`'s own
`results.json` or the Foreman's already-made REPLAN/ESCALATE diagnosis.
Actually revising a block's content stays a `REPLAN` pause for the human,
never something the loop does to itself.

### Failure routine (issue #14, step 3)

Scoped **per verify item ID**, not per task as a whole — `verify` reports
per item precisely so a repeat failure on the *same* item can be
distinguished from a new failure on a *different* one
(`docs/design/build-scripts.md`: "a caller can tell whether a second
failure lands on the same item as the first").

1. **First FAIL on an item.** The Foreman reads that item's `detail` from
   `verify`'s report and chooses:
   - **FIX** — dispatch a fresh executor scoped to only that item's gap,
     when the detail reads as a narrow, mechanical miss (an edge case, an
     off-by-one, a wrong path) that doesn't call the task's whole approach
     into question.
   - **RESAMPLE** — dispatch a wholly fresh executor for the entire task
     from scratch (discarding the failed attempt), when the detail reads as
     a wrong approach (wrong file touched, task misunderstood, a Not-here
     boundary crossed).
   Either way, re-run Step 2.4 (`verify`) against the new attempt.
2. **Second FAIL on the *same* item ID.** Before treating it as genuine,
   the Foreman re-runs `scripts/verify` exactly once more against the same,
   already-produced artifacts (no new executor dispatched) to rule out an
   environment flake. If that re-run now PASSes, the loop resumes at Step
   2.6 as an ordinary PASS. If it FAILs again, it's a genuine second
   failure: the Foreman stops dispatching further attempts at this task and
   diagnoses:
   - **REPLAN** — the checkpoint block itself was wrong or
     under-specified (a `Done means` that can't actually be met as written,
     a `Rests on` that didn't hold). Task status becomes `REPLAN`; the
     Foreman pauses the session for the human to revise the block (by
     hand, since `/plan` doesn't exist) before `/build` can resume it. This
     is the one status-flip suffix that isn't terminal: `status-flip`
     overwrites a `REPLAN` suffix on this task's own resume, rather than
     refusing on it — see "Status-flip persistence"'s Interface bullet for
     why the write-once idempotency rule carves this status out.
   - **ESCALATE** — something deeper than this task: a contract mismatch
     with an earlier task, a missing dependency, a design assumption that
     doesn't hold in the real codebase. Task status becomes `ESCALATE`; per
     `PRODUCT.md`'s Revision loop (critical user journey 3), the session
     verdict becomes **ESCALATED** and the work is hand-off material for
     `/design` in revision mode, not something this loop keeps working on.
   Either diagnosis is the Foreman's judgment call, made from `verify`'s
   accumulated per-item detail across both attempts — never automated,
   never deferred past this point.
3. **A failure never resolves itself silently.** There is no
   auto-continue: every REPLAN, ESCALATE, or setup-stop pause blocks on an
   explicit human acknowledgment before `/build` proceeds — "no timeout
   auto-continue" (issue #14, step 4) is a hard rule, not a default.

### Cadence (issue #14, step 4)

- A task with no explicit risk tag (the common case, since `/plan` — the
  only thing that assigns `LOW`/`REPLAN-RISK`/`ESCALATE-RISK` per
  `DESIGN.md`'s Vocabulary table — doesn't exist yet) defaults to **LOW**
  and streams: a clean PASS moves straight to the next task with no pause.
- A hand-authored plan may optionally tag a task's checkpoint block with an
  explicit risk annotation (`REPLAN-RISK` / `ESCALATE-RISK`) if the human
  writing it already knows a task is dicey; the Foreman honors that tag by
  pausing for human ack *before* dispatching that task's executor, not only
  after a failure. Exact hand-authoring syntax is a build-phase drafting
  decision (see Open questions).
- A REPLAN or ESCALATE outcome from the failure routine always pauses,
  regardless of any pre-assigned risk tag — that pause is not optional
  cadence, it's the failure routine's own terminal step.

### Session verdicts

| Verdict | When |
|---|---|
| `BUILT` | Every task in the plan reaches `PASS`. Hands to `/gate-audit` (or reports "ready for review" if studious isn't installed — graceful degradation, `PRODUCT.md` principle "Standalone-capable"). |
| `PAUSED` | A dirty (or missing) baseline stopped Setup, or a task's failure routine resolved to `REPLAN`, or a risk-tagged task is waiting for pre-dispatch ack, or a `status-flip`/`verify` usage error persisted after retry. Resumable once the human acts. |
| `ESCALATED` | A task's failure routine resolved to `ESCALATE`. Terminal for this session — hands back to `/design` in revision mode per `PRODUCT.md`'s Revision loop. |

**`PAUSED` is never reported bare.** The table above collapses four
distinct causes (missing/dirty baseline, `REPLAN`, a risk-tagged
pre-dispatch ack, a persisted script usage error) into one token, and a
bare "PAUSED" would leave the human guessing which. Every `PAUSED` report
names, in the same message: which of those four triggered it, and the
specific action that resumes `/build` (fix the baseline and re-invoke;
revise the checkpoint block by hand and re-invoke; acknowledge the risk
tag to proceed; fix the transcription bug and re-invoke). This is a
commitment on the report's content, not a new verdict token — `PAUSED`
stays a single entry in the Vocabulary table `DESIGN.md` already owns.

### Principle alignment

"Judgment in the model, mechanics in scripts" is this story's central
shape: the Foreman decides FIX-vs-RESAMPLE and REPLAN-vs-ESCALATE (judgment
calls no script could make), while every PASS/FAIL determination, every
evidence write, and — as of this revision — every status flip's *actual
write to the plan file* are script outputs and script mechanics, not the
model's. `PRODUCT.md` names "status flips" as a script concern explicitly;
`status-flip` is what makes that literally true here, not just
true-in-spirit: the Foreman decides *what* status a task reaches (directly
from `verify`'s `overall` field for PASS, from its own diagnosis for
REPLAN/ESCALATE), but a script performs the mechanical edit and commit
either way. "Nothing signs off on itself" is why the checks `verify` runs
come from this task's own checkpoint block, transcribed by the Foreman,
never from the executor's self-report (Alternatives considered #4), and
why `verify` always runs after, never inside, the executor's own subagent
turn. "Recommend one action; the human
decides. Propose; never apply" is the failure routine's and cadence's whole
posture — every REPLAN, ESCALATE, and risk-tagged pause blocks on the human,
and the Foreman never auto-continues past one. "Standalone-capable" is
`BUILT`'s graceful fallback when studious isn't installed. "Anti-cleverness
tripwire" is why this is a single sequential for-loop with one Foreman and
one fresh executor at a time — no named sub-roles, no parallel dispatch, no
resident coordinator.

## User journey

Walks `PRODUCT.md` critical user journey 2 (**Quick path**), the epic's
named near-term dogfood target, with journey 1 (Full cycle) and journey 3
(Revision loop) as the same mechanics under a longer or a failing plan:

1. The developer hand-writes a `PLAN.md` with one checkpoint block (quick
   path) or several in spine order (full cycle, once `/plan` exists),
   matching the M0 dogfood's validated format.
2. The developer invokes `/build`. The Foreman reads the target project's
   `CLAUDE.md` for its baseline command, names a fresh branch/worktree, and
   calls `worktree-setup`. A dirty baseline stops here (`PAUSED`) before any
   executor exists.
3. On a clean baseline, the Foreman splits the plan into task blocks and, for
   the first (only, in the quick path) task, dispatches a fresh executor
   with exactly that task's block. The executor implements under
   `task-execution-discipline`, commits, and reports back its commit SHA,
   its `Evidence`, and a `verify`-shaped items JSON.
4. The Foreman independently re-runs `verify` after that commit. A clean
   PASS: `evidence-capture` writes the dated evidence folder, then the
   Foreman calls `status-flip`, which reads `verify`'s own `results.json`,
   derives the PASS token itself, annotates the task's status in `PLAN.md`,
   and commits that annotation.
5. All tasks PASS (here, the one task): session verdict `BUILT`. The
   developer runs `/gate-audit` next, per the quick path, and can open
   `docs/jig/evidence/<date>-<task>/` to see exactly what was independently
   re-checked and when.
6. **Injected-failure variant** (this story's other required
   demonstration): the same flow, but the executor's first attempt leaves a
   `Done means` item FAILing. The Foreman reads `verify`'s per-item detail,
   chooses FIX or RESAMPLE, re-verifies. If the same item fails again, the
   Foreman rules out a flake with one more `verify` re-run, then diagnoses
   REPLAN or ESCALATE and pauses — the developer sees exactly which item
   failed twice and why, and decides the next step by hand.

No step of either journey changes shape from what `PRODUCT.md` already
committed to; this story is the first thing that actually walks them.

## Out of scope

- **The inspector** (issue #15) — explicit no-op stub only, as designed
  above; this story does not build, simulate, or partially implement it.
- **`/plan` and a real `plan-lint`** (M3) — this story consumes a
  hand-written `PLAN.md`. The Foreman's own task-splitting judgment (Step 1)
  is a narrow, model-side stopgap for *this* story's own input, not a
  general-purpose parser competing with or pre-empting `plan-lint`'s future
  job; once `/plan`/`plan-lint` exist, they become the producer of
  `PLAN.md`, and nothing here needs to change to consume their output, since
  the checkpoint-block shape is unchanged.
- **Modifying `scripts/worktree-setup`, `scripts/verify`, or
  `scripts/evidence-capture`** — this story is their first caller, not a
  change to their contracts. Any gap found while wiring them in (e.g. a
  flag that doesn't exist yet) is a finding for the build phase to
  surface, not a license to redesign them here. (`scripts/status-flip` is
  a new fourth script this story does add and build — see "Status-flip
  persistence" — not an exception to this bullet, which only rules out
  changing the three pre-existing scripts' contracts.)
- **Modifying `skills/task-execution-discipline/SKILL.md`** — read, not
  edited, by this story.
- **Risk-tag assignment logic** — that's `/plan`'s job (`DESIGN.md`
  Vocabulary: "assigned by `/plan`"). This story only defines what `/build`
  does with a tag if one is present by hand, and what it defaults to when
  none is (see Cadence).
- **A general fix for the M0 friction report's finding 6** (coarser
  trailing headings silently absorbed) — that's `plan-lint`'s eventual
  concern for *machine* parsing. This doc only asserts the Foreman's own
  judgment-based reading avoids reproducing that specific bug for its own,
  narrower splitting need.
- **`/finish`, PR creation, cctx harvest** (M5) — out of this story; `BUILT`
  hands off to `/gate-audit`, full stop.
- **Concurrent or multi-repo `/build` sessions** — carried forward
  unchanged from `docs/design/build-scripts.md`'s own scoping; the
  sequential for-loop is the only shape designed here.
- **A timeout-based auto-continue past any pause** — explicitly ruled out
  (issue #14, step 4); every pause blocks on a human, unconditionally.

## Alternatives considered

1. **Foreman inlines each task's `Read first` file contents directly into
   the dispatch prompt**, instead of naming pointers for the executor to
   read itself. Rejected: inlining bloats the dispatch prompt with content
   that may already be stale by dispatch time, duplicates work the
   executor's own Read tool does natively once it's running inside the
   worktree, and adds templating logic to the Foreman for no behavioral
   gain — narrower Foreman surface, same isolation guarantee either way.
2. **Rely solely on `task-execution-discipline`'s model-invoked
   auto-trigger**, with no explicit reference in the dispatch prompt.
   Rejected: the epic pre-mortem's risk #2 asks specifically whether a real
   dispatch prompt can be inspected and confirmed to include the
   discipline skill — leaving that to implicit description-matching is
   unverifiable by inspection and risks a fresh, minimal-context executor
   never triggering it at all. A one-line explicit pointer costs nothing
   and removes the ambiguity outright; it doesn't change the skill from
   model-invoked to user-invoked, since the pointer only names the trigger
   condition the skill's own description already declares.
3. **A separate status-tracking file** (e.g., a `BUILD-STATE.json` the
   Foreman or `status-flip` maintains) instead of annotating the plan
   file's own task headings in place. Rejected per "minimize structural
   drift, prefer reuse over creation" and `PRODUCT.md`'s explicit "no
   work-ledger machinery" — the plan file is already the single source of
   truth for a task; a status suffix on its own heading needs no new
   persistence format and stays trivially diffable in the same commit
   history `/gate-audit` already reads. (This alternative is about
   introducing a new *format/file*; see #5, below, for the separate
   question of who performs the write to the existing plan file.)
4. **Let the executor itself invoke `scripts/verify`** and report the
   result up to the Foreman, instead of the Foreman invoking it
   independently after the executor's subagent has already ended. Rejected:
   this is the one alternative that would silently violate "nothing signs
   off on itself" — an executor that runs its own verification and reports
   the outcome is grading its own work, exactly the self-report
   `scripts/verify`'s own docstring and `PRODUCT.md`'s principle exist to
   close off. The executor supplies neither the checks nor the verdict:
   the Foreman transcribes the verify-shaped items itself from the task's
   own checkpoint block (its `Done means` lines), and `verify` alone
   decides PASS/FAIL against the executor's already-committed work — see
   Step 2, above.
5. **The Foreman edits the plan file's task heading directly** (its own
   Edit tool, its own `git commit`) instead of calling a dedicated
   `status-flip` script. This was this doc's own original design, and a
   design-review pass flipped it: it contradicts `DESIGN.md`'s Vocabulary
   table ("flipped by scripts only, never the model," line 40) and
   `PRODUCT.md`'s "Judgment in the model, mechanics in scripts" principle,
   which names "status flips" as a script concern by name — a mechanical
   text edit and commit is exactly the kind of judgment-free operation
   that principle assigns to scripts. It also leaves no structural
   guarantee against a mis-transcription (a heading written `PASS` while
   `verify`'s own `results.json` says `FAIL`) — nothing rechecks the two
   against each other. Rejected in favor of `status-flip`, which derives
   the PASS token directly from `results.json` rather than accepting the
   Foreman's word for it (see "Status-flip persistence").

## Operational readiness

`skills/build/SKILL.md` is a prompt file read by a Claude Code session, not
a deployed service — no runtime process, no data migration.

- **Rollout**: replaces the M1 stub's frontmatter/body in place, and adds
  one new script, `scripts/status-flip`, alongside the three already
  shipped by story `build-scripts`; no feature flag, no staged rollout.
  Nothing else in the repo changes behavior as a side effect of this
  story.
- **Rollback**: `git revert` the commits that replace the stub and add
  `status-flip`; the three pre-existing scripts and the discipline skill
  are unaffected since this story doesn't touch them.
- **Failure visibility**: this is the one story in the epic with an actual
  "production" analog — a live `/build` session a human is watching in
  real time. Its observability surface is exactly what the design produces:
  the dated `docs/jig/evidence/<date>-<task>/` folder per PASSed task, the
  in-place status annotation `status-flip` writes to the plan file's own
  task headings, and the session verdict (`BUILT`/`PAUSED`/`ESCALATED`)
  reported directly to the
  invoking human — no separate log aggregator or metrics dashboard is
  needed or proposed for a foreground, human-attended CLI/chat workflow.
  The acceptance criteria's required demonstration (one real red→green
  task, one deliberately-injected failure) is this story's own smoke test:
  if the evidence folder, the plan-file annotation, and the correct verdict
  don't all show up for both runs, the design isn't done, regardless of how
  the `SKILL.md` prose reads.

## Open questions

- **Exact hand-authoring syntax for an optional per-task risk tag**
  (`REPLAN-RISK` / `ESCALATE-RISK`), since `/plan` isn't the one assigning
  it yet. This doc commits to the behavior (honor it if present, default
  `LOW` if absent) but not the literal checkpoint-block field name/format —
  a build-phase drafting decision, ideally one that won't need a rewrite
  once `/plan` starts assigning it for real.
- **Whether one environment-flake re-run of `verify` is the right number**
  before treating a repeat failure as genuine. This doc commits to exactly
  one, bounded, to keep the mechanism simple and avoid an unbounded retry
  loop (itself an anti-cleverness concern) — but hasn't been tested against
  a real flaky suite yet, only reasoned about.
- **Resolved by this revision** (previously open): what the Foreman does if
  `scripts/verify` or `scripts/status-flip` itself exits 2 (a usage error).
  See Step 2.4 and "Status-flip persistence" — either is treated as a
  Foreman-side bug distinct from a task FAIL and doesn't count against the
  Failure routine's two-failure budget; a repeated exit 2 after one retry
  pauses the session instead of looping.
- **`status-flip`'s exact heading-match algorithm** (e.g., matching on the
  numeric task label vs. the full heading text) is a build-phase detail —
  this doc commits to "exactly one match or refuse," not the literal
  matching implementation.
- **Whether `/gate-audit` (or a human) needs anything from `/build` beyond
  the evidence folder and the annotated `PLAN.md`** to pick up the quick
  path cleanly — this doc assumes those two artifacts are sufficient
  hand-off material, matching `docs/design/build-scripts.md`'s own framing
  of the evidence folder as "the paper trail `/gate-audit` reads," but that
  assumption is untested against a real `/gate-audit` run over this story's
  output.
