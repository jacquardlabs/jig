"""Regression tests for scripts/design-lint (story design-lint, issue #9).

Exercises the script as a black box (subprocess against the real
executable), matching `test_verify.py`/`test_evidence_capture.py`'s own
convention, never importing its internals directly. Each violation fixture
is `CLEAN_DOC` with exactly one targeted change, so a failure names the
*specific* element this story's acceptance criteria require:

1. Clean pass: a 7-section, fully-conformant doc exits 0.
2. Each of Check 1's three sub-cases (missing required section,
   out-of-range count, unrecognized heading), Check 2 (prose-only
   Contracts), Check 3 (unresolvable Assumptions path), Check 4
   (purely-happy-path Experience), and Check 5 (unruled fork) exits 1 and
   names the specific violation, per `docs/design/design-lint.md`'s own
   "Tests" plan (Operational readiness).
3. Three premortem-driven regressions
   (docs/studious/premortems/design-lint.md): risk #7 (backtick-quoted
   filler doesn't count as concreteness), risk #3 (a genuine failure path
   phrased without a listed token is a documented, deliberate false
   negative — not a bug), and risk #4/#5 (path-citation escape safety and
   an in-body `---` divider don't crash or mis-slice the parser).

Run with:

    uv run --no-project python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "design-lint"

# A fully-conformant 7-section design-<slug>.md, styled after the one real
# `/design` precedent this repo has (docs/jig/dogfood/design-viva-unified-
# session.md) but adapted so every check actually resolves clean against a
# throwaway fixture repo: every `(qN)` fork carries a ruling verb in its own
# sentence/bullet, `Contracts` carries a fenced code block plus
# artifact-shaped inline code, `Assumptions` mixes an interview-ruled bullet
# with a tree-checkable one, and `Experience` names a failure path alongside
# its happy path.
CLEAN_DOC = """# Design: unified Q&A handoff (fixture)

## Intent

The batch interview ranked (q1) this handoff ahead of an alternative
full-rewrite design, on the grounds that it ships sooner without touching
the QA server's own contract.

## Experience

- Same browser tab for the whole session — no new tab, no manual re-invoke
  by the human.
- If the review server fails to start, the QA tab stays on its current
  cards and shows no crash — the handoff simply doesn't fire (see Risks).

## Contracts

Session state is written as:

```json
{"answers": "answers.json", "review": "review-r1.json"}
```

The handoff endpoint is `POST /handoff {url}`, implemented in
`src/server.py:5-8`.

## Approach

1. Launch the QA server as today (unchanged).
2. Claude reads `answers.json`, drafts the design doc.
3. Claude launches a review-mode server and signals the QA tab to redirect.

## Assumptions

- Session continuity is a two-process, same-tab client redirect (q2), a
  call the interview confirmed after review.
- The handoff endpoint is implemented at `src/server.py:20-22`, which this
  design confirms exists in the checkout.

## Not doing

- A fully server-autonomous handoff — q3 rejected this alternative outright.

## Risks

- If the handoff step forgets to call `/complete` on the QA server, the
  process leaks — a correctness requirement, not an implementation detail.

---

## Revision History

Signed off via viva review — 1 round, 7 sections, 0 revised. 2026-07-16
"""

# A minimal doc carrying only the three unconditionally-required sections —
# below the 5-section floor by count alone, independent of vocabulary or
# missing-section concerns (both of the three required names are present).
OUT_OF_RANGE_COUNT_DOC = """# Design: too few sections (fixture)

## Experience

- If the request fails, the client shows an error and stops.

## Contracts

```json
{"answers": "answers.json"}
```

## Assumptions

- The config lives at `src/server.py`, which this design confirms exists.
"""


def run_script(doc_path: Path, repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), "--doc", str(doc_path), "--repo", str(repo)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _write_repo_with_server(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "server.py").write_text("def handoff():\n    pass\n", encoding="utf-8")
    return repo


def _write_doc(tmp: Path, text: str, name: str = "design-fixture.md") -> Path:
    doc = tmp / name
    doc.write_text(text, encoding="utf-8")
    return doc


class TestDesignLintCleanPass(unittest.TestCase):
    def test_conformant_doc_exits_zero_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, CLEAN_DOC)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("clean pass", result.stdout)
            self.assertNotIn("[FAIL]", result.stdout)


class TestDesignLintCheck1SectionVocabulary(unittest.TestCase):
    def test_missing_required_section_is_named(self) -> None:
        assumptions_block = (
            "## Assumptions\n\n"
            "- Session continuity is a two-process, same-tab client redirect (q2), a\n"
            "  call the interview confirmed after review.\n"
            "- The handoff endpoint is implemented at `src/server.py:20-22`, which this\n"
            "  design confirms exists in the checkout.\n\n"
        )
        self.assertIn(assumptions_block, CLEAN_DOC)
        doc_text = CLEAN_DOC.replace(assumptions_block, "")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("missing required section 'Assumptions'", result.stdout)

    def test_out_of_range_section_count_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, OUT_OF_RANGE_COUNT_DOC)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("3 top-level sections found; DESIGN.md requires 5-8", result.stdout)

    def test_unrecognized_heading_is_named(self) -> None:
        self.assertIn("## Approach\n", CLEAN_DOC)
        doc_text = CLEAN_DOC.replace("## Approach\n", "## Implementation Plan\n", 1)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "section 'Implementation Plan' does not match jig's canonical section vocabulary",
                result.stdout,
            )


class TestDesignLintCheck2ContractsConcrete(unittest.TestCase):
    def test_prose_only_contracts_is_named(self) -> None:
        contracts_body = (
            "Session state is written as:\n\n"
            "```json\n"
            '{"answers": "answers.json", "review": "review-r1.json"}\n'
            "```\n\n"
            "The handoff endpoint is `POST /handoff {url}`, implemented in\n"
            "`src/server.py:5-8`.\n\n"
        )
        self.assertIn(contracts_body, CLEAN_DOC)
        prose_only = (
            "The system hands session state between phases through a small,\n"
            "already-existing HTTP surface shared by both servers involved.\n\n"
        )
        doc_text = CLEAN_DOC.replace(contracts_body, prose_only)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("section 'Contracts' has no concrete shape markers", result.stdout)

    def test_backtick_quoted_filler_does_not_count_as_concrete(self) -> None:
        """Premortem risk #7: a Contracts section dense with backticks that
        name no real artifact (`maybe`, `later`, `soon`) must still fail —
        the concreteness check counts artifact-shaped spans, not any
        backtick span."""
        contracts_body = (
            "Session state is written as:\n\n"
            "```json\n"
            '{"answers": "answers.json", "review": "review-r1.json"}\n'
            "```\n\n"
            "The handoff endpoint is `POST /handoff {url}`, implemented in\n"
            "`src/server.py:5-8`.\n\n"
        )
        self.assertIn(contracts_body, CLEAN_DOC)
        filler_only = (
            "This might land `later`, `maybe` as a fast-follow, `soon` after\n"
            "this ships — details `tbd`.\n\n"
        )
        doc_text = CLEAN_DOC.replace(contracts_body, filler_only)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("section 'Contracts' has no concrete shape markers", result.stdout)


class TestDesignLintContractsArtifactSpanThreshold(unittest.TestCase):
    """Premortem risk #6: pins the exact MIN_ARTIFACT_SPANS boundary so a
    future threshold change is a deliberate edit, not a silent drift — a
    Contracts section with no fence/table still passes at exactly the
    floor and still fails one span short of it."""

    CONTRACTS_BLOCK = (
        "Session state is written as:\n\n"
        "```json\n"
        '{"answers": "answers.json", "review": "review-r1.json"}\n'
        "```\n\n"
        "The handoff endpoint is `POST /handoff {url}`, implemented in\n"
        "`src/server.py:5-8`.\n\n"
    )

    def test_exactly_the_floor_with_no_fence_or_table_still_passes(self) -> None:
        self.assertIn(self.CONTRACTS_BLOCK, CLEAN_DOC)
        prose_with_three_artifact_spans = (
            "Session state lives in `answers.json`, `review-input-r1.json`,\n"
            "and `review-r1.json` — one file per phase, no consolidation.\n\n"
        )
        doc_text = CLEAN_DOC.replace(self.CONTRACTS_BLOCK, prose_with_three_artifact_spans)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_one_short_of_the_floor_with_no_fence_or_table_fails(self) -> None:
        self.assertIn(self.CONTRACTS_BLOCK, CLEAN_DOC)
        prose_with_two_artifact_spans = (
            "Session state lives in `answers.json` and `review-r1.json` —\n"
            "one file per phase, no consolidation.\n\n"
        )
        doc_text = CLEAN_DOC.replace(self.CONTRACTS_BLOCK, prose_with_two_artifact_spans)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("section 'Contracts' has no concrete shape markers", result.stdout)


class TestDesignLintCheck3AssumptionsCheckable(unittest.TestCase):
    def test_unresolvable_cited_path_is_named(self) -> None:
        self.assertIn("`src/server.py:20-22`", CLEAN_DOC)
        doc_text = CLEAN_DOC.replace("`src/server.py:20-22`", "`src/does-not-exist.py:20-22`", 1)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("assumption bullet cites a path that does not exist in the tree", result.stdout)
            self.assertIn("src/does-not-exist.py", result.stdout)

    def test_bullet_with_neither_tag_nor_path_is_named(self) -> None:
        bullet = (
            "- The handoff endpoint is implemented at `src/server.py:20-22`, which this\n"
            "  design confirms exists in the checkout.\n"
        )
        self.assertIn(bullet, CLEAN_DOC)
        untagged = "- The handoff endpoint is implemented sensibly, by design.\n"
        doc_text = CLEAN_DOC.replace(bullet, untagged)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("is neither interview-ruled", result.stdout)

    def test_absolute_and_traversal_citations_are_refused_not_crashed(self) -> None:
        """Premortem risk #4: an absolute or `../`-escaping citation must
        report as an unresolved path, never crash the resolver or
        (worse) resolve outside the given --repo."""
        bullet = (
            "- The handoff endpoint is implemented at `src/server.py:20-22`, which this\n"
            "  design confirms exists in the checkout.\n"
        )
        self.assertIn(bullet, CLEAN_DOC)
        escaping = (
            "- The handoff endpoint touches `/etc/passwd` and `../../../etc/hosts`,\n"
            "  both outside this checkout.\n"
        )
        doc_text = CLEAN_DOC.replace(bullet, escaping)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("does not exist in the tree", result.stdout)


class TestDesignLintCheck4ExperienceFailurePath(unittest.TestCase):
    def test_purely_happy_path_experience_is_named(self) -> None:
        failure_bullet = (
            "- If the review server fails to start, the QA tab stays on its current\n"
            "  cards and shows no crash — the handoff simply doesn't fire (see Risks).\n"
        )
        self.assertIn(failure_bullet, CLEAN_DOC)
        doc_text = CLEAN_DOC.replace(failure_bullet, "")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("section 'Experience' has no failure-path language", result.stdout)

    def test_genuine_failure_without_a_listed_token_is_still_rejected(self) -> None:
        """Premortem risk #3: Check 4's vocabulary is deliberately narrow.
        An Experience section that plainly describes a real failure path,
        but phrases it without any of the closed token list, is a known,
        accepted false negative — the mechanical check has no way to tell
        it apart from a genuinely happy-path-only section, and that's the
        documented trade-off, not a bug this story fixes."""
        failure_bullet = (
            "- If the review server fails to start, the QA tab stays on its current\n"
            "  cards and shows no crash — the handoff simply doesn't fire (see Risks).\n"
        )
        self.assertIn(failure_bullet, CLEAN_DOC)
        unlisted_failure_language = (
            "- Should the reviewer's laptop lose connectivity mid-session, the\n"
            "  browser tab simply sits idle until they reconnect and reload by hand.\n"
        )
        doc_text = CLEAN_DOC.replace(failure_bullet, unlisted_failure_language)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("section 'Experience' has no failure-path language", result.stdout)


class TestDesignLintCheck5ForkRulings(unittest.TestCase):
    def test_unruled_fork_is_named_by_number(self) -> None:
        ruled_clause = "a\n  call the interview confirmed after review."
        self.assertIn(ruled_clause, CLEAN_DOC)
        unruled_clause = "a\n  call the interview made after some discussion."
        doc_text = CLEAN_DOC.replace(ruled_clause, unruled_clause)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("fork q2 has no recorded ruling", result.stdout)


class TestDesignLintRevisionHistoryAndDividers(unittest.TestCase):
    def test_in_body_horizontal_rule_does_not_mis_slice_sections(self) -> None:
        """Premortem risk #5: parsing splits on `## ` headings alone, never
        on a `---` divider, so a horizontal rule used mid-section (not the
        Revision History trailer) must not disturb the section count or
        any other check's result."""
        risks_body = (
            "- If the handoff step forgets to call `/complete` on the QA server, the\n"
            "  process leaks — a correctness requirement, not an implementation detail.\n"
        )
        self.assertIn(risks_body, CLEAN_DOC)
        with_stray_rule = risks_body + "\n---\n\nA stray horizontal rule, not a Revision History trailer.\n"
        doc_text = CLEAN_DOC.replace(risks_body, with_stray_rule)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            doc = _write_doc(tmp_path, doc_text)

            result = run_script(doc, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("clean pass", result.stdout)


class TestDesignLintUsageErrors(unittest.TestCase):
    def test_unreadable_doc_path_is_a_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = _write_repo_with_server(tmp_path)
            missing_doc = tmp_path / "does-not-exist.md"

            result = run_script(missing_doc, repo)

            self.assertEqual(result.returncode, 2)
            self.assertIn("could not read", result.stderr)

    def test_non_directory_repo_is_a_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            doc = _write_doc(tmp_path, CLEAN_DOC)
            not_a_dir = tmp_path / "not-a-dir.txt"
            not_a_dir.write_text("nope\n", encoding="utf-8")

            result = run_script(doc, not_a_dir)

            self.assertEqual(result.returncode, 2)
            self.assertIn("is not a directory", result.stderr)


if __name__ == "__main__":
    sys.exit(unittest.main())
