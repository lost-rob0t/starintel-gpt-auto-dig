from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "scrape_fbi_procurement.py"
SPEC = importlib.util.spec_from_file_location("scrape_fbi_procurement", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FbiProcurementScraperTests(unittest.TestCase):
    def test_biz_repository_parser_keeps_same_host_https_links(self) -> None:
        payload = b"""
        <html><body>
          <a href="/file-repository/fbi-contracting-opportunities-forecast-fy26.xlsx/view">FY26 Forecast</a>
          <a href="https://biz.fbi.gov/file-repository/fbi-contracting-opportunities-forecast-fy26.xlsx/view#download">duplicate</a>
          <a href="https://example.com/nope">external</a>
          <a href="mailto:someone@example.com">mail</a>
        </body></html>
        """
        links = MODULE.repository_view_links(payload, MODULE.BIZ_FILE_REPOSITORY)
        self.assertEqual(1, len(links))
        self.assertEqual(
            "https://biz.fbi.gov/file-repository/fbi-contracting-opportunities-forecast-fy26.xlsx/view",
            links[0].url,
        )
        self.assertEqual("FY26 Forecast", links[0].title)

    def test_download_parser_excludes_view_and_image_links(self) -> None:
        payload = b"""
        <html><body>
          <a href="/file-repository/fy26.pdf/view">view</a>
          <a href="/file-repository/fy26.pdf">Download file</a>
          <a href="/file-repository/fy26.pdf/@@images/image">preview</a>
          <a href="/file-repository/vendors.xlsx">Vendor List</a>
        </body></html>
        """
        links = MODULE.download_links(payload, MODULE.BIZ_FILE_REPOSITORY)
        self.assertEqual(
            [
                "https://biz.fbi.gov/file-repository/fy26.pdf",
                "https://biz.fbi.gov/file-repository/vendors.xlsx",
            ],
            [link.url for link in links],
        )

    def test_date_ranges_never_exceed_one_year(self) -> None:
        ranges = MODULE.split_date_ranges(date(2024, 1, 1), date(2026, 8, 3))
        self.assertEqual(date(2024, 1, 1), ranges[0][0])
        self.assertEqual(date(2026, 8, 3), ranges[-1][1])
        for start, end in ranges:
            self.assertLessEqual((end - start).days, 365)
        for previous, current in zip(ranges, ranges[1:]):
            self.assertEqual(previous[1].toordinal() + 1, current[0].toordinal())

    def test_date_ranges_handle_february_29(self) -> None:
        ranges = MODULE.split_date_ranges(date(2024, 2, 29), date(2025, 3, 2))
        self.assertEqual((date(2024, 2, 29), date(2025, 2, 27)), ranges[0])
        self.assertEqual((date(2025, 2, 28), date(2025, 3, 2)), ranges[1])

    def test_sam_query_redacts_api_key(self) -> None:
        url = MODULE.sam_query_url(
            api_key="super-secret",
            start=date(2026, 1, 1),
            end=date(2026, 8, 3),
            organization_name="FEDERAL BUREAU OF INVESTIGATION",
            procurement_type="r",
            limit=100,
            offset=0,
        )
        public = MODULE.public_sam_query(url)
        self.assertNotIn("super-secret", public)
        self.assertIn("api_key=REDACTED", public)
        self.assertIn("ptype=r", public)

    def test_usaspending_payload_uses_exact_award_ids_and_fbi_scope(self) -> None:
        payload = MODULE.usaspending_payload(
            award_ids=["15F06725F0001209"],
            start=date(2025, 1, 1),
            end=date(2026, 8, 3),
            page=1,
            limit=100,
        )
        filters = payload["filters"]
        self.assertEqual(['"15F06725F0001209"'], filters["award_ids"])
        self.assertNotIn("keywords", filters)
        self.assertEqual(
            "Federal Bureau of Investigation",
            filters["agencies"][0]["name"],
        )
        self.assertIn("Contract Award Type", payload["fields"])
        self.assertNotIn("generated_unique_award_id", payload["fields"])
        self.assertFalse(payload["subawards"])

    def test_usaspending_queries_separate_ids_and_keywords(self) -> None:
        queries = list(
            MODULE.usaspending_queries(
                award_ids=["15F06725F0001209"],
                keywords=["terrorist screening center", "threat screening center"],
                start=date(2025, 1, 1),
                end=date(2026, 8, 3),
                page=1,
                limit=100,
            )
        )
        self.assertEqual(3, len(queries))
        self.assertIn("award_ids", queries[0]["filters"])
        self.assertEqual(
            [["terrorist screening center"], ["threat screening center"]],
            [query["filters"]["keywords"] for query in queries[1:]],
        )

    def test_usaspending_payload_rejects_ambiguous_filters(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.usaspending_payload(
                award_ids=["15F06725F0001209"],
                keywords=["threat screening center"],
                start=date(2025, 1, 1),
                end=date(2026, 8, 3),
                page=1,
                limit=100,
            )
        with self.assertRaises(ValueError):
            MODULE.usaspending_payload(
                start=date(2025, 1, 1),
                end=date(2026, 8, 3),
                page=1,
                limit=100,
            )

    def test_blob_storage_uses_content_hash(self) -> None:
        payload = b"official public file"
        with tempfile.TemporaryDirectory() as directory:
            destination = MODULE.save_blob(
                payload,
                url="https://biz.fbi.gov/file-repository/test.pdf",
                download_dir=Path(directory),
            )
            self.assertTrue(destination.is_file())
            self.assertEqual(".pdf", destination.suffix)
            self.assertEqual(MODULE.sha256_bytes(payload), destination.stem)
            self.assertEqual(payload, destination.read_bytes())

    def test_jsonl_output_is_deterministic_and_deduplicated(self) -> None:
        records = [
            MODULE.raw_record(
                source="z",
                record_type="item",
                source_url="https://example.test/z",
                payload={"b": 2},
                retrieved_at="2026-08-03T00:00:00Z",
            ),
            MODULE.raw_record(
                source="a",
                record_type="item",
                source_url="https://example.test/a",
                payload={"a": 1},
                retrieved_at="2026-08-03T00:00:00Z",
            ),
        ]
        records.append(dict(records[0]))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.jsonl"
            self.assertEqual(2, MODULE.write_jsonl(records, output))
            rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(["a", "z"], [row["source"] for row in rows])
        self.assertEqual(64, len(rows[0]["sha256"]))


if __name__ == "__main__":
    unittest.main()
