from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class NimSiteScalingTests(unittest.TestCase):
    def test_overlapping_topics_store_references_not_raw_copies(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        binary = repo / "bin" / "starintel-site"
        self.assertTrue(binary.is_file(), "nimble buildFast must run before this test")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / "digs" / "alpha" / "run-1"
            packet.mkdir(parents=True)
            raw_documents = [
                {
                    "_id": "starintel:person:alice-example",
                    "dataset": "alpha-dataset",
                    "dtype": "person",
                    "title": "Alice Example",
                    "summary": "alpha beta overlap",
                    "date_updated": "2026-08-09T00:00:00Z",
                    "schema_version": "0.9.0",
                    "sources": ["https://example.invalid/alice"],
                },
                {
                    "_id": "starintel:org:example-labs",
                    "dataset": "alpha-dataset",
                    "dtype": "org",
                    "title": "Example Labs",
                    "summary": "alpha beta overlap",
                    "date_updated": "2026-08-09T00:00:00Z",
                    "schema_version": "0.9.0",
                    "sources": ["https://example.invalid/labs"],
                },
            ]
            transport = packet / "starintel-documents.jsonl"
            transport.write_text(
                "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in raw_documents),
                encoding="utf-8",
            )
            topics = root / "topics.json"
            topics.write_text(
                json.dumps(
                    {
                        "topics": [
                            {"id": "alpha", "title": "Alpha", "match": {"terms": ["alpha"]}},
                            {"id": "beta", "title": "Beta", "match": {"terms": ["beta"]}},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            site = root / "site"
            org = root / "org"
            bulk = root / "bulk"
            base_url = "https://example.invalid/release"
            subprocess.run(
                [
                    str(binary),
                    "--input",
                    str(root / "digs"),
                    "--db",
                    str(root / "db"),
                    "--output",
                    str(site),
                    "--org-output",
                    str(org),
                    "--bulk-output",
                    str(bulk),
                    "--bulk-base-url",
                    base_url,
                    "--config",
                    str(root / "missing-site-config.json"),
                    "--topics",
                    str(topics),
                    "--assets",
                    str(root / "missing-assets"),
                ],
                check=True,
                cwd=repo,
            )
            subprocess.run(
                [
                    "python3",
                    "scripts/externalize_search_indexes.py",
                    "--site",
                    str(site),
                    "--transport",
                    "pages-static",
                ],
                check=True,
                cwd=repo,
            )

            canonical = bulk / "starintel-complete-corpus.jsonl"
            self.assertEqual(canonical.read_text(encoding="utf-8").count("\n"), 2)
            self.assertFalse((site / "org").exists())
            self.assertTrue((site / "indexes" / "records").is_dir())
            self.assertTrue((site / "indexes" / "search").is_dir())
            self.assertFalse(any(site.rglob("starintel-documents.jsonl")))
            self.assertTrue((org / "alpha" / "person-alice-example.org").is_file())

            alpha_members = (bulk / "memberships" / "topic-alpha.ids").read_text(encoding="utf-8")
            beta_members = (bulk / "memberships" / "topic-beta.ids").read_text(encoding="utf-8")
            self.assertIn("starintel:person:alice-example", alpha_members)
            self.assertIn("starintel:person:alice-example", beta_members)

            alpha_manifest = json.loads(
                (site / "dataset-alpha" / "downloads" / "dataset-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(alpha_manifest["record_count"], 2)
            self.assertEqual(alpha_manifest["membership"]["format"], "newline-delimited-canonical-ids")
            self.assertTrue(alpha_manifest["membership"]["url"].endswith("topic-alpha.ids.gz"))
            self.assertEqual(alpha_manifest["search"]["mode"], "starintel-pages-static-index-v1")

            corpus_manifest = json.loads(
                (site / "downloads" / "starintel-complete-corpus.manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(corpus_manifest["data"]["record_count"], 2)
            self.assertEqual(corpus_manifest["data"]["distribution"], "external-bulk-shards")
            self.assertGreaterEqual(len(corpus_manifest["data"]["files"]), 1)

            graph = json.loads((site / "alpha" / "graph.json").read_text(encoding="utf-8"))
            self.assertTrue(graph["nodes"])
            self.assertIn("documents.html?id=", graph["nodes"][0]["href"])
            self.assertFalse((site / "alpha" / "nodes").exists())

            index_config = json.loads((site / "search-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index_config["format"], "starintel-pages-static-index-v1")
            self.assertEqual(index_config["record_count"], 2)
            self.assertTrue(index_config["records"]["pages"])
            self.assertTrue(index_config["search"]["segments"])

            record_segment = index_config["records"]["pages"][0]
            record_path = site / record_segment["url"]
            payload = record_path.read_bytes()
            self.assertEqual(len(payload), record_segment["length"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), record_segment["sha256"])
            rows = json.loads(payload)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], "starintel:org:example-labs")

            search_segment = next(
                segment
                for segments in index_config["search"]["segments"].values()
                for segment in segments
            )
            search_path = site / search_segment["url"]
            search_payload = search_path.read_bytes()
            self.assertLessEqual(
                len(search_payload), index_config["search"]["max_segment_bytes"]
            )
            self.assertEqual(len(search_payload), search_segment["length"])
            self.assertEqual(
                hashlib.sha256(search_payload).hexdigest(), search_segment["sha256"]
            )
            self.assertIsInstance(json.loads(search_payload), dict)

            site_bytes = sum(path.stat().st_size for path in site.rglob("*") if path.is_file())
            canonical_bytes = canonical.stat().st_size
            self.assertLess(site_bytes, canonical_bytes * 20 + 500_000)


if __name__ == "__main__":
    unittest.main()
