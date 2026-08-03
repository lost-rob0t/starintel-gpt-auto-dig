from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MERGE_DIR = REPO_ROOT / "digs/hunter-biden/2026-08-03-bhr-partners-merged"
SCRIPT_PATH = MERGE_DIR / "build-merged-corpus.py"
INDEX_PATH = MERGE_DIR / "packet-index.json"


class BhrMergedCorpusTest(unittest.TestCase):
    def test_materializes_all_prior_packets_without_duplicates(self) -> None:
        spec = importlib.util.spec_from_file_location("bhr_merged_corpus", SCRIPT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        merged_bytes, manifest = module.build(REPO_ROOT, INDEX_PATH)

        self.assertTrue(merged_bytes.endswith(b"\n"))
        self.assertEqual(476, len(merged_bytes.splitlines()))
        self.assertEqual(11, manifest["packet_count"])
        self.assertEqual(476, manifest["record_count"])
        self.assertEqual(0, manifest["duplicate_ids"])
        self.assertEqual(
            {
                "investigation-target": 118,
                "org": 59,
                "person": 34,
                "relation": 202,
                "source": 63,
            },
            manifest["counts"],
        )
        self.assertEqual(64, len(manifest["sha256"]))


if __name__ == "__main__":
    unittest.main()
