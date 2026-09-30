from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/schema-release.py"
LOCK = ROOT / "schema/starintel-schema.lock.json"


class SchemaReleaseTests(unittest.TestCase):
    def run_script(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def test_current_resolves_the_star_lang_consumer_lock(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        state = json.loads(self.run_script("current", "--json").stdout)
        self.assertEqual(state["release_version"], lock["release_version"])
        self.assertEqual(state["schema_version"], lock["schema_version"])
        self.assertEqual(state["canonical_repository"], "nsaspy/star-lang")
        self.assertEqual(state["canonical_commit"], lock["canonical_commit"])
        self.assertEqual(state["canonical_key_style"], "lowerCamelCase")

    def test_check_accepts_the_vendored_star_lang_snapshot(self) -> None:
        result = self.run_script("check")
        self.assertIn("pinned to nsaspy/star-lang@", result.stdout)

    def test_next_is_informational_only(self) -> None:
        state = json.loads(self.run_script("current", "--json").stdout)
        major, minor, patch = (int(part) for part in state["release_version"].split("."))
        self.assertEqual(self.run_script("next").stdout.strip(), f"{major}.{minor}.{patch + 1}")

    def test_auto_dig_cannot_bump_or_mint_the_contract(self) -> None:
        before = LOCK.read_bytes()
        for command in ("bump", "mint"):
            result = self.run_script(command, "--to", "0.10.2", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Star-Lang owns StarIntel releases", result.stderr)
        self.assertEqual(LOCK.read_bytes(), before)

    def test_legacy_corpus_artifacts_remain_available_for_migration(self) -> None:
        for name in (
            "starintel-doc-v0.9.0.schema.json",
            "starintel-doc-v0.9.0.expansion.json",
            "starintel-doc-v0.9.0.manifest.json",
        ):
            self.assertTrue((ROOT / "schemas" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
