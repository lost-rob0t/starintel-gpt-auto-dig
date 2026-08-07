from __future__ import annotations

import argparse
import contextlib
import asyncio
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import wef_depth7 as MODULE

CONFIG_PATH = ROOT / "scrapers" / "wef-depth-7.json"


def args(**overrides: Any) -> argparse.Namespace:
    values = {
        "page_size": 100,
        "max_pages": 2,
        "max_depth": 1,
        "ignore_robots": False,
        "download_dir": None,
        "archive_limit": 25,
        "archive_content": False,
        "max_document_bytes": 4_000_000,
        "github_file_limit": 10,
        "auditor_download": False,
        "auditor_hit_limit": 10,
        "auditor_row_limit": 1000,
        "max_dataset_bytes": 1_000_000,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class FakeLegistarClient:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def json(self, url: str, *, max_bytes: int = 32_000_000) -> Any:
        del max_bytes
        self.urls.append(url)
        if "/Matters?" in url:
            if "%24skip=0" in url:
                return [
                    {
                        "MatterId": 42,
                        "MatterFile": "1894-2024",
                        "MatterTitle": "Authorize AndHealth tax year 2023 payment",
                        "MatterInSiteURL": "https://columbus.legistar.com/LegislationDetail.aspx?ID=42",
                    },
                    {
                        "MatterId": 43,
                        "MatterTitle": "Unrelated zoning action",
                    },
                ]
            return []
        endpoint = url.rsplit("/", 1)[-1]
        return [{"endpoint": endpoint, "MatterId": 42}]


class FakeSiteClient:
    def __init__(self, pages: Mapping[str, bytes]) -> None:
        self.pages = dict(pages)

    def robots_allowed(self, url: str) -> bool:
        return True

    def fetch(self, url: str, *, accept: str = "*/*", max_bytes: int = 16_000_000):
        del accept, max_bytes
        body = self.pages[url]
        content_type = "application/pdf" if url.endswith(".pdf") else "text/html; charset=utf-8"
        return body, {"Content-Type": content_type}, url


class WefDepth7ScraperTests(unittest.TestCase):
    def test_config_enumerates_exactly_eight_targets(self) -> None:
        config, targets = MODULE.load_config(CONFIG_PATH)
        self.assertEqual(1, config["schema_version"])
        self.assertEqual(8, len(targets))
        self.assertEqual(8, len({target.target_id for target in targets}))
        self.assertTrue(all(target.collectors for target in targets))
        self.assertTrue(all(target.keywords for target in targets))

    def test_job_enumeration_covers_every_target(self) -> None:
        _, targets = MODULE.load_config(CONFIG_PATH)
        jobs = MODULE.enumerate_jobs(targets, [])
        self.assertGreaterEqual(len(jobs), 20)
        self.assertEqual(
            {target.target_id for target in targets},
            {job.target.target_id for job in jobs},
        )
        self.assertTrue({"legistar", "site", "wayback", "github", "auditor"} <= {job.collector for job in jobs})

    def test_keyword_matching_is_case_insensitive_and_deterministic(self) -> None:
        hits = MODULE.keyword_hits(
            {"title": "Smart COLUMBUS Green IT Playbook"},
            ("Green IT", "smart columbus", "missing"),
        )
        self.assertEqual(("Green IT", "smart columbus"), hits)

    def test_page_parser_normalizes_links_and_metadata(self) -> None:
        parser = MODULE.PageParser("https://example.org/base/")
        parser.feed(
            """<html><head><title>  Test Page </title><meta name='description' content='Summary'></head>
            <body><a href='../report.pdf'> Annual Report </a><p>Evidence text</p></body></html>"""
        )
        self.assertEqual("Test Page", parser.title)
        self.assertEqual("Summary", parser.meta["description"])
        self.assertEqual(
            [("Annual Report", "https://example.org/report.pdf")],
            parser.links,
        )
        self.assertIn("Evidence text", parser.text)

    def test_legistar_collector_expands_matching_matter(self) -> None:
        _, targets = MODULE.load_config(CONFIG_PATH)
        target = next(item for item in targets if "andhealth" in item.target_id)
        client = FakeLegistarClient()
        collector = MODULE.LegistarCollector(
            client,
            args(),
            {"legistar_root": "https://webapi.legistar.com/v1/columbus"},
        )
        observations = list(collector.collect(target))
        self.assertEqual(1, len(observations))
        record = observations[0].as_dict()
        self.assertEqual("legistar-matter", record["kind"])
        self.assertIn("AndHealth", record["matched_keywords"])
        self.assertEqual(
            {"attachments", "sponsors", "relations", "versions", "histories"},
            set(record["payload"]["related"]),
        )

    def test_site_collector_hashes_matching_document(self) -> None:
        start = "https://example.org/"
        report = "https://example.org/green-it-report.pdf"
        pages = {
            start: b"<html><head><title>Green IT</title></head><body><a href='/green-it-report.pdf'>Green IT report</a></body></html>",
            report: b"%PDF-1.4 fake Green IT report",
        }
        target = MODULE.TargetPlan(
            target_id="target:test",
            title="Test",
            collectors=("site",),
            keywords=("Green IT",),
            seed_urls=(start,),
        )
        collector = MODULE.SiteCollector(FakeSiteClient(pages), args(max_pages=5, max_depth=2), {})
        observations = list(collector.collect(target))
        kinds = [observation.kind for observation in observations]
        self.assertIn("web-page", kinds)
        self.assertIn("document", kinds)
        document = next(observation.as_dict() for observation in observations if observation.kind == "document")
        self.assertEqual(64, len(document["payload"]["sha256"]))
        self.assertEqual(len(pages[report]), document["payload"]["size"])

    def test_auditor_rows_parse_csv_and_json(self) -> None:
        collector = MODULE.AuditorCollector(object(), args(auditor_row_limit=2), {})
        csv_rows = list(collector._rows(b"Vendor,Amount\nHNTB,10\nAndHealth,20\nOther,30\n", "csv"))
        self.assertEqual([(1, {"Vendor": "HNTB", "Amount": "10"}), (2, {"Vendor": "AndHealth", "Amount": "20"})], csv_rows)
        json_rows = list(collector._rows(b'[{"Vendor":"HNTB"},{"Vendor":"AndHealth"}]', "json"))
        self.assertEqual("HNTB", json_rows[0][1]["Vendor"])

    def test_writer_actor_deduplicates_observations(self) -> None:
        async def run() -> tuple[int, list[dict[str, Any]]]:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "out.jsonl"
                writer = MODULE.WriterActor(path)
                task = asyncio.create_task(writer.run())
                observation = MODULE.Observation(
                    collector="site",
                    target_id="target:test",
                    kind="web-page",
                    source_url="https://example.org/",
                    payload={"title": "Example"},
                    retrieved_at="2026-07-31T00:00:00Z",
                )
                await writer.send(observation)
                await writer.send(observation)
                await writer.send(MODULE.Stop())
                await task
                records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                return writer.count, records

        count, records = asyncio.run(run())
        self.assertEqual(1, count)
        self.assertEqual(1, len(records))
        self.assertEqual("sha256:", records[0]["observation_id"][:7])

    def test_parse_args_rejects_invalid_actor_count(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                MODULE.parse_args(["--concurrency", "0"])


if __name__ == "__main__":
    unittest.main()
