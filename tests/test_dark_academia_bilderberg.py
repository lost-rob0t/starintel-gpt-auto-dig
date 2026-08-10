from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from scrape_dark_academia_memberships import PersonRecord, Scraper


class FixtureScraper(Scraper):
    def __init__(self, html: str):
        super().__init__({"targets": []}, ROOT)
        self.html = html

    def fetch(self, url: str, *, allow_binary: bool = False) -> tuple[str, int, str]:
        return self.html, 200, url


class BilderbergParserRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = ROOT / "tests" / "fixtures" / "bilderberg_participants_split.html"
        cls.html = fixture.read_text(encoding="utf-8")
        cls.target = {
            "dataset": "bilderberg",
            "name": "Bilderberg Meetings",
            "org_id": "starintel:org:bilderberg-meetings",
        }

    def test_split_role_fragments_are_reconstructed(self) -> None:
        scraper = FixtureScraper(self.html)
        records = scraper.extract_bilderberg(
            self.target,
            "https://www.bilderbergmeetings.org/meetings/meeting-2023/participants-2023",
        )
        roles = {record.name: record.role for record in records}
        self.assertEqual(roles["Alex Karp"], "CEO, Palantir Technologies")
        self.assertEqual(
            roles["Jen Easterly"],
            "Director, Cybersecurity and Infrastructure Security Agency",
        )
        self.assertEqual(
            roles["José Luís Arnaut"],
            "Managing Partner, CMS Rui Pena & Arnaut",
        )
        self.assertEqual(roles["Nadia Calviño"], "President, European Investment Bank")

    def test_participant_role_always_maps_to_participant_in(self) -> None:
        scraper = FixtureScraper(self.html)
        records = scraper.extract_bilderberg(
            self.target,
            "https://www.bilderbergmeetings.org/meetings/meeting-2023/participants-2023",
        )
        self.assertTrue(records)
        self.assertTrue(all(scraper.relation_predicate(record) == "participant_in" for record in records))

    def test_non_participant_role_mapping_is_unchanged(self) -> None:
        scraper = FixtureScraper(self.html)
        record = PersonRecord(
            dataset="example",
            name="Example Person",
            role="CEO",
            organization_name="Example Org",
            organization_id="starintel:org:example",
            source_url="https://example.test/person",
            source_title="Example",
            role_category="leadership",
        )
        self.assertEqual(scraper.relation_predicate(record), "executive_of")


if __name__ == "__main__":
    unittest.main()
