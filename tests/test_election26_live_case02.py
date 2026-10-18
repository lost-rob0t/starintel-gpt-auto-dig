"""Official-source, nonpartisan election-administration case #2751/02."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from starintel_doc.canonical import validate_document

ROOT = Path(__file__).resolve().parents[1]
PACKET = (ROOT / "digs" / "election-26-test" /
          "2026-10-17-request-2751-live" / "02-election-administration.jsonl")
SOURCE_URLS = [
    "https://about.usps.com/postal-bulletin/2026/pb22701/html/cover_003.htm",
    "https://www.eac.gov/voters/register-and-vote-in-your-state",
]
EXPECTED_ID = "starintel:document:autodig-2751-case02-election-admin-20261017"


class Election26LiveCase02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        records = [json.loads(line) for line in PACKET.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        if len(records) != 1:
            raise AssertionError("Case 02 packet must contain exactly one document")
        cls.doc = records[0]

    def test_maintained_canonical_runtime(self) -> None:
        validate_document(self.doc)

    def test_id_dataset_and_release(self) -> None:
        self.assertEqual(self.doc["id"], EXPECTED_ID)
        self.assertEqual(self.doc["dataset"], "election-26-test")
        self.assertEqual(self.doc["dtype"], "document")
        self.assertEqual(self.doc["schemaVersion"], "0.10.1")

    def test_exact_two_official_sources(self) -> None:
        self.assertEqual(self.doc["sourceUrls"], SOURCE_URLS)
        self.assertEqual(len(self.doc["provenance"]["publisherStatements"]), 2)
        self.assertEqual(self.doc["extensions"]["autoDig"]["realSourcesReviewed"], 2)

    def test_date_and_jurisdiction_caveat(self) -> None:
        statements = self.doc["provenance"]["publisherStatements"]
        self.assertIn("November 3, 2026", statements[0]["observedClaim"])
        self.assertIn("States and territories", statements[1]["observedClaim"])
        self.assertIn("not assert a uniform", self.doc["notes"])
        self.assertIn("UNAVAILABLE", self.doc["provenance"]["sourceByteHashes"])

    def test_no_individual_voter_records(self) -> None:
        ext = self.doc["extensions"]["autoDig"]
        self.assertEqual(ext["caseId"], "02")
        self.assertEqual(ext["personLevelRecordsRetrieved"], 0)
        self.assertFalse(ext["syntheticFixture"])
        self.assertTrue(ext["noPersonProfiling"])
        self.assertTrue(ext["noPoliticalAdvocacy"])
        self.assertFalse(set(self.doc) & {"address", "email", "phone", "ssn", "voterId"})


if __name__ == "__main__":
    unittest.main()
