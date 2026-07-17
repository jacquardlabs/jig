# Demo: revision-loop state (ESCALATE)

Scratch state `escalate` (see `../setup.sh`): Task 1 flipped ` [PASS]` and
Task 2 flipped ` [ESCALATE]` by real `status-flip` runs; Task 3 untouched;
studious absent. The human's conversational input, in a fresh
conversation: "/coach — the build escalated on something. Help."

## Step 1 — evidence, verbatim

```
$ grep -n '^### Task' PLAN.md
13:### Task 1 — Add `.github/workflows/ci.yml`'s `test` job [PASS]
25:### Task 2 — Add the `lint` job (Ruff + both plan-lint fixtures) to `.github/workflows/ci.yml` [ESCALATE]
38:### Task 3 — Update `CLAUDE.md`'s Linter row to drop the "not yet wired into a CI job" caveat

$ git log --format='%s%n%n%b' --grep='status-flip: task 2'
status-flip: task 2 -> ESCALATE

Design assumption falsified: docs/design/plan-lint-ci.md's Proposed design has the lint job asserting both fixture exit codes in one uniform step shape, but broken-plan.md's expected exit 1 cannot be expressed as the same plain invocation as clean-plan.md's exit 0 -- the design's own 'symmetrical two-invocation' claim needs revising, which is outside this plan's authority.

$ ls docs/design/
plan-lint-ci.md
```

## The coach's output

State: escalated on Task 2 — the design, not the plan, is in question.

- Task 2 carries the ` [ESCALATE]` suffix (a `PLAN.md` heading suffix,
  script-written; no studious gate verdict was read here).
- The ESCALATE finding lives in the status-flip commit's body, quoted
  verbatim above — an ` [ESCALATE]` is terminal for the build session:
  `PRODUCT.md`'s journey 3 routes it back to `/design` in revision mode,
  never back to hand-editing the plan.
- The design doc in question is `docs/design/plan-lint-ci.md`.

**Next: dispatch `/design` in revision mode**, with two things passed
explicitly — the quoted ESCALATE finding ("Design assumption falsified:
docs/design/plan-lint-ci.md's Proposed design has the lint job asserting
both fixture exit codes in one uniform step shape, but broken-plan.md's
expected exit 1 cannot be expressed as the same plain invocation as
clean-plan.md's exit 0 -- the design's own 'symmetrical two-invocation'
claim needs revising, which is outside this plan's authority.") and the
design doc path `docs/design/plan-lint-ci.md`.

- Why: the recorded finding names a falsified design assumption — exactly
  what ` [ESCALATE]` exists for; revising the checkpoint block by hand
  (the ` [REPLAN]` move) would paper over a design-level contradiction.
- Rough cost: `/design` — one interactive session: 5–9 interview answers
  plus per-section sign-off; the most human attention.
- Path ahead: `/plan` (re-plan against the `REVISED` doc) → `/build` →
  `/finish` — skipping the `/gate-design-review` recommendation for the
  revised doc — studious not installed; named, not silent.

Dispatch `/design` in revision mode now, with the quoted finding and
`docs/design/plan-lint-ci.md`? (On an explicit yes — and only then — the
coach invokes the `design` skill via the Skill tool with exactly that
context as the argument, never "see conversation above." Not executed
here: no live human confirmed.)
