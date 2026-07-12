"""Regression tests for scripts/worktree-setup (story build-scripts, issue #14).

Exercises the script against a throwaway git repo (`tests/_tempgit.py`),
never the real jig repo or this story's own worktree, checking this story's
acceptance criteria mechanically:

1. Happy path: a green baseline creates the branch + worktree and exits 0.
2. Dirty baseline: a failing baseline command stops before returning
   success, frames the failure as pre-existing (not caused by this build
   session), names the failing command, and leaves the worktree in place
   for inspection (docs/studious/premortems/build-scripts.md, risk #3).
3. Collision: re-running against an existing branch/worktree fails loudly
   with the exact remediation command to retry (risk #2), rather than
   silently reusing stale state.
4. Not a git repo: refuses with a usage error rather than a traceback.

Run with:

    uv run --no-project python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _tempgit import init_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "worktree-setup"

PASS_CMD = "python3 -c 'pass'"
FAIL_CMD = "python3 -c 'import sys; sys.exit(1)'"


def run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, timeout=30, check=False)


class TestWorktreeSetupHappyPath(unittest.TestCase):
    def test_green_baseline_creates_branch_and_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            worktree = Path(tmp) / "wt"

            result = run_script(
                ["--repo", str(repo), "--branch", "feature-x", "--path", str(worktree), "--baseline", PASS_CMD]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(worktree.is_dir())
            branches = subprocess.run(
                ["git", "-C", str(repo), "branch", "--list", "feature-x"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertIn("feature-x", branches.stdout)


class TestWorktreeSetupDirtyBaseline(unittest.TestCase):
    def test_failing_baseline_stops_and_frames_as_pre_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            worktree = Path(tmp) / "wt"

            result = run_script(
                ["--repo", str(repo), "--branch", "feature-y", "--path", str(worktree), "--baseline", FAIL_CMD]
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BASELINE FAILURE", result.stderr)
            self.assertIn("pre-existing", result.stderr)
            self.assertIn(FAIL_CMD, result.stderr)
            # Left in place for inspection, not deleted (Alternatives considered #3).
            self.assertTrue(worktree.is_dir())


class TestWorktreeSetupCollision(unittest.TestCase):
    def test_rerun_with_same_branch_fails_loud_with_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo)
            worktree = Path(tmp) / "wt"

            first = run_script(
                ["--repo", str(repo), "--branch", "feature-z", "--path", str(worktree), "--baseline", PASS_CMD]
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = run_script(
                ["--repo", str(repo), "--branch", "feature-z", "--path", str(worktree), "--baseline", PASS_CMD]
            )

            self.assertNotEqual(second.returncode, 0)
            self.assertIn("collision", second.stderr)
            self.assertIn("worktree remove", second.stderr)
            self.assertIn(str(worktree), second.stderr)
            self.assertIn("branch -D feature-z", second.stderr)


class TestWorktreeSetupNotAGitRepo(unittest.TestCase):
    def test_refuses_when_repo_arg_is_not_a_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            not_repo = Path(tmp) / "not-a-repo"
            not_repo.mkdir()
            worktree = Path(tmp) / "wt"

            result = run_script(
                ["--repo", str(not_repo), "--branch", "feature-w", "--path", str(worktree), "--baseline", PASS_CMD]
            )

            self.assertEqual(result.returncode, 2)
            self.assertFalse(worktree.exists())


if __name__ == "__main__":
    sys.exit(unittest.main())
