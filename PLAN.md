# Plan: persist a replay bundle per build task (issue #34)

Spine: Task 1 -> Task 2 -> Task 3 -> Task 4 (Task 2 rests on Task 1's
recorded model value; Task 3 rests on both, closing the `unavailable`-
fallback gap `/gate-acceptance`'s product review found between the two;
Task 4 is independent of Tasks 1-3's own shipped behavior — a `/build`-
mechanics fix `/gate-audit`'s re-audit found, applied to the same branch)

Inventory finding, stated plainly before drafting: `scripts/evidence-capture`
needs **zero code changes**. Its `--artifact PRODUCER:LABEL=PATH` mechanism
(`scripts/evidence-capture`) is already fully generic — it copies whatever
file it's handed into the evidence folder and manifests it, never
interpreting content. The design doc's own language ("evidence-capture...
writes one additional artifact") reads as if evidence-capture itself needs
new logic; verified against the real script and `skills/build/SKILL.md`'s
own step 7, it doesn't. The entire scope is two small additions to
`skills/build/SKILL.md`'s prose: one at step 2 (Dispatch), one at step 7
(On overall PASS) — reusing the existing `--artifact` call step 7 already
makes for `verify:results`, exactly the way a `probe` item's artifact
already rides that same call.

Also verified against the real repo, not trusted from the design doc's
prose: step 7 only ever runs on the already-known-PASS branch (`verify`,
step 5, determines `results.json`'s own `overall` field first;
`status-flip` only reads it afterward) — so "no bundle for a task that
doesn't reach PASS" and "only the final, PASS-reaching attempt" are both
already true for free at this hook point, not new logic either task below
needs to build.

Infra inventory (issue #13): test runner is `uv run --no-project python3
-m unittest discover -s tests -v`, per `CLAUDE.md`. No `probe`-tier item
is proposed by either task below — no scripted-browser/UI-driving tooling
exists in this repo (confirmed: no `playwright` in any manifest, no
config file), and nothing in this feature needs live-UI observation; every
`Done means` item below is `test-backed` against `skills/build/SKILL.md`'s
own prose, matching `tests/test_build_skill.py`'s established
phrase-assertion convention for this exact class of change.

### Task 1 — Foreman records which model it dispatched the Executor on [PASS]
Why now:    the bundle's one decisive field needs a real, known value before anything can assemble a bundle around it — and this is independently valuable on its own, the one visible change the design doc's User journey names.
Read first: `skills/build/SKILL.md`
Rests on:   n/a
Do:         add to step 2 (Dispatch), beside the existing "capture this attempt's dispatch timestamp" instruction, a parallel instruction to name which model the Executor runs on — an explicit override if one is passed, otherwise the Foreman's own resolved session model (stated in its own system prompt) since a no-override dispatch inherits it. State it plainly, mirroring step 5's own "state the computed load-bearing set plainly before proceeding" pattern.
Not here:   bundle assembly (Task 2); any `evidence-capture` code change (confirmed unnecessary, see inventory above); issue #33's own dispatch-telemetry event (a separate, cross-repo story).

Done means:
1. [cap]  `skills/build/SKILL.md` step 2's dispatch text names which model the Executor runs on, distinguishing an explicit `override` from the `inherited` case, immediately beside the existing dispatch-timestamp capture           (tier: test-backed `tests/test_build_skill.py`)
2. [hold] the existing dispatch-timestamp and boundary-line phrase assertions in `tests/test_build_skill.py` still pass unchanged                                                                             (tier: test-backed `tests/test_build_skill.py`)
Evidence: n/a

### Task 2 — Foreman assembles and writes the replay bundle via evidence-capture's existing artifact mechanism [PASS]
Why now:    Task 1's recorded model is the last of four fields the bundle needs; this task wires all four into the one write path the design doc calls for.
Read first: `skills/build/SKILL.md`, `scripts/evidence-capture`
Rests on:   Task 1 (needs the recorded model value from Task 1's own dispatch-time addition)
Do:         add to step 7 (On overall PASS), immediately before the existing `scripts/evidence-capture` call, an instruction to assemble one JSON object at a scratch path — `task_id`, title, the task's own checkpoint block as raw verbatim text, the verify command(s) and result already sitting in `results.json`, and Task 1's recorded model — then add one more `--artifact build:replay-bundle=<scratch-path>/replay-bundle.json` flag to the same `evidence-capture` call `verify:results` already uses. No new evidence-capture invocation, no new commit, matching exactly how a `probe` item's own artifact already rides that call.
Not here:   the replay harness itself (issue #41, explicitly out of scope in the design doc); issue #33's richer identity fields (`run_id`/`step_id`/`parent_step_id`/`skill`/`role`/`routing_reason`) — none exist in this session model today; full attempt-by-attempt retry history — only the final attempt this hook point ever sees.

Done means:
1. [cap]  step 7's new instruction states the bundle is assembled at a scratch path (never inside the worktree first) before the existing evidence-capture call, naming all four fields: `task_id`, title, raw checkpoint-block text, and the verify command/result already in `results.json`                (tier: test-backed `tests/test_build_skill.py`)
2. [cap]  step 7's new instruction states the one additional `--artifact build:replay-bundle=<scratch-path>/replay-bundle.json` flag added to the existing evidence-capture call, not a second invocation                                                                                                          (tier: test-backed `tests/test_build_skill.py`)
3. [hold] the existing step 7 phrase assertions in `tests/test_build_skill.py` (the `verify:results` artifact call, the commit-before-status-flip ordering) still pass unchanged                                                                                                                                     (tier: test-backed `tests/test_build_skill.py`)
Evidence: n/a

### Task 3 — Foreman's dispatch-model instruction covers the undeterminable case [PASS]
Why now:    `/gate-acceptance`'s product review (SHOULD FIX) found the design doc's own Failure path — an `unavailable` sentinel when the dispatch model genuinely can't be determined — was dropped from the shipped step 2/step 7 prose; closing it before merge keeps the design's own documented degradation path from silently regressing to "refuse the whole capture" or improvisation.
Read first: `skills/build/SKILL.md`, `docs/design/replay-bundle.md`
Rests on:   Task 1, Task 2 (extends the exact instructions both tasks added; doesn't change either's shipped behavior)
Do:         add one sentence to step 2's "Name this attempt's dispatch model" bullet naming a third case — when the model genuinely can't be determined, state it plainly as `unavailable` — beside the existing `override`/`inherited` cases, per the design doc's own Failure path (`docs/design/replay-bundle.md`'s User journey section: "the bundle still gets written — the `model` field is recorded as `unavailable`, not a reason for `evidence-capture` to refuse the whole capture"). Reference this case from step 7's bundle-assembly bullet so a Foreman hitting it still assembles and writes the bundle with `model` recorded as `unavailable`, never refusing the whole `evidence-capture` call.
Not here:   any new test coverage for what actually triggers the undeterminable case in practice (the design doc itself calls this near-zero probability); any change to the already-shipped `override`/`inherited` cases.

Done means:
1. [cap]  step 2's dispatch-model instruction names a third case, `unavailable`, for when the model genuinely can't be determined, immediately beside the existing `override`/`inherited` cases           (tier: test-backed `tests/test_build_skill.py`)
2. [cap]  step 7's bundle-assembly instruction states that an `unavailable` value is written into the bundle rather than refusing the `evidence-capture` call                                              (tier: test-backed `tests/test_build_skill.py`)
3. [hold] the existing step 2 and step 7 phrase assertions in `tests/test_build_skill.py` (the `override`/`inherited` cases, the four-field bundle, the single `--artifact` flag) still pass unchanged        (tier: test-backed `tests/test_build_skill.py`)
Evidence: n/a

### Task 4 — Foreman's step 1.5 gains a defined path for a plan growing mid-session [PASS]
Why now:    `/gate-audit`'s re-audit found (Important, architecture) that step 1.5's "compute once... it never changes mid-loop" invariant has no defined path for what this exact session did — appending Task 3 with a `Rests on:` line that retroactively made the already-`PASS`ed, leaf-classified Task 2 load-bearing. The catch-up inspection performed this session held by human diligence, not by any mechanism `/build` itself provides, and invented an ad hoc evidence-dir naming convention (`2-retroactive-inspection`) with no sanction anywhere in `skills/build/SKILL.md`.
Read first: `skills/build/SKILL.md`
Rests on:   n/a (a `/build`-mechanics fix, independent of Tasks 1-3's own replay-bundle behavior)
Do:         amend step 1.5's own text to name the plan-growth case explicitly: if `PLAN.md` is amended after task 1 is ever dispatched — a new task appended whose own `Rests on:` line names a task that already reached `PASS` — recompute the load-bearing set immediately, before dispatching the new task's own executor. Any task whose status changes from leaf to load-bearing under the recompute, having already reached `PASS` without an Inspector, gets a retroactive catch-up Inspector dispatched now, scoped to that task's own already-existing commit(s), before the new dependent task's own executor is dispatched. Capture the catch-up Inspector's report under a sanctioned evidence-dir naming convention, `<task>-retroactive-inspection` — `evidence-capture` always stamps against current `HEAD`, so reusing the task's own original evidence folder would misdate the inspection against a later, unrelated commit.
Not here:   adopting the auditor's other named option (forbidding a `Rests on:` back-reference to an already-`PASS`ed task) — this task keeps plans free to grow, matching this session's own successful workaround, rather than restricting it; any change to how `/plan` itself proposes a spine; a generalized "recompute on every step" mechanism beyond the specific amendment-triggered case named here.

Done means:
1. [cap]  step 1.5's text names the plan-growth case: a new task's `Rests on:` line naming an already-`PASS`ed task triggers an immediate load-bearing-set recompute, before that new task's own executor is dispatched           (tier: test-backed `tests/test_build_skill.py`)
2. [cap]  step 1.5's text states that a task whose status changes from leaf to load-bearing under the recompute, having already reached `PASS` without an Inspector, gets a retroactive catch-up Inspector dispatched now, scoped to that task's own existing commit(s)           (tier: test-backed `tests/test_build_skill.py`)
3. [cap]  step 1.5's text names the sanctioned evidence-dir naming convention for a retroactive catch-up inspection, `<task>-retroactive-inspection`, and states why the task's own original evidence folder isn't reused           (tier: test-backed `tests/test_build_skill.py`)
4. [hold] the existing step 1.5 "compute once... before task 1 is ever dispatched" phrase assertions in `tests/test_build_skill.py` still pass unchanged           (tier: test-backed `tests/test_build_skill.py`)
Evidence: n/a

Risk: REPLAN-RISK (Task 2) — the design doc's own "Accepted limit" (Open
questions) concedes the no-override-inherits-the-Foreman's-model equation
Task 1 records is asserted, not independently verified anywhere in this
plan; if that equation is ever false in practice, Task 2's bundle carries
a wrong-but-confident value with no sentinel distinguishing it from a
correct one — a design-level question (real independent corroboration
needs cctx's own session-trace export, per the design doc), not a local
retry, if it surfaces.

Mitigation performed before Task 2's dispatch: a direct empirical spot
check, run immediately before this task's dispatch, of a plain Task-tool
subagent given no model override — it self-reported "Sonnet 5 /
claude-sonnet-5," matching the Foreman's own resolved session model
exactly (this Foreman's own system prompt states the same model). This
is real, single-sample corroboration in this exact session and harness
version — not the permanent, cctx-trace-backed proof the design doc's
"Accepted limit" scopes to issue #33, and the equation could still drift
in a future session or a different harness release. The tag stays
REPLAN-RISK; this note records the corroboration actually gathered, not
a downgrade of the underlying limit.

## Not-here follow-ups
- Independent corroboration of the recorded `model` field against cctx's
  own session-trace export — deferred to issue #33/cctx#193/#196, per the
  design doc's own "Accepted limit" resolution.
- Issue #33's richer identity fields (`run_id`, `step_id`, `parent_step_id`,
  `skill`, `role`, `routing_reason`) — not adopted; revisit once #33 ships.
- The replay harness itself (issue #41) that will eventually read these
  bundles — a separate, differently-scoped story.
- A `viva-qa` bug surfaced during this feature's own `/design` session
  (a submitted note with no accompanying choice is silently dropped) —
  already filed as a comment on jacquardlabs/viva#121, not a jig follow-up.

---

## Revision History

Signed off via viva review — 1 round, 4 sections, 0 revised. 2026-07-16
