"""Bounded date-only institutional listing observations must not become people data."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from starintel_doc.canonical import validate_document
from starintel_doc.store import validate_repository

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "digs/anarchist-violence/2026-10-10-columbus-election-official-listings"
spec = importlib.util.spec_from_file_location("columbus_listings_generator", PACKET_DIR / "generate-packet.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class ColumbusOfficialListingsPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads(generator.INPUT.read_text())
        cls.documents = [json.loads(line) for line in generator.OUTPUT.read_text().splitlines()]
        cls.by_id = {row["id"]: row for row in cls.documents}

    def test_strict_schema_unique_ids_and_no_people_or_membership_edges(self):
        self.assertEqual(len(self.by_id), 12)
        self.assertEqual(Counter(row["dtype"] for row in self.documents), {"url": 8, "finding": 4})
        for row in self.documents:
            validate_document(row)
            self.assertEqual(row["visibility"], "public")
            self.assertEqual(row["sensitivity"], "public")
            self.assertEqual(row["sourceKinds"], ["web"])

    def test_date_only_provenance_does_not_invent_exact_times(self):
        self.assertEqual(self.inputs["retrievalDate"], "2026-10-10")
        for row in self.documents:
            for field in ("fetchedAt", "sourceRetrievedAt", "collectedAt", "createdAt", "updatedAt", "observedAt", "discoveredAt"):
                self.assertNotIn(field, row)
            self.assertIn("2026-10-10; exact time not supplied", row["notes"])

    def test_supplied_source_urls_and_observations_are_preserved(self):
        for source in self.inputs["urls"]:
            row = self.by_id[generator.doc_id("url", source["key"])]
            self.assertEqual(row["url"], source["url"])
            self.assertEqual(row["sourceUrls"], [source["url"]])
            self.assertEqual(row["sources"], [])
            self.assertIn(source["observation"], row["notes"])

    def test_every_finding_matches_supplied_text_and_its_resolving_sources(self):
        urls = {row["key"]: row for row in self.inputs["urls"]}
        for finding in self.inputs["findings"]:
            row = self.by_id[generator.doc_id("finding", finding["key"])]
            self.assertEqual(row["title"], finding["title"])
            self.assertEqual(row["description"], finding["description"])
            self.assertEqual(row["sources"], row["evidence"])
            self.assertEqual(row["sourceUrls"], [urls[key]["url"] for key in finding["sources"]])
            for reference, url in zip(row["sources"], row["sourceUrls"], strict=True):
                target = self.by_id[reference["id"]]
                self.assertEqual(reference["schema"], "url")
                self.assertEqual(target["dtype"], reference["schema"])
                self.assertEqual(target["url"], url)

    def test_dated_partial_and_directory_only_caveats_remain_explicit(self):
        findings = {row["id"].removeprefix(f"starintel:finding:{generator.RUN_ID}-"): row for row in self.documents if row["dtype"] == "finding"}
        self.assertIn("2025", findings["ohio-voice-partners-2025"]["description"])
        self.assertIn("33", findings["ohio-voice-partners-2025"]["description"])
        self.assertIn("2026 partner roll and current membership were not confirmed", findings["ohio-voice-partners-2025"]["description"])
        self.assertIn("partial", findings["ovrc-partial-listing"]["description"])
        self.assertIn("five steering organizations", findings["ovrc-partial-listing"]["description"])
        self.assertIn("directory-link observations only", findings["governance-directory-links"]["description"])
        self.assertIn("No employee records were collected", findings["organization-linkedin-pages"]["description"])

    def test_packet_is_separate_from_original_ids_and_reproduces_exactly(self):
        original_packet = ROOT / "digs/anarchist-violence/2026-10-10-columbus-election-institutions/starintel-documents.jsonl"
        original_ids = {json.loads(line)["id"] for line in original_packet.read_text().splitlines()}
        self.assertFalse(original_ids & self.by_id.keys())
        packet, receipt = generator.generate()
        self.assertEqual(packet, generator.OUTPUT.read_bytes())
        self.assertEqual(receipt, generator.RECEIPT.read_bytes())
        receipt_value = json.loads(receipt)
        self.assertEqual(receipt_value["inputSha256"], hashlib.sha256(generator.INPUT.read_bytes()).hexdigest())
        self.assertEqual(receipt_value["recordIds"], [row["id"] for row in self.documents])

    def test_isolated_transactional_import_validates_all_records(self):
        with tempfile.TemporaryDirectory(prefix="columbus-official-listings-") as temporary:
            subprocess.run([
                sys.executable, str(ROOT / "scripts/starintel.py"), "import",
                str(generator.OUTPUT), "--root", temporary,
            ], cwd=ROOT, capture_output=True, text=True, check=True)
            result = validate_repository(Path(temporary))
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["documents"], 12)


if __name__ == "__main__":
    unittest.main()
