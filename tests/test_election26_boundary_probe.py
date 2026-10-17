"""Regression check for the isolated, synthetic election-26 boundary benchmark.

These are not verified FEC facts and are not a production dataset import.
GitHub write acceptance is observed separately from this schema test.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from starintel_doc.canonical import validate_document

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "01-neutral-control": 1,
    "02-civic-procedure": 2,
    "03-fec-committee-registry": 5,
    "04-org-to-org-finance": 10,
    "05-receipt-amendment-reversal": 15,
    "06-independent-expenditures": 24,
    "07-public-lobbying-procurement": 35,
    "08-public-speech-news": 50,
    "09-civic-group-relations": 75,
    "10-cross-category-load": 120,
}
DATA = ROOT / "digs" / "election-26-test" / "2026-10-17-boundary-probe"
FORBIDDEN_KEYS = frozenset({
    "address", "addresses", "postalAddress", "postalCode", "zipCode",
    "zip", "zip_code", "ssn", "phone", "phones", "email", "emails",
    "dateOfBirth", "birthDate", "preciseLocation", "coordinates",
})


def load_case(slug: str) -> list[dict]:
    with (DATA / f"{slug}.ndjson").open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def nested_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(nested_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(nested_keys(child))
        return keys
    return set()


class Election26BoundaryProbeTests(unittest.TestCase):
    def test_all_ten_cases_are_complete_canonical_synthetic_records(self) -> None:
        seen: set[str] = set()
        self.assertEqual(
            {p.stem for p in DATA.glob("*.ndjson")},
            set(CASES),
        )
        for slug, expected in CASES.items():
            with self.subTest(case=slug):
                records = load_case(slug)
                self.assertEqual(len(records), expected)
                available = {doc["id"]: doc["dtype"] for doc in records}
                self.assertEqual(len(available), expected)
                for doc in records:
                    validate_document(doc)
                    self.assertEqual(doc["schemaVersion"], "0.10.1")
                    self.assertEqual(doc["dataset"], "election-26-test")
                    self.assertEqual(doc["visibility"], "public")
                    self.assertNotIn(doc["id"], seen)
                    seen.add(doc["id"])
                    fixture = doc["extensions"]["boundary.fixture"]
                    self.assertIs(fixture["synthetic"], True)
                    self.assertIs(fixture["fixtureOnly"], True)
                    self.assertEqual(fixture["caseId"], slug[:2])
                    self.assertTrue(fixture["taskPrompt"])
                    self.assertFalse(nested_keys(doc) & FORBIDDEN_KEYS)
                    if doc["dtype"] == "relation":
                        for endpoint in (doc["source"], doc["destination"]):
                            self.assertEqual(available.get(endpoint["id"]), endpoint["schema"])
        self.assertEqual(len(seen), 337)


if __name__ == "__main__":
    unittest.main()
