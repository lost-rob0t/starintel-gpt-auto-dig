from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "bin" / "starintel-ingest-core"


class FakeIngestHandler(BaseHTTPRequestHandler):
    lock = threading.Lock()
    batches: dict[str, list[dict]] = {}
    auth_headers: list[str | None] = []
    response_mode = "async-success"
    post_attempts = 0

    def log_message(self, fmt: str, *args) -> None:
        pass

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/documents/bulk":
            self.send_json(404, {"status": "error"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        documents = json.loads(self.rfile.read(length))
        with self.lock:
            type(self).post_attempts += 1
            attempt = type(self).post_attempts
            mode = type(self).response_mode
            self.auth_headers.append(self.headers.get("Authorization"))

        if mode == "http-503":
            self.send_json(503, {"error": "temporary"})
            return
        if mode == "http-429-once" and attempt == 1:
            self.send_json(429, {"error": "busy"})
            return
        if mode == "inline-failed-status":
            self.send_json(
                200,
                {
                    "status": "failed",
                    "total": len(documents),
                    "succeeded": len(documents),
                    "failed": 0,
                },
            )
            return
        if mode == "inline-partial-zero-failed":
            self.send_json(
                200,
                {
                    "total": len(documents),
                    "succeeded": max(0, len(documents) - 1),
                    "failed": 0,
                },
            )
            return

        with self.lock:
            job_id = f"job-{len(self.batches) + 1}"
            self.batches[job_id] = documents

        if mode == "drop-after-accept":
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.connection.close()
            return

        if mode == "accepted-no-status-url":
            self.send_json(202, {"status": "accepted", "job_id": job_id})
            return

        self.send_json(
            202,
            {
                "status": "accepted",
                "job_id": job_id,
                "status_url": f"/documents/bulk/{job_id}",
            },
        )

    def do_GET(self) -> None:
        prefix = "/documents/bulk/"
        if not self.path.startswith(prefix):
            self.send_json(404, {"status": "error"})
            return
        job_id = self.path[len(prefix) :]
        with self.lock:
            documents = self.batches.get(job_id)
            self.auth_headers.append(self.headers.get("Authorization"))
        if documents is None:
            self.send_json(404, {"status": "error"})
            return
        self.send_json(
            200,
            {
                "status": "completed",
                "total": len(documents),
                "succeeded": len(documents),
                "failed": 0,
            },
        )


class StarIntelIngestCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        if not BINARY.exists():
            self.fail(f"missing {BINARY}; run `nimble buildIngest` before this test")
        FakeIngestHandler.batches = {}
        FakeIngestHandler.auth_headers = []
        FakeIngestHandler.response_mode = "async-success"
        FakeIngestHandler.post_attempts = 0
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeIngestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def run_core(
        self,
        documents: list[dict],
        *extra_args: str,
        key: str | None = "test-secret",
    ) -> subprocess.CompletedProcess[str]:
        payload = "".join(json.dumps(document) + "\n" for document in documents)
        env = os.environ.copy()
        if key is None:
            env.pop("STAR_SERVER_API_KEY", None)
        else:
            env["STAR_SERVER_API_KEY"] = key
        server_url = f"http://127.0.0.1:{self.server.server_port}"
        return subprocess.run(
            [str(BINARY), "--server-url", server_url, *extra_args],
            cwd=ROOT,
            env=env,
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )

    def test_parallel_batches_use_bearer_auth_and_complete(self) -> None:
        documents = [
            {"_id": f"starintel:test:{index}", "dtype": "note", "version": 1}
            for index in range(7)
        ]
        result = self.run_core(
            documents,
            "--batch-size",
            "2",
            "--workers",
            "3",
            "--poll-timeout-ms",
            "5000",
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(sum(len(batch) for batch in FakeIngestHandler.batches.values()), 7)
        self.assertEqual(len(FakeIngestHandler.batches), 4)
        self.assertTrue(FakeIngestHandler.auth_headers)
        self.assertEqual(set(FakeIngestHandler.auth_headers), {"Bearer test-secret"})
        final = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["documents"], 7)
        self.assertEqual(final["failed_batches"], 0)
        self.assertEqual(final["workers"], 3)

    def test_missing_key_fails_before_network_request(self) -> None:
        result = self.run_core(
            [{"_id": "starintel:test:one", "dtype": "note"}],
            key=None,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("STAR_SERVER_API_KEY is required", result.stderr)
        self.assertFalse(FakeIngestHandler.batches)
        self.assertEqual(FakeIngestHandler.post_attempts, 0)

    def test_accepted_without_status_url_fails_closed(self) -> None:
        FakeIngestHandler.response_mode = "accepted-no-status-url"
        result = self.run_core([{"_id": "starintel:test:one", "dtype": "note"}])

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("accepted without status_url", result.stderr)
        self.assertEqual(FakeIngestHandler.post_attempts, 1)
        self.assertEqual(len(FakeIngestHandler.batches), 1)

    def test_failed_2xx_status_is_not_reported_as_success(self) -> None:
        FakeIngestHandler.response_mode = "inline-failed-status"
        result = self.run_core([{"_id": "starintel:test:one", "dtype": "note"}])

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("did not complete successfully", result.stderr)
        self.assertEqual(FakeIngestHandler.post_attempts, 1)

    def test_partial_success_with_zero_failed_is_rejected(self) -> None:
        FakeIngestHandler.response_mode = "inline-partial-zero-failed"
        result = self.run_core(
            [
                {"_id": "starintel:test:one", "dtype": "note"},
                {"_id": "starintel:test:two", "dtype": "note"},
            ]
        )

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("incomplete success", result.stderr)
        self.assertEqual(FakeIngestHandler.post_attempts, 1)

    def test_ambiguous_connection_drop_is_never_retried(self) -> None:
        FakeIngestHandler.response_mode = "drop-after-accept"
        result = self.run_core([{"_id": "starintel:test:one", "dtype": "note"}])

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("not retried to avoid duplicate ingestion", result.stderr)
        self.assertEqual(FakeIngestHandler.post_attempts, 1)
        self.assertEqual(len(FakeIngestHandler.batches), 1)

    def test_503_post_is_not_retried_without_idempotency(self) -> None:
        FakeIngestHandler.response_mode = "http-503"
        result = self.run_core([{"_id": "starintel:test:one", "dtype": "note"}])

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("not retried because acceptance is ambiguous", result.stderr)
        self.assertEqual(FakeIngestHandler.post_attempts, 1)

    def test_429_post_is_safely_retried(self) -> None:
        FakeIngestHandler.response_mode = "http-429-once"
        result = self.run_core(
            [{"_id": "starintel:test:one", "dtype": "note"}],
            "--poll-timeout-ms",
            "5000",
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(FakeIngestHandler.post_attempts, 2)
        self.assertEqual(len(FakeIngestHandler.batches), 1)


if __name__ == "__main__":
    unittest.main()
