from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "scrape_tsc_job_postings.py"
SPEC = importlib.util.spec_from_file_location("scrape_tsc_job_postings", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TscJobPostingCollectorTests(unittest.TestCase):
    def test_html_to_text_removes_markup(self) -> None:
        self.assertEqual(
            "Identity resolution & threat screening",
            MODULE.html_to_text("<p>Identity <b>resolution</b> &amp; threat screening</p>"),
        )

    def test_normalize_and_match_public_posting(self) -> None:
        raw = {
            "id": "posting-1",
            "text": "Intelligence Analyst II",
            "description": "<p>Requisition #: 1645</p>",
            "lists": [
                {
                    "text": "Mission",
                    "content": "<p>Identity resolution, threat screening, and biometric data.</p>",
                }
            ],
            "categories": {
                "location": "Vienna, VA",
                "team": "Intelligence Analysis",
                "department": "Mission Services",
                "commitment": "Regular",
                "allLocations": ["Vienna, VA"],
            },
            "workplaceType": "onsite",
            "hostedUrl": "https://jobs.lever.co/agile-defense/posting-1",
            "applyUrl": "https://jobs.lever.co/agile-defense/posting-1/apply",
        }
        posting = MODULE.normalized_posting(raw)
        terms, locations = MODULE.match_posting(
            posting,
            terms=["identity resolution", "threat screening", "unmatched"],
            locations=["Vienna, VA"],
        )
        self.assertEqual(["identity resolution", "threat screening"], terms)
        self.assertEqual(["Vienna, VA"], locations)
        self.assertEqual(["1645"], MODULE.extract_requisition_codes(posting))
        self.assertEqual("Mission Services", posting["categories"]["department"])
        self.assertNotIn("applicationQuestions", posting)

    def test_listing_url_validates_site_slug(self) -> None:
        url = MODULE.listing_url("agile-defense", skip=100, limit=50)
        self.assertIn("/agile-defense?", url)
        self.assertIn("mode=json", url)
        self.assertIn("skip=100", url)
        self.assertIn("limit=50", url)
        with self.assertRaises(ValueError):
            MODULE.listing_url("https://example.com", skip=0, limit=100)

    def test_location_match_can_retain_posting_without_mission_term(self) -> None:
        posting = MODULE.normalized_posting(
            {
                "id": "posting-2",
                "text": "Mission Support",
                "categories": {"location": "Vienna, Virginia"},
            }
        )
        terms, locations = MODULE.match_posting(
            posting,
            terms=["threat screening"],
            locations=["Vienna, Virginia"],
        )
        self.assertEqual([], terms)
        self.assertEqual(["Vienna, Virginia"], locations)

    def test_jsonl_output_is_deterministic_and_deduplicated(self) -> None:
        records = [
            {
                "site": "agile-defense",
                "posting_id": "b",
                "sha256": "b" * 64,
                "payload": {"title": "B"},
            },
            {
                "site": "agile-defense",
                "posting_id": "a",
                "sha256": "a" * 64,
                "payload": {"title": "A"},
            },
        ]
        records.append(dict(records[0]))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "jobs.jsonl"
            self.assertEqual(2, MODULE.write_jsonl(records, output))
            rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(["a", "b"], [row["posting_id"] for row in rows])


if __name__ == "__main__":
    unittest.main()
