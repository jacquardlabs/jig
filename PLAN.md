# Plan: persist a replay bundle per build task (issue #34)

Spine: Task 1 -> Task 2 (Task 2 rests on Task 1's recorded model value)

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
