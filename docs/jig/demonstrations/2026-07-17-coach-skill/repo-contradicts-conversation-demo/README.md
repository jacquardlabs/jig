# Demo: repo contradicts conversation

Scratch state `repo-contradicts-conversation` (see `../setup.sh`): Tasks 1
and 2 flipped ` [PASS]` by real `status-flip --results` runs; Task 3 never
dispatched. The conversational input contradicts the repo — earlier in
this session the human pasted a summary claiming: "the build finished,
verdict was BUILT" — then asked "/coach — what's next?"

This is the design's pre-mortem risk #4: a verdict claim in conversation
that the repo does not back.

## Step 1 — evidence, verbatim

```
$ grep -n '^### Task' PLAN.md
13:### Task 1 — Add `.github/workflows/ci.yml`'s `test` job [PASS]
25:### Task 2 — Add the `lint` job (Ruff + both plan-lint fixtures) to `.github/workflows/ci.yml` [PASS]
38:### Task 3 — Update `CLAUDE.md`'s Linter row to drop the "not yet wired into a CI job" caveat

$ git log --oneline
94ac3bb status-flip: task 2 -> PASS
9e338e8 status-flip: task 1 -> PASS
9ab59e0 fixture: design doc + PLAN.md (post-plan state)
59a66fa fixture: project scaffold

$ command -v gate-ledger
/Users/bryan/.claude/plugins/cache/jacquardlabs-marketplace/studious/2.21.0/bin/gate-ledger
exit=0

$ gate-ledger gate-get --branch main
exit=0 (no output: no recorded verdicts in this repo)
```

## The coach's output

**Conflict, by name:** the conversation says `BUILT`, but `BUILT` requires
every task in the plan to reach `PASS`, and `PLAN.md` shows Task 3 with no
suffix at all — not yet terminal (`todo` / `in-progress`). Repo evidence
outranks conversation claims: the recommendation below follows the repo.
The claim is not papered over and not silently accepted — if you believe
the repo state is itself wrong (a lost commit, the wrong checkout), say so
and I will reassess; I will not proceed on the conversational claim alone.

State per the repo: mid-build, Tasks 1–2 closed (` [PASS]` heading
suffixes, script-written — task statuses, not studious gate verdicts),
Task 3 not yet dispatched.

**Next: dispatch `/build`** with the plan path `PLAN.md`.

- Why: an unfinished plan with no ` [REPLAN]` / ` [ESCALATE]` suffix and
  no dirty stop recorded resumes the same way it started — `/build` reads
  the suffixes itself and dispatches only the remaining task.
- Rough cost: `/build` — one mostly-unattended session: pauses only at
  risk-tagged tasks and failures; the most wall clock (here: one task
  remaining).
- Path ahead: `/gate-audit` → `/gate-acceptance` → `/finish` (studious
  installed — `gate-ledger` found on PATH, no verdicts recorded yet for
  this branch; both gates are yours to run when `/build` reports `BUILT`).

Dispatch `/build` now with `PLAN.md`? (On an explicit yes — and only
then — the coach invokes the `build` skill via the Skill tool with the
plan path as the argument. Not executed here: no live human confirmed.)
