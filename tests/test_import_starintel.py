"""Importer unit tests: batcher, checkpoint dedup, and counter categories (no network)."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from queue import Queue

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))

from import_starintel import (  # noqa: E402
    BULK_INLINE_LIMIT,
    Checkpoint,
    Counters,
    batcher,
    iter_source_files,
)
from backend.server_client import BulkResult, StarIntelServerError  # noqa: E402


def valid_doc(doc_id: str) -> dict:
    return {
        "_id": doc_id,
        "dataset": "test",
        "dtype": "org",
        "schema_version": "0.9.0",
        "version": 1,
        "date_added": "2026-08-28T00:00:00Z",
        "date_updated": "2026-08-28T00:00:00Z",
        "sources": [{"name": "test", "url": "https://example.com"}],
        "evidence": [],
        "data": {"name": "T"},
    }


class BatcherTests(unittest.TestCase):
    def test_batches_and_sentinels(self) -> None:
        items = [(f"src{i}", valid_doc(f"starintel:org:b{i}")) for i in range(25)]
        q: Queue = Queue()
        stop = threading.Event()
        batcher(iter(items), 10, q, stop, workers=2)
        batches = []
        while True:
            batch = q.get(timeout=1)
            if batch is None:
                break
            batches.append(batch)
        self.assertEqual([10, 10, 5], [len(b) for b in batches])
        # the loop above consumed one sentinel; workers-1 remain queued
        self.assertEqual(q.qsize(), 1)

    def test_stop_event_short_circuits(self) -> None:
        items = [(f"src{i}", valid_doc(f"starintel:org:c{i}")) for i in range(50)]
        q: Queue = Queue()
        stop = threading.Event()
        stop.set()
        batcher(iter(items), 10, q, stop, workers=1)
        self.assertEqual(q.qsize(), 1)  # only the sentinel

    def test_inline_limit_documented(self) -> None:
        self.assertEqual(BULK_INLINE_LIMIT, 10)


class CheckpointTests(unittest.TestCase):
    def test_record_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ckpt.jsonl"
            ck = Checkpoint(path, resume=False)
            ck.record("starintel:org:a")
            ck.record("starintel:org:b")
            ck.close()
            ck2 = Checkpoint(path, resume=True)
            self.assertTrue(ck2.seen("starintel:org:a"))
            self.assertFalse(ck2.seen("starintel:org:c"))
            ck2.record("starintel:org:c")
            ck2.close()
            ck3 = Checkpoint(path, resume=True)
            self.assertEqual(len(ck3), 3)
            ck3.close()

    def test_no_resume_ignores_old_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ckpt.jsonl"
            ck = Checkpoint(path, resume=False)
            ck.record("starintel:org:old")
            ck.close()
            ck2 = Checkpoint(path, resume=False)
            self.assertFalse(ck2.seen("starintel:org:old"))
            ck2.close()


class CounterTests(unittest.TestCase):
    def test_as_dict_categories(self) -> None:
        counters = Counters()
        counters.bump("attempted", 10)
        counters.bump("accepted", 8)
        counters.bump("invalid", 1)
        counters.bump("failed", 1)
        summary = counters.as_dict(2.0)
        self.assertEqual(summary["attempted"], 10)
        self.assertEqual(summary["accepted"], 8)
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["documents_per_second"], 5.0)

    def test_result_mapping(self) -> None:
        result = BulkResult(accepted=3, failed=1, errors=[{"index": 1, "error": "bad"}])
        self.assertEqual(result.accepted, 3)
        self.assertEqual(result.failed, 1)

    def test_permanent_error_status(self) -> None:
        err = StarIntelServerError("no", status=422)
        self.assertEqual(err.status, 422)
        self.assertTrue(400 <= (err.status or 0) < 500)


class SourceFileTests(unittest.TestCase):
    def test_iter_source_files_dtype_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "org").mkdir()
            (root / "person").mkdir()
            (root / "org" / "a.ndjson").write_text(json.dumps(valid_doc("starintel:org:a")) + "\n")
            (root / "person" / "b.ndjson").write_text(json.dumps(valid_doc("starintel:person:b")) + "\n")
            (root / "notes.txt").write_text("skip me")
            files = iter_source_files(root)
            self.assertEqual(len(files), 2)
            self.assertEqual({f.parent.name for f in files}, {"org", "person"})


if __name__ == "__main__":
    unittest.main()
