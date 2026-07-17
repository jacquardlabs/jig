# Demo: mid-build PAUSED state (REPLAN)

Scratch state `mid-build-replan` (see `../setup.sh`): the post-plan state
after a partial build — Task 1 flipped ` [PASS]` by a real `status-flip
--results` run, Task 2 flipped ` [REPLAN]` by a real `status-flip --status
REPLAN --reason` run, Task 3 untouched. The human's conversational input,
in a fresh conversation the day after: "/coach — yesterday's build stopped
somewhere. What now?"

## Step 1 — evidence, verbatim

```
$ grep -n '^### Task' PLAN.md
13:### Task 1 — Add `.github/workflows/ci.yml`'s `test` job [PASS]
25:### Task 2 — Add the `lint` job (Ruff + both plan-lint fixtures) to `.github/workflows/ci.yml` [REPLAN]
38:### Task 3 — Update `CLAUDE.md`'s Linter row to drop the "not yet wired into a CI job" caveat

$ git log --oneline
782f602 status-flip: task 2 -> REPLAN
9e338e8 status-flip: task 1 -> PASS
9ab59e0 fixture: design doc + PLAN.md (post-plan state)
59a66fa fixture: project scaffold

$ git log --format='%H%n%s%n%n%b' --grep='status-flip: task 2'
782f602a5f71d7a366daf93fdeee9aaa1c90b0af
status-flip: task 2 -> REPLAN

Done means 2 unmeetable as written: a plain 'scripts/plan-lint tests/fixtures/plan-lint/broken-plan.md' step exits 1 and fails the job, so the job can never 'still report success on that expected 1'. The block's Do: needs the expected-1 invocation scripted (e.g. guard the step so exit 1 is the passing outcome) before an executor can satisfy the item.
```

## The coach's output

State: mid-build, paused on Task 2.

- Task 1 carries the ` [PASS]` suffix, Task 2 carries ` [REPLAN]`, Task 3
  carries no suffix — task-status suffixes per `scripts/status-flip`'s own
  grammar (these are `PLAN.md` heading suffixes, not studious gate
  verdicts; no gate verdict was read here).
- The Foreman's reason lives in commit `782f602`'s body (quoted verbatim
  above) — a `REPLAN` is resumable: the block gets revised by hand, then
  `/build` re-runs; nothing routes back to `/design` for this.

**Next: a manual step — revise Task 2's checkpoint block by hand.** The
recorded reason, quoted: "Done means 2 unmeetable as written: a plain
'scripts/plan-lint tests/fixtures/plan-lint/broken-plan.md' step exits 1
and fails the job, so the job can never 'still report success on that
expected 1'. The block's Do: needs the expected-1 invocation scripted
(e.g. guard the step so exit 1 is the passing outcome) before an executor
can satisfy the item."

- Why: ` [REPLAN]` is the one state whose next step belongs to the human's
  editor, not to a dispatched skill — the plan cannot be amended by the
  loop under its own failure pressure, and the coach writes nothing.
- Rough cost: a REPLAN block revision — minutes of hand editing.
- Path ahead: `/build` → `/gate-audit` → `/gate-acceptance` → `/finish`.

Tell me when the block is revised. I will then re-read `PLAN.md` — fresh
evidence, not memory — and, if the revision holds, ask: "dispatch `/build`
with `PLAN.md` now?" One confirmation, one dispatch, as always. (No
dispatch occurs in this transcript: the manual step is the
recommendation, and no live human has revised the block or confirmed.)
