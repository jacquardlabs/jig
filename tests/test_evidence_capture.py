"""Regression tests for scripts/evidence-capture (story build-scripts, issue #14).

Exercises the script against a throwaway git repo (`tests/_tempgit.py`),
never the real jig repo, checking this story's acceptance criteria
mechanically:

1. Happy path: artifacts + a manifest.json land in
   `docs/jig/evidence/<date>-<task>/`, stamped `>=` the last code commit.
2. An uncommitted working tree at capture time refuses rather than
   stamping a vacuous `now >= baseline-commit` timestamp
   (docs/studious/premortems/build-scripts.md, risk #1).
3. An artifact whose own mtime predates the last commit (copied forward
   from a prior attempt) is refused even when the tree is otherwise clean
   (same premortem doc, risk #1's second defense).
4. Re-running against an existing evidence directory refuses without
   `--force`.

Run with:

    uv run --no-project python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from _tempgit import init_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "evidence-capture"


def run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, timeout=30, check=False)


class TestEvidenceCaptureHappyPath(unittest.TestCase):
    def test_writes_artifacts_and_freshness_stamped_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)

            # Artifact must postdate the commit — sleep past filesystem mtime granularity.
            time.sleep(0.05)
            artifact = Path(tmp) / "verify-output.txt"
            artifact.write_text("[PASS] item 1\noverall=PASS\n", encoding="utf-8")

            evidence_root = Path(tmp) / "evidence"
            result = run_script(
                [
                    "--task",
                    "task-1",
                    "--repo",
                    str(repo),
                    "--date",
                    "2026-07-12",
                    "--evidence-root",
                    str(evidence_root),
                    "--artifact",
                    f"verify:results={artifact}",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            target_dir = evidence_root / "2026-07-12-task-1"
            self.assertTrue(target_dir.is_dir())
            manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["task"], "task-1")
            self.assertEqual(manifest["date"], "2026-07-12")
            self.assertIn("commit_sha", manifest)
            self.assertEqual(len(manifest["artifacts"]), 1)
            self.assertEqual(manifest["artifacts"][0]["producer"], "verify")
            self.assertEqual(manifest["artifacts"][0]["label"], "results")
            self.assertTrue((target_dir / manifest["artifacts"][0]["path"]).is_file())
            self.assertGreaterEqual(manifest["captured_at"], manifest["commit_timestamp"])


class TestEvidenceCaptureFreshnessRefusals(unittest.TestCase):
    def test_refuses_when_working_tree_is_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            # Uncommitted change — the quick-path case risk #1 names.
            (repo / "uncommitted.txt").write_text("wip\n", encoding="utf-8")

            artifact = Path(tmp) / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")

            result = run_script(
                [
                    "--task",
                    "task-1",
                    "--repo",
                    str(repo),
                    "--evidence-root",
                    str(Path(tmp) / "evidence"),
                    "--artifact",
                    f"verify:results={artifact}",
                ]
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("uncommitted", result.stderr)

    def test_refuses_when_artifact_predates_last_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)

            # Artifact created, then made to look older than the commit it's
            # supposed to evidence (copied-forward-from-a-prior-attempt shape).
            artifact = Path(tmp) / "stale-artifact.txt"
            artifact.write_text("old evidence\n", encoding="utf-8")
            long_ago = time.time() - 3600
            os.utime(artifact, (long_ago, long_ago))

            result = run_script(
                [
                    "--task",
                    "task-1",
                    "--repo",
                    str(repo),
                    "--evidence-root",
                    str(Path(tmp) / "evidence"),
                    "--artifact",
                    f"verify:results={artifact}",
                ]
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("stale", result.stderr)
            self.assertIn(str(artifact), result.stderr)


class TestEvidenceCaptureCollision(unittest.TestCase):
    def test_refuses_to_overwrite_existing_directory_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            time.sleep(0.05)
            artifact = Path(tmp) / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")
            evidence_root = Path(tmp) / "evidence"

            args = [
                "--task",
                "task-1",
                "--repo",
                str(repo),
                "--date",
                "2026-07-12",
                "--evidence-root",
                str(evidence_root),
                "--artifact",
                f"verify:results={artifact}",
            ]
            first = run_script(args)
            self.assertEqual(first.returncode, 0, first.stderr)

            second = run_script(args)
            self.assertEqual(second.returncode, 2)
            self.assertIn("--force", second.stderr)

            third = run_script([*args, "--force"])
            self.assertEqual(third.returncode, 0, third.stderr)


class TestEvidenceCaptureUsageErrors(unittest.TestCase):
    def test_missing_artifact_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            missing = Path(tmp) / "does-not-exist.txt"

            result = run_script(
                [
                    "--task",
                    "task-1",
                    "--repo",
                    str(repo),
                    "--evidence-root",
                    str(Path(tmp) / "evidence"),
                    "--artifact",
                    f"verify:results={missing}",
                ]
            )
            self.assertEqual(result.returncode, 2)

    def test_task_id_with_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            artifact = Path(tmp) / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")

            result = run_script(
                [
                    "--task",
                    "../../etc",
                    "--repo",
                    str(repo),
                    "--evidence-root",
                    str(Path(tmp) / "evidence"),
                    "--artifact",
                    f"verify:results={artifact}",
                ]
            )
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    sys.exit(unittest.main())
