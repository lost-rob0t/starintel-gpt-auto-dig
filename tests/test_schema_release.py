from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "schema-release.py"
MANIFEST = ROOT / "schemas" / "starintel-doc-v0.9.0.manifest.json"
EXPANSION = ROOT / "schemas" / "starintel-doc-v0.9.0.expansion.json"
RELEASE_FILES = (
    Path("schemas/starintel-doc-v0.9.0.manifest.json"),
    Path("schemas/starintel-doc-v0.9.0.expansion.json"),
    Path("conformance/implementations.json"),
    Path("conformance/__init__.py"),
    Path("starintel_auto_dig.nimble"),
    Path("tests/test_operation_registry.py"),
    Path("conformance/fixtures.py"),
)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SchemaReleaseTests(unittest.TestCase):
    def run_script(self, *args: str, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), *args],
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

    def test_real_bump_updates_release_profile_and_expansion_hash(self) -> None:
        state = json.loads(self.run_script("current", "--json").stdout)
        target = state["next_release_version"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in RELEASE_FILES:
                source = ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

            result = self.run_script("bump", "--to", target, root=root)
            self.assertIn(f"updated StarIntel release to {target}", result.stdout)

            manifest = json.loads((root / MANIFEST.relative_to(ROOT)).read_text(encoding="utf-8"))
            expansion = json.loads((root / EXPANSION.relative_to(ROOT)).read_text(encoding="utf-8"))
            self.assertEqual(manifest["release_version"], target)
            self.assertEqual(manifest["profile_version"], target)
            self.assertEqual(expansion["profile_version"], target)
            self.assertNotIn("release_version", expansion)
            self.assertEqual(manifest["expansion_content_hash"], canonical_hash(expansion))
            self.assertEqual(self.run_script("check", root=root).returncode, 0)

    def test_check_accepts_current_repository_state(self) -> None:
        result = self.run_script("check")
        self.assertIn("metadata is consistent", result.stdout)


if __name__ == "__main__":
    unittest.main()
