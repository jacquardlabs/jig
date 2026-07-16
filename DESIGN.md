# Design system

jig is a Claude Code plugin — its user-facing surface is the set of
commands/skills it exposes and the vocabulary they emit, not a visual UI.
**M1 (repo & plugin scaffold, #30) has shipped**: `.claude-plugin/plugin.json`
and `skills/{design,plan,build,finish,coach,task-execution-discipline}/`
all exist, each user-invoked skill carrying a stub `SKILL.md` with valid
frontmatter and an explicit "not yet implemented" description. No skill has
real behavior behind it yet — `/design`, `/plan`, `/build`, `/finish`, and
the coach still land in M2–M6. Everything below is still extracted from the
project's ratified handoff document, not from running code, since the
stubs emit no vocabulary of their own yet. Re-run `/extract-design-system`
once M2–M6 land real implementations.

## Surfaces

| Surface | Framework / tech | Entry point |
|---------|------------------|-------------|
| `plugin` | Claude Code plugin (skills + deterministic scripts) | Scaffolded, not yet implemented — `skills/design`, `skills/plan`, `skills/build`, `skills/finish`, and `skills/coach` exist as stub `SKILL.md` files (M1); real behavior lands M2–M6. `scripts/design-lint` and `scripts/plan-lint` are executable stubs that exit 0 unconditionally. |

## Semantic palette

No color/terminal-style palette exists — jig's plugin surface renders as
plain text inside Claude Code's chat interface, not a styled terminal or web
UI. The functional equivalent of "state → style" here is the closed verdict
vocabulary each command emits (see Vocabulary and Plugin/prompt tooling
below) — state is signaled by which token a command returns, not by color.

## Vocabulary

The canonical verdict enums each future command commits to, per the
ratified handoff. Source of truth for all of these is currently the handoff
document itself; once each skill ships, its own `SKILL.md` becomes the real
source and this table should be updated to point there.

| Concept | Canonical display | Source of truth | Consumers |
|---------|-------------------|-----------------|-----------|
| `/design` verdict | `DESIGNED` \| `NEEDS RESEARCH` \| `REVISED` | handoff §5.1 (future: `skills/design/SKILL.md`) | `/design` output; read by `/plan` and studious's `/gate-design-review` |
| `/plan` verdict | `PLAN READY` \| `DESIGN GAP` \| `TOO BIG` | handoff §5.2 (future: `skills/plan/SKILL.md`) | `/plan` output; `DESIGN GAP` routes back to `/design` |
| `/build` task status | `todo` → `in-progress` → `PASS`/`REPLAN`/`ESCALATE` | `skills/build/SKILL.md` | flipped by scripts only, never the model |
| `/build` failure-routine action | `FIX` \| `RESAMPLE` | `skills/build/SKILL.md` | the Foreman's own per-attempt judgment call after an item FAIL; transient, never written as a task status suffix |
| `/build` session verdict | `BUILT` \| `PAUSED` \| `ESCALATED` | handoff §5.3 | reported to the coach and the human |
| inspector verdict | `CLEAR` \| `DEFECT` \| `CONCERN` | `skills/build/SKILL.md` (step 2.6) | `/build`'s failure routine; `CONCERN` forwards to `/gate-audit` |
| `/finish` verdict | `MERGE` \| `PR` \| `KEEP` \| `DISCARD` | handoff §5.4 | closes out a build branch |
| checkpoint item type | `cap` \| `hold` | handoff §4 | every checkpoint block in `PLAN.md` |
| verification tier | `script` \| `test-backed` \| `probe` | handoff §4 | every checkpoint item; no `judgment` tier permitted |
| risk tag | `LOW` \| `REPLAN-RISK` \| `ESCALATE-RISK` | handoff §5.2 step 4 | assigned by `/plan`, consumed by `/build`'s cadence/pause logic |

## Formatting

- **The checkpoint block** (handoff §4) is jig's closest analog to a type
  scale — a fixed template every task in `PLAN.md` follows: `Why now` / `Read
  first` / `Rests on` / `Do` / `Not here` / `Done means` (numbered cap/hold
  items with a verification tier) / `Evidence`. Every item: ≥1 cap, ≥1 hold,
  ≤5 items total.
- **Design doc structure** (handoff §5.1 step 4): 5-8 sections, each tied to
  a named downstream consumer (Intent, Experience, Contracts, Approach,
  Assumptions, Not doing, Risks — see the section→consumer table in §5.1).
- **Task calibration**: `/plan` produces 3-8 tasks per plan; <3 is too big to
  verify, >8 is fragmenting or the feature itself is `TOO BIG`.
- **PR evidence table** (handoff §5.4): promotes each task's Done-means into
  the PR body as item → verification method → evidence link → pass.

## Per-surface conventions

### Plugin / prompt tooling

- **Command naming**: single verb, slash-prefixed — `/design`, `/plan`,
  `/build`, `/finish`. The coach's own invocation convention isn't yet
  specified in the handoff (unclear if it gets its own slash command or is
  invoked another way) — flagged as needing clarification before M6.
- **Verdict vocabulary**: see the Vocabulary table above — each command owns
  a distinct enum with no reused tokens *within jig itself*. One
  cross-project watch-item: jig's `/build` task-status token `PASS` and
  studious's own gate-verdict `PASS` (used across `/gate-audit` etc.) are the
  same word for a related-but-distinct concept (a task passing verification
  vs. a gate passing judgment). Not a conflict today since they never appear
  in the same table, but worth explicit disambiguation once both surfaces
  are visible together in a PR body (jig's `/finish` promotes Done-means
  into the PR; studious's gates also report there).
- **Severity/tier vocabulary**: jig's risk tags (`LOW`/`REPLAN-RISK`/
  `ESCALATE-RISK`) are a deliberately different vocabulary from studious's
  report tiers (Critical/Important/Track) — different axis (plan-time risk
  vs. review-time severity), not meant to align. Worth a note in CLAUDE.md
  once both appear in the same operator-facing surface (e.g. a joint
  changelog), so the distinction doesn't read as an inconsistency.
- **Report/output structure**: see Formatting above — the checkpoint block
  and PR evidence table are the two structural conventions that exist so
  far.

## Anti-patterns (do NOT do these)

<!-- Left empty per the extraction process — this needs your intent, not an
     assumption. Candidates worth ruling on once M2+ lands: reusing a gate
     token (PASS, etc.) for a jig-internal concept with different meaning;
     inventing a visual palette before any surface actually renders visually. -->

---

## Top inconsistencies / risks if left unaddressed

Since no skill has real behavior yet, these are design-level risks surfaced
by this extraction, not code drift:

1. **No behavioral surface exists to extract from yet** — M1's stub
   `SKILL.md` files exist (see Surfaces above) but emit no vocabulary of
   their own, so this entire document is still sourced from the handoff
   text. Re-run `/extract-design-system` once M2-M6 replace the stubs with
   real behavior, and point the Vocabulary table's "source of truth" column
   at each `SKILL.md` instead of the handoff.
2. **`PASS` token collision risk** — jig's task-level `PASS` and studious's
   gate-level `PASS` are different concepts sharing a word; low risk today,
   real risk once both appear in the same PR.
3. **Risk-tag vs. severity-tier vocabulary divergence** — intentional, but
   undocumented anywhere a human would see both systems side by side.
4. **Coach invocation convention unspecified** — the only one of the five
   commands without a stated slash-command form.
5. **No palette or formatting convention exists for a future non-chat
   surface** (e.g. a report or CLI wrapper) — not needed today, but the
   handoff doesn't rule one out either, so this doc would need a real
   Surfaces-table addition if one is ever added.
