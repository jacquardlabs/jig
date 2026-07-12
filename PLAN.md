# PLAN — ruff-extend-select-fix

Quick-path plan (one checkpoint block). This is also the M5 (`/finish`)
epic's own required real `/build` demonstration (docs/design/finish-skill.md,
"Required demonstration"): a genuine, non-scratch evidence folder for
`/finish` Step 1 to promote.

### Task 1 — Fix ruff config: select -> extend-select [PASS]
Why now:    Issue #36 (m1-followup finale audit, code-auditor): pyproject.toml's [tool.ruff.lint] uses `select`, which *replaces* ruff's default rule set instead of adding to it -- silently disabling Pyflakes (F: unused imports, undefined names) and the default pycodestyle error checks (E4/E7/E9), even though CLAUDE.md's own checklist calls those out. `ruff check .` has been passing clean against a weaker rule set than the docs imply.
Read first: pyproject.toml
Rests on:   none
Do:         Change pyproject.toml's [tool.ruff.lint] table from `select = [...]` to `extend-select = [...]` (same six rule categories: B, C4, PERF, PIE, RUF, SIM), so ruff's own default E4/E7/E9/F rules stay active alongside them. Re-run ruff and the full test suite to confirm nothing regresses under the now-stricter config.
Not here:   Do not add new ruff rule categories beyond the existing six; do not wire `ruff check .` into a CI job (issue #36's own request already names that as a separate follow-up, not this task's scope); do not touch any other pyproject.toml table.

Done means:
1. [cap]  pyproject.toml's [tool.ruff.lint] declares extend-select, not select (tier: script)
2. [hold] `ruff check .` exits 0 under the corrected config (tier: script)
3. [hold] full test suite (tests/) still passes (tier: test-backed)
Evidence: pyproject.toml diff; `ruff check .` transcript; full test-suite run transcript.

## Not-here follow-ups
- Wire `ruff check .` into a CI job (issue #36's own request already names this as a follow-up, not this task's scope).
- Audit other Jacquard Labs repos for the same `select`-vs-`extend-select` mistake.
