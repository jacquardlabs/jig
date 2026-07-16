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

## Proposed design

Consumer: product-reviewer Q2/Q6; `/plan`'s spine-building step.

Whenever a `/build` task reaches a real `PASS` in this session,
`evidence-capture` — already invoked at exactly that point, already holding
the commit sha and the task's `verify:results` — writes one additional
artifact into the same per-task folder it already owns
(`docs/jig/evidence/<date>-<task>/`): a self-contained replay bundle
carrying:

- the task's own identity: `task_id` (its heading number, e.g. `"1"`) and
  title — nothing richer (see Alternatives, and Out of scope)
- the task's own checkpoint block, captured as **raw verbatim text** — not
  a second, informal parse of `PLAN.md`'s own grammar
- the verification command(s) actually run and their result — already
  sitting in the `verify:results` artifact `evidence-capture` captures
  today; this design promotes it into the bundle, it doesn't re-derive it
- which model executed the task's fresh executor

That last field needs a real, small addition to `/build` itself, not just
to `evidence-capture`: today `skills/build/SKILL.md` has no step that
records which model a dispatched executor ran on at all (confirmed
directly — grepped the file for "model"; zero hits describing this).
`/build` gains a small new step, at dispatch time, naming the model it's
about to hand the fresh executor — mirroring how step 1.5 already states
the computed load-bearing set plainly before proceeding, rather than
leaving either fact implicit. The exact hand-off mechanism from that new
step into `evidence-capture`'s own capture call is left to `/plan`'s own
checkpoint-block breakdown (see Open questions) — out of this doc's
altitude per the design-doc-contract's own implementation-detail
exclusion.

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

**Failure path:** if the dispatching session can't determine which model
it handed the fresh executor (an invocation context where the model name
genuinely isn't recoverable), the bundle still gets written — the
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
  strings). Worth a viva issue; not fixed by this design.
- PRODUCT.md's two documented personas don't cleanly name "whoever
  eventually runs the replay harness and interprets its findings" (see
  Problem & persona). This design anchors on the primary persona's
  indirect benefit rather than inventing a third one — worth revisiting
  once the harness (#41) actually has a real user.

---

## Revision History

Signed off via viva review — 1 round, 8 sections, 0 revised. 2026-07-16
