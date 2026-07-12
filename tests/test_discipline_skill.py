"""Regression tests for the task-execution-discipline skill (issue #6, story
discipline-skill).

Standard library only, matching test_scaffold.py's convention. Run with:

    uv run --no-project python3 -m unittest discover -s tests -v

Checks this story's acceptance criteria mechanically:

1. `skills/task-execution-discipline/SKILL.md` exists with valid `name`/
   `description` frontmatter, `name` matching the directory.
2. The description reads as **model-invoked** — a "Use when..." trigger
   naming the moment it fires, not a user-invoked slash-command verb and
   not one of the other five skills' "STUB — not yet implemented" stub
   language (this skill has real content, unlike those stubs).
3. No `SKILL.md` is nested deeper than the directory's top level (regression
   guard for the same failure mode test_scaffold.py guards for the five
   user-invoked skills — viva#101).
4. The body carries jig's own checkpoint-block vocabulary (`cap`/`hold`,
   `Not here`, `Done means`, `Evidence`, the `PASS`/`FIX`/`REPLAN`/`ESCALATE`
   status enum) rather than reading as a verbatim copy of Superpowers'
   generic source material.
5. The skill does not appear among jig's five user-invoked slash commands
   documented in README.md — it is consumed by model judgment, not typed by
   a human.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "task-execution-discipline"
SKILL_MD = SKILL_DIR / "SKILL.md"
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Jig's own checkpoint-block vocabulary (DESIGN.md: Vocabulary, Formatting)
# the canon must be adapted into, not left as Superpowers' generic terms.
JIG_VOCABULARY = (
    "cap",
    "hold",
    "Not here",
    "Done means",
    "Evidence",
    "PASS",
    "FIX",
    "REPLAN",
    "ESCALATE",
    "test-backed",
)

# A phrase distinctive to Superpowers' source skills that has no jig
# equivalent — its presence would signal a verbatim copy rather than an
# adaptation into jig's own vocabulary.
SUPERPOWERS_ONLY_PHRASE = "your human partner"


class TestDisciplineSkillFile(unittest.TestCase):
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
        self.assertEqual(name_match.group(1), "task-execution-discipline")

    def test_description_is_present_and_non_empty(self) -> None:
        desc_match = re.search(
            r"^description:\s*(\S.*)$", self.frontmatter, re.MULTILINE
        )
        self.assertIsNotNone(
            desc_match, f"{SKILL_MD} missing non-empty description: field"
        )
        self.description = desc_match.group(1)

    def test_description_reads_as_model_invoked_trigger(self) -> None:
        desc_match = re.search(
            r"^description:\s*(.*)$", self.frontmatter, re.MULTILINE
        )
        self.assertIsNotNone(desc_match)
        description = desc_match.group(1)
        # Model-invoked skills in this install phrase their description as a
        # trigger on the moment they should fire ("Use when...") rather than
        # a slash-command imperative. This distinguishes it from a stub.
        self.assertIn(
            "Use when",
            description,
            "description should read as a 'Use when...' trigger, "
            "the model-invoked convention this install already follows",
        )
        self.assertNotIn(
            "STUB",
            description,
            "this skill ships real content; it is not one of the five "
            "STUB placeholder skills",
        )

    def test_not_documented_as_a_slash_command(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "/task-execution-discipline",
            readme,
            "this is a model-invoked skill, not one of jig's five "
            "user-invoked slash commands",
        )

    def test_no_nested_skill_md(self) -> None:
        nested = list(SKILL_DIR.rglob("SKILL.md"))
        self.assertEqual(
            nested,
            [SKILL_MD],
            f"{SKILL_DIR} contains nested SKILL.md files: {nested}",
        )

    def test_body_uses_jig_checkpoint_vocabulary(self) -> None:
        missing = [term for term in JIG_VOCABULARY if term not in self.body]
        self.assertEqual(
            missing,
            [],
            f"{SKILL_MD} body is missing jig vocabulary terms: {missing}",
        )

    def test_body_is_not_a_verbatim_superpowers_copy(self) -> None:
        self.assertNotIn(
            SUPERPOWERS_ONLY_PHRASE,
            self.body,
            f"{SKILL_MD} should adapt Superpowers' canon into jig's own "
            "vocabulary, not copy it verbatim",
        )

    def test_body_names_all_three_pillars(self) -> None:
        for pillar in ("TDD", "YAGNI", "Verification"):
            with self.subTest(pillar=pillar):
                self.assertIn(pillar, self.body)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
