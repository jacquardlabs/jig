"""Regression tests for skills/build/SKILL.md (issue #14, story build-skill).

Standard library only, matching test_scaffold.py's convention. Run with:

    uv run --no-project python3 -m unittest discover -s tests -v

Checks this story's acceptance criteria mechanically, by inspecting the
prose `/build`'s Foreman session actually reads (the same approach
test_discipline_skill.py already takes for its own sibling skill):

1. `skills/build/SKILL.md` has valid `name`/`description` frontmatter,
   `name` matching the directory, and no longer reads as the M1 stub.
2. The dispatch-prompt instructions name exactly the two things an executor
   receives (the task's checkpoint block verbatim + the
   task-execution-discipline trigger) and explicitly rule out the design
   doc and other tasks' history -- the acceptance criteria's central claim
   and the epic pre-mortem's risk #1/#2.
3. The body carries jig's own /build-level vocabulary (`PASS`/`FIX`/
   `REPLAN`/`ESCALATE`, `BUILT`/`PAUSED`/`ESCALATED`, `LOW`/`REPLAN-RISK`/
   `ESCALATE-RISK`), derived from DESIGN.md at test time (see
   `_vocabulary.py` / `test_vocabulary_derivation.py`), not hand-copied.
4. The Failure routine's two-step shape (FIX/RESAMPLE on a first FAIL, one
   flake-ruling-out re-verify then REPLAN/ESCALATE on a genuine second FAIL
   on the *same* item) and "no timeout auto-continue" are all named.
5. `verify` is called only after the executor's own commit -- premortem
   risk #4 -- and its `--since` freshness floor is a fresh per-dispatch
   timestamp, never the executor's own commit SHA (that would make a
   `probe` item's own artifact always predate it -- issue #44).
6. `status-flip`'s PASS path is described deriving its token from
   `results.json` alone, never from a Foreman-supplied status string --
   premortem risk #2's mis-transcription guard.
7. The rough-in inspector is named as an explicit no-op stub pointing at
   issue #15 -- premortem risk #4 -- not silently skipped or simulated.
8. `PAUSED` is never described as reported bare -- every cause names its
   own resume action -- premortem risk #6.
9. No `SKILL.md` is nested deeper than the directory's top level (regression
   guard for the same failure mode test_scaffold.py guards against).
10. The dispatch prompt's boundary line itself instructs the executor to
    commit and return the SHA, and the executor-return contract no longer
    claims the executor emits verify's ITEMS_SCHEMA JSON -- the Foreman
    transcribes that JSON from the checkpoint block's own `Done means`
    lines instead (gate-acceptance fix-and-retry finding on this story:
    the dispatch prompt never taught the executor to commit or hand back
    a SHA/JSON, contradicted by the demonstrated evidence).
11. Step 1.1's missing-baseline-convention PAUSE (stop before any worktree,
    name the missing convention plus the resume action, never guess or
    add a workaround flag) and Step 1.4's trailing-coarser-heading
    exclusion from the last task's block are each present and unambiguous
    -- epic m4-closeout finale-audit follow-up (issue #50, story
    safety-behavior-regression-tests), covering pre-mortem risks #5 and #7
    that this file didn't yet check phrase-for-phrase.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from _frontmatter import FRONTMATTER
from _vocabulary import derive_build_vocabulary

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "build"
SKILL_MD = SKILL_DIR / "SKILL.md"
DESIGN_MD = REPO_ROOT / "DESIGN.md"

BUILD_VOCABULARY = derive_build_vocabulary(DESIGN_MD.read_text(encoding="utf-8"))


class TestBuildSkillFile(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SKILL_MD.is_file(), f"{SKILL_MD} does not exist")
        self.text = SKILL_MD.read_text(encoding="utf-8")
        match = FRONTMATTER.match(self.text)
        self.assertIsNotNone(match, f"{SKILL_MD} has no --- frontmatter block")
        self.frontmatter = match.group(1)
        self.body = self.text[match.end() :]

    def test_name_matches_directory(self) -> None:
        name_match = re.search(r"^name:\s*(\S+)", self.frontmatter, re.MULTILINE)
        self.assertIsNotNone(name_match, f"{SKILL_MD} missing name: field")
        self.assertEqual(name_match.group(1), "build")

    def test_description_is_present_and_no_longer_a_stub(self) -> None:
        desc_match = re.search(r"^description:\s*(.*)$", self.frontmatter, re.MULTILINE)
        self.assertIsNotNone(desc_match, f"{SKILL_MD} missing description: field")
        description = desc_match.group(1)
        self.assertTrue(description.strip())
        self.assertNotIn(
            "STUB",
            description,
            "build has real orchestration content as of story build-skill; "
            "it is no longer one of the STUB placeholder skills",
        )
        self.assertNotIn("Do not invoke for actual build work yet", self.body)

    def test_description_is_a_valid_unquoted_yaml_plain_scalar(self) -> None:
        desc_match = re.search(r"^description:\s*(.*)$", self.frontmatter, re.MULTILINE)
        self.assertIsNotNone(desc_match)
        description = desc_match.group(1)
        self.assertNotIn(
            ": ",
            description,
            "unquoted description contains ': ' -- a strict YAML frontmatter "
            "loader will fail to parse this plain scalar",
        )
        self.assertNotRegex(
            description,
            r"\s#",
            "unquoted description contains whitespace followed by '#' -- a "
            "strict YAML loader reads this as a comment and silently "
            "truncates the rest of the value",
        )

    def test_no_nested_skill_md(self) -> None:
        nested = list(SKILL_DIR.rglob("SKILL.md"))
        self.assertEqual(nested, [SKILL_MD], f"{SKILL_DIR} contains nested SKILL.md files: {nested}")


class TestBuildVocabularyDerivation(unittest.TestCase):
    def test_derived_vocabulary_is_non_empty(self) -> None:
        # Guards against a parsing regression turning the vocabulary check
        # below into a vacuous no-op.
        self.assertGreaterEqual(
            len(BUILD_VOCABULARY),
            8,
            f"derived BUILD_VOCABULARY looks too short ({BUILD_VOCABULARY!r}) -- "
            "check DESIGN.md's Vocabulary table still matches _vocabulary.py's "
            "parsing assumptions",
        )


def _normalize_ws(text: str) -> str:
    """Collapse whitespace runs (including line-wrap newlines) to a single
    space, so a multi-word phrase check doesn't break on where prose
    happens to be hand-wrapped."""
    return re.sub(r"\s+", " ", text)


class TestBuildSkillBody(unittest.TestCase):
    def setUp(self) -> None:
        self.body = SKILL_MD.read_text(encoding="utf-8")
        self.flat_body = _normalize_ws(self.body)

    def assertPhraseIn(self, phrase: str) -> None:
        self.assertIn(_normalize_ws(phrase), self.flat_body, f"phrase not found (whitespace-normalized): {phrase!r}")

    def test_body_uses_build_level_vocabulary(self) -> None:
        missing = [term for term in BUILD_VOCABULARY if term not in self.body]
        self.assertEqual(missing, [], f"{SKILL_MD} body is missing /build vocabulary terms: {missing}")

    def test_names_the_three_roles(self) -> None:
        for role in ("Foreman", "Executor", "Scripts"):
            with self.subTest(role=role):
                self.assertIn(role, self.body)

    def test_names_all_four_scripts(self) -> None:
        for script in ("worktree-setup", "verify", "evidence-capture", "status-flip"):
            with self.subTest(script=script):
                self.assertIn(script, self.body)

    def test_dispatch_prompt_is_scoped_to_task_block_plus_discipline_trigger(self) -> None:
        # The acceptance criteria's central claim: exactly the task block +
        # Read-first contents + task-execution-discipline -- not the design
        # doc, not other tasks' history.
        self.assertIn("task-execution-discipline", self.body)
        self.assertIn("design doc", self.body.lower())
        self.assertIn("other task", self.body.lower())
        self.assertPhraseIn("Nothing else goes into the dispatch prompt")

    def test_dispatch_prompt_tells_executor_to_commit_and_return_the_sha(self) -> None:
        # gate-acceptance fix-and-retry finding: the dispatch prompt must
        # itself instruct the commit + SHA hand-back that step 2.4 relies
        # on -- a fresh executor given only the task block + boundary line
        # has no other way to learn this convention (demonstrated gap in
        # docs/jig/demonstrations/2026-07-12-build-skill/README.md).
        self.assertPhraseIn("Commit your change yourself as your last act, and end your final message with the commit SHA you just created")

    def test_executor_return_contract_does_not_claim_a_fenced_json_block(self) -> None:
        # The executor's context (task block + boundary line) never
        # mentions verify's ITEMS_SCHEMA, so step 2.4 must not claim the
        # executor emits that JSON -- the Foreman transcribes it instead
        # (step 2.5), matching the demonstrated behavior in this story's
        # evidence folder.
        self.assertNotIn("fenced JSON block", self.body)
        self.assertPhraseIn("The executor never emits `scripts/verify`'s `ITEMS_SCHEMA` JSON itself")

    def test_foreman_transcribes_items_from_the_checkpoint_block(self) -> None:
        self.assertPhraseIn("Transcribe the items file yourself")
        self.assertPhraseIn("one entry per numbered `Done means` item in *this task's own checkpoint block*")

    def test_failure_routine_names_fix_and_resample(self) -> None:
        for token in ("FIX", "RESAMPLE"):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_failure_routine_rules_out_a_flake_before_genuine_second_failure(self) -> None:
        self.assertIn("flake", self.body.lower())
        self.assertPhraseIn("same, already-produced artifacts")
        self.assertPhraseIn("no new executor dispatched")

    def test_no_timeout_auto_continue_is_named(self) -> None:
        self.assertIn("no timeout auto-continue", self.body.lower())

    def test_verify_ordered_strictly_after_executor_commit(self) -> None:
        self.assertPhraseIn("always happens *after* the executor's own commit, never")
        self.assertPhraseIn("--since <this attempt's dispatch timestamp from step 2.2>")

    def test_verify_since_floor_is_not_the_executors_own_commit_sha(self) -> None:
        # Issue #44: a probe artifact is written to disk before it's
        # committed, so its mtime is always at or before that very
        # commit's own timestamp -- using the executor's own commit SHA as
        # --since makes every probe item structurally unpassable. SKILL.md
        # must no longer instruct that value, and must capture a fresh
        # per-dispatch timestamp instead (including on Failure-routine
        # retries).
        self.assertNotIn("--since <the executor's reported commit SHA>", self.body)
        self.assertPhraseIn("Capture this attempt's dispatch timestamp")
        self.assertPhraseIn("Never the executor's own reported commit SHA")
        self.assertPhraseIn("capture a fresh dispatch timestamp per step 2.2 for each one")

    def test_verify_exit_2_is_not_a_task_fail(self) -> None:
        self.assertPhraseIn("Exit code 2 from `verify` is not a task FAIL")
        self.assertPhraseIn("does **not** count against the Failure routine's two-failure budget")

    def test_evidence_directory_is_committed_before_status_flip(self) -> None:
        # A real smoke-test run surfaced this gap: evidence-capture writes
        # files but never commits them, so the *next* task's
        # evidence-capture call refuses against the resulting dirty tree
        # unless the Foreman commits the evidence directory itself first.
        self.assertPhraseIn("Commit the evidence directory `evidence-capture` just wrote")
        self.assertPhraseIn("Do this before calling `status-flip`, not after")

    def test_status_flip_pass_path_derives_token_from_results_only(self) -> None:
        self.assertPhraseIn("`status-flip` derives the `PASS` token itself from")
        self.assertPhraseIn("you never hand it a status string on this path")

    def test_step_5_instructs_scratch_path_for_items_and_results(self) -> None:
        # Issue #45: the Foreman's own transient items.json/results.json
        # must never land inside the worktree, or evidence-capture's
        # clean-tree check refuses on task 1 -- before the task can ever
        # complete, not just before a later one.
        self.assertPhraseIn(
            "Write this items file, and `verify`'s `--out results.json` "
            "below, to a scratch path outside the worktree"
        )
        self.assertPhraseIn("never a path under `<worktree>` itself")
        self.assertPhraseIn("issue #45")

    def test_step_7_evidence_capture_points_at_the_scratch_path_results(self) -> None:
        # The evidence-capture call in step 7 must reuse step 5's
        # scratch-path results.json directly, never a copy staged inside
        # the worktree first -- the same seam issue #45 names.
        self.assertPhraseIn(
            "pointing `--artifact` straight at each scratch-path file, never "
            "at a path staged inside `<worktree>` first"
        )
        self.assertPhraseIn(
            "`evidence-capture` reads an artifact from wherever `--artifact` names "
            "it and copies it into the worktree's own evidence directory itself"
        )

    def test_step_7_probe_artifacts_get_a_fresh_copy_before_evidence_capture(self) -> None:
        # m4-verify-fixes epic-finale audit, code-auditor finding 1: a probe
        # item's own artifact is committed by the executor inside the
        # worktree, so its mtime is always at or before that commit's own
        # timestamp -- the same structural fact issue #44 diagnosed for
        # verify's --since floor, this time tripping evidence-capture's own
        # stale-artifact refusal. Step 7 must instruct a fresh, non-preserving
        # copy before handing such an artifact to --artifact.
        self.assertPhraseIn(
            "copy each such artifact into the scratch dir with a plain, "
            "non-preserving copy"
        )
        self.assertPhraseIn(
            "point `--artifact` at the copy, never at the in-worktree original"
        )

    def test_step_7_status_flip_reuses_the_same_scratch_path_results(self) -> None:
        self.assertPhraseIn(
            "the same scratch-path file from step 5 — `status-flip` only "
            "reads it, never requires it to live in the worktree either"
        )

    def test_inspector_is_an_explicit_no_op_stub_pointing_at_its_issue(self) -> None:
        self.assertIn("no-op", self.body.lower())
        self.assertIn("issue #15", self.body)
        self.assertPhraseIn("Do not call it, simulate it")

    def test_paused_is_never_reported_bare(self) -> None:
        self.assertPhraseIn("Never report `PAUSED` bare")
        self.assertPhraseIn("four distinct causes")

    def test_replan_is_overwritable_not_terminal(self) -> None:
        self.assertPhraseIn("overwrites a prior `REPLAN` suffix")
        self.assertPhraseIn("one status that isn't terminal")

    def test_standalone_capable_degradation_is_named(self) -> None:
        self.assertPhraseIn("If studious is installed")
        self.assertPhraseIn("ready for review directly")

    def test_body_names_all_checkpoint_block_fields(self) -> None:
        for field in ("Why now", "Read first", "Rests on", "Do", "Not here", "Done means", "Evidence"):
            with self.subTest(field=field):
                self.assertIn(field, self.body)

    def test_step_1_1_missing_baseline_convention_pauses_before_any_worktree(self) -> None:
        # Step 1.1 / epic pre-mortem risk #5 (docs/studious/premortems/build-skill.md):
        # a target CLAUDE.md that names no baseline command *at all* is a
        # Setup-time stop for the Foreman itself -- distinct from
        # scripts/worktree-setup's own dirty-baseline case (a *named*
        # command that then fails after the worktree already exists; see
        # TestWorktreeSetupDirtyBaseline in test_worktree_setup.py). This
        # checks the instruction is unambiguous by requiring every one of
        # its load-bearing parts to be in the body together: the exact
        # trigger (no convention at all, not merely an unfamiliar one), the
        # exact stop point (before any worktree is created), the exact
        # verdict token (PAUSED), the exact resume action (add a
        # baseline-command convention, then re-invoke), and the explicit
        # refusal to paper over the gap by guessing a runner or inventing a
        # workaround flag -- silent, unverified building is what this stop
        # exists to prevent.
        self.assertPhraseIn("If the target project's `CLAUDE.md` names no baseline command at all")
        self.assertPhraseIn("stop here — before creating any worktree — and report **PAUSED**")
        self.assertPhraseIn(
            'naming exactly what\'s missing (no "Tests" or equivalent convention in `CLAUDE.md`) '
            "and the resume action (add a baseline-command convention to `CLAUDE.md`, "
            "then re-invoke `/build`)"
        )
        self.assertPhraseIn(
            "Do not add a second input or flag to work around this; silent, unverified "
            "building is the one thing this stop exists to prevent"
        )
        self.assertPhraseIn("never guess a test runner and never hardcode one")

    def test_step_1_4_excludes_trailing_coarser_heading_from_last_task_block(self) -> None:
        # Step 1.4 / epic pre-mortem risk #7: splitting the plan into task
        # blocks is the Foreman's own judgment, explicitly *not* a
        # mechanical heading-depth parser -- and must not let a coarser
        # trailing section (e.g. a closing "## Not-here follow-ups") bleed
        # into the last task's dispatched block, reproducing the real M0
        # dogfood bug this instruction exists to prevent. No script performs
        # this split (status-flip only edits a single `### Task <label>`
        # heading line in place, see test_status_flip.py's
        # TestStatusFlipHeadingMatch), so a phrase-level check on the
        # Foreman's own reading instructions -- rather than a live parser
        # demonstration -- is the regression guard available here.
        self.assertPhraseIn("This is your own judgment, not a mechanical heading-depth parser")
        self.assertPhraseIn(
            "read to each `### Task N — <title>` heading and stop accumulating a "
            "task's content at the next `### ` heading"
        )
        self.assertPhraseIn("Explicitly exclude any trailing content at a coarser heading level")
        self.assertPhraseIn("a closing `## Not-here follow-ups` section")
        self.assertPhraseIn(
            "a naive parser silently absorbs that trailing section into the preceding task card"
        )
        self.assertPhraseIn("a real bug the project's own M0 dogfood surfaced")
        self.assertPhraseIn("read for meaning and don't reproduce it")


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
