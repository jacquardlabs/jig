# Design: `/coach` (user-invoked orchestrator)

## Problem & persona

Primary persona, verbatim from `PRODUCT.md`:

> A developer using Claude Code, likely already pairing it with studious's
> judgment gates, who wants a repeatable, verifiable build/implementation
> workflow instead of ad hoc prompting or Superpowers.

That persona's problem today: all four working skills have shipped (M2–M5),
and each one names its next step only at the instant its own session ends —
`/build`'s `BUILT` says "run `/gate-audit` next"; `/design`'s `DESIGNED`
hands to `/gate-design-review`. Nothing guides re-entry from anywhere else:
a fresh conversation over a repo carrying yesterday's `PAUSED` build, an
`[ESCALATE]` suffix nobody acted on, a signed-off design doc that never got
a plan. Reconstructing "where am I, what's next" means hand-reading
`PLAN.md` heading suffixes, `docs/design/`, evidence folders, and
`gate-ledger` output — exactly the ad hoc workflow `PRODUCT.md` says jig
exists to replace. `skills/coach/SKILL.md` is still the M1 stub ("Do not
invoke for actual coaching work yet"), and its invocation convention is
`DESIGN.md`'s open risk #4 — the only one of the five commands without a
stated slash-command form. `PRODUCT.md`'s critical user journeys 1 (Full
cycle) and 3 (Revision loop) both route through the slot this story fills.

## Proposed design

One file changes behavior: `skills/coach/SKILL.md` replaces its M1 stub
with the coach specified below. No new scripts, no script changes, and no
writes of any kind at run time — the coach reads, recommends, and
dispatches; it never does the work itself.

### Invocation convention (closes DESIGN.md risk #4)

| Option | Convention | Tradeoff |
|---|---|---|
| A — `/coach`, a user-invoked skill | Same "single verb, slash-prefixed" convention as `/design`/`/plan`/`/build`/`/finish` — "coach" is the verb. Frontmatter description triggers on an explicit ask only. | One more user-invoked skill, zero new mechanism. The human must know to ask — which is the Pocock posture, not a gap. |
| B — model-invoked, auto-triggering on a session verdict | The coach would appear unbidden when `PAUSED`/`ESCALATED` lands. | Auto-triggering is the resident-coordinator shape `PRODUCT.md`'s "What we're NOT building" rules out, and exactly pre-mortem risk #5's "auto-triggering" failure. The story title itself says user-invoked. |
| C — a deterministic `scripts/pipeline-state` reporter plus a thin skill over it | State reading becomes a script; the skill only phrases it. | The assessment feeds a judgment call (which one action, for this human, now) — principle 1 puts that in the model. A script here owns no pass/fail determination and no write, re-implements `PLAN.md` parsing two consumers already do, and adds a drift surface for nothing. |

**(recommended): A.** Ruled: A — issue #21 and the story title both name a
user-invoked orchestrator, A is the only option consistent with both the
existing naming convention and pre-mortem risk #5's two failure directions
(uninvokable / auto-triggering).

The shipped frontmatter (STUB marker and "do not invoke" description gone):

```yaml
name: coach
description: >-
  jig's coach — assesses pipeline state from the repo and conversation,
  recommends exactly one next action with why, rough cost, and the path
  ahead, and dispatches /design, /plan, /build, or /finish one at a time on
  explicit human confirmation, passing context explicitly. Use when the
  user says /coach, asks where they are in the pipeline or what to do
  next, or wants help recovering after a PAUSED or ESCALATED /build
  session. Does no work itself — writes no code, flips no statuses,
  records no verdicts, and never dispatches without confirmation.
```

The description triggers on an explicit ask ("/coach", "where am I",
"what's next") — never on the mere presence of a verdict token earlier in
the conversation. That wording is what keeps a user-invoked skill from
becoming option B through the back door.

### Step 1 — Evidence-based state assessment

The coach reads the repo before it believes anything. Signals, cheapest
first — each one named against the grammar its producing script actually
writes, not the handoff's paraphrase (pre-mortem risk #1):

| Signal | Read from | Establishes |
|---|---|---|
| Design docs | `docs/design/*.md` (Glob) | Which stories have designs. A `## Revision History` heading means at least one completed viva sign-off — viva appends it the moment a review round finishes (per `skills/plan/SKILL.md` Step 6). A doc without one exists but is unconfirmed from the repo alone. |
| Plan | `PLAN.md` at the repo root — a filesystem read, never `git ls-files` (jig's own `.gitignore` excludes `/PLAN.md` as disposable scaffolding) | A plan exists; its `### Task N — <title>` blocks. |
| Task statuses | Heading suffixes ` [PASS]` / ` [REPLAN]` / ` [ESCALATE]` — `scripts/status-flip`'s own `SUFFIX_RE` grammar, written only by that script | Which tasks closed, which paused or escalated. No suffix means not yet terminal (todo / in-progress). |
| Failure reasons | `git log` for the `status-flip: task <N> -> REPLAN\|ESCALATE` commit — the Foreman's `--reason` lives in that commit's body, not in `PLAN.md` | The finding `/design` revision mode (or the human's block revision) needs, quoted verbatim. |
| Evidence & reports | `docs/jig/evidence/<date>-<task>/`, `docs/jig/reports/` | Which tasks captured evidence; whether a story already closed out via `/finish`. |
| Gate verdicts | `command -v gate-ledger`; if found, `gate-ledger gate-get --branch <branch>` (recorded verdict history) and `gate-ledger status` | Which studious gates actually recorded verdicts. Not found: the assessment states "studious not installed — no recorded gate verdicts to read" and treats gates per the degradation rules below — never assumes one passed. |
| Conversation | Session verdicts stated earlier in this conversation (`BUILT`/`PAUSED`/`ESCALATED`, `DESIGNED`/`NEEDS RESEARCH`/`REVISED`, `PLAN READY`/`DESIGN GAP`/`TOO BIG`) | Fills only the gaps the repo cannot show — e.g. a `NEEDS RESEARCH` verdict that deliberately wrote nothing to disk. |

Three hard rules govern the read:

- **Repo evidence outranks conversation claims.** A conflict — the
  conversation says `BUILT`, `PLAN.md` shows an unsuffixed task — is
  reported by name, never silently resolved in either direction, and the
  recommendation follows the repo (pre-mortem risk #4).
- **Vocabulary discipline.** Task-status `[PASS]` (a `PLAN.md` heading
  suffix, per task, script-written) and studious's gate verdict `PASS` (a
  gate-ledger record, per gate) are different concepts sharing a word
  (DESIGN.md risk #2). The assessment names which one it read, every time.
- **Ambiguity is asked, never guessed.** Two designs in flight, more than
  one plan-shaped file, an unclear story slug — ask the human once, by
  name, the same escalation shape `/plan`'s input step already uses.

The assessment prints before the recommendation: the state, then the
evidence line behind each claim — so a misread fails visibly, in front of
the human, before any confirmation is requested.

### Step 2 — Exactly one recommendation

The output is a coach's call, not a menu: one action, why (the evidence
lines that determined it), rough cost, the path ahead, then the
confirmation question. The action comes from a closed set (principle 4):
dispatch one of `/design` `/plan` `/build` `/finish`; recommend the human
run a named studious gate; name a manual step; or state "nothing to
dispatch." Routing, observed state → the one action:

| Observed state | Next action (exactly one) | Context handed over |
|---|---|---|
| No design doc, no `PLAN.md`; studious installed, no should-we-build verdict recorded | Recommend the human run `/gate-should-we-build` | The feature idea from conversation |
| No design doc, no `PLAN.md`; studious absent | Dispatch `/design` — skip named: "`/gate-should-we-build` skipped — studious not installed" | The one-line feature ask |
| Design doc present and signed off (`## Revision History`, or this conversation's own `DESIGNED`); studious installed, no design-review verdict recorded | Recommend the human run `/gate-design-review` | The doc path |
| Design doc signed off, design-review verdict recorded (or studious absent — gap named); no `PLAN.md` | Dispatch `/plan` | The design doc path |
| `PLAN.md` present, no terminal suffixes | Dispatch `/build` | The plan path |
| `[REPLAN]` suffix on Task N | Name the manual step: revise Task N's checkpoint block by hand, quoting the status-flip commit's reason; after the human says done, reassess and recommend `/build` | The quoted REPLAN reason |
| `[ESCALATE]` suffix on Task N | Dispatch `/design` in revision mode | The ESCALATE finding (status-flip commit body, quoted) plus the design doc path |
| Every task `[PASS]`; studious installed, audit/acceptance not yet recorded | Recommend the human run `/gate-audit` (then `/gate-acceptance`) | The branch name |
| Every task `[PASS]`; gates recorded — or studious absent, with the skipped gates named | Dispatch `/finish` | Nothing beyond the invocation — `/finish` reads `PLAN.md` and the evidence folders itself |
| Dated build report exists for this story / branch closed out | Nothing to dispatch — state it and stop | — |

Rough cost is stated from a fixed vocabulary — order-of-magnitude, honest
about human attention vs. wall clock, never a fabricated number:

- `/design` — one interactive session: 5–9 interview answers plus
  per-section sign-off; the most human attention.
- `/plan` — one session: drafting mostly unattended, then one review card
  per task.
- `/build` — one mostly-unattended session: pauses only at risk-tagged
  tasks and failures; the most wall clock.
- `/finish` — one interactive session: per-item follow-up confirmations
  plus one verdict choice.
- A studious gate — minutes: a single human-run judgment read.
- A REPLAN block revision — minutes of hand editing.

The path ahead is one line: the remaining steps of `PRODUCT.md`'s journey 1
from the recommended action onward.

### Step 3 — Dispatch on confirmation (the Pocock rule)

Issue #21's rule, applied verbatim: user-invoked skills orchestrate;
model-invoked skills hold reusable discipline; user-invoked never calls
user-invoked — except the coach, whose sole job is dispatching them one at
a time on human confirmation.

- A dispatch happens only after the human's explicit confirmation in the
  same turn — never inferred from a prior yes, a stated preference, or
  silence (the same consent bar `/finish`'s harvest step already sets).
- One confirmation, one dispatch. Never two skills queued from one
  confirmation; never a dispatched skill's verdict auto-consumed into a
  second dispatch. When the dispatched session ends, the coach reassesses
  from fresh repo evidence (Step 1 again, never memory) and recommends
  again — a new confirmation each time.
- Mechanism: invoke the target skill by name via the Skill tool, passing
  the routing table's context column as the argument, explicitly — never
  "see conversation above."
- The four jig skills are the only dispatch targets. Studious gates are
  recommended for the human to run, never dispatched — the coach's
  exception to the Pocock rule covers jig's own four and nothing wider.
  viva is never invoked by the coach; the dispatched skills own their own
  viva rounds.

### Shortcuts are first-class

A stated shortcut is honored and its skipped steps named, never blocked
(principle 9; `PRODUCT.md` journey 2). The persona who says "small fix,
skip the ceremony" gets: "Quick path: hand-author a single-task `PLAN.md`
in the checkpoint-block format, then I dispatch `/build` — skipping
`/design`, `/gate-design-review`, and `/plan`; `/gate-audit` still applies
after `BUILT`."

### Does no work itself

The coach's tool use is read-only, always: Read/Glob/Grep, `git log`,
`git status`, `gate-ledger gate-get`/`status`, `command -v`. It never
writes or edits a file (no code, no docs, no state file of its own), never
flips a status, never records a verdict, never runs a gate, a lint, a
test, or a build script, and never commits. Anything that looks like work
is the dispatched skill's job or the human's.

### Degrades gracefully without studious

Every routing row that touches a gate carries a named studious-absent
line: the gate is skipped by name with the reason stated ("studious not
installed"), and the flow continues to the next jig-owned step. Never an
error, never a silent omission (principle 10).

### Principle alignment

- "Recommend one action; the human decides. Propose; never apply" — this
  skill *is* that principle: one action, confirmation-gated, nothing
  applied.
- "Judgment in the model, mechanics in scripts" — the recommendation is
  judgment; nothing here writes or determines pass/fail, so there is no
  mechanics to script. The state read reuses grammars scripts already own
  (`status-flip`'s `SUFFIX_RE`, gate-ledger's JSON) — the same sanctioned
  "mechanical read of prose already in hand" `/build`'s steps 1.4–1.5
  perform in-model.
- "Nothing signs off on itself" — structurally satisfied: the coach
  produces no artifact to sign off.
- "Anti-cleverness tripwire" — no persona name, no resident role, no
  ceremony: a session that ends when the recommendation is confirmed,
  declined, or answered with "nothing to dispatch."

## User journey

Primary walk — re-entry mid-build (journey 1, resumed): a developer opens
a fresh conversation on a repo left mid-flow yesterday and types `/coach`.

1. The coach reads: `docs/design/checkout-flow.md` carries `## Revision
   History`; `PLAN.md` exists; Tasks 1–2 are `[PASS]`, Task 3 is
   `[REPLAN]`; `git log` holds `status-flip: task 3 -> REPLAN` with reason
   "Done means 2 unmeetable as written"; `gate-ledger gate-get` shows a
   recorded design-review verdict.
2. It prints that state with the evidence line behind each claim, then:
   **Next:** revise Task 3's checkpoint block by hand — quoting the REPLAN
   reason — with why, rough cost (minutes of hand editing), and the path
   ahead (`/build` → `/gate-audit` → `/gate-acceptance` → `/finish`).
3. The human revises the block and says done. The coach re-reads `PLAN.md`
   — fresh evidence, not memory — and asks: "dispatch `/build` with
   `PLAN.md` now?"
4. On the explicit yes, it dispatches `/build`, passing the plan path. The
   session is now `/build`'s; when its verdict lands, the human can invoke
   `/coach` again.

Revision loop (journey 3): Task 2 carries `[ESCALATE]` — the coach quotes
the ESCALATE reason from the status-flip commit body and recommends
dispatching `/design` in revision mode with that finding plus the design
doc path; one confirmation, one dispatch.

Failure paths, each visible rather than absorbed:

- **Repo contradicts conversation.** The conversation says `BUILT`;
  `PLAN.md` shows Task 4 unsuffixed. The coach reports the conflict by
  name and follows the repo — the claim is never papered over.
- **studious not installed.** Every gate recommendation degrades by name:
  "skipping the `/gate-audit` recommendation — studious not installed;
  proceeding to `/finish`, whose own precondition trust boundary still
  applies." No error, no silent gap.
- **Ambiguity.** Two design docs without plans — the coach stops and asks
  which story is in play, once, by name, instead of guessing.
- **Declined recommendation.** The human says no — the coach stops. It
  does not argue, loop the recommendation, or dispatch anything.

## Out of scope

- **No verdict enum for the coach.** It is not a pipeline judgment point;
  its closed vocabulary is the action set in Step 2. A fifth verdict enum
  would add a `DESIGN.md` Vocabulary row with no consumer.
- **No state file, ledger, or memory of its own** — every invocation
  reassesses from the repo; `PRODUCT.md` rules out work ledgers and
  resident monitors.
- **No auto-invocation** (rejected option B) and **no chaining** — one
  confirmation, one dispatch, ever.
- **No dispatching studious gates or viva** — gates are human-run
  recommendations; viva belongs to the skills that own review rounds.
- **No epic/multi-story awareness** — studious's own epic driver owns
  multi-story orchestration; the coach is single-story, current-repo.
  (Open question below.)
- **No cost telemetry** — rough cost is the fixed vocabulary in Step 2,
  not a cctx integration.
- **No new scripts** and no changes to the four existing skills — the
  coach adapts to their shipped contracts, never the reverse.

## Alternatives considered

- **No coach at all** (the simplest alternative): each skill's verdict
  already names its next step, and README's pipeline diagram documents the
  order. Rejected: that guidance exists only at the instant a session ends
  and only in that conversation — it cannot help re-entry from a fresh
  conversation, a `PAUSED` repo, or an unacted `[ESCALATE]`, which is the
  problem this story exists to solve.
- **Model-invoked auto-trigger** (option B above): rejected — the
  resident-coordinator shape `PRODUCT.md` rules out, and pre-mortem risk
  #5's named failure mode.
- **Deterministic `pipeline-state` script** (option C above): rejected for
  v1 — no write, no pass/fail determination, so no mechanics to own;
  worth revisiting only if a second consumer for machine-readable pipeline
  state ever appears.
- **Put the coach in studious** (its `/work-on` already navigates a
  flow): rejected — studious's identity is judgment and it steps back at
  build time by design (`PRODUCT.md`'s origin story); jig's coach
  orchestrates jig's four skills, and the two compose across the existing
  sibling contract without either owning the other.

## Operational readiness

N/A in the deployment sense — a local plugin skill with no service, no
migration, no rollout — but the section's real question (how we know it
works or fails) has concrete answers:

- **Rollback**: revert `skills/coach/SKILL.md` to the M1 stub; no other
  file, script, or sibling plugin is touched.
- **Knowing it works**: the build phase commits demonstration transcripts
  under `docs/jig/demonstrations/<date>-coach-skill/` covering at least 3
  distinct pipeline states — no-artifacts, post-plan, and mid-build
  `PAUSED` — plus the repo-contradicts-conversation case (pre-mortem risk
  #4), satisfying the acceptance criteria's own demonstration requirement.
- **Failure visibility in use**: every recommendation prints its evidence
  lines first, so a state misread fails visibly in front of the human
  before any confirmation is requested — the coach's only output is
  words, and the evidence-first format is what makes those words
  checkable.
- **No logs, metrics, or alarms**: none exist for any jig skill; the
  committed demos plus evidence-first output are the monitoring surface a
  local tool honestly has.

## Open questions

- **Epic-aware coaching**: should a later version read `gate-ledger
  epic-get`/`work-get` to coach inside a studious-driven epic? Deferred —
  v1 is single-story, and the epic driver already owns that loop.
- **Cost calibration**: should cctx (when installed) supply observed
  session costs to replace the static vocabulary? Deferred until the
  static one proves too coarse in real use.
- **Plan path**: v1 assumes `PLAN.md` at the repo root, matching
  `/build`'s own default. If a multi-plan convention ever emerges, the
  routing table needs a plan-path fork it does not have today.
- **Sign-off signal coupling**: `## Revision History` as the "signed off"
  repo signal is viva's appending convention, read secondhand. If viva
  changes it, the coach's detection needs a new repo signal — worth a note
  in any future viva-contract change review.
