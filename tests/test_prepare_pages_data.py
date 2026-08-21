from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "prepare_pages_data.py"
spec = importlib.util.spec_from_file_location("prepare_pages_data", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class PreparePagesDataTests(unittest.TestCase):
    def test_hydrates_graph_summaries_and_materializes_full_working_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site = root / "site"
            bulk = root / "bulk"
            record_dir = site / "indexes" / "records"
            surface = site / "alpha"
            record_dir.mkdir(parents=True)
            surface.mkdir(parents=True)
            bulk.mkdir(parents=True)

            documents = [
                {
                    "_id": "starintel:financial-observation:a",
                    "dataset": "alpha-data",
                    "dtype": "financial-observation",
                    "title": "Observation A",
                    "summary": "Large ledger payload should stay out of browser metadata.",
                    "status": "reviewed",
                    "date_updated": "2026-08-09T00:00:00Z",
                },
                {
                    "_id": "starintel:person:alice",
                    "dataset": "alpha-data",
                    "dtype": "person",
                    "title": "Alice",
                    "summary": "Alice has a useful source-backed profile summary.",
                    "status": "reviewed",
                    "date_updated": "2026-08-09T00:00:00Z",
                },
            ]
            corpus = bulk / "starintel-complete-corpus.jsonl"
            corpus.write_text(
                "".join(json.dumps(document, separators=(",", ":")) + "\n" for document in documents),
                encoding="utf-8",
            )

            rows = [
                ["alpha", "starintel:financial-observation:a", "Observation A", "financial-observation", "alpha-data", "reviewed", "2026-08-09T00:00:00Z"],
                ["alpha", "starintel:person:alice", "Alice", "person", "alpha-data", "reviewed", "2026-08-09T00:00:00Z"],
            ]
            record_path = record_dir / "page-00000.json"
            payload = json.dumps(rows, separators=(",", ":")).encode("utf-8") + b"\n"
            record_path.write_bytes(payload)
            (site / "search-index.json").write_text(
                json.dumps(
                    {
                        "format": "starintel-pages-static-index-v1",
                        "record_count": 2,
                        "minimum_query_characters": 2,
                        "search": {"prefix_length": 2, "max_segment_bytes": 1024, "segments": {}},
                        "records": {
                            "page_size": 2000,
                            "page_count": 1,
                            "fields": ["target", "id", "title", "dtype", "dataset", "status", "updated"],
                            "sorted_by": "id",
                            "pages": [
                                {
                                    "url": "indexes/records/page-00000.json",
                                    "length": len(payload),
                                    "sha256": hashlib.sha256(payload).hexdigest(),
                                    "first_id": rows[0][1],
                                    "last_id": rows[-1][1],
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            (surface / "documents.json").write_text(
                json.dumps([{"id": "starintel:person:alice"}]),
                encoding="utf-8",
            )

            result = module.prepare(
                site,
                bulk,
                summary_limit=180,
                quasar_limit=500,
                root_limit=2000,
            )

            self.assertEqual(result["records"], 2)
            self.assertEqual(result["hydrated_summaries"], 1)
            hydrated_rows = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(hydrated_rows[0][7], "")
            self.assertEqual(
                hydrated_rows[1][7],
                "Alice has a useful source-backed profile summary.",
            )

            config = json.loads((site / "search-index.json").read_text(encoding="utf-8"))
            self.assertEqual(config["records"]["fields"][-1], "summary")
            page = config["records"]["pages"][0]
            hydrated_payload = record_path.read_bytes()
            self.assertEqual(page["length"], len(hydrated_payload))
            self.assertEqual(page["sha256"], hashlib.sha256(hydrated_payload).hexdigest())

            surface_docs = json.loads((surface / "quasar-documents.json").read_text(encoding="utf-8"))
            self.assertEqual([document["_id"] for document in surface_docs], ["starintel:person:alice"])
            self.assertEqual(surface_docs[0]["summary"], documents[1]["summary"])

            root_docs = json.loads((site / "quasar-documents.json").read_text(encoding="utf-8"))
            self.assertEqual([document["_id"] for document in root_docs], ["starintel:person:alice"])


if __name__ == "__main__":
    unittest.main()
