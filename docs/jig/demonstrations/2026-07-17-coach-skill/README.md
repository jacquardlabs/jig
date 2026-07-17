# coach-skill demonstration evidence (2026-07-17)

Committed alongside story `coach-skill`'s build-phase implementation
(`skills/coach/SKILL.md`), to satisfy `docs/design/coach-skill.md`'s
Operational readiness section: demonstration transcripts covering at least
3 distinct pipeline states — no-artifacts, post-plan, and mid-build
`PAUSED` — plus the repo-contradicts-conversation case (the design's
pre-mortem risk #4). A fifth demo covers the ` [ESCALATE]` revision-loop
row, since it is the acceptance criteria's named context-passing case
(`/design` revision mode gets the ESCALATE finding). Per this repo's own
principle 7 (`.gitignore`'s comment), this folder — like `docs/design/` —
is disposable: it lives on this branch to give
`/gate-audit`/`/gate-acceptance` something real to review, and is expected
to be removed at merge, matching the precedent set by
`docs/jig/demonstrations/2026-07-16-plan-skill/`.

Nothing below is simulated or hand-narrated in place of a real command:
every command output quoted in the five demo READMEs is copied verbatim
from an actual invocation against a real scratch git repository, and every
` [PASS]` / ` [REPLAN]` / ` [ESCALATE]` suffix in those repos was written
by a real `scripts/status-flip` run (the only tool allowed to write one),
never typed by hand. `setup.sh` in this folder rebuilds all five states:

```bash
./setup.sh <scratch-root> <jig-repo-root>
```

Fixtures are reused, not invented: the plan is the plan-skill story's
real, viva-approved, plan-lint-clean ci-wiring `PLAN.md`
(`../2026-07-16-plan-skill/ci-wiring-demo/PLAN.md`), and the design doc is
the real `docs/design/plan-lint-ci.md` it was drafted from — one coherent
feature walked through five pipeline states.

What each demo shows, per `skills/coach/SKILL.md`'s own steps:

| Demo | Pipeline state | Routing row exercised |
|---|---|---|
| `no-artifacts-demo/` | No design doc, no `PLAN.md` | Recommend the human run `/gate-should-we-build` (studious installed); dispatch `/design` with the skip named (studious absent — both sub-cases captured) |
| `post-plan-demo/` | Design doc + `PLAN.md`, no task suffixes | Dispatch `/build` with the plan path; studious-absent gap named |
| `mid-build-paused-demo/` | Task 1 ` [PASS]`, Task 2 ` [REPLAN]` | Name the manual step, quoting the status-flip commit's reason |
| `escalate-demo/` | Task 1 ` [PASS]`, Task 2 ` [ESCALATE]` | Dispatch `/design` in revision mode with the quoted finding + doc path |
| `repo-contradicts-conversation-demo/` | Conversation says `BUILT`; Task 3 unsuffixed | Conflict reported by name; recommendation follows the repo |

## What this does *not* claim

Each transcript is `skills/coach/SKILL.md`'s Steps 1–2 hand-executed by
this build session against the captured state — the same approach the
plan-skill demos took for `/plan`'s steps. The one leg no unattended
session can honestly produce is Step 3's dispatch itself: a dispatch
requires a live human's explicit confirmation in the same turn, and
fabricating that confirmation would be exactly the consent violation the
Pocock rule exists to prevent. Every transcript therefore ends at the
confirmation question — the coach's own designed stopping point when no
human has yet said yes — with the would-be Skill-tool dispatch and its
explicit context argument stated but not executed.
