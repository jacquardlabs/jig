# Demo: no-artifacts state

Scratch state `no-artifacts` (see `../setup.sh`): a project with
`PRODUCT.md` and `CLAUDE.md` only — no `docs/design/`, no `PLAN.md`, no
evidence folders. The human's conversational input: "/coach — I want to
wire plan-lint and Ruff into CI. Where do I start?"

## Step 1 — evidence, verbatim

```
$ ls docs/design/*.md
(eval):3: no matches found: docs/design/*.md
exit=1

$ test -f PLAN.md
exit=1

$ command -v gate-ledger
/Users/bryan/.claude/plugins/cache/jacquardlabs-marketplace/studious/2.21.0/bin/gate-ledger
exit=0

$ gate-ledger gate-get --branch main
exit=0 (no output: no recorded verdicts in this repo)

$ gate-ledger status
exit=0
```

## The coach's output (sub-case 1: studious installed)

State: nothing in flight.

- No design doc — `docs/design/*.md` matched nothing (exit 1).
- No plan — `PLAN.md` absent at the repo root (filesystem read; exit 1).
- studious installed — `gate-ledger` found on PATH, but `gate-ledger
  gate-get --branch main` returned no recorded verdicts: no
  should-we-build verdict exists for this idea.

**Next: run `/gate-should-we-build`** with the feature idea from this
conversation ("wire scripts/plan-lint and Ruff into CI").

- Why: no artifact exists yet and studious is installed with no recorded
  should-we-build verdict — the pipeline's journey 1 opens with the
  worth-building judgment, and skipping it silently would un-name a gate
  your install expects to run.
- Rough cost: a studious gate — minutes: a single human-run judgment read.
- Path ahead: `/design` → `/gate-design-review` → `/plan` → `/build` →
  `/gate-audit` → `/gate-acceptance` → `/finish`.

That gate is yours to run, not mine to dispatch — gates are recommended,
never dispatched. Tell me when its verdict is recorded and I'll reassess
from the repo.

## Sub-case 2: studious absent

The same state read with `gate-ledger` off PATH:

```
$ env PATH=/usr/bin:/bin sh -c 'command -v gate-ledger'
exit=1
```

The assessment's gate line becomes: studious not installed — no recorded
gate verdicts to read.

**Next: dispatch `/design`** — skip named: "`/gate-should-we-build`
skipped — studious not installed."

- Why: no design doc, no plan, and no gate tooling to route through — the
  first jig-owned step of journey 1 is `/design`.
- Rough cost: `/design` — one interactive session: 5–9 interview answers
  plus per-section sign-off; the most human attention.
- Path ahead: `/plan` → `/build` → `/finish` (the studious gates between
  them stay skipped by name while studious is absent).

Dispatch `/design` now with the one-line feature ask "wire
scripts/plan-lint and Ruff into CI"? (On an explicit yes — and only then —
the coach invokes the `design` skill via the Skill tool with exactly that
argument. Not executed here: no live human confirmed, and the Pocock rule
does not let the coach infer one.)
