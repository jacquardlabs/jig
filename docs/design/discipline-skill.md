# Design: Task-execution-discipline skill

## Problem & persona

Primary persona, verbatim from `PRODUCT.md`:

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

That persona's problem today: jig's `/build` (M4, currently a stub per
`skills/build/SKILL.md`) is designed as "a for-loop of fresh executors per
task" (`PRODUCT.md`, critical user journey 1). "Fresh" is the point — each
executor starts with no memory of the prior task's decisions — but it also
means each executor independently decides, from scratch, whether to write a
test before code, how tightly to bound a task's scope, and what evidence
justifies calling a task done. Nothing today hands that judgment down as a
shared, consistent starting position. Without it, a fresh-executor-per-task
loop reintroduces the exact inconsistency the persona is trying to leave
behind by choosing jig over "ad hoc prompting" — the same discipline
questions re-litigated, and answered differently, task after task.

Issue #6 (this story's source) names the fix: a **model-invoked** skill —
one the executor's own judgment triggers because its description matches
the moment ("about to implement," "about to claim done"), not one a human
runs by name — holding that discipline as reusable text every fresh
executor loads the same way. Per the issue's cited invocation rule:
"user-invoked skills orchestrate, model-invoked skills hold reusable
discipline." `/build` is the orchestrator; this skill is the discipline it
leans on.

## Proposed design

One new file: `skills/task-execution-discipline/SKILL.md`, in its own
top-level directory under `skills/` — a sixth directory alongside jig's
five user-invoked skills (`design`, `plan`, `build`, `finish`, `coach`), not
nested inside any of them. (Why its own directory, not folded into
`skills/build/`: see Alternatives considered.)

What changes for the persona: nothing yet observable — M4 hasn't shipped
`/build`'s for-loop, so nothing invokes this skill in a running session
today. What this story delivers is the canon `/build`'s fresh executors
will draw on once M4 wires the loop: a single skill whose frontmatter
`description` is written as a trigger ("use when about to implement a
checkpoint item," "use when about to claim a task's Done-means is
satisfied"), matching the phrasing convention every other model-invoked
skill in this Claude Code install already uses (e.g. Studious's own
`skills/*/SKILL.md` route on "Use when..." language, never a command
verb). That phrasing is what makes it model-invoked rather than
user-invoked — there is no separate frontmatter field for the distinction;
it's carried entirely by how the description reads and by the skill never
appearing in jig's five-command surface (`README.md`, `DESIGN.md`'s Plugin
naming convention).

The canon itself holds three named pillars, adapted from Superpowers'
`test-driven-development` and `verification-before-completion` skills (read
directly from the installed Superpowers plugin, version 6.1.1, as the
"~80%... kept from Superpowers" issue #6 refers to) into jig's own
vocabulary from `DESIGN.md`'s Vocabulary table, rather than copied verbatim:

1. **TDD-per-capability** — Superpowers' Iron Law ("no production code
   without a failing test first") and Red-Green-Refactor cycle, retargeted
   from generic "feature/bug fix" language to jig's checkpoint-block unit:
   a task's **cap** items (`DESIGN.md`: checkpoint item type `cap` \|
   `hold`), specifically those carrying the **test-backed** verification
   tier. "Per-capability" names that unit explicitly instead of leaving it
   implicit, since a jig task can carry several cap items in one checkpoint
   block.
2. **YAGNI** — Superpowers folds this into `test-driven-development`'s
   GREEN-step Bad/Good example rather than giving it a dedicated section;
   jig's canon calls it out as its own named pillar because jig has an
   explicit scope-boundary artifact Superpowers doesn't: the checkpoint
   block's **Not here** field (`DESIGN.md` Formatting). The adapted
   guidance ties scope discipline to that field directly — code that
   reaches past a task's stated `Do` into its `Not here` is the YAGNI
   violation, not an abstract "don't over-engineer."
3. **Verification-before-completion** — Superpowers' Iron Law ("no
   completion claims without fresh verification evidence") and Gate
   Function, retargeted to jig's own status and evidence vocabulary: a
   task's status flip (`todo` → `in-progress` → `PASS`/`FIX`/`REPLAN`/
   `ESCALATE`, `DESIGN.md`) is asserted by scripts only, never
   self-reported by the executor, and every claim of done cites the
   checkpoint block's **Evidence** field. This is the same non-negotiable
   `PRODUCT.md` leans on twice: "Judgment in the model, mechanics in
   scripts" (status flips are a script's call, not the model's) and
   "Nothing signs off on itself" (executor attestation is structurally
   worthless).

All three pillars point back at PRODUCT.md's "Anti-cleverness tripwire"
principle by staying a plain reusable text file the executor reads, not a
mechanism with its own state or control flow.

## User journey

Walks `PRODUCT.md` critical user journey 1 (Full cycle), the `/build` step:
"for-loop: fresh executor per task, script-verified, conditional inspector
on load-bearing tasks."

1. `/plan` has already produced a checkpoint block for a task, with at
   least one **cap** item carrying a **test-backed** verification tier, a
   stated `Do`, a stated `Not here`, and a `Done means` field.
2. `/build`'s for-loop spins up a fresh executor for that task. The
   executor reads the checkpoint block. Nothing in its context carries
   over from the previous task's executor — by design.
3. Before writing implementation code for the cap item, the executor's own
   judgment recognizes "about to implement a checkpoint item" against this
   skill's description and loads it — same as any other model-invoked
   skill triggers today, no explicit call from `/build`'s orchestration
   logic required. TDD-per-capability governs: write the test, watch it
   fail, then write the minimal code.
4. While implementing, YAGNI bounds the executor to the task's `Do`; the
   checkpoint block's `Not here` field is the concrete fence, not a vague
   instinct.
5. Before the executor claims the task's `Done means` is satisfied (which a
   script then reads to flip status toward `PASS`), verification-before-
   completion governs: the claim must cite fresh evidence the checkpoint
   block's `Evidence` field can hold, not "should work now."
6. No step in this journey changes as a result of this skill shipping —
   the for-loop, the checkpoint-block shape, and the script-only status
   flip are all M3/M4 territory. This story only puts the shared text in
   place for that future loop to read.

## Out of scope

- Implementing `/build`'s for-loop itself (M4) — this story ships the
  discipline text the loop will later read, not the loop.
- Any wiring code that explicitly invokes this skill — Claude Code's own
  model-invocation mechanism (description-match triggering) is the
  invocation path; there is no dispatch code for a worker in this story to
  write.
- Splitting the canon into three separate skill files, one per pillar —
  see Alternatives considered.
- Changing any of the five existing user-invoked stub skills
  (`skills/{design,plan,build,finish,coach}/SKILL.md`) or their frontmatter.
- Resolving the coach's invocation convention (`DESIGN.md`'s open item #4,
  "Coach invocation convention unspecified") — unrelated to this skill.
- Writing real content for `scripts/plan-lint` / `scripts/design-lint`
  beyond their existing M1 stub behavior — out of this story per the
  epic's own pre-mortem risk #4 (stub scripts are the correct M1 output).
- Reconciling `tests/test_scaffold.py`'s `EXPECTED_SKILLS` tuple (owned by
  the already-merged `scaffold-skeleton` story) with the new sixth
  directory this story adds — flagged under Open questions, not resolved
  here, since that test file belongs to a sibling story.

## Alternatives considered

1. **Three separate skill files** (`skills/tdd-discipline/`,
   `skills/yagni/`, `skills/verification-before-completion/`), one per
   pillar, mirroring Superpowers' own file-per-skill layout. Rejected:
   issue #6 asks for "a model-invoked skill" (singular) holding the
   reusable discipline text, and Superpowers itself doesn't actually split
   YAGNI out as its own file (it lives inside `test-driven-development`) —
   so three files would be *less* faithful to the source material, not
   more, and would fragment `/build`'s context ration across three
   auto-triggered surfaces with overlapping "about to implement /
   about to claim done" descriptions competing for the same moment.
2. **Nest the file inside `skills/build/`**, since it exists to serve
   `/build` specifically. Rejected per this epic's own pre-mortem (risk
   #2): nesting a skill inside another skill's directory is the exact,
   evidenced failure mode behind viva#101 ("viva-qa and viva-diff never
   register as skills — one directory per skill required"). This skill
   needs its own top-level directory regardless of which command
   eventually consumes it.
3. **Copy Superpowers' two source files verbatim**, concatenated. Rejected:
   verbatim text carries Superpowers' own vocabulary (generic
   "feature"/"bug fix" framing, a plain Red-Green-Refactor cycle with no
   task-status concept) rather than jig's checkpoint-block vocabulary
   (`cap`/`hold`, `Done means`, `Evidence`, verification tiers
   `script`/`test-backed`/`probe`, the `PASS`/`FIX`/`REPLAN`/`ESCALATE`
   status enum). A fresh executor reading the verbatim version would have
   to translate Superpowers' terms into jig's own on every task; adapting
   the text once here removes that translation tax. This is also what the
   acceptance criteria asks for directly: "canon adapted from Superpowers,"
   not "canon copied from Superpowers."

## Operational readiness

N/A — no operational surface. This is a static Markdown text file read by
a model at skill-invocation time; it has no runtime process, no data
migration, no rollout beyond a normal merge, and nothing to monitor via
logs, metrics, or alarms. Rollback is a plain `git revert` of the commit
that adds the file.

## Open questions

- `tests/test_scaffold.py` (landed by the already-merged `scaffold-skeleton`
  story) asserts `skills/` contains *exactly* the five user-invoked
  directories (`test_no_extra_top_level_skill_dirs`, `EXPECTED_SKILLS =
  ("design", "plan", "build", "finish", "coach")`). Adding this story's
  sixth, model-invoked directory will fail that set-equality check as
  written. This story's build phase (or a fast-follow) needs to update that
  test to distinguish "user-invoked skill directories" from "all skill
  directories" rather than widen `EXPECTED_SKILLS` to blur the two
  categories together — flagging here rather than silently patching a
  sibling story's test file from this story's worktree.
- Whether Claude Code's plugin loader needs any registration for a
  model-invoked skill beyond the file existing at
  `skills/<name>/SKILL.md` with valid frontmatter. Every skill observed in
  this environment (jig's own five stubs, all of Studious's and
  Superpowers' skills) relies solely on directory presence plus
  frontmatter — no separate manifest listing — so this design assumes the
  same holds here. Not independently verified against Claude Code's loader
  source; the build phase should confirm the file is actually discoverable
  once written, not just structurally correct.
- The exact prose of the three pillars is a build-phase drafting decision
  once this structure is approved; this doc commits to the shape (one
  file, three named pillars, jig's own vocabulary throughout) rather than
  final wording.
