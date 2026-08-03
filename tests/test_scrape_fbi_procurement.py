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
          <a href="/file-repository/fbi-contracting-opportunities-forecast-fy26">FY26 Forecast</a>
          <a href="https://biz.fbi.gov/file-repository/fbi-contracting-opportunities-forecast-fy26#download">duplicate</a>
          <a href="https://example.com/nope">external</a>
          <a href="mailto:someone@example.com">mail</a>
        </body></html>
        """
        links = MODULE.parse_links(payload, MODULE.BIZ_FILE_REPOSITORY)
        self.assertEqual(1, len(links))
        self.assertEqual(
            "https://biz.fbi.gov/file-repository/fbi-contracting-opportunities-forecast-fy26",
            links[0].url,
        )
        self.assertEqual("FY26 Forecast", links[0].title)

    def test_date_ranges_never_exceed_one_year(self) -> None:
        ranges = MODULE.split_date_ranges(date(2024, 1, 1), date(2026, 8, 3))
        self.assertEqual(date(2024, 1, 1), ranges[0][0])
        self.assertEqual(date(2026, 8, 3), ranges[-1][1])
        for start, end in ranges:
            self.assertLessEqual((end - start).days, 365)
        for previous, current in zip(ranges, ranges[1:]):
            self.assertEqual(previous[1].toordinal() + 1, current[0].toordinal())

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
            keywords=["threat screening center"],
            start=date(2025, 1, 1),
            end=date(2026, 8, 3),
            page=1,
            limit=100,
        )
        filters = payload["filters"]
        self.assertEqual(['"15F06725F0001209"'], filters["award_ids"])
        self.assertEqual(["threat screening center"], filters["keywords"])
        self.assertEqual(
            "Federal Bureau of Investigation",
            filters["agencies"][0]["name"],
        )
        self.assertFalse(payload["subawards"])

    def test_jsonl_output_is_deterministic(self) -> None:
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
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.jsonl"
            self.assertEqual(2, MODULE.write_jsonl(records, output))
            rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(["a", "z"], [row["source"] for row in rows])
        self.assertEqual(64, len(rows[0]["sha256"]))


if __name__ == "__main__":
    unittest.main()
