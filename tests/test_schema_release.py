from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "schema-release.py"
MANIFEST = ROOT / "schemas" / "starintel-doc-v0.9.0.manifest.json"


class SchemaReleaseTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def test_current_uses_release_version_not_base_schema_filename(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        result = self.run_script("current", "--json")
        state = json.loads(result.stdout)
        self.assertEqual(state["release_version"], manifest["release_version"])
        self.assertEqual(state["profile_version"], manifest["profile_version"])
        self.assertEqual(state["schema_version"], manifest["schema_version"])
        self.assertNotEqual(
            state["release_version"],
            state["schema_version"],
            "release and immutable base schema are intentionally distinct in the additive v0.9 line",
        )

    def test_next_is_patch_after_current_release(self) -> None:
        state = json.loads(self.run_script("current", "--json").stdout)
        major, minor, patch = (int(value) for value in state["release_version"].split("."))
        self.assertEqual(state["next_release_version"], f"{major}.{minor}.{patch + 1}")
        self.assertEqual(self.run_script("next").stdout.strip(), state["next_release_version"])

    def test_dry_run_bump_changes_nothing(self) -> None:
        state = json.loads(self.run_script("current", "--json").stdout)
        before = MANIFEST.read_bytes()
        result = self.run_script("bump", "--to", state["next_release_version"], "--dry-run")
        self.assertIn("No files changed.", result.stdout)
        self.assertEqual(MANIFEST.read_bytes(), before)

    def test_check_accepts_current_repository_state(self) -> None:
        result = self.run_script("check")
        self.assertIn("metadata is consistent", result.stdout)


if __name__ == "__main__":
    unittest.main()
