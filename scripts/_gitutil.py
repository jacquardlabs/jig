"""Shared git-shelling helpers for jig's build scripts.

`worktree-setup`, `verify`, and `evidence-capture` (story build-scripts,
issue #14) each need to ask a repository the same handful of questions —
its top-level path, whether it has uncommitted changes, its last commit's
sha/timestamp. Previously each script would have defined its own copy;
this module is the one place it lives, mirroring the `tests/_frontmatter.py`
/ `tests/_vocabulary.py` leading-underscore "shared, not itself collected"
convention already established in this repo.

Not a package, not importable from outside `scripts/` — each script adds
its own directory to `sys.path` before importing this (see any script's
top for the pattern). Deliberately dependency-free (standard library only)
so each script stays a standalone CLI tool per `docs/design/build-scripts.md`.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 600.0
"""Shared generous default for the --timeout of `worktree-setup`'s baseline
command and `verify`'s command-tier items (issue #49) -- the same value in
both, so they don't drift apart. Suites legitimately run minutes; a hung
command (waiting on stdin, deadlocked, network-bound with no timeout of its
own) should still be killed well short of hanging a session indefinitely."""


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command, capturing output as text, never raising on non-zero exit."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def git_repo_root(path: Path) -> Path | None:
    """Resolve `path` to its enclosing git repo's top-level directory, or None."""
    try:
        result = run(["git", "rev-parse", "--show-toplevel"], cwd=path)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def working_tree_status(repo: Path) -> str:
    """Return `git status --porcelain` output for `repo` (empty string = clean)."""
    return run(["git", "-C", str(repo), "status", "--porcelain"]).stdout


def last_commit_sha_and_epoch(repo: Path) -> tuple[str, float] | None:
    """Return (sha, commit-timestamp-as-epoch-seconds) for HEAD in `repo`, or None."""
    result = run(["git", "-C", str(repo), "log", "-1", "--format=%H%x09%ct"])
    if result.returncode != 0 or not result.stdout.strip():
        return None
    sha, _, epoch_str = result.stdout.strip().partition("\t")
    return sha, float(epoch_str)


def resolve_revision_epoch(repo: Path, revision: str) -> float | None:
    """Resolve a git revision (branch, tag, sha) to its commit timestamp, or None."""
    result = run(["git", "-C", str(repo), "show", "-s", "--format=%ct", revision])
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return float(result.stdout.strip())


def branch_exists(repo: Path, branch: str) -> bool:
    return run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"]).returncode == 0


def is_ancestor(repo: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    """Whether `ancestor` is an ancestor of (or equal to) `descendant` in
    `repo`. False for an unresolvable/orphaned `ancestor` -- never raises,
    so a caller checking freshness against a since-rewritten commit gets a
    plain FAIL rather than an exception."""
    return run(["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def worktree_registered(repo: Path, path: Path) -> bool:
    """Whether `path` is already registered as a worktree of `repo`."""
    result = run(["git", "-C", str(repo), "worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return False
    target = path.resolve()
    for line in result.stdout.splitlines():
        if line.startswith("worktree ") and Path(line[len("worktree ") :]).resolve() == target:
            return True
    return False
