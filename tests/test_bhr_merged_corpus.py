from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MERGE_DIR = REPO_ROOT / "digs/hunter-biden/2026-08-03-bhr-partners-merged"
SCRIPT_PATH = MERGE_DIR / "build-merged-corpus.py"
INDEX_PATH = MERGE_DIR / "packet-index.json"
ARBITRATION_TARGET_ID = "starintel:investigation-target:bhr-obtain-beijing-arbitration-award"


class BhrMergedCorpusTest(unittest.TestCase):
    def test_materializes_prior_packets_with_documented_revision_precedence(self) -> None:
        spec = importlib.util.spec_from_file_location("bhr_merged_corpus", SCRIPT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        merged_bytes, manifest = module.build(REPO_ROOT, INDEX_PATH)
        documents = [json.loads(line) for line in merged_bytes.splitlines()]
        arbitration_targets = [
            document for document in documents if document["_id"] == ARBITRATION_TARGET_ID
        ]

        self.assertTrue(merged_bytes.endswith(b"\n"))
        self.assertEqual(475, len(documents))
        self.assertEqual(11, manifest["packet_count"])
        self.assertEqual(476, manifest["raw_record_count"])
        self.assertEqual(475, manifest["record_count"])
        self.assertEqual(1, manifest["resolved_duplicate_ids"])
        self.assertEqual(
            {
                "investigation-target": 117,
                "org": 59,
                "person": 34,
                "relation": 202,
                "source": 63,
            },
            manifest["counts"],
        )
        self.assertEqual(1, len(arbitration_targets))
        self.assertEqual(
            "Obtain the December 25, 2025 Beijing arbitration award",
            arbitration_targets[0]["title"],
        )
        self.assertEqual(
            "explicit-documented-correction",
            manifest["duplicate_resolutions"][0]["method"],
        )
        self.assertEqual(64, len(manifest["sha256"]))


if __name__ == "__main__":
    unittest.main()
