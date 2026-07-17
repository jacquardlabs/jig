# Design: persist a replay bundle per build task (issue #34)

## Problem & persona

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

Consumer: the human deciding to fund the work; product-reviewer Q1.

This feature's direct beneficiary is genuinely indirect, and that's worth
naming rather than papering over: nobody runs a replay *harness* today
(issue #41 is the harness itself, not yet built), so there is no user
sitting down to consult a replay bundle this week. The problem it solves is
one step removed — the primary persona above wants a *verifiable* build
workflow, and every real `/build` task today is a model-routing decision
(which model executed this task) made once, verified once, and then
discarded. There is no way to later ask "would a cheaper model have passed
this same task?" without re-creating the task's exact inputs by hand. This
design gives that persona, in a future session tuning their own team's
routing choices, a zero-marginal-cost record of what already happened —
without inventing a third, undocumented persona for "whoever eventually
runs the harness." PRODUCT.md names two personas (primary: a developer
using jig day-to-day; secondary: a standalone user with no other
jacquardlabs tooling); neither is written as "a jig maintainer optimizing
model cost," and this design deliberately doesn't fabricate that as a new
one — see Open questions.

**Resolved at `/gate-design-review`, not deferred:** the reviewer's own
SHOULD FIX asked whether building bundle-before-harness is deliberate
sequencing or accidental scope. It's deliberate, and issue #34 itself
already says so — its own "Feeds" section states plainly that "the
cross-cutting replay harness... needs these bundles for its first loop,"
meaning the harness *cannot* be designed against real inputs until bundles
already exist to feed it. Write-ahead-of-read isn't a gap here; it's the
only order this dependency can run in. That doesn't make the indirection
free, though — pre-mortem risk #2 (this schema going stale before #41 ever
reads it) is the real cost of that ordering, and the safeguard is to bound
it to an existing checkpoint rather than "revisit someday": the next
`/deep-review architecture` pass (CLAUDE.md's own quarterly-or-pre-major-
feature cadence) should confirm at least one bundle has ever been read by
anything before assuming this schema still holds.

## Proposed design

Consumer: product-reviewer Q2/Q6; `/plan`'s spine-building step.

Whenever a `/build` task reaches a real `PASS` in this session,
`evidence-capture` — already invoked at exactly that point, already holding
the commit sha and the task's `verify:results` — writes one additional
artifact into the same per-task folder it already owns
(`docs/jig/evidence/<date>-<task>/`): a self-contained replay bundle
carrying:

Consolidated into one `replay-bundle.json` rather than left as two new
discrete files (`model`, the raw checkpoint block) alongside what
`evidence-capture` already writes: the harness's own first loop (per issue
#34's own "Feeds" wording) reads *one task* as *one eval case* — a single
file gives it one atomic read per case instead of reassembling one from
several files in a folder whose other contents (`manifest.json`,
freshness-check metadata) aren't part of the case at all.

- the task's own identity: `task_id` (its heading number, e.g. `"1"`) and
  title — nothing richer (see Alternatives, and Out of scope)
- the task's own checkpoint block, captured as **raw verbatim text** — not
  a second, informal parse of `PLAN.md`'s own grammar
- the verification command(s) actually run and their result — already
  sitting in the `verify:results` artifact `evidence-capture` captures
  today; this design promotes it into the bundle, it doesn't re-derive it
- which model the Foreman dispatched the Executor on

That last field needs a real, small addition to `/build` itself, not just
to `evidence-capture`: today `skills/build/SKILL.md` has no step that
records which model a dispatched Executor ran on at all (confirmed
directly — grepped the file for "model"; zero hits describing this).
`/build` gains a small new step, at dispatch time, naming the model it's
about to hand the fresh Executor — mirroring how step 1.5 already states
the computed load-bearing set plainly before proceeding, rather than
leaving either fact implicit. The exact hand-off mechanism from that new
step into `evidence-capture`'s own capture call is left to `/plan`'s own
checkpoint-block breakdown (see Open questions) — out of this doc's
altitude per the design-doc-contract's own implementation-detail
exclusion.

**Resolved, not deferred: this is not the self-attestation "nothing signs
off on itself" rules out — but the first attempt at this resolution
overstated the mechanism, and a re-review of this doc caught it.** "Nothing
signs off on itself" is about a *judgment* a task can't be trusted to make
about its own work (did I actually pass, is my own test meaningful) — it's
why `status-flip` never lets the model write its own `PASS`. The `model`
field carries no such judgment. But the claim that it's simply "a parameter
the Foreman sets in its own immediately-preceding tool call" is only true
for one of two real dispatch shapes, not both: the Task/Agent dispatch's
own `model` parameter is *optional* — when the Foreman passes an explicit
override, that value is exactly what gets set, trivially self-logged. When
it's omitted (dispatching with no override, the common case), the Executor
instead inherits the Foreman's own resolved session model — nothing was
"set" in that call at all. The fix isn't to weaken this to best-effort
recovery, though: a Foreman session already knows its own model identity
directly, stated in its own system prompt, independent of whether it chose
to override the dispatch. So in *both* shapes the fact is knowable at
dispatch time, not discovered afterward — an explicit override is what was
set; an inherited dispatch is the Foreman's own already-known identity.
Either way it's the same class of self-log `verify:results` already is (the
command that ran, logged as what it was, not re-judged), never a self-grade.
Given that, the expected `unavailable` rate is near-zero: the only
legitimate case is a dispatch path outside the Foreman's own visibility
entirely, not the ordinary override-or-inherit shape above.

Only the task's **final, PASS-reaching attempt** is captured — not the
full `FIX`/`RESAMPLE` retry history a task may have gone through. No bundle
is written at all for a task that doesn't reach `PASS` in this session
(paused, escalated, or otherwise left inconclusive) — there is no partial
or null-result bundle shape.

## User journey

Consumer: product-reviewer Q3; `/plan`'s task-boundary decisions.

Touches critical user journeys 1 (Full cycle) and 2 (Quick path) equally —
both eventually call `/build`, and this hooks into `/build`'s own
per-task completion, not a step either journey adds separately.

The developer's day-to-day flow is unchanged: they run `/build` against a
real `PLAN.md`; task 1 reaches `PASS`; `evidence-capture` writes the
evidence folder exactly as it does today, and — new, but invisible to
them unless they go looking — also writes `replay-bundle.json` inside it.
Nothing about `/finish`'s own PR evidence table changes; the bundle is a
byproduct file, never something `/finish` surfaces to a human reviewer.
The one visible change: `/build`'s own transcript now states which model
it dispatched for each task, where today it says nothing.

**Failure path:** if the Foreman can't determine which model it handed
the Executor (an invocation context where the model name genuinely isn't
recoverable — see Proposed design for why this should be rare), the
bundle still gets written — the
`model` field is recorded as `unavailable`, not a reason for
`evidence-capture` to refuse the whole capture. A replay bundle missing
one field is still useful evidence of the task's inputs and verification
result; failing the capture entirely over one unrecoverable field would
throw away the parts that aren't in question, the same "don't discard
what you can still verify" posture `evidence-capture`'s own freshness
checks already take toward a task's other artifacts.

## Out of scope

Consumer: product-reviewer Q4.

- The replay harness itself (issue #41) — this design writes the bundle
  only; nothing here reads one back.
- Full attempt-by-attempt retry history — only the final passing attempt.
- A bundle for a task that doesn't reach `PASS` this session.
- Issue #33's richer identity fields (`run_id`, `step_id`,
  `parent_step_id`, `skill`, `role`, `routing_reason`) — none of these
  exist in `/build`'s own session model today (confirmed: zero mentions in
  `skills/build/SKILL.md`); revisit once #33 actually ships them.
- A structured parse of the checkpoint block — raw text only.
- Wiring into cctx's own cost-attribution join — that's #33's and #40's
  job, cross-repo, not this bundle's.

## Alternatives considered

Consumer: product-reviewer Q5; future readers reconsidering a rejected
path.

1. **Write the bundle at `/finish` time instead**, assembling it from
   already-captured evidence plus `PLAN.md`'s still-on-disk checkpoint
   blocks at close-out. Rejected: `/finish`'s own Step 6 cleanup deletes
   `PLAN.md`, and more importantly a `KEEP`/`DISCARD`/paused branch may
   never reach `/finish` at all — writing at `/build` time means every
   real `PASS` gets a durable bundle regardless of whether the branch is
   ever closed out, reusing `evidence-capture`'s existing "scripts write,
   session commits" ownership instead of inventing a second, not-always-
   reached write path.
2. **Speculatively pre-adopt issue #33's full proposed identity shape**
   now. Rejected: half those fields (`run_id`, `step_id`, `parent_step_id`)
   don't correspond to anything `/build`'s own session model tracks today;
   committing to them now risks a bundle schema that has to be reworked
   once #33's real shape actually ships and possibly differs from its own
   current issue-body draft.
3. **Capture full attempt-by-attempt retry history.** Rejected for this
   pass: real added complexity (every `FIX`/`RESAMPLE` cycle needing its
   own record) for a benefit — a richer future eval signal — the harness's
   first loop doesn't need; it only needs one task's final input/
   verification pairing.
4. **Refuse the `model` field entirely, treating any self-reported value
   as untrustworthy the same way a task's own PASS/FAIL claim is.**
   Rejected: this conflates two different things "nothing signs off on
   itself" separates — a *judgment* about one's own work (what that
   principle targets) and a *fact* about a parameter just set in one's own
   preceding action (what this field is). Refusing it would throw away the
   one datum the entire feature exists to capture, over a category error
   about what the principle actually rules out.

## Operational readiness

Consumer: `/gate-audit`'s operability lane; `/build`'s rollout-tier
verification.

No deployed service, no data migration — the same class of change as
`design-lint`/`plan-lint`'s own stories: a script (`evidence-capture`)
plus a small addition to a skill's own prose (`skills/build/SKILL.md`).
Rollback is a plain revert of both; no already-written bundle needs
cleanup, since nothing downstream reads one yet (the harness doesn't
exist). How this is known to be working or failing: `evidence-freshness`
already re-validates every artifact in a task's evidence folder (commit-
sha ancestry, mtime) — a missing, stale, or malformed
`replay-bundle.json` surfaces exactly the way any other evidence-capture
artifact problem does today, with no new monitoring surface needed.

## Open questions

Consumer: the human sponsor; the next `/design` revision round.

- The exact Foreman-to-`evidence-capture` hand-off mechanism for the model
  name (a new CLI flag? a sidecar file the Foreman writes and
  `evidence-capture` reads?) is left to `/plan`'s own checkpoint-block
  breakdown, not pinned here.
- Once issue #33 ships a real dispatch-telemetry event with real
  `run_id`/`step_id` fields, should `replay-bundle.json` be extended to
  carry them, or should the two stay deliberately separate artifacts for
  different consumers? Not resolved here — flagged for whoever builds #33.
- **A real bug surfaced during this design's own interview round:**
  `viva-qa` silently drops a submitted `note` when no `choice` accompanies
  it — confirmed directly (a comment clarifying that cctx#193 had closed
  never appeared in `.viva/answers.json`, both recorded notes were empty
  strings). Already tracked: jacquardlabs/viva#121 (same root cause, a
  narrower trigger); this design's repro is recorded there as a comment,
  broadening its scope. Not fixed by this design.
- **Resolved at `/gate-design-review`:** PRODUCT.md's two documented
  personas don't cleanly name "whoever eventually runs the replay harness
  and interprets its findings" — see Problem & persona's own resolution
  (issue #34's stated "Feeds" dependency makes the sequencing intentional,
  bounded by the next `/deep-review architecture` pass, not left open).

---

## Revision History

Signed off via viva review — 1 round, 8 sections, 0 revised. 2026-07-16

Signed off via viva review — 1 round, 8 sections, 0 revised. 2026-07-16
