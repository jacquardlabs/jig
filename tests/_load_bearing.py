"""A test-side reference implementation of step 1.5's load-bearing-set
derivation (story rough-in-inspector, issue #15).

`skills/build/SKILL.md` deliberately keeps this derivation as Foreman
*prose* -- a fresh `/build` session reads `Rests on:` lines and reasons
about them itself, the same class of judgment-free-but-not-code-parseable
procedure step 1.4's own trailing-heading exclusion already is (see the
design doc's Alternatives #4: "not adopted this pass"). This module is not
that procedure and is never imported by any script or skill -- it exists
only so a test can demonstrate, mechanically, that the *algorithm the
prose describes* is well-defined and produces the right partition for a
plan shaped like the story's own required demonstration (one task another
task's `Rests on:` line names, one leaf).

Not a test module -- nothing here is collected by `unittest discover`,
matching the `_vocabulary.py` / `_tempgit.py` "shared, not itself
collected" convention already established in this repo.
"""
from __future__ import annotations

import re

TASK_HEADING_RE = re.compile(r"^### Task (\S+) — .*$", re.MULTILINE)
RESTS_ON_RE = re.compile(r"^Rests on:\s*(.*)$", re.MULTILINE)


def _task_blocks(plan_text: str) -> list[tuple[str, str]]:
    """Split `plan_text` into `(label, block_text)` pairs, one per
    `### Task <label> — ...` heading, in document order -- mirroring step
    1.4's own "stop at the next `### ` heading" rule."""
    headings = list(TASK_HEADING_RE.finditer(plan_text))
    blocks = []
    for i, match in enumerate(headings):
        start = match.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(plan_text)
        blocks.append((match.group(1), plan_text[start:end]))
    return blocks


def derive_load_bearing_set(plan_text: str) -> frozenset[str]:
    """The set of task labels that are load-bearing: some *other* task
    block's own `Rests on:` line names them by heading label (e.g. the
    literal text "Task 2"), per step 1.5's stated rule. A task never
    contributes its own label to its own load-bearing status -- only
    another task's `Rests on:` line counts."""
    blocks = _task_blocks(plan_text)
    load_bearing: set[str] = set()
    for label, block in blocks:
        rests_on_matches = RESTS_ON_RE.findall(block)
        rests_on_text = " ".join(rests_on_matches)
        for other_label, _ in blocks:
            if other_label == label:
                continue
            if re.search(rf"\bTask {re.escape(other_label)}\b", rests_on_text):
                load_bearing.add(other_label)
    return frozenset(load_bearing)
