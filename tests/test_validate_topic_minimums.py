#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-for-merge.py"
SPEC = importlib.util.spec_from_file_location("validate_for_merge", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TopicMinimumValidationTest(unittest.TestCase):
    def test_parse_topic_minimums(self) -> None:
        self.assertEqual(
            MODULE.parse_topic_minimums(["GOP=100000", "dnc=50000"]),
            {"gop": 100000, "dnc": 50000},
        )

    def test_conflicting_minimums_fail(self) -> None:
        with self.assertRaises(RuntimeError):
            MODULE.parse_topic_minimums(["gop=100000", "GOP=100001"])

    def test_generated_topic_manifest_count_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="topic-minimum-test-") as tmp:
            site = Path(tmp)
            downloads = site / "dataset-gop" / "downloads"
            downloads.mkdir(parents=True)
            manifest = downloads / "topic-manifest.json"
            manifest.write_text(
                json.dumps({"topic_dataset": "gop", "record_count": 100000}) + "\n",
                encoding="utf-8",
            )

            MODULE.validate_topic_minimums(site, {"gop": 100000})
            with self.assertRaises(RuntimeError):
                MODULE.validate_topic_minimums(site, {"gop": 100001})

    def test_missing_topic_manifest_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="topic-minimum-test-") as tmp:
            with self.assertRaises(RuntimeError):
                MODULE.validate_topic_minimums(Path(tmp), {"gop": 1})


if __name__ == "__main__":
    unittest.main()
