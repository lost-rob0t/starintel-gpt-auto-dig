from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import-starintel-documents.py"
SPEC = importlib.util.spec_from_file_location("import_starintel_documents", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def write_packet(path: Path, documents: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(document, separators=(",", ":")) + "\n" for document in documents),
        encoding="utf-8",
    )


class ImportStarIntelDocumentsTests(unittest.TestCase):
    def test_diff_mode_imports_appended_document_but_not_existing_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init")
            git(root, "config", "user.email", "test@example.invalid")
            git(root, "config", "user.name", "Auto Dig Test")

            packet = root / "digs" / "example" / "2026-09-01-test" / "starintel-documents.jsonl"
            existing = {"_id": "starintel:test:existing", "dtype": "note", "version": 1}
            new = {"_id": "starintel:test:new", "dtype": "note", "version": 1}
            write_packet(packet, [existing])
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            write_packet(packet, [existing, new])
            git(root, "add", ".")
            git(root, "commit", "-m", "add logical document")

            records = MODULE.collect_new_documents(root, base)
            self.assertEqual([record.document_id for record in records], [new["_id"]])

    def test_all_mode_prefers_newer_integer_version_for_duplicate_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document_id = "starintel:test:versioned"
            write_packet(
                root / "digs" / "example" / "2026-09-01-test" / "starintel-documents.jsonl",
                [{"_id": document_id, "dtype": "note", "version": 1, "data": {"value": "old"}}],
            )
            db_path = root / "db" / "note" / f"{document_id}.ndjson"
            write_packet(
                db_path,
                [{"_id": document_id, "dtype": "note", "version": 2, "data": {"value": "new"}}],
            )

            records = MODULE.collect_all_documents(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].document["version"], 2)

    def test_all_mode_prefers_db_for_same_version_packet_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document_id = "starintel:dataset-manifest:bilderberg-public-roster"
            write_packet(
                root / "db" / "dataset-manifest" / f"{document_id}.ndjson",
                [
                    {
                        "_id": document_id,
                        "dtype": "dataset-manifest",
                        "version": 1,
                        "data": {"surface": "db"},
                    }
                ],
            )
            write_packet(
                root / "digs" / "dark-academia" / "run" / "starintel-documents.jsonl",
                [
                    {
                        "_id": document_id,
                        "dtype": "dataset-manifest",
                        "version": 1,
                        "data": {"surface": "packet"},
                    }
                ],
            )

            records = MODULE.collect_all_documents(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].document["data"]["surface"], "db")

    def test_diff_merge_remains_strict_for_same_version_conflict(self) -> None:
        document_id = "starintel:test:strict"
        records = [
            MODULE.DocumentRecord(
                {
                    "_id": document_id,
                    "dtype": "note",
                    "version": 1,
                    "data": {"value": "a"},
                },
                "digs/a/starintel-documents.jsonl:1",
            ),
            MODULE.DocumentRecord(
                {
                    "_id": document_id,
                    "dtype": "note",
                    "version": 1,
                    "data": {"value": "b"},
                },
                "digs/b/starintel-documents.jsonl:1",
            ),
        ]
        with self.assertRaises(ValueError):
            MODULE.merge_records(records)

    def test_upload_batch_sends_bearer_auth_and_polls_async_job(self) -> None:
        client = MODULE.IngestClient(
            "https://ingest.example.test",
            "secret-key",
            poll_interval=0,
            poll_timeout=1,
        )
        responses = [
            {"status": "accepted", "job_id": "job-1", "status_url": "/documents/bulk/job-1"},
            {"status": "completed", "total": 1, "succeeded": 1, "failed": 0},
        ]

        def fake_request(method: str, path: str, payload=None):
            self.assertIn(method, {"POST", "GET"})
            if method == "POST":
                self.assertEqual(path, "/documents/bulk")
                self.assertEqual(payload[0]["_id"], "starintel:test:one")
            else:
                self.assertEqual(path, "/documents/bulk/job-1")
            return responses.pop(0)

        with mock.patch.object(client, "request_json", side_effect=fake_request):
            result = client.upload_batch(
                [{"_id": "starintel:test:one", "dtype": "note", "version": 1}]
            )

        self.assertEqual(result["status"], "completed")
        self.assertFalse(responses)

    def test_request_json_sets_bearer_header(self) -> None:
        client = MODULE.IngestClient("https://ingest.example.test", "secret-key")
        response = mock.MagicMock()
        response.read.return_value = b'{"total":1,"succeeded":1,"failed":0}'
        context = mock.MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False

        with mock.patch.object(MODULE.urllib.request, "urlopen", return_value=context) as urlopen:
            client.request_json(
                "POST",
                "/documents/bulk",
                [{"_id": "starintel:test:one", "dtype": "note", "version": 1}],
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-key")
        self.assertEqual(request.get_header("Content-type"), "application/json")


if __name__ == "__main__":
    unittest.main()
