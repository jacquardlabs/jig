"""Derives jig's checkpoint-block vocabulary from `DESIGN.md` rather than a
hand-maintained copy.

`test_discipline_skill.py` checks
`skills/task-execution-discipline/SKILL.md`'s body against whatever
vocabulary this module currently derives from `DESIGN.md` -- so a
deliberate rename in `DESIGN.md`'s Vocabulary table (the single source of
truth per the ratified handoff) surfaces as a test failure instead of
being silently missed by an independent, hand-copied tuple.
`test_vocabulary_derivation.py` exercises this module directly, including
a demonstration that a token change in the source is caught.
`test_build_skill.py` uses the same mechanism, via `derive_build_vocabulary`,
for `skills/build/SKILL.md`'s own Foreman-facing vocabulary.

Not itself a test module -- nothing here is collected by `unittest
discover`.
"""
from __future__ import annotations

import re

_BACKTICK = re.compile(r"`([^`]+)`")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")

# Vocabulary-table concepts that belong to a /build executor's checkpoint
# block -- task-execution-discipline's own domain -- as opposed to
# /design's, /plan's, /finish's, or the inspector's verdict vocabularies,
# none of which this skill discusses. A structural selection of *which
# rows* are in scope, not a copy of the *tokens* those rows currently hold.
RELEVANT_VOCABULARY_CONCEPTS = frozenset(
    {"/build task status", "checkpoint item type", "verification tier"}
)

# Vocabulary-table concepts that belong to the /build Foreman's own domain
# (skills/build/SKILL.md) -- the task-status enum it flips via status-flip,
# its own session verdict, and the risk tag its cadence logic reacts to --
# as opposed to /design's, /plan's, or /finish's verdict vocabularies, none
# of which this skill discusses.
BUILD_VOCABULARY_CONCEPTS = frozenset(
    {"/build task status", "/build session verdict", "risk tag"}
)

# Vocabulary-table concepts that belong to /finish's own domain
# (skills/finish/SKILL.md) -- just its own closed verdict enum, as opposed
# to /design's, /plan's, or /build's verdict vocabularies, none of which
# this skill discusses.
FINISH_VOCABULARY_CONCEPTS = frozenset({"/finish verdict"})


def _section(markdown: str, heading: str) -> str:
    """Return the text of a `## {heading}` section, up to the next `## `."""
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", markdown, re.MULTILINE)
    if match is None:
        return ""
    rest = markdown[match.end() :]
    end = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def _table_rows(section: str) -> list[list[str]]:
    """Parse a GFM table's `| a | b |` lines into stripped cell lists,
    respecting `\\|` as an escaped literal pipe rather than a delimiter."""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        inner = line[1:-1] if line.endswith("|") else line[1:]
        rows.append([cell.strip() for cell in _CELL_SPLIT.split(inner)])
    return rows


def _backtick_tokens(cell: str) -> list[str]:
    return _BACKTICK.findall(cell)


def _plain_text(cell: str) -> str:
    return _BACKTICK.sub(r"\1", cell).replace("\\|", "|").strip()


def _vocabulary_table_tokens(design_md: str, concepts: frozenset[str] = RELEVANT_VOCABULARY_CONCEPTS) -> list[str]:
    """Canonical-display tokens from the Vocabulary table's rows whose
    concept cell (column 1) falls within `concepts`."""
    tokens: list[str] = []
    for row in _table_rows(_section(design_md, "Vocabulary")):
        if len(row) < 2:
            continue
        if _plain_text(row[0]) in concepts:
            tokens.extend(_backtick_tokens(row[1]))
    return tokens


def _checkpoint_block_bullet(design_md: str) -> str:
    section = _section(design_md, "Formatting")
    match = re.search(
        r"-\s+\*\*The checkpoint block\*\*.*?(?=\n-\s+\*\*|\Z)", section, re.DOTALL
    )
    return match.group(0) if match else ""


def _executor_checkpoint_fields(design_md: str) -> list[str]:
    """The checkpoint-block field names DESIGN.md's Formatting section
    lists that a /build *executor* consumes while working a task (`Not
    here`, `Done means`, `Evidence`) -- everything after `Do` in the fixed
    field order the block's bullet documents -- as opposed to the fields a
    plan's *author* sets before handing the task off (`Why now`, `Read
    first`, `Rests on`), which this skill never discusses.
    """
    tokens = _backtick_tokens(_checkpoint_block_bullet(design_md))
    if "Do" not in tokens:
        return []
    return tokens[tokens.index("Do") + 1 :]


def derive_jig_vocabulary(design_md: str) -> tuple[str, ...]:
    """jig's own checkpoint-block vocabulary (DESIGN.md: Vocabulary,
    Formatting), derived from `design_md`'s text rather than an
    independent, hand-maintained tuple -- so a token DESIGN.md renames
    changes what this returns, and a SKILL.md that wasn't updated to match
    fails the check instead of silently passing.
    """
    seen: dict[str, None] = {}
    for token in (
        *_vocabulary_table_tokens(design_md),
        *_executor_checkpoint_fields(design_md),
    ):
        seen.setdefault(token, None)
    return tuple(seen)


def derive_build_vocabulary(design_md: str) -> tuple[str, ...]:
    """The /build Foreman's own vocabulary (DESIGN.md: Vocabulary table's
    `/build task status`, `/build session verdict`, and `risk tag` rows),
    derived from `design_md`'s text rather than an independent,
    hand-maintained tuple -- same rationale as `derive_jig_vocabulary`,
    scoped to what `skills/build/SKILL.md` (not the executor-facing
    discipline skill) discusses.
    """
    seen: dict[str, None] = {}
    for token in _vocabulary_table_tokens(design_md, BUILD_VOCABULARY_CONCEPTS):
        seen.setdefault(token, None)
    return tuple(seen)


def derive_finish_vocabulary(design_md: str) -> tuple[str, ...]:
    """/finish's own verdict vocabulary (DESIGN.md: Vocabulary table's
    `/finish verdict` row -- `MERGE` | `PR` | `KEEP` | `DISCARD`), derived
    from `design_md`'s text rather than an independent, hand-maintained
    tuple -- same rationale as `derive_jig_vocabulary`, scoped to what
    `skills/finish/SKILL.md` discusses.
    """
    seen: dict[str, None] = {}
    for token in _vocabulary_table_tokens(design_md, FINISH_VOCABULARY_CONCEPTS):
        seen.setdefault(token, None)
    return tuple(seen)
