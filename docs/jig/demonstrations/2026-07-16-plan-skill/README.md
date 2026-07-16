# plan-skill demonstration evidence (2026-07-16)

Committed alongside story `plan-skill`'s build-phase implementation
(`skills/plan/SKILL.md`), to satisfy `docs/design/plan-skill.md`'s
Operational readiness section, "Required demonstrations." Per this repo's
own principle 7 (`.gitignore`'s comment), this folder — like
`docs/design/` — is disposable: it lives on this branch to give
`/gate-audit`/`/gate-acceptance` something real to review, and is expected
to be removed at merge once its substance is folded into the PR's
Done-means evidence table, matching the precedent already set on this
epic (commits `f2aff29`, `2194a68`, `0d76450`, `e6fd44e` on sibling
stories).

Nothing below is simulated or hand-narrated in place of a real command:
every JSON file, every `plan-lint`/`parse_sections.py` output, and every
grep/parse result quoted in the two READMEs is copied verbatim from an
actual invocation, run from this worktree, against the real (uncommitted
at draft time, now committed as evidence) `PLAN.md` this session drafted.

## `ci-wiring-demo/` — demonstrations 1, 2, 3

A real, currently-unblocked small jig feature — wiring `scripts/plan-lint`
and Ruff into CI, named explicitly in `docs/design/plan-lint.md`'s own Out
of scope as "unblocked by this story... but not built by it" — planned by
hand-executing `/plan`'s own Steps 1–4 against a real, newly-written design
doc (`docs/design/plan-lint-ci.md`) and against this repo's real, current
state (its `.github/workflows/`, `CLAUDE.md`, `pyproject.toml`,
`tests/fixtures/plan-lint/*`).

- `PLAN.md` — the real drafted plan. Three calibrated tasks, a `Spine:`
  preamble line (not a heading, per Step 2), risk-free (`LOW`) checkpoint
  blocks, and a real `## Not-here follow-ups` section with three concrete
  (non-placeholder) bullets.
- `plan-lint-output.txt` — `scripts/plan-lint`'s real, unmodified output
  against this file: **0 violations across 3 task(s), exit 0**, on the
  first draft (satisfies Step 5: "a real invocation with a real exit code
  branched on").
- `build-step-1.4-split-check.md` — reproduces `/build`'s own Step 1.4
  splitting rule (a Foreman's judgment call, not a separate script;
  matches the same regex pair `scripts/plan-lint`'s `split_tasks()`
  already encodes for the identical purpose) against this real file: three
  clean task blocks, the trailing `## Not-here follow-ups` section
  correctly excluded from Task 3's — directly answers demonstration 2 and
  epic pre-mortem risk #4.
- `viva-round-trip/` — the real, unmodified `scripts/parse_sections.py`
  (viva 1.18.0, the version actually installed) run against this real
  `PLAN.md`, twice: once with bare auto-detect, once with the explicit
  `--split-on` pattern `/plan`'s own `SKILL.md` mandates. Both produce the
  identical, correct 5-section split (preamble, Task 1, Task 2, Task 3,
  Not-here follow-ups) — no absorption. A third and fourth run reproduce
  the Revision-History collision case against a copy of this same real
  file with a second `##` heading appended: auto-detect alone collapses to
  **2 sections** (every task merged into the preamble!), while the
  explicit `--split-on` pattern stays correct at 5. This directly
  re-confirms, against the real artifact rather than only the pre-existing
  `plan-lint` fixture, both halves of demonstration 3 and closes epic
  pre-mortem risk #5 a second time.

### What this does *not* claim

`docs/design/plan-skill.md`'s own Verdicts table defines `PLAN READY` as
firing only once "every task reaches viva `approved`" — a human decision,
made by a person clicking through viva's browser UI, section by section.
This build-phase session is an unattended agent with no interactive
channel to a live human reviewer (no browser, no `AskUserQuestion`-style
tool available in this dispatch). Submitting an "approved" verdict through
viva's own HTTP API on the human's behalf was considered and rejected —
that would be exactly the self-sign-off `PRODUCT.md`'s "Nothing signs off
on itself" principle exists to forbid, not a legitimate substitute the way
`docs/jig/demonstrations/2026-07-12-build-skill/`'s `claude -p
--agent general-purpose` substitution was for a fresh executor (a
functionally-equivalent isolated process, not a stand-in for a human
*judgment*). So: every **mechanical** gate this plan must clear before a
human ever sees it — `plan-lint`'s real exit code, `/build`'s real
Step 1.4 split, and viva's real section-split mechanism (auto-detect *and*
the Revision-History collision case) — is verified above, for real,
against the real artifact. The one remaining leg, a human actually
clicking through viva's review cards to `approved`, needs a live session
with the project's own user and could not be honestly fabricated here.
This is flagged as the open item for `/gate-acceptance` to weigh, matching
this epic's own established precedent of a "Fix" cycle when a build-phase
demonstration's evidence is incomplete (see `f2aff29`, `2194a68`).

## `design-gap-demo/` — demonstration 4

`jig` itself has no UI surface (this design doc's own Step 1b finding), so
this demonstration needed a second, disposable target-project fixture per
the design's own Open Questions. `fixture-repo/` is a minimal
Node/Express app fixture with a `CLAUDE.md` naming no scripted-probe tool,
a `package.json` naming neither `playwright` nor an equivalent, no
`playwright.config.*`, and one design doc
(`docs/design/widget-color-picker.md`) whose one load-bearing user-journey
step explicitly requires a live-observed screenshot, not a DOM-attribute
assertion. `README.md` in that folder runs Step 1b's three checkable
signals for real against the fixture (including a real wrinkle: a naive
`grep -i playwright` false-positives on the fixture's own disclaimer
prose, so the actual check has to parse `package.json`'s dependency keys
structurally) and reports the resulting `DESIGN GAP`, naming the specific
gap and the concrete resume action per the Verdicts table's own
requirement.
