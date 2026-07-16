# Design: the rough-in inspector (`/build` step 2.6, issue #15)

## Problem & persona

Primary persona, verbatim from `PRODUCT.md`:

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

That persona's problem today: `/build` (shipped M4, `skills/build/SKILL.md`)
already delivers on half of "nothing signs off on itself" — every
`Done means` item is re-verified by a script (`verify`), never trusted from
the executor's own report. But the *other* half of that same principle,
"independent fresh-context review at boundaries," has no boundary review at
all. Step 2.6 is a literal, named no-op: *"Issue #15's rough-in inspector
isn't built yet. Do not call it, simulate it, or treat this as a step to
skip past like a broken reference: this is a named, deliberate pass-through
straight from step 5 to step 7."* Every task — including one whose
committed contract every later task in the plan will build directly on top
of — reaches `PASS` on script-verified `Done means` alone.

Scripts are structurally blind to exactly three things, named in issue #15:
whether a new test actually asserts the promised capability (or something
adjacent/vacuous), whether the shipped contract matches what downstream
tasks will assume it means (shape, names, error behavior), and whether the
implementation games the check itself (hardcoding, special-casing the
probe, gaming a hold) rather than doing the work. `verify` can confirm a
command exited zero; it cannot read whether the test behind that exit code
means anything. Today, a load-bearing task can ship a self-dealing test or
a silently-wrong contract, reach `PASS`, and only surface the real defect
several tasks later as a confusing `ESCALATE` on a downstream task that
built on top of it — expensive to diagnose compared to catching it at the
boundary where it was introduced, and exactly the gap `PRODUCT.md`'s
"Nothing signs off on itself" principle names but `/build`'s M4 slice
doesn't yet close. This is also a named, first-class limitation in the
epic goal this story serves: M4 doesn't close cleanly with a known
in-loop-review gap left as a permanent no-op.

## Proposed design

One file changes behavior: `skills/build/SKILL.md`'s step 2.6 replaces its
no-op with a real, conditional dispatch. No script changes are required —
this design reuses `evidence-capture`'s existing `--artifact
PRODUCER:LABEL=PATH` mechanism (already accepts any number of `--artifact`
flags per task) rather than inventing a new persistence path, and
`status-flip`'s `PASS` derivation is untouched (it reads only
`results.json`'s `overall` field today, and continues to after this
story).

### Jurisdiction — narrow, exactly issue #15's three lenses, no wider

This is epic pre-mortem risk #1's own named concern, so it is stated once,
plainly, as the jurisdiction's complete boundary:

1. **Test self-dealing** — do the new tests assert the promised capability,
   or something adjacent/vacuous?
2. **Contract match** — does the frozen contract match its design section
   (shape, names, error behavior), as downstream tasks will consume it?
3. **Technicality gaming** — hardcoding, special-casing the probe, gaming
   a hold?

Nothing else. No security review, no style review, no performance review,
no re-litigating `verify`'s own `PASS`/`FAIL` — those already belong to
scripts (mechanical checks) or to studious's `/gate-audit` (the nine
general-purpose auditor lanes already named in `reference/severity-
rubric.md`). Adding a fourth lens here — even a reasonable-sounding one —
would duplicate `/gate-audit` instead of catching what it structurally
can't: things a script can't decide, on a boundary `/gate-audit` won't see
until much later, in a much bigger diff.

### Who dispatches, and on what

**Load-bearing derivation (mechanical, provisional — epic pre-mortem risk
#2).** "Load-bearing" means *other tasks in this same plan depend on this
task's contract* — mechanically, "has downstream dependents" is read off
the plan's own `Rests on:` prose, the same field every checkpoint block
already carries (`skills/build/SKILL.md`'s own task-block template). The
Foreman computes this **once**, immediately after Step 1.4's existing
task-split (which already reads every task block into memory, in document
order) — not per-task at dispatch time, since the full set of `Rests on:`
lines is already fully known before any task is dispatched: for every task
N, task N is load-bearing iff *any other* task block's own `Rests on:`
line names task N (its heading number, e.g. "Task 2", or an unambiguous
title match to task N's own heading). This produces a fixed load-bearing
set for the whole run, computed before task 1 is ever dispatched.

This is deliberately **not** a new script. Step 1.4's own task-splitting is
already an explicit precedent for a mechanical-but-unscripted Foreman
procedure — reading `Rests on:` prose for meaning is the same class of
judgment-free-but-not-code-parseable task the SKILL.md already declines to
hand to "a naive parser" for the trailing-heading case. The distinction the
acceptance criteria draws ("derived mechanically... never declared by the
executor") is about *who gets a vote* — the executor never gets to say
whether its own task is load-bearing, matching "nothing signs off on
itself" applied to jurisdiction itself, not the executor. It is not a
claim that this must live in a `.py` file.

**This heuristic is explicitly provisional**, stated here so a future
reader (or `premortem-auditor`) doesn't mistake it for the permanent
mechanism: it works only for the hand-authored, quick-path `PLAN.md` this
project's own dogfood currently uses, where `Rests on:` is free prose a
human wrote. It has real failure modes — a `Rests on:` line that doesn't
literally name the task it depends on (false negative: a genuinely
load-bearing task skipped), or one that mentions a task number only in
passing (false positive: a leaf task inspected unnecessarily, which
`/build`'s own eval-gate, see Out of scope, is the intended way to detect
and correct). Once `/plan` (M3) emits a real spine map with structured
dependency edges instead of prose to pattern-match, this derivation should
be replaced with a read of that structure — not extended or patched
further in its current prose-matching form.

**A leaf task (not in the load-bearing set): no dispatch, no dead step.**
Exactly today's pass-through behavior, straight from step 5 to step 7 —
except the Foreman now states explicitly, in its own output, *why*: "task
N is not load-bearing (no other task's `Rests on:` names it) — inspector
skipped." A silent skip and a stated skip are behaviorally identical to
the plan's outcome, but only one of them is legible to the human reading
the session, matching "every degradation graceful, none silent."

**A load-bearing task: dispatch a fresh Inspector.** This is the third
named role in `/build`, alongside Foreman and Executor — not "a named
agent persona" in the sense `PRODUCT.md`'s anti-cleverness principle rules
out (that principle targets sprint-ceremony roleplay and resident
coordinators; `/build` already names two functional roles, and a third
with its own narrow, mechanical trigger condition is the same kind of
thing, not a step toward BMAD-style ceremony). Unlike the Foreman, the
Inspector **does** see a diff — jurisdiction 1–3 are unanswerable without
reading the actual shipped code, and the Foreman's own "never see a diff"
rule was scoped to keep the Foreman from second-guessing `verify`'s
mechanical result, not to keep every jig role diff-blind forever. The
Inspector's dispatch is narrow in the same spirit as the Executor's:

- This task's own checkpoint block, verbatim (the same block the Executor
  received).
- The named commit or commit range for *this task only* — from this
  task's first dispatch through its final, verify-passed commit (spanning
  any FIX/RESAMPLE re-dispatches) — so the Inspector reads `git diff`/`git
  show` itself, scoped to exactly this task's own change, never an earlier
  or later task's commits.
- The `Read first` paths named in the block (as paths, per the Executor's
  own convention — never inlined content), so the Inspector can read the
  same reference material the Executor was pointed at.
- **If and only if** this task's block cites a design-doc section (a
  `Read first` or `Do` line naming one) — that section, and nothing wider.
  When no design doc exists at all (the common case for this project's own
  quick-path dogfood today, since M2/M3 aren't built), the "contract
  match" lens instead checks the shipped contract against the checkpoint
  block's own `Do`/`Done means` prose — the contract of record when no
  design doc exists, not a fabricated requirement for one. This is
  "Standalone-capable" applied one level down: the *inspector itself*
  degrades gracefully depending on what artifacts this particular plan
  actually has, rather than assuming a full-cycle plan shape that M4's own
  dogfood doesn't yet produce.

Explicitly excluded from the Inspector's context, mirroring the Executor's
own isolation boundary: the full `PLAN.md`, any other task's history, and
this session's own conversation. One more fresh-context reviewer at the
boundary, not a second set of eyes on everything.

### Verdicts

**`CLEAR`.** Proceeds to step 2.7 exactly as today. The Inspector's own
report (its reasoning against each of the three lenses, cited against the
diff) is written to the same scratch path `verify`'s `results.json`
already uses (never inside the worktree first — issue #45's clean-tree
rule applies identically here) and captured as one more `evidence-capture`
artifact alongside the existing `verify:results=...` call:
`--artifact inspector:report=<scratch-path>/inspector-report.md`. No new
evidence-capture invocation, no new commit — one more `--artifact` flag on
the call `/build` already makes.

**`DEFECT` — wires into the Failure routine as a first failure.** Tracked
under its own item ID (distinct from `verify`'s numbered `Done means`
items — e.g. `"inspector"`, exact naming a build-phase detail) so the
Failure routine's existing "scoped per verify item ID" rule keeps a repeat
`DEFECT` on *this* task distinguishable from an unrelated `FAIL` on a
different item, or from a later task's own first `DEFECT`. A first
`DEFECT` gets the Foreman's ordinary FIX-vs-RESAMPLE judgment call, from
the Inspector's own cited detail — no new decision procedure, the same one
`verify`'s first `FAIL` already uses. After a FIX or RESAMPLE re-dispatch,
`verify` and (since this task is still load-bearing) the Inspector both
run again against the new attempt.

A second `DEFECT` on the *same* item ID needs one adaptation, flagged as
an open question rather than settled here: the existing "second FAIL"
step rules out an environment flake by re-running the same deterministic
script once more against the same artifacts. An Inspector's verdict is a
fresh LLM judgment call, not a deterministic re-run of the same command —
"re-run it to rule out a flake" doesn't transfer literally. The design's
recommendation (not fixed as final) is a second, independent fresh-context
Inspector dispatch against the same, already-produced artifacts — no new
executor, matching the existing rule's shape — as the closest analogue to
"rule out noise before treating it as genuine." Either way, the outcome
shape is unchanged: a confirmed genuine repeat is the Foreman's own
REPLAN-vs-ESCALATE diagnosis, exactly as today, `status-flip` called
identically.

**`CONCERN` — non-blocking, forwarded to `/gate-audit`'s relevant lane.**
The task proceeds straight to `PASS` (step 2.7), same as `CLEAR`. "Forward"
is deliberately the simplest thing that works, not a new integration:
the Inspector's report — including which of the three lenses it concerns,
and the recommended lane below — is captured via the exact same
`evidence-capture` artifact call `CLEAR` uses. Because that evidence
directory is already committed to the branch as part of step 2.7 (existing
behavior, unchanged), the `CONCERN` report is automatically part of the
diff `/gate-audit`'s auditors already review when a human runs that gate
later — no coupling to `gate-ledger`, no dependency on studious being
installed at all (`gate-ledger`'s own evidence log is a structured
command-execution record; it has no field for a qualitative finding like
this, and reaching into a sibling plugin's internal ledger would break
"Standalone-capable" for a user with no studious install). A self-describing
committed file that a diligent auditor's own "review the full changeset"
mandate already covers *is* the forward.

Lens → recommended `/gate-audit` lane, derived from each auditor's own
stated rubric in `reference/severity-rubric.md` (not invented):

| Lens | Lane | Why this lane |
|---|---|---|
| Test self-dealing | `test-auditor` | Its own rubric already asks "does new/changed behavior carry tests, do the tests assert real outcomes" — the identical question. |
| Contract match | `architecture-auditor` | Its own rubric already asks "does it fit existing patterns? any coupling concerns?" — a downstream-consumed contract mismatch is exactly a coupling concern. |
| Technicality gaming | `code-auditor` | Its own rubric covers code that technically passes but doesn't do the real work — the general-purpose "is this actually the thing" lane, closest existing fit among the nine. |

### Principle alignment

"Nothing signs off on itself" is this story's whole point: today only
scripts re-verify the executor; after this story, a fresh-context reviewer
also stands at the boundary a script can't reach. "Judgment in the model,
mechanics in scripts" is exactly why `DEFECT`/`CONCERN` themselves stay a
judgment call (an LLM reads the diff and decides) while everything around
that call — evidence capture, the failure-routine wiring, `status-flip`'s
`PASS` derivation — stays mechanical and untouched. "Standalone-capable"
is why forwarding a `CONCERN` reuses a plain committed file instead of a
new studious/`gate-ledger` dependency. "Anti-cleverness tripwire" is why
this adds one narrowly-triggered role with a mechanical gate, not a
resident reviewer, a persona, or ceremony around it.

## User journey

Walks the quick-path shape `PRODUCT.md`'s critical user journey 2
describes, and the exact shape this project's own dogfood has already
demonstrated twice (`ef95db6`'s two live `/build` demonstrations) — since
`/plan` (M3) doesn't exist yet, this is the only real journey this story
can be demonstrated against today, not a hypothetical full-cycle one:

1. The developer hand-writes a two-task `PLAN.md`: task 1 does the
   groundwork, task 2's `Rests on:` line names task 1 by number. `/build`
   splits both blocks at Step 1.4 and computes the load-bearing set once:
   task 1 is in it (task 2 rests on it); task 2 is not (nothing rests on
   it).
2. Task 1's executor implements and commits; `verify` independently
   confirms `PASS`. Since task 1 is load-bearing, the Foreman dispatches a
   fresh Inspector with task 1's checkpoint block, its commit, and its
   `Read first` paths. Say it returns `CLEAR`: the Foreman notes the
   verdict, captures the Inspector's report as one more evidence artifact
   alongside `results.json`, and proceeds to step 2.7 exactly as an
   uninspected task would today.
3. Task 2's executor implements and commits; `verify` confirms `PASS`.
   Task 2 is not load-bearing: the Foreman states so explicitly and skips
   straight to step 2.7 — no dispatch, no dead step, the same shipped
   behavior as today's no-op, just no longer silent about why.
4. **A `DEFECT` branch on task 1** (a companion or later demonstration):
   the Inspector finds task 1's new test asserts nothing about the
   promised capability. The Foreman treats this exactly like a `verify`
   `FAIL` on task 1 — FIX or RESAMPLE, a fresh attempt, `verify` and the
   Inspector both re-run — through to a genuine second `DEFECT` and a
   `REPLAN`/`ESCALATE` diagnosis, or a passing retry that proceeds
   normally.
5. **A `CONCERN` branch on task 1**: the Inspector notes the contract is
   fine to build on but flags a naming inconsistency downstream tasks
   should know about. Task 1 still reaches `PASS`; the concern rides along
   in that task's own evidence directory, tagged for the
   `architecture-auditor` lane, sitting in the branch's diff the moment a
   human later runs `/gate-audit`.
6. The developer sees, for the first time, a real fresh-context check at
   exactly the one boundary scripts can't reach — and, just as
   importantly, sees it *not* fire on the leaf task, so the loop stays as
   fast as it is today everywhere an inspector adds nothing.

No other step of `/build`'s existing journey changes shape — this story
inserts one conditional dispatch between an unchanged step 2.5 and an
unchanged step 2.7.

## Out of scope

- **A permanent, structurally-sound spine map or dependency graph.** That's
  `/plan`'s (M3) job. This story's load-bearing derivation is a stated,
  provisional textual heuristic over hand-authored `Rests on:` prose —
  explicitly meant to be replaced, not extended, once M3 ships.
- **A fourth (or any additional) inspection lens.** Only the three named in
  issue #15. No security, performance, or style review — `/gate-audit`
  already owns those, at a coarser grain, later.
- **Inspecting leaf tasks, ever, regardless of risk tag or complexity.** The
  gate is load-bearing-or-not, mechanically, full stop — not a judgment
  call about whether a particular leaf task "feels important."
- **Any new persistent document class, new script, or new studious/
  `gate-ledger` coupling.** This design reuses `evidence-capture`'s
  existing `--artifact` mechanism only; no script's CLI contract changes.
- **Auto-invoking `/gate-audit`, or auto-filing an issue, on a `CONCERN`.**
  `/gate-audit` still runs only when the human runs it, per `BUILT`'s
  existing hand-off. This story only guarantees the concern is already
  sitting in the diff by the time they do.
- **The eval-gate itself** (issue #15's own text: "run branches with
  inspector-on-all vs. load-bearing-only, diff catches, let the delta set
  the dial"). That is a follow-on measurement exercise across multiple
  real builds, not something this story's build phase performs — flagged
  under Open questions as unscheduled future work.
- **Redefining `FIX`/`RESAMPLE`/`REPLAN`/`ESCALATE` semantics, or
  `status-flip`'s `PASS` derivation.** Reused verbatim, unchanged; `DEFECT`
  plugs into the existing Failure routine rather than growing a parallel
  one.
- **NOTES-stub production or consumption.** Unrelated mechanism (see
  `docs/design/finish-skill.md`'s own Out of scope); this story doesn't
  touch it either.

## Alternatives considered

1. **Inspect every task ("inspector-on-all"), skip the load-bearing gate
   entirely.** Rejected: directly contradicts issue #15's own explicit
   narrow-jurisdiction framing ("only what scripts cannot decide") and
   `PRODUCT.md`'s anti-cleverness stance against added ceremony. It's also
   literally the *other* arm of issue #15's own eval-gate — "inspector-on-
   all" is the baseline the eval-gate exists to diff against and shrink
   from, not a shape to ship as the default.
2. **Let the executor self-declare its own task load-bearing** in its
   final message, consumed by the Foreman. Rejected by the acceptance
   criteria in so many words ("never declared by the executor") —
   "nothing signs off on itself" applies to jurisdiction exactly as it
   applies to `Done means`: the party being judged doesn't get a vote on
   whether it's judged.
3. **Fold the three lenses into the Foreman's own Failure-routine
   judgment**, i.e. let the Foreman itself read the diff instead of
   dispatching a fresh reviewer. Rejected: the Foreman is structurally
   diff-blind today by design ("You never see a diff and never run `git
   diff` yourself"); undoing that for every load-bearing task would widen
   the Foreman's own remit and collapse "fresh-context review at
   boundaries" into "the same context that already trusts the executor" —
   the opposite of what an independent reviewer is for.
4. **A new script (e.g. `scripts/load-bearing-check`) that parses `Rests
   on:` references**, mirroring `verify`/`status-flip`'s own script-only
   posture. Considered, not adopted this pass: Step 1.4's own task-
   splitting is the direct precedent for keeping a mechanical-but-prose-
   dependent read inside the Foreman's own procedure rather than a script,
   specifically because reading `Rests on:` prose for meaning is the same
   class of task Step 1.4 already declines to hand to "a naive parser."
   Worth revisiting once `/plan` (M3) emits data a script *could* parse
   without judgment.
5. **Gate on the plan's own `Risk:` tag** (`REPLAN-RISK`/`ESCALATE-RISK`)
   instead of load-bearing status. Rejected: risk tags and load-bearing-
   ness are different axes (a `LOW`-risk task can still be load-bearing;
   an `ESCALATE-RISK` leaf task inspects nothing downstream) —
   `DESIGN.md`'s own vocabulary table already keeps risk tags and
   inspector verdicts as separate rows for exactly this reason. Reusing
   the wrong axis would either miss real load-bearing tasks with no risk
   tag (the common case, since no `/plan` exists yet to assign one) or
   inspect risk-tagged leaves for no reason tied to jurisdiction.

## Operational readiness

`skills/build/SKILL.md`'s step 2.6 is a prompt-file change plus one
additional `--artifact` flag on an existing script call; no deployed
service, no data migration, no new script.

- **Rollout**: replaces the no-op step in place, same pattern as
  `build-skill`'s own M4 rollout of the prior stub. No feature flag, no
  staged rollout — the load-bearing gate itself is the built-in scoping
  mechanism.
- **Rollback**: `git revert` the commit; `evidence-capture`'s `--artifact`
  contract is additive (accepts any number of artifacts already) so no
  other caller of that script is affected either way.
- **Failure visibility**: matching `PAUSED`'s own "never bare" rule, the
  Foreman states, at the moment either `DEFECT` or `CONCERN` fires, which
  of the three lenses triggered and the Inspector's own cited reasoning —
  never a bare token. A leaf-task skip is stated too (see Proposed
  design), not silent.
- **Required demonstration** (this story's own acceptance criteria: "one
  load-bearing task (fires) and one leaf task (skipped)"): a real, fresh
  `/build` run over a genuine two-task hand-written `PLAN.md` with a real
  `Rests on:` back-reference — the same live-demonstration bar
  `build-skill` already set (`ef95db6`), not a narrated or simulated
  dispatch. The build phase should capture at minimum: the computed
  load-bearing set right after Step 1.4, the Inspector's actual dispatch
  prompt for the load-bearing task (to confirm the isolation boundary
  above holds in practice, the same scrutiny `build-skill`'s own
  pre-mortem risk #1 already applied to the Executor's dispatch), and the
  leaf task's explicit skip note.

## Open questions

- **Exact re-check semantics for a second `DEFECT` on the same item ID**
  (Proposed design, `DEFECT`). Whether a second independent Inspector
  dispatch is the right proxy for "rule out noise," or whether a repeat
  `DEFECT` should simply always count as genuine without any recheck step
  (Inspector dispatches are not free the way re-running a script twice
  is). Left to the build phase.
- **Exact pseudo-item-ID naming** for wiring `DEFECT` into the Failure
  routine's per-item-ID bookkeeping (e.g., the literal string
  `"inspector"`). No product-visible difference either way; a build-phase
  detail.
- **Whether the load-bearing derivation should graduate from Foreman
  procedure to a small script** before or only after `/plan` (M3) ships a
  structured spine map (see Alternatives #4). Not resolved here.
- **The eval-gate** (issue #15's own text) is unscheduled — no story yet
  owns "measure inspector-on-all vs. load-bearing-only and let the delta
  set the dial." Worth a fast-follow issue once real `DEFECT`/`CONCERN`
  data exists across a handful of real builds using this story's shipped
  gate.
- **Out-of-spine-order `Rests on:` references** (a task's `Rests on:` line
  naming a task that appears *later* in document order than itself) — the
  mechanical scan as designed doesn't assume document order, only text
  matching, but this hasn't been exercised against a plan authored out of
  spine order. Likely harmless (the scan is symmetric), but not stress-
  tested here.
- **`DESIGN.md`'s Vocabulary table** already lists the inspector-verdict
  row with "source of truth: handoff §5.3 (future: `skills/build/
  SKILL.md`)" — once this story ships, that row's source-of-truth column
  should point at `SKILL.md` instead, matching the pattern the table
  itself already documents for every other row. A small follow-up for the
  build phase to fold in, not a design decision this doc needs to make.
