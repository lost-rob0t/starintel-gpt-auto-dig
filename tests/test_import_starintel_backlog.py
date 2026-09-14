from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import-starintel-backlog.py"
SPEC = importlib.util.spec_from_file_location("starintel_backlog_import", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


@dataclass(frozen=True)
class Record:
    document_id: str
    document: dict


class BacklogImportTests(unittest.TestCase):
    def test_request_too_large_detection(self) -> None:
        self.assertTrue(MODULE.request_too_large("POST failed with HTTP 413: nginx"))
        self.assertTrue(MODULE.request_too_large("413 Request Entity Too Large"))
        self.assertFalse(MODULE.request_too_large("POST failed with HTTP 503"))

    def test_clean_413_is_bisected_and_each_success_is_ledgered(self) -> None:
        records = [
            Record(f"doc-{index}", {"_id": f"doc-{index}", "dtype": "source"})
            for index in range(4)
        ]
        attempts: list[tuple[int, int]] = []

        def fake_run_batch(_core, _records, first, past_last):
            attempts.append((first, past_last))
            if past_last - first == 4:
                return 1, "POST failed with HTTP 413: Request Entity Too Large"
            return 0, '{"status":"completed"}'

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            import_log = root / "canonical-import.jsonl"
            failed_log = root / "failed-import.jsonl"
            state = {
                "confirmed_offset": 0,
                "completed_batches": 0,
                "imported_documents": 0,
            }
            with patch.object(MODULE, "run_batch", side_effect=fake_run_batch):
                ok = MODULE.ingest_range(
                    core=Path("unused"),
                    records=records,
                    first=0,
                    past_last=4,
                    chunk_no=1,
                    import_log=import_log,
                    failed_log=failed_log,
                    run_id="test-run",
                    source_commit="abc123",
                    state=state,
                )

            self.assertTrue(ok)
            self.assertEqual(attempts, [(0, 4), (0, 2), (2, 4)])
            self.assertEqual(state["confirmed_offset"], 4)
            self.assertEqual(state["completed_batches"], 2)
            self.assertEqual(state["imported_documents"], 4)

            imported = [json.loads(line) for line in import_log.read_text().splitlines()]
            self.assertEqual([event["document_ids"] for event in imported], [["doc-0", "doc-1"], ["doc-2", "doc-3"]])
            self.assertEqual([event["confirmed_offset"] for event in imported], [2, 4])

            failures = [json.loads(line) for line in failed_log.read_text().splitlines()]
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]["record_type"], "ingress-413")
            self.assertEqual(failures[0]["status"], "recovered-by-split")
            self.assertFalse(failures[0]["replay_requires_review"])
            self.assertEqual(failures[0]["document_ids"], ["doc-0", "doc-1", "doc-2", "doc-3"])

    def test_non_413_failure_stays_ambiguous_and_does_not_advance(self) -> None:
        records = [Record("doc-0", {"_id": "doc-0", "dtype": "source"})]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = {
                "confirmed_offset": 0,
                "completed_batches": 0,
                "imported_documents": 0,
            }
            with patch.object(MODULE, "run_batch", return_value=(1, "HTTP 502 Bad Gateway")):
                ok = MODULE.ingest_range(
                    core=Path("unused"),
                    records=records,
                    first=0,
                    past_last=1,
                    chunk_no=1,
                    import_log=root / "canonical-import.jsonl",
                    failed_log=root / "failed-import.jsonl",
                    run_id="test-run",
                    source_commit="abc123",
                    state=state,
                )
            self.assertFalse(ok)
            self.assertEqual(state["confirmed_offset"], 0)
            event = json.loads((root / "failed-import.jsonl").read_text().strip())
            self.assertEqual(event["status"], "failed-or-ambiguous")
            self.assertTrue(event["replay_requires_review"])


if __name__ == "__main__":
    unittest.main()
