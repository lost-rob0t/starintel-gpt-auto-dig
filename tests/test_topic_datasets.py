from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "starintel_site" / "topic_datasets.py"
SPEC = importlib.util.spec_from_file_location("topic_datasets", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TopicDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "excluded_source_datasets": ["daily"],
            "topics": [
                {
                    "id": "wef",
                    "title": "WEF",
                    "match": {"targets": ["wef"], "terms": ["world economic forum"]},
                },
                {
                    "id": "ohio",
                    "title": "Ohio",
                    "match": {"targets": ["ohio", "columbus"], "terms": ["ohio"]},
                },
            ],
        }

    def test_wef_packets_merge_into_wef(self) -> None:
        topics = MODULE.topics_for_document("global-wef-network", {"dataset": "daily", "title": "World Economic Forum"}, self.config)
        self.assertEqual("wef", topics[0]["id"])

    def test_ohio_terms_merge_across_targets(self) -> None:
        topics = MODULE.topics_for_document("flock-safety", {"dataset": "flock", "summary": "Columbus, Ohio contract"}, self.config)
        self.assertEqual("ohio", topics[0]["id"])

    def test_unmatched_target_gets_its_own_topic(self) -> None:
        topics = MODULE.topics_for_document("palantir", {"dataset": "contracts", "title": "Palantir"}, self.config)
        self.assertEqual("palantir", topics[0]["id"])

    def test_daily_is_excluded_from_source_catalog(self) -> None:
        self.assertTrue(MODULE.excluded_source_dataset("daily", self.config))
        self.assertFalse(MODULE.excluded_source_dataset("wef", self.config))


if __name__ == "__main__":
    unittest.main()
