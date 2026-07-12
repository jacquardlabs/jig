"""Regression tests for coach/SKILL.md's description-template divergence
(issue #28, story coach-description-fix).

Standard library only, matching test_scaffold.py's convention. Run with:

    uv run --no-project python3 -m unittest discover -s tests -v

Checks this story's acceptance criteria mechanically:

1. `skills/coach/SKILL.md`'s `description:` frontmatter opens with the same
   milestone + doc-citation shape the other three still-stub skills
   (`design`/`plan`/`finish`) already share -- "STUB -- not yet implemented
   (jig milestone M<n>, see PRODUCT.md's critical user journeys and
   DESIGN.md's <citation>). Will become jig's ..." -- rather than omitting
   the parenthetical and burying its milestone/doc citation at the end of
   the sentence (gate-audit's Important finding, m1-scaffold epic finale;
   see docs/studious/premortems and jig issue #28).

   `build` shared this template through M1-M3; story `build-skill` (M4)
   replaced its stub with real orchestration content, so it is no longer
   part of this stub-only regression set -- see test_build_skill.py for its
   own acceptance checks instead. `finish` shared it through M1-M4; story
   `finish-skill` (M5) replaced its stub with real closing-out content, so
   it is no longer part of this set either -- see test_finish_skill.py.
2. coach's description keeps citing its own open question (M6, DESIGN.md's
   "Top inconsistencies / risks" section (#4)) rather than silently
   dropping the detail while normalizing the opener.
3. All remaining stub descriptions stay valid unquoted YAML plain scalars --
   no mid-string `": "` (test_discipline_skill.py's existing regression
   guard, extended here to all of them) and no whitespace-then-`#` (a second
   failure mode this story's own fix attempt tripped over: a strict YAML
   loader reads it as a comment and silently truncates the rest of the
   value). Cross-checked against a real YAML parse where PyYAML is
   available.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from _frontmatter import FRONTMATTER

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# The user-invoked skill stubs that still share one description template.
# `build` graduated out of this set at story build-skill (M4); `finish`
# graduated out at story finish-skill (M5) -- both now ship real content,
# checked by test_build_skill.py / test_finish_skill.py instead.
STUB_SKILLS = ("design", "plan", "coach")

# The opener every stub description must share: milestone + doc citation up
# front, before "Will become jig's ..." -- not buried at the end of the
# sentence the way coach's used to read.
STUB_OPENER = re.compile(
    r"^STUB — not yet implemented \("
    r"jig milestone [^,]+, "
    r"see PRODUCT\.md's critical user journeys and DESIGN\.md's .+?"
    r"\)\. Will become jig's "
)


def _description_for(skill: str) -> str:
    skill_md = SKILLS_DIR / skill / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    assert match is not None, f"{skill_md} has no --- frontmatter block"
    desc_match = re.search(r"^description:\s*(.*)$", match.group(1), re.MULTILINE)
    assert desc_match is not None, f"{skill_md} missing description: field"
    return desc_match.group(1)


class TestStubDescriptionTemplate(unittest.TestCase):
    def test_all_stub_skills_share_the_opener_template(self) -> None:
        for skill in STUB_SKILLS:
            with self.subTest(skill=skill):
                description = _description_for(skill)
                self.assertRegex(
                    description,
                    STUB_OPENER,
                    f"skills/{skill}/SKILL.md's description should open "
                    "with the shared milestone + doc-citation stub "
                    "template, like the other user-invoked stubs",
                )

    def test_coach_description_still_cites_its_open_question(self) -> None:
        description = _description_for("coach")
        self.assertIn(
            "M6",
            description,
            "coach's description should still name the milestone (M6) "
            "its invocation-convention question resolves by",
        )
        self.assertIn(
            "Top inconsistencies",
            description,
            "coach's description should still point at DESIGN.md's "
            "\"Top inconsistencies / risks\" entry (#4) for its own "
            "open question, since coach has no Vocabulary-table row",
        )

    def test_stub_descriptions_are_valid_unquoted_yaml_plain_scalars(self) -> None:
        # Same regression guard test_discipline_skill.py already applies to
        # its own skill, extended with a second failure mode this story's
        # own fix attempt tripped over: a YAML plain (unquoted) scalar
        # cannot contain ": " (colon followed by a space) mid-string, and a
        # "#" preceded by whitespace starts a comment that silently
        # truncates the rest of the value -- both break a strict frontmatter
        # loader without raising, so a naive regex-only test would miss it.
        for skill in STUB_SKILLS:
            with self.subTest(skill=skill):
                description = _description_for(skill)
                self.assertNotIn(
                    ": ",
                    description,
                    "unquoted description contains ': ' -- a strict YAML "
                    "frontmatter loader will fail to parse this plain "
                    "scalar; quote the value or rephrase to avoid a "
                    "mid-string colon",
                )
                self.assertNotRegex(
                    description,
                    r"\s#",
                    "unquoted description contains whitespace followed by "
                    "'#' -- a strict YAML loader reads this as a comment "
                    "and silently truncates the rest of the value; "
                    "rephrase so '#' is never preceded by whitespace "
                    "(e.g. 'section (#4)' not 'section #4')",
                )

    def test_stub_description_frontmatter_round_trips_through_yaml(self) -> None:
        # Belt-and-suspenders: parse each stub's frontmatter with a real
        # YAML loader and confirm it agrees with the regex-based extraction
        # the rest of this suite (and test_scaffold.py) relies on. Catches
        # any future divergence the two narrower checks above don't
        # anticipate.
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed in this environment")
        for skill in STUB_SKILLS:
            with self.subTest(skill=skill):
                skill_md = SKILLS_DIR / skill / "SKILL.md"
                text = skill_md.read_text(encoding="utf-8")
                match = FRONTMATTER.match(text)
                self.assertIsNotNone(match)
                parsed = yaml.safe_load(match.group(1))
                self.assertEqual(parsed["description"], _description_for(skill))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
