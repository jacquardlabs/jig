"""Regression tests for scripts/verify (story build-scripts, issue #14).

Checks this story's acceptance criteria mechanically:

1. `script` / `test-backed` items independently re-run their own named
   command and PASS/FAIL on its exit code.
2. `probe` items PASS only when the supplied artifact exists, is
   non-empty, isn't older than `--since`, and (if given) matches the
   expected pattern.
3. Per-item results are always reported, not collapsed into one boolean;
   overall PASS requires every item to PASS.
4. Fails closed: an empty or malformed items document is a usage error
   (exit 2), never a vacuous PASS (docs/studious/premortems/
   build-scripts.md, risk #4).
5. A `probe` item without `--since` is also a usage error — the recency
   floor is verify's own, not merely delegated to `evidence-capture`
   (same premortem doc, risk #5).

Run with:

    uv run --no-project python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify"


def run_script(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, timeout=30, check=False)


def write_items(tmp: Path, items: list[dict], task: str = "task-1") -> Path:
    path = tmp / "items.json"
    path.write_text(json.dumps({"task": task, "items": items}), encoding="utf-8")
    return path


class TestVerifyCommandTiers(unittest.TestCase):
    def test_script_item_passes_on_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp), [{"id": 1, "kind": "cap", "tier": "script", "command": "python3 -c 'pass'"}]
            )
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("[PASS] item 1", result.stdout)
            self.assertIn("overall=PASS", result.stdout)

    def test_script_item_fails_on_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp),
                [{"id": 1, "kind": "hold", "tier": "script", "command": "python3 -c 'import sys; sys.exit(3)'"}],
            )
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("[FAIL] item 1", result.stdout)
            self.assertIn("overall=FAIL", result.stdout)

    def test_test_backed_item_runs_named_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp),
                [{"id": 1, "kind": "cap", "tier": "test-backed", "command": "python3 -c 'assert 1 + 1 == 2'"}],
            )
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_items_must_pass_for_overall_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp),
                [
                    {"id": 1, "kind": "cap", "tier": "script", "command": "python3 -c 'pass'"},
                    {"id": 2, "kind": "hold", "tier": "script", "command": "python3 -c 'import sys; sys.exit(1)'"},
                ],
            )
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("[PASS] item 1", result.stdout)
            self.assertIn("[FAIL] item 2", result.stdout)


class TestVerifyProbeTier(unittest.TestCase):
    def test_probe_item_passes_when_artifact_fresh_and_matches_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            artifact = Path(tmp) / "ps-check.txt"
            artifact.write_text("no orphaned process found\n", encoding="utf-8")
            items_path = write_items(
                Path(tmp),
                [{"id": 1, "kind": "cap", "tier": "probe", "artifact": str(artifact), "pattern": "no orphaned process"}],
            )
            result = run_script(["--items", str(items_path), "--since", since])
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_probe_item_fails_when_artifact_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            missing = Path(tmp) / "does-not-exist.txt"
            items_path = write_items(Path(tmp), [{"id": 1, "kind": "cap", "tier": "probe", "artifact": str(missing)}])
            result = run_script(["--items", str(items_path), "--since", since])
            self.assertEqual(result.returncode, 1)
            self.assertIn("not found", result.stdout)

    def test_probe_item_fails_when_artifact_predates_since(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "stale.txt"
            artifact.write_text("stale evidence\n", encoding="utf-8")
            since = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            items_path = write_items(Path(tmp), [{"id": 1, "kind": "cap", "tier": "probe", "artifact": str(artifact)}])
            result = run_script(["--items", str(items_path), "--since", since])
            self.assertEqual(result.returncode, 1)
            self.assertIn("stale", result.stdout)

    def test_probe_item_without_since_is_a_usage_error_not_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "artifact.txt"
            artifact.write_text("content\n", encoding="utf-8")
            items_path = write_items(Path(tmp), [{"id": 1, "kind": "cap", "tier": "probe", "artifact": str(artifact)}])
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 2)
            self.assertIn("--since", result.stderr)
            self.assertNotIn("PASS", result.stdout)


class TestVerifyFailsClosed(unittest.TestCase):
    def test_empty_items_list_is_a_usage_error_not_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(Path(tmp), [])
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 2)
            self.assertIn("no items to verify", result.stderr)
            self.assertNotIn("PASS", result.stdout)

    def test_unknown_tier_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp), [{"id": 1, "kind": "cap", "tier": "judgment", "command": "python3 -c 'pass'"}]
            )
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 2)
            self.assertIn("tier", result.stderr)

    def test_missing_command_for_script_tier_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(Path(tmp), [{"id": 1, "kind": "cap", "tier": "script"}])
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 2)

    def test_malformed_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = Path(tmp) / "items.json"
            items_path.write_text("not json", encoding="utf-8")
            result = run_script(["--items", str(items_path)])
            self.assertEqual(result.returncode, 2)


class TestVerifyOutput(unittest.TestCase):
    def test_writes_json_results_when_out_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items_path = write_items(
                Path(tmp), [{"id": 1, "kind": "cap", "tier": "script", "command": "python3 -c 'pass'"}]
            )
            out_path = Path(tmp) / "results.json"
            result = run_script(["--items", str(items_path), "--out", str(out_path)])
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["overall"], "PASS")
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["status"], "PASS")


if __name__ == "__main__":
    sys.exit(unittest.main())
