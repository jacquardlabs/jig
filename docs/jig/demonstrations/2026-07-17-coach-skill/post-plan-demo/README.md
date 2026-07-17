# Demo: post-plan state

Scratch state `post-plan` (see `../setup.sh`): the real
`docs/design/plan-lint-ci.md` plus the real, viva-approved ci-wiring
`PLAN.md`, committed; no task has any status suffix; studious absent. The
human's conversational input, in a fresh conversation with no prior
verdicts: "/coach — where am I on the CI wiring work?"

## Step 1 — evidence, verbatim

```
$ ls docs/design/
plan-lint-ci.md

$ grep -n '^## Revision History' docs/design/plan-lint-ci.md
exit=1

$ test -f PLAN.md
exit=0

$ grep -n '^### Task' PLAN.md
13:### Task 1 — Add `.github/workflows/ci.yml`'s `test` job
25:### Task 2 — Add the `lint` job (Ruff + both plan-lint fixtures) to `.github/workflows/ci.yml`
38:### Task 3 — Update `CLAUDE.md`'s Linter row to drop the "not yet wired into a CI job" caveat

$ ls docs/jig/evidence docs/jig/reports
ls: docs/jig/evidence: No such file or directory
ls: docs/jig/reports: No such file or directory
exit=1

$ env PATH=/usr/bin:/bin sh -c 'command -v gate-ledger'
exit=1
```

## The coach's output

State: planned, not yet built.

- One design doc — `docs/design/plan-lint-ci.md`. It carries no
  `## Revision History` heading, so a completed viva sign-off is
  unconfirmed from the repo alone (and this fresh conversation holds no
  `DESIGNED` verdict to fill that gap).
- A plan exists — `PLAN.md` at the repo root (filesystem read), three
  `### Task N` blocks, none carrying a ` [PASS]` / ` [REPLAN]` /
  ` [ESCALATE]` suffix: every task is still not yet terminal
  (`todo` / `in-progress`).
- No evidence folders, no build reports — nothing has been built.
- studious not installed — no recorded gate verdicts to read; the
  design-review gate this plan would normally have passed through is a
  named gap, not an assumed pass.

**Next: dispatch `/build`** with the plan path `PLAN.md`.

- Why: a plan with zero terminal suffixes is exactly the "PLAN.md present,
  no terminal suffixes" row — building is the only step that moves this
  state, and re-running `/design` or `/plan` would redo signed work.
- Rough cost: `/build` — one mostly-unattended session: pauses only at
  risk-tagged tasks and failures; the most wall clock.
- Path ahead: `/finish` (skipping the `/gate-audit` and `/gate-acceptance`
  recommendations — studious not installed; named here, not silently
  omitted).

Dispatch `/build` now with `PLAN.md`? (On an explicit yes — and only
then — the coach invokes the `build` skill via the Skill tool with the
plan path as the argument. Not executed here: no live human confirmed.)
