from __future__ import annotations

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
MANIFEST = ROOT / "schemas" / "starintel-doc-v0.10.1.manifest.json"
LEGACY_MANIFEST = ROOT / "schemas" / "starintel-doc-v0.9.0.manifest.json"
LEGACY_EXPANSION = ROOT / "schemas" / "starintel-doc-v0.9.0.expansion.json"
RELEASE_FILES = (
    Path("schemas/starintel-doc-v0.10.1.manifest.json"),
    Path("schemas/starintel-doc-v0.10.1.schema.json"),
    Path("conformance/implementations.json"),
    Path("conformance/__init__.py"),
    Path("starintel_auto_dig.nimble"),
    Path("tests/test_operation_registry.py"),
    Path("conformance/fixtures.py"),
)


def canonical_hash(value: Any) -> str:
    import hashlib

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
        # The unified 0.10 line reunifies release and base schema versions;
        # the legacy 0.9 line kept them intentionally distinct.
        self.assertEqual(
            state["release_version"],
            state["schema_version"],
            "0.10.1 reunifies the release and base schema versions",
        )
        legacy = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
        self.assertNotEqual(legacy["release_version"], legacy["schema_version"])

    def test_legacy_0_9_artifacts_remain_available(self) -> None:
        for path in (
            LEGACY_MANIFEST,
            LEGACY_EXPANSION,
            ROOT / "schemas" / "starintel-doc-v0.9.0.schema.json",
            ROOT / "schemas" / "starintel-network-capture-v0.9.2.manifest.json",
        ):
            self.assertTrue(path.exists(), path)

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

    def test_real_bump_updates_release_and_profile(self) -> None:
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

            manifest = json.loads((root / "schemas" / "starintel-doc-v0.10.1.manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["release_version"], target)
            self.assertEqual(manifest["profile_version"], target)
            # Unified lines carry no active expansion registry.
            self.assertNotIn("expansion_registry_path", manifest)
            self.assertEqual(self.run_script("check", root=root).returncode, 0)

    def test_check_accepts_current_repository_state(self) -> None:
        result = self.run_script("check")
        self.assertIn("metadata is consistent", result.stdout)

    def test_mint_refuses_non_advancing_or_unprepared_target(self) -> None:
        state = json.loads(self.run_script("current", "--json").stdout)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in RELEASE_FILES:
                source = ROOT / relative
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            for target in (state["schema_version"], "0.10.0", "0.9.5"):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "--root", str(root), "mint", "--to", target],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertNotEqual(proc.returncode, 0, target)


if __name__ == "__main__":
    unittest.main()
