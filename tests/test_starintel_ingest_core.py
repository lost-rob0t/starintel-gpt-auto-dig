from __future__ import annotations

import json
import os
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
            job_id = f"job-{len(self.batches) + 1}"
            self.batches[job_id] = documents
            self.auth_headers.append(self.headers.get("Authorization"))
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
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeIngestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_parallel_batches_use_bearer_auth_and_complete(self) -> None:
        documents = [
            {"_id": f"starintel:test:{index}", "dtype": "note", "version": 1}
            for index in range(7)
        ]
        payload = "".join(json.dumps(document) + "\n" for document in documents)
        env = os.environ.copy()
        env["STAR_SERVER_API_KEY"] = "test-secret"
        server_url = f"http://127.0.0.1:{self.server.server_port}"

        result = subprocess.run(
            [
                str(BINARY),
                "--server-url",
                server_url,
                "--batch-size",
                "2",
                "--workers",
                "3",
                "--poll-timeout-ms",
                "5000",
            ],
            cwd=ROOT,
            env=env,
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
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
        env = os.environ.copy()
        env.pop("STAR_SERVER_API_KEY", None)
        server_url = f"http://127.0.0.1:{self.server.server_port}"
        payload = json.dumps({"_id": "starintel:test:one", "dtype": "note"}) + "\n"

        result = subprocess.run(
            [str(BINARY), "--server-url", server_url],
            cwd=ROOT,
            env=env,
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("STAR_SERVER_API_KEY is required", result.stderr)
        self.assertFalse(FakeIngestHandler.batches)


if __name__ == "__main__":
    unittest.main()
