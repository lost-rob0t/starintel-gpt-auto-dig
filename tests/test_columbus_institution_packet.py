"""Regression checks for the bounded published-wire institutional adaptation."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from starintel_doc.canonical import DOCUMENT_TYPES, validate_document
from starintel_doc.store import packet_paths, validate_repository


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "digs/anarchist-violence/2026-10-10-columbus-election-institutions"
spec = importlib.util.spec_from_file_location("columbus_packet_generator", PACKET_DIR / "generate-packet.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class ColumbusInstitutionPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = generator.original_records()
        cls.documents = [json.loads(line) for line in generator.PACKET.read_text().splitlines()]
        cls.by_id = {row["id"]: row for row in cls.documents}
        cls.receipt = json.loads(generator.RECEIPT.read_text())

    def test_original_archive_is_byte_exact_and_not_a_canonical_packet(self):
        self.assertEqual(hashlib.sha256(generator.ARCHIVE.read_bytes()).hexdigest(), generator.ARCHIVE_SHA256)
        self.assertNotIn(generator.ARCHIVE, packet_paths(ROOT))
        self.assertNotIn(PACKET_DIR, generator.ARCHIVE.parents)
        self.assertEqual(len(self.original), 13)

    def test_all_ids_and_supported_dtypes_are_preserved_or_deliberately_mapped(self):
        self.assertEqual(len(self.by_id), 13)
        self.assertEqual(set(self.by_id), {row["id"] for row in self.original})
        self.assertEqual(Counter(row["dtype"] for row in self.documents), {"url": 5, "org": 6, "relation": 1, "finding": 1})
        for document in self.documents:
            self.assertIn(document["dtype"], DOCUMENT_TYPES)
            validate_document(document)
            self.assertEqual(document["schemaVersion"], "0.10.1")
            self.assertNotIn("data", document)
            for opaque in ("extensions", "raw", "rawContent", "metadata", "provenance"):
                self.assertNotIn(opaque, document)

    def test_unchanged_org_relation_facts_and_shared_provenance(self):
        common = ("id", "dataset", "collectedAt", "collectionMethod", "collector", "confidence", "notes", "runId", "sourceUrls")
        for original in self.original:
            document = self.by_id[original["id"]]
            for key in common:
                self.assertEqual(document[key], original[key], (original["id"], key))
            if original["dtype"] in {"org", "relation"}:
                for key, value in original.items():
                    self.assertEqual(document[key], value, (original["id"], key))

    def test_webpage_fields_and_exact_retrieval_precision_have_an_explicit_home(self):
        for original in self.original:
            if original["dtype"] != "source":
                continue
            document = self.by_id[original["id"]]
            seconds = int(datetime.fromisoformat(original["retrievedAt"].replace("Z", "+00:00")).timestamp())
            self.assertEqual(document["url"], original["url"])
            self.assertEqual(document["contentTitle"], original["title"])
            self.assertEqual(document["fetchedAt"], seconds)
            self.assertEqual(document["sourceRetrievedAt"], seconds)
            self.assertEqual(document["sources"], [])
            for unsupported in ("accessMethod", "kind", "retrievedAt", "title"):
                self.assertNotIn(unsupported, document)
                self.assertIn(unsupported, original)

    def test_review_result_and_all_supporting_observations_survive(self):
        original = next(row for row in self.original if row["dtype"] == "research-pass")
        document = self.by_id[original["id"]]
        self.assertEqual(document["title"], original["researchQuestion"])
        self.assertEqual(document["description"], original["findings"][0]["description"])
        self.assertEqual(document["status"], original["status"])
        self.assertEqual([ref["id"] for ref in document["evidence"]], original["supportingRecordIds"])
        self.assertEqual(len(document["evidence"]), 12)
        for field in generator.REVIEW_ONLY:
            self.assertNotIn(field, document)
            self.assertIn(field, original)

    def test_all_references_resolve_to_the_correct_dtype_and_supporting_url(self):
        generator.validate_references(self.documents)
        for document in self.documents:
            if document["dtype"] == "url":
                continue
            supported_urls = [self.by_id[ref["id"]]["url"] for ref in document["sources"]]
            self.assertEqual(supported_urls, document["sourceUrls"])
            self.assertTrue(document["sources"])

    def test_added_metadata_is_public_and_uses_the_original_collection_time(self):
        for document in self.documents:
            self.assertEqual(document["createdAt"], document["collectedAt"])
            self.assertEqual(document["updatedAt"], document["collectedAt"])
            self.assertEqual(document["sourceKinds"], ["web"])
            self.assertEqual(document["visibility"], "public")
            self.assertEqual(document["sensitivity"], "public")

    def test_receipt_accounts_for_every_original_field(self):
        self.assertEqual(self.receipt["originalSha256"], generator.ARCHIVE_SHA256)
        self.assertEqual(self.receipt["canonicalSha256"], hashlib.sha256(generator.PACKET.read_bytes()).hexdigest())
        for original, receipt in zip(self.original, self.receipt["records"], strict=True):
            self.assertEqual(original["id"], receipt["id"])
            mapped = {key.split("[")[0] for key in receipt["mappedFields"]}
            accounted = set(receipt["preservedFields"]) | set(receipt["archiveOnlyFields"]) | mapped | {"dtype"}
            self.assertEqual(set(original), accounted, original["id"])

    def test_cli_reproduction_matches_committed_artifact_bytes(self):
        packet, receipt = generator.generate()
        self.assertEqual(packet, generator.PACKET.read_bytes())
        self.assertEqual(receipt, generator.RECEIPT.read_bytes())

    def test_transactional_import_only_in_an_isolated_temporary_database(self):
        with tempfile.TemporaryDirectory(prefix="columbus-institution-packet-") as temporary:
            subprocess.run([
                sys.executable, str(ROOT / "scripts/starintel.py"), "import",
                str(generator.PACKET), "--root", temporary,
            ], cwd=ROOT, capture_output=True, text=True, check=True)
            result = validate_repository(Path(temporary))
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["documents"], 13)
            for document in self.documents:
                path = Path(temporary) / "db" / document["dtype"] / f"{document['id']}.ndjson"
                self.assertTrue(path.is_file())
                self.assertEqual(json.loads(path.read_text()), document)
                self.assertEqual(path.read_bytes().count(b"\n"), 1)


if __name__ == "__main__":
    unittest.main()
