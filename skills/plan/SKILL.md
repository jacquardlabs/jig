---
name: plan
description: STUB — not yet implemented (jig milestone M3, see PRODUCT.md's critical user journeys and DESIGN.md's Vocabulary table). Will become jig's /plan skill — inventory, spine, checkpoint blocks (cap/hold items, verification tiers), lint, and a viva review, emitting the PLAN READY | DESIGN GAP | TOO BIG verdict per the ratified handoff (§5.2). Do not invoke for actual planning work yet; there is no behavior behind this file.
---

# /plan (stub)

This is a scaffold placeholder, not a working skill. It exists so `skills/`
has the directory shape jig's later milestones implement into (M1 —
Repo & plugin scaffold), per this repo's own acceptance criteria.

When M3 implements `/plan`, this file becomes the real entry point:
inventory → spine → checkpoint blocks → lint (`scripts/plan-lint`) → viva
review, per the critical user journey in `PRODUCT.md` and the verdict
vocabulary in `DESIGN.md`.
