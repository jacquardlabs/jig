# Design: Build scripts (worktree setup, baseline check, verification re-run, evidence capture)

## Problem & persona

Primary persona, verbatim from `PRODUCT.md`:

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

That persona's problem today: `/build` is still a stub (`skills/build/SKILL.md`),
but `PRODUCT.md`'s critical user journey already commits to what it must become —
"for-loop: fresh executor per task, **script-verified**, conditional inspector."
"Script-verified" is not decoration; it is the persona's actual reason for
choosing jig over ad hoc prompting or Superpowers, and it operationalizes two
of `PRODUCT.md`'s five leading principles: "Judgment in the model, mechanics
in scripts" (status flips, verification runs, and evidence capture are never
self-reported by the model) and "Nothing signs off on itself" (executor
attestation is structurally worthless; scripts re-verify everything).

Issue #14 splits `/build`'s three roles — Foreman, Executor, Scripts — across
two build-side stories in this epic. This story owns the Scripts role's
mechanical duties named in its own acceptance criteria: create an isolated
worktree and refuse to start work against a broken baseline; independently
re-check a task's Done-means items one by one rather than trust the
executor's claim; and write a dated, freshness-stamped evidence trail. This
is also the concrete enabler of the epic goal — "dogfood the quick path
(single task block → `/build` → `/gate-audit`) before `/design`/`/plan`
exist" — since the quick path still needs somewhere isolated to build, a way
to know the task actually passed, and something for `/gate-audit` to read
afterward, even with no `/plan`-generated `PLAN.md` in front of it.

Without these three mechanisms: (a) a fresh executor could start task 1
against an already-failing suite and misattribute pre-existing breakage to
its own task, exactly the ambiguity a fresh-context loop is supposed to
avoid; (b) nothing would independently confirm a task's Done-means items
were satisfied — the friction report from this project's own M0 dogfood
(`docs/jig/dogfood/FRICTION-REPORT.md`, branch `docs/m0-paper-dogfood`)
already observed the sibling tool viva doing this correctly (`revision_history.py`
derived the real revised-section count and ignored the caller's claimed
summary) and named it as consistent with jig's own "nothing signs off on
itself" principle — `/build`'s scripts need the equivalent; (c) there would
be no artifact trail proving a task's evidence was produced by the actual
work, rather than stale output copied forward from an earlier, possibly
failed, attempt.

## Proposed design

Three new executable scripts land under `scripts/`, alongside the existing
flat, one-script-per-concern layout (`scripts/plan-lint`, `scripts/design-lint`):
`scripts/worktree-setup`, `scripts/verify`, `scripts/evidence-capture`. Nothing
else changes — no `SKILL.md` is touched (the sibling `build-skill` story
wires these in), no `PLAN.md` format is introduced or altered, and the two
existing lint stubs keep their current M1 stub behavior untouched.

What the persona experiences, once `build-skill` wires these in: `/build`
stops before doing any work if the environment it would build in isn't
provably clean; a task is never marked done on the executor's word alone;
and every completed task leaves behind a dated folder a human (or
`/gate-audit`) can open and see exactly what was independently re-checked
and when. What doesn't change: the persona still authors (or `/plan` still
produces) the checkpoint block itself — `Do` / `Not here` / `Done means` /
`Evidence` — these scripts only consume it, never generate or edit it.

Per-script contract, described at the behavior level (exact
argument/flag shapes are a build-phase decision, not fixed here — see Open
questions):

- **`worktree-setup`** — given a branch name and the target project's own
  baseline verification command (e.g., its test suite invocation, however
  that project's `CLAUDE.md` names it — jig's own scripts don't hardcode any
  one project's test runner), creates a fresh branch and git worktree, then
  runs the baseline command inside it before any task is dispatched. A
  non-zero result (or any failing test) is a **dirty baseline**: the script
  exits non-zero with the failing output surfaced, and does not proceed —
  `/build`'s session stops before task 1, per this story's acceptance
  criteria. The worktree it created is left in place rather than deleted, so
  the failure stays inspectable (see Alternatives considered). Colliding
  with an existing branch/worktree of the same name fails loudly rather than
  silently reusing state — a stale worktree masquerading as a fresh one is
  the exact ambiguity this script exists to prevent.
- **`verify`** — given a task identifier and that task's Done-means items
  (already extracted from the checkpoint block — see Alternatives considered
  for why `verify` doesn't parse `PLAN.md` prose itself), independently
  re-runs each item according to its verification tier and reports a
  per-item PASS/FAIL, not a single suite-level boolean: a `script` item runs
  its named command and checks the exit code; a `test-backed` item runs the
  specific named test (not merely "the suite is green") and checks that test's
  own result; a `probe` item — inherently a human/observational check, e.g.
  "ps check" or "screenshot" — is verified by confirming a caller-supplied
  artifact exists, is non-empty, and (when an expected pattern is given)
  matches it; `verify` never takes the screenshot or runs `ps` on the
  executor's behalf, since choosing what observation proves a given
  capability is the checkpoint block author's judgment call, not a generic
  script's to invent. Every item — `cap` and `hold` alike — must PASS for
  the task to be considered verified; the cap/hold distinction is a
  categorization other consumers (the inspector, issue #15) use, not a
  difference in pass/fail weight here. Per-item results are always reported,
  even on an overall PASS, so a caller can tell whether a second failure
  lands on the *same* item as the first (the failure routine in issue #14
  needs exactly that distinction to choose FIX/RESAMPLE vs. REPLAN/ESCALATE).
- **`evidence-capture`** — given a task identifier and the artifacts
  `verify` (or `worktree-setup`) just produced, writes them to
  `docs/jig/evidence/<date>-<task>/` per this story's acceptance criteria,
  alongside a small manifest recording a timestamp, the commit SHA it was
  checked against, and which script produced each artifact. The freshness
  rule: the recorded timestamp must be `>=` the last code commit's
  timestamp on the branch being built. If it would be earlier, the script
  refuses to write and exits non-zero — evidence cannot be back-dated or
  copied forward from a prior, possibly stale, attempt. This directly
  operationalizes "Nothing signs off on itself": an evidence folder can only
  exist if it was provably produced after the commit it's supposed to be
  evidencing.

Principle alignment: "Judgment in the model, mechanics in scripts" is the
story's whole shape — all three scripts are pure mechanics, no scripts here
make a judgment call. "Nothing signs off on itself" is `verify`'s and
`evidence-capture`'s reason for existing at all. "Recommend one action; the
human decides. Propose; never apply" shapes `worktree-setup`'s dirty-baseline
stop (surface and halt, never auto-fix the baseline) and its collision
behavior (fail loud, never silently reuse). "Standalone-capable" is satisfied
trivially here — none of the three scripts calls out to studious, viva, or
any other sibling plugin; they are plain, dependency-free CLI tools.

## User journey

Walks `PRODUCT.md`'s critical user journey 2 (**Quick path**: "a single task
block straight to `/build`, then `/gate-audit`") — the journey the epic goal
explicitly names as this milestone's near-term dogfood target, since `/design`
and `/plan` don't exist yet. (Journey 1, the Full cycle, uses the same three
scripts identically once `/plan` exists; nothing below is quick-path-specific
except the absence of a `/plan`-generated `PLAN.md`.)

1. The developer has a single, hand-written checkpoint block — `Do` /
   `Not here` / `Done means` (cap/hold items, each with a verification tier)
   / `Evidence` — matching the format this project's own M0 dogfood produced
   and validated by hand (`docs/jig/dogfood/PLAN-viva-unified-session.md`,
   branch `docs/m0-paper-dogfood`).
2. The developer invokes `/build` (the sibling `build-skill` story). Before
   dispatching any executor, `/build`'s foreman calls `worktree-setup` with a
   fresh branch name and this project's baseline verification command.
3. `worktree-setup` creates the branch and worktree, then runs the baseline
   command inside it. If the baseline is dirty, the run stops here — the
   developer sees the pre-existing failure and resolves it outside `/build`;
   no executor is ever dispatched against an ambiguous starting point.
4. On a green baseline, `/build`'s foreman dispatches a fresh executor for
   the task, carrying only the task block, its Read-first pointers, and the
   task-execution-discipline skill (already merged, sibling story). The
   executor implements per TDD-per-capability and claims the Done-means
   items are satisfied.
5. Before that claim is accepted, `/build` calls `verify` with the task's
   Done-means items. `verify` independently re-runs each item per its tier
   and reports per-item PASS/FAIL. Only a clean per-item PASS moves the task
   toward a `PASS` status (the status-flip mechanics themselves are the
   sibling `build-skill` story's concern — see Out of scope).
6. On a verified PASS, `/build` calls `evidence-capture` with the task id
   and `verify`'s artifacts. `evidence-capture` stamps and writes them to
   `docs/jig/evidence/<date>-<task>/`, refusing the write if the stamp would
   predate the task's own commit.
7. The developer runs `/gate-audit` next, per the quick path. `/gate-audit`
   (or the developer directly) can open `docs/jig/evidence/<date>-<task>/`
   and see exactly what was independently re-checked, and when — the paper
   trail the quick path promises in place of a bare session transcript.

No step of either journey changes shape as a result of this story — these
scripts are the first real implementation of mechanics `PRODUCT.md`'s
journeys already named as "script-verified" and "evidence captured," not a
new step being added to them.

## Out of scope

- `/build`'s `SKILL.md` itself — the foreman/executor dispatch loop, the
  failure routine's FIX/RESAMPLE/REPLAN/ESCALATE branching, and the session
  verdict (`BUILT`/`PAUSED`/`ESCALATED`) belong to the sibling `build-skill`
  story (issue #14's skill half).
- The rough-in inspector (issue #15) — a separate story; none of these three
  scripts invokes it, stubs it, or assumes its existence.
- Status-flip persistence (`todo` → `in-progress` → `PASS`/`FIX`/`REPLAN`/
  `ESCALATE`). Issue #14's own Scripts-role bullet names "status flips"
  alongside worktree setup, verification, and evidence capture, but this
  story's acceptance criteria names only the latter three. Rather than
  silently absorb or silently drop the fourth item, this doc narrows to
  exactly what was assigned and flags the gap explicitly — see Open
  questions.
- A general `PLAN.md` markdown parser. `verify` consumes an already-extracted
  list of Done-means items, not raw checkpoint-block prose — parsing the
  checkpoint block's grammar for real is `/plan`'s (M3) job, via
  `plan-lint`, and this epic's own pre-mortem already names leaving
  `plan-lint` at its M1 stub behavior as the correct scope for now.
- Any change to `scripts/plan-lint` or `scripts/design-lint` beyond their
  existing stub behavior.
- Generating probe artifacts (taking a screenshot, running `ps`) on the
  executor's behalf — `verify` checks a supplied artifact's existence,
  freshness, and optional content match; producing that artifact is the
  executor's or the checkpoint-block author's job, per `PRODUCT.md`'s "no
  judgment tier" closed-enum discipline (`DESIGN.md`'s verification-tier
  row: `script` \| `test-backed` \| `probe` — no `judgment` tier permitted).
- CI wiring (a workflow job invoking these scripts on every PR) — `CLAUDE.md`
  notes even Ruff isn't wired into CI yet; that's a separate, unscoped
  concern this story doesn't pick up.
- Concurrent or multi-repo `/build` sessions — one `worktree-setup` call
  assumes a single sequential build, per the "sequential for-loop is the
  default" anti-cleverness principle; no locking or concurrency handling is
  designed here.

## Alternatives considered

1. **One combined `scripts/build` entrypoint with subcommands** (`build
   setup`, `build verify`, `build evidence`) instead of three separate
   executables. Rejected: the existing convention is one script per concern
   (`plan-lint`, `design-lint`), independently invocable and testable; three
   flat scripts keep that consistency (minimize structural drift) and let
   `build-skill`'s foreman call exactly the one it needs without a shared
   dispatch layer to build and maintain. A combined entrypoint is also a
   step toward the fleet-orchestration machinery `PRODUCT.md`'s "What we're
   NOT building" and the anti-cleverness principle both rule out.
2. **Have `verify` parse `PLAN.md`'s raw markdown directly**, full
   checkpoint-block grammar included, instead of accepting a pre-extracted
   item list. Rejected: that grammar isn't finalized — the M0 dogfood's own
   friction report found a real gap in it (coarser headings silently
   absorbed into the preceding task card) that a from-scratch parser here
   would have to solve twice: once ad hoc now, once for real when `/plan`
   (M3) and its `plan-lint` ship. Accepting a small, already-extracted item
   list keeps `verify`'s surface narrow and leaves the parsing problem with
   the story that actually owns the grammar.
3. **Auto-delete the worktree on a dirty-baseline stop**, cleaning up
   immediately rather than leaving it for inspection. Rejected: per
   "Recommend one action; the human decides. Propose; never apply," a
   script should surface a failure and let the human choose the next step
   (fix the baseline, discard the attempt, chase a flake) rather than
   mechanically destroying the one artifact that shows what went wrong. A
   stray worktree is cheap; a deleted diagnostic isn't.
4. **Let `verify`'s probe-tier check accept a caller-supplied PASS/FAIL
   boolean** instead of requiring a backing artifact. Rejected: an
   unsupported boolean is exactly the self-report `DESIGN.md`'s "no
   judgment tier permitted" rule and `PRODUCT.md`'s "Nothing signs off on
   itself" principle exist to close off — indistinguishable from the
   executor grading its own work.

## Operational readiness

These are one-shot local CLI scripts a Claude Code skill (or a human) invokes
inside a git worktree — no deployed service, no data migration, no running
process to monitor.

- **Rollout**: purely additive files under `scripts/`; nothing existing
  changes behavior. No feature flag or staged rollout needed.
- **Rollback**: `git revert` the commit that adds them. If reverted after
  `build-skill` has already wired them into `/build`'s `SKILL.md`, that
  sibling story's own fallback behavior is its concern, not this one's.
- **Failure visibility**: each script exits non-zero on its own failure
  condition (dirty baseline, any Done-means item FAIL, a stale
  evidence-write attempt) and prints a human-readable reason. There is no
  log aggregator or metric dashboard to wire for a one-shot CLI tool — the
  exit code plus the evidence directory's manifest are the observability
  surface, read by the calling skill, `/gate-audit`, or a human directly.

## Open questions

- Where "status flips" (named in issue #14's Scripts-role bullet, absent
  from this story's acceptance criteria) actually lands: a fast-follow to
  this story, folded into `build-skill`'s foreman state, or a story not yet
  filed. This doc doesn't resolve it — flagging so `build-skill`'s design
  doc makes an explicit call rather than the gap going unnoticed because
  each story assumed the other covered it.
- The exact input shape `verify` expects for a task's pre-extracted
  Done-means items (a small JSON document vs. a line-oriented text format)
  is a build-phase drafting decision once this doc's shape — accept
  extracted items, don't parse raw `PLAN.md` — is approved.
- How the target project's baseline verification command reaches
  `worktree-setup`: this doc assumes `build-skill`'s foreman supplies it
  (e.g., read from that project's own `CLAUDE.md` "Tests" convention, the
  way this very repo's `CLAUDE.md` documents its own `unittest` invocation),
  since deciding "which command is the suite" is a per-project judgment call
  this script shouldn't hardcode or infer on its own. Worth confirming
  explicitly in `build-skill`'s design doc rather than assuming silently.
- Whether `evidence-capture`'s freshness check should compare against the
  last commit on the branch being built (this doc's assumption, the simpler
  of the two) or, more strictly, the last commit touching the specific files
  a task's evidence covers. Flagging as a possible over- or under-strictness
  risk to confirm at build time, not resolved here.
