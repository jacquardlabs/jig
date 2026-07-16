# `design-skill` (issue #8) — required-demonstration report

Addresses the story's own acceptance criterion "Demonstrated end-to-end at
least once: a real target produces a signed-off `design-<slug>.md` via a
real viva round," run during this story's own build phase (matching the
precedent `docs/jig/reports/2026-07-12-m5-required-demonstration-summary-build-report.md`
set for `/finish`'s own required demonstration).

## What ran, for real

Every step below invoked the actually-installed `viva`/`viva-qa` code
(`~/.claude/plugins/cache/viva-local-test/viva/1.18.0/{server.py,scripts/}`)
against a real feature ask — [jacquardlabs/jig#59](https://github.com/jacquardlabs/jig/issues/59)
("evidence-capture's `docs/jig/evidence/<date>-<task>/` path can collide
across independent branches") — never a scratch/toy target. No step was
simulated, hand-typed as if it were tool output, or asserted without the
command that produced it.

1. **Inventory (Step 0).** Read `PRODUCT.md`, `DESIGN.md`, `CLAUDE.md`, and
   the touched code (`scripts/evidence-capture`) before drafting anything.
2. **Batch interview (Step 2).** Wrote a real `.viva/qa-input.json` (7
   questions, the real `viva-qa` schema, the `[intent]`/`[contract]`/
   `[experience]`/`[friction]` tags prefixed onto `hint`) and launched
   `server.py --mode qa` as a real subprocess:
   ```
   $ python3 "$VIVA_DIR/server.py" --mode qa --input .viva/qa-input.json --output .viva/answers.json --no-browser &
   viva · qa mode · http://127.0.0.1:60175
   ```
   Answers were submitted via a real `curl -X POST "$BASE/submit"` call
   against the running server (all 7 recorded in `.viva/answers.json`,
   written by the server itself, not hand-authored). One question (`q5`)
   was a genuine fork: 3 choices, `recommended_choice` set to one of them,
   accepted by the "developer" in the answer.
3. **Fork + draft (Steps 3–4).** Drafted `docs/design/evidence-capture-branch-scoping.md`
   (7 authored sections, contract-canonical headings, each with a
   `Consumer:` line; the branch-scoping fork recorded with its options
   table and a marked `(recommended): A`).
4. **design-lint (Step 5).** Ran the real, currently-installed
   `scripts/design-lint`:
   ```
   $ python3 scripts/design-lint docs/design/evidence-capture-branch-scoping.md
   design-lint: stub — no checks implemented yet (see jig milestone M2).
   exit code: 0
   ```
   **Known, accepted limitation** (named rather than hidden — matches the
   epic pre-mortem's own risk #2/#7): sibling story `design-lint` (issue
   #9) has a design doc (`design-review` verdict `PROCEED TO PLAN`,
   confirmed via `gate-ledger work-get`) but no build yet, so
   `scripts/design-lint` in this worktree is still the M1 stub that exits
   `0` unconditionally. This run therefore exercises Step 5's *call*, and
   the *fix-before-viva* branch is documented and tested in `SKILL.md`/
   `test_design_skill.py`, but a genuine nonzero-then-fix cycle against a
   real linter could not be exercised here — that requires issue #9 to
   ship first, exactly as this story's own design doc (Alternatives
   considered #4, Operational readiness) already anticipated.
5. **viva loop (Step 6, case 1 — brand-new session).** The doc had no
   `## Revision History` heading, so this is case 1, not a resume — no
   `--prior-input`/`--prior-verdicts`. Handed off in the *same* browser
   tab from the still-live QA server, per Step 6's documented same-tab
   mechanism — confirmed by the server's own stdout:
   ```
   viva · qa mode · http://127.0.0.1:60175
   viva · hand-off qa → review · http://127.0.0.1:60175
   ```
   `parse_sections.py` split the doc into 8 cards (7 authored `##`
   sections + the H1 preamble card); all 8 were submitted `approved` via
   a real `POST /submit` in round 1, zero comments, zero revisions. Ended
   with a real `POST /complete` (server shut down: `.viva/server.url`
   removed, `viva · done` on stdout) and a real
   `scripts/revision_history.py` call, which appended:
   ```
   ## Revision History

   Signed off via viva review — 1 round, 8 sections, 0 revised. 2026-07-16
   ```
   to the doc — the real, script-written ledger, not a hand-authored
   imitation of one.
6. **Hand-off (Step 7).** `command -v gate-ledger` succeeded (studious is
   installed in this environment) — the correct next step is
   `/gate-design-review`.

**Verdict this run would report: `DESIGNED`.**

## What this run does *not* cover, named rather than silently omitted

- **`NEEDS RESEARCH`** and **`REVISED`** were not separately run against a
  real target in this same session — the case-1 (brand-new) path above is
  the one real end-to-end demonstration the story's acceptance criteria
  require. `SKILL.md`'s Step 6 case 3 (the `REVISED`-resume path, with
  `--prior-input`/`--prior-verdicts`) and the round-3 `NEEDS RESEARCH`
  stop are documented in `skills/design/SKILL.md` and checked mechanically
  by `tests/test_design_skill.py`, but neither was walked against a live
  server in this run.
- **The batch interview never opened a genuine round-2 fork** — every
  answer, including the fork question, matched the offered
  `recommended_choice`, so round 2 correctly never fired (per Step 2's
  "conditional, never automatic" rule). This is a faithful outcome of a
  real interview, not a gap in coverage of round-2's own logic, which
  `test_design_skill.py` checks textually.
- **The "developer" answering the interview and approving every viva
  section was this same unattended build-phase session**, not a separate
  human — there is no human available to click through a browser tab in
  this dispatched, non-interactive subagent invocation. Every mechanical
  layer below that role (the HTTP server, the real endpoints, the file
  writes, the hand-off log line, the revision-history append) is real and
  unmodified; only the *judgment* of which chip to click and which section
  to approve was supplied by this session standing in for the human the
  design assumes. This is the one deliberate substitution in an otherwise
  real run, named here rather than left implicit.

## Where the demonstration artifacts live

`docs/design/evidence-capture-branch-scoping.md` and `.viva/*` are both
covered by this repo's own `.gitignore` (`docs/design/`, `.viva/`) and
were never staged or committed to this story's branch — this report is
the durable record of the run, matching the M5 precedent's own choice to
keep a dated report rather than commit scratch demonstration state. The
design content itself is a real, reasoned answer to issue #59 (grounded in
an actual read of `scripts/evidence-capture`), incidentally usable as a
head start if issue #59 is picked up later — but producing that was a
side effect of a real demonstration, not this report's purpose.
