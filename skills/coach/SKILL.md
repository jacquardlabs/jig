---
name: coach
description: STUB — not yet implemented. Will become jig's coach, the orchestrator that reads /build session verdicts (BUILT | PAUSED | ESCALATED) and helps a stuck loop recover. Its own invocation convention (slash command vs. another mechanism) is an open question flagged in DESIGN.md, to be resolved before M6. Do not invoke for actual coaching work yet; there is no behavior behind this file.
---

# coach (stub)

This is a scaffold placeholder, not a working skill. It exists so `skills/`
has the directory shape jig's later milestones implement into (M1 —
Repo & plugin scaffold), per this repo's own acceptance criteria.

DESIGN.md's "Top inconsistencies / risks" section (#4) notes the coach is
the only one of the five commands without a stated slash-command form —
that decision is out of scope for this scaffold and belongs to the
milestone that implements it (M6 per PRODUCT.md's critical user journeys).
