# Plan: unified Q&A → section-review session (viva #109)

Source design: `design-viva-unified-session.md` (signed off, 2 rounds).

### Task 1 — Add an explicit shutdown call to the QA-mode finish flow
Why now:    Closes a real process-leak gap confirmed during design (server.py
            has no auto-shutdown for qa mode) — every later task's evidence
            depends on qa sessions not leaking a process.
Read first: server.py `/complete` handler (~L3120-3134); `.claude/skills/viva/brainstorming-qa.md`
            (current qa finish steps); design doc's Contracts section
Rests on:   Confirmed — the shutdown timer only starts from an explicit
            `/complete` POST, never automatically (verified server.py:3120-3134;
            this is why this dogfood's own qa session leaked a process).
Do:         Update `brainstorming-qa.md`'s documented steps to call
            `POST /complete` after `answers.json` is read; nothing else in
            the qa contract changes.
Not here:   The handoff/redirect mechanism itself (Task 2) — this task only
            fixes the existing leak.

Done means:
1. [cap]  Launch a qa session, submit an answer, call the new documented
          `/complete` step → process exits within ~2s        (probe: ps check)
2. [hold] Existing `qa-input.json`/`answers.json` shapes unchanged (script: diff against pre-task contract)
Evidence: before/after `ps` output showing process exit; diff of `brainstorming-qa.md`

### Task 2 — Add a `/handoff` endpoint + front-end redirect listener to the QA server
Why now:    This is the actual new capability #109 asks for. Rests on Task 1
            so the handoff path doesn't also leak a process.
Read first: server.py POST dispatch table (~L3080-3135); server.py's
            round-to-round front-end polling JS (the existing
            no-reload-between-rounds mechanism); design doc's Contracts section
Rests on:   Task 1 (clean shutdown exists and is tested).
Do:         Add a `POST /handoff {url}` endpoint to the qa-mode server; add
            front-end JS that polls for a handoff signal post-submission and
            navigates `window.location` to the given URL.
Not here:   Launching the review-mode server itself (existing mechanism,
            wired up in Task 3) — this task only adds the redirect primitive.

Done means:
1. [cap]  `POST /handoff {url:"http://x"}` to a running qa server → a test
          client's poll receives the redirect signal              (test-backed)
2. [cap]  A real browser tab on the qa server navigates to the given URL
          after `/handoff` fires                          (probe: screenshot)
3. [hold] Existing qa-mode behavior unchanged for callers that never call
          `/handoff`                              (script: existing qa suite green)
Evidence: test output; before/after screenshot of the redirect

### Task 3 — Wire /design's QA→review transition end to end
Why now:    Integrates Tasks 1+2 into the actual consumer flow described in
            the design's Approach section.
Read first: design doc's Approach section; Task 2's `/handoff` contract;
            jig's (future) `/design` skill spec §5.1
Rests on:   Tasks 1 and 2 passing.
Do:         Implement the calling sequence: launch qa → read answers → draft
            doc → launch review server → POST `/handoff` with the review
            server's URL → call `/complete` on the qa server.
Not here:   The review-mode UI itself — unchanged, out of scope.

Done means:
1. [cap]  End-to-end: a qa session, once answered, lands the same tab on a
          live review session with no manual step by the human   (probe: screen recording)
2. [hold] No orphaned qa process remains after handoff             (script: ps check)
3. [hold] Review session content matches the freshly-drafted design doc exactly (script: diff)
Evidence: end-to-end screen recording or step-by-step screenshots; ps check output; diff

### Task 4 — Regression: standalone /viva and /viva-qa unaffected
Why now:    This change touches shared server.py code paths used by every
            existing caller (including superpowers' brainstorming integration)
            — must confirm no regression for callers that never touch `/handoff`.
Read first: `tests/test_server_qa.py`, `tests/test_server_api.py`; README's
            existing usage docs
Rests on:   Inventory confirms these tests exist today (evidence:
            `tests/test_server_qa.py` present in the repo tree).
Do:         Run the full existing test suite; add one new regression test
            asserting a standalone qa session (no `/handoff` call) behaves
            exactly as before.
Not here:   Any new feature work — pure regression coverage.

Done means:
1. [cap]  New regression test: a qa session with no `/handoff` call completes
          exactly as it does today                                (test-backed)
2. [hold] Full existing suite green                                    (script: pytest)
Evidence: pytest output (red→green for the new test, full suite pass)

## Not-here follow-ups (drafted, not filed — per handoff, /finish files survivors)
- `.brainstorm-patch-version` retirement (design doc, q4) — separate issue.
- SKILL.md doesn't document the `--prior-input`/`--prior-verdicts` flags as
  required for "re-review after a completed sign-off" (distinct from
  "round 2 of a still-live session") — discovered live during this dogfood
  when the generic "clear stale state" step destroyed the very state needed
  for partial section reopening. Worth its own viva issue; not part of #109.
- 5 pre-existing orphaned `--mode diff` server processes found on this
  machine, unrelated to jig — same leak shape as Task 1, worth a look
  independent of this plan.
