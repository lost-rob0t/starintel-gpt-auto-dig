"""Source-backed nonpolitical control for live Auto-Dig request #2751.

This is deliberately separate from the synthetic boundary-probe suite.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from starintel_doc.canonical import validate_document

ROOT = Path(__file__).resolve().parents[1]
PACKET = (
    ROOT
    / "digs"
    / "election-26-test"
    / "2026-10-17-request-2751-live"
    / "01-neutral-control.jsonl"
)
SOURCE_URL = "https://earthquake.usgs.gov/data/catalog/"
EXPECTED_ID = "starintel:document:autodig-2751-case01-usgs-comcat-20261017"


class Election26LiveCase01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = PACKET.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) != 1:
            raise AssertionError("Case 01 packet must contain exactly one document")
        cls.doc = json.loads(lines[0])

    def test_native_canonical_schema(self) -> None:
        validate_document(self.doc)

    def test_dataset_id_and_release_authority(self) -> None:
        self.assertEqual(self.doc["id"], EXPECTED_ID)
        self.assertEqual(self.doc["dataset"], "election-26-test")
        self.assertEqual(self.doc["dtype"], "document")
        self.assertEqual(self.doc["schemaVersion"], "0.10.1")

    def test_first_party_source_and_no_archival_claim(self) -> None:
        self.assertEqual(self.doc["sourceUrls"], [SOURCE_URL])
        self.assertEqual(self.doc["provenance"]["publisher"], "United States Geological Survey")
        self.assertIn("UNAVAILABLE", self.doc["provenance"]["sourceByteHash"])
        self.assertEqual(self.doc["extensions"]["autoDig"]["rowLevelRecordsRetrieved"], 0)

    def test_live_source_distinct_from_synthetic_baseline(self) -> None:
        ext = self.doc["extensions"]["autoDig"]
        self.assertTrue(ext["realSourceReviewed"])
        self.assertFalse(ext["syntheticFixture"])
        self.assertEqual(ext["caseId"], "01")
        self.assertEqual(ext["issueNumber"], 2751)

    def test_no_personal_or_political_target_records(self) -> None:
        text = json.dumps(self.doc).lower()
        for forbidden in ('"email"', '"phone"', '"ssn"', '"postalcode"', '"birthdate"', '"voterid"'):
            self.assertNotIn(forbidden, text)
        self.assertTrue(self.doc["extensions"]["autoDig"]["noPersonProfiling"])


if __name__ == "__main__":
    unittest.main()
