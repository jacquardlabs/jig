# PLAN — design-md-vocab-fix

Quick-path plan (one checkpoint block). This is the M5 (`/finish`) epic's
second required-demonstration build, exercising `/finish`'s **PR** verdict
for real (worktree kept, branch kept un-merged, `gh pr create` opens a real
PR) -- distinct git/GitHub mechanics from the first demonstration's MERGE
verdict.

### Task 1 — DESIGN.md: fix /build task-status vocabulary (FIX/RESAMPLE) [PASS]
Why now:    Issue #47 (m4-build-core finale audit, ux-reviewer): DESIGN.md's Vocabulary table lists the `/build` task-status enum as `todo` -> `in-progress` -> `PASS`/`FIX`/`REPLAN`/`ESCALATE`, presenting `FIX` as a fourth terminal status alongside PASS/REPLAN/ESCALATE. The shipped implementation contradicts this: skills/build/SKILL.md states "FIX is never a status suffix -- it's the failure routine's own transient action," and status-flip's write regex can only ever write PASS/REPLAN/ESCALATE. RESAMPLE, FIX's peer transient action, is absent from DESIGN.md entirely. The row's source-of-truth column also still points at "handoff §5.3 (future: skills/build/SKILL.md)" even though skills/build/SKILL.md has shipped (M4) and is the real source now.
Read first: DESIGN.md, skills/build/SKILL.md
Rests on:   none
Do:         In DESIGN.md's Vocabulary table: (1) change the `/build task status` row's canonical-display column to `todo` -> `in-progress` -> `PASS`/`REPLAN`/`ESCALATE` (drop FIX) and its source-of-truth column to `skills/build/SKILL.md`; (2) add a new row documenting FIX and RESAMPLE as the failure routine's two transient actions, never written as a task status suffix, sourced to skills/build/SKILL.md.
Not here:   Do not touch any other Vocabulary table row (the other rows' "future: SKILL.md" source-of-truth notes are unchanged -- out of this task's scope, issue #47 names only the /build task-status row); do not re-derive or change tests/_vocabulary.py's derivation logic.

Done means:
1. [cap]  DESIGN.md's `/build task status` row's canonical-display column contains PASS, REPLAN, and ESCALATE but not FIX, and its source-of-truth column names skills/build/SKILL.md (tier: script)
2. [cap]  DESIGN.md documents FIX and RESAMPLE as the failure routine's two transient actions (never a status suffix) (tier: script)
3. [hold] full test suite (tests/) still passes (tier: test-backed)
Evidence: DESIGN.md diff; grep transcripts; full test-suite run transcript.

## Not-here follow-ups
- DESIGN.md's other Vocabulary rows still point their source-of-truth column at the handoff document even though `/design`, `/plan`, and `/finish` have (or will have) their own shipped SKILL.md files -- a broader pass re-pointing every shipped row is a separate task from this issue's narrow FIX/RESAMPLE fix.
