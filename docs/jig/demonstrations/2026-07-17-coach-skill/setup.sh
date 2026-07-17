#!/usr/bin/env bash
# Rebuilds the five scratch pipeline states the coach-skill demonstrations
# were captured against. Every state is a real git repo; the REPLAN /
# ESCALATE / PASS suffixes are written by real `scripts/status-flip` runs
# (never by hand), so the commits the coach's Step 1 reads are the genuine
# artifact of the only tool allowed to write them.
#
# Usage: ./setup.sh <scratch-root> <jig-repo-root>
#
# Fixtures reused, not invented: the plan is the plan-skill story's real,
# viva-approved, plan-lint-clean ci-wiring PLAN.md
# (docs/jig/demonstrations/2026-07-16-plan-skill/ci-wiring-demo/PLAN.md);
# the design doc is the real docs/design/plan-lint-ci.md it was drafted
# from. Both live on this same branch and die at merge together with this
# folder.
set -euo pipefail

scratch="$1"
jig="$2"
plan_src="$jig/docs/jig/demonstrations/2026-07-16-plan-skill/ci-wiring-demo/PLAN.md"
design_src="$jig/docs/design/plan-lint-ci.md"
status_flip="$jig/scripts/status-flip"

mk_project() { # $1 = state dir
  mkdir -p "$1"
  cd "$1"
  git init -q -b main .
  git config user.email coach-demo@example.invalid
  git config user.name coach-demo
  printf '# Product context (fixture)\n\nMinimal target-project stand-in for the coach demonstrations.\n' > PRODUCT.md
  printf '# CLAUDE.md (fixture)\n\nMinimal conventions stand-in for the coach demonstrations.\n' > CLAUDE.md
  git add -A
  git commit -qm "fixture: project scaffold"
}

add_plan_state() { # run from inside a state dir
  mkdir -p docs/design
  cp "$design_src" docs/design/plan-lint-ci.md
  cp "$plan_src" PLAN.md
  git add -A
  git commit -qm "fixture: design doc + PLAN.md (post-plan state)"
}

printf '{"overall": "PASS"}\n' > "$scratch/results-pass.json"

# State A -- no artifacts: a project with no design doc and no PLAN.md.
mk_project "$scratch/no-artifacts"

# State B -- post-plan: design doc + PLAN.md, no task suffixes yet.
mk_project "$scratch/post-plan"
add_plan_state

# State C -- mid-build PAUSED: Task 1 [PASS] (real --results flip),
# Task 2 [REPLAN] (real --status flip carrying the Foreman's --reason).
mk_project "$scratch/mid-build-replan"
add_plan_state
"$status_flip" --plan PLAN.md --task 1 --results "$scratch/results-pass.json"
"$status_flip" --plan PLAN.md --task 2 --status REPLAN --reason \
  "Done means 2 unmeetable as written: a plain 'scripts/plan-lint tests/fixtures/plan-lint/broken-plan.md' step exits 1 and fails the job, so the job can never 'still report success on that expected 1'. The block's Do: needs the expected-1 invocation scripted (e.g. guard the step so exit 1 is the passing outcome) before an executor can satisfy the item."

# State D -- revision loop: Task 1 [PASS], Task 2 [ESCALATE] (real flip
# carrying the design-level finding /design revision mode needs).
mk_project "$scratch/escalate"
add_plan_state
"$status_flip" --plan PLAN.md --task 1 --results "$scratch/results-pass.json"
"$status_flip" --plan PLAN.md --task 2 --status ESCALATE --reason \
  "Design assumption falsified: docs/design/plan-lint-ci.md's Proposed design has the lint job asserting both fixture exit codes in one uniform step shape, but broken-plan.md's expected exit 1 cannot be expressed as the same plain invocation as clean-plan.md's exit 0 -- the design's own 'symmetrical two-invocation' claim needs revising, which is outside this plan's authority."

# State E -- repo contradicts conversation: Tasks 1-2 [PASS] via real
# flips, Task 3 left unsuffixed; the conversation (see the demo README)
# claims BUILT.
mk_project "$scratch/repo-contradicts-conversation"
add_plan_state
"$status_flip" --plan PLAN.md --task 1 --results "$scratch/results-pass.json"
"$status_flip" --plan PLAN.md --task 2 --results "$scratch/results-pass.json"

printf 'setup: five states built under %s\n' "$scratch"
