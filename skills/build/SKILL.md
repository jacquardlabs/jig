---
name: build
description: STUB — not yet implemented (jig milestone M4, see PRODUCT.md's critical user journeys and DESIGN.md's Vocabulary table). Will become jig's /build skill — a for-loop of fresh executors per task, script-verified status flips (todo → in-progress → PASS/FIX/REPLAN/ESCALATE), and a conditional inspector on load-bearing tasks, emitting a BUILT | PAUSED | ESCALATED session verdict per the ratified handoff (§5.3). Do not invoke for actual build work yet; there is no behavior behind this file.
---

# /build (stub)

This is a scaffold placeholder, not a working skill. It exists so `skills/`
has the directory shape jig's later milestones implement into (M1 —
Repo & plugin scaffold), per this repo's own acceptance criteria.

When M4 implements `/build`, this file becomes the real entry point: a
sequential for-loop of fresh executors per task, status flipped by scripts
only (never the model), with a conditional inspector on load-bearing tasks,
per the critical user journey in `PRODUCT.md` and the verdict vocabulary in
`DESIGN.md`.
