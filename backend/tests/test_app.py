"""Backend API tests: run lifecycle, validation gate, projection safety."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.config import BackendConfig  # noqa: E402


def valid_document(doc_id: str = "starintel:org:test-org") -> dict:
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
        "data": {"name": "Test Org"},
    }


class BackendApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "digs" / "test-target" / "run-one").mkdir(parents=True)
        (root / "digs" / "test-target" / "run-one" / "starintel-documents.jsonl").write_text(
            json.dumps(valid_document()) + "\n"
            + json.dumps({**valid_document("starintel:person:test-person"), "dtype": "person"}) + "\n"
            + "not json at all\n",
            encoding="utf-8",
        )
        (root / "db" / "document").mkdir(parents=True)
        cfg = BackendConfig(root=root, state_dir=root / "state", server_url="http://127.0.0.1:59999")
        self.cfg = cfg
        self.client = TestClient(create_app(cfg))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_capabilities(self) -> None:
        res = self.client.get("/api/v1/capabilities")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["schema_version"], "0.9.0")
        self.assertIn("org", body["dtypes"])
        self.assertIn("start", body["actions"])

    def test_health_readiness(self) -> None:
        self.assertEqual(self.client.get("/health").json()["ok"], True)
        body = self.client.get("/readyz").json()
        self.assertEqual(body["status"], "degraded")  # no server at 59999
        self.assertEqual(body["checks"]["corpus"], "ok")
        self.assertEqual(body["checks"]["digs"], "ok")

    def test_create_run_idempotent(self) -> None:
        body = {"run_id": "run-alpha", "target": "test-target", "description": "d"}
        first = self.client.post("/api/v1/runs", json=body, headers={"Idempotency-Key": "k1"})
        self.assertEqual(first.status_code, 201)
        second = self.client.post("/api/v1/runs", json=body, headers={"Idempotency-Key": "k1"})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["run_id"], second.json()["run_id"])
        self.assertEqual(second.json()["idempotency_keys"], ["k1"])

    def test_lifecycle_transitions(self) -> None:
        run = {"run_id": "run-beta", "target": "test-target"}
        self.client.post("/api/v1/runs", json=run)
        self.assertEqual(self.client.post("/api/v1/runs/run-beta/start").json()["state"], "running")
        self.assertEqual(self.client.post("/api/v1/runs/run-beta/pause").json()["state"], "paused")
        self.assertEqual(self.client.post("/api/v1/runs/run-beta/resume").json()["state"], "running")
        self.assertEqual(self.client.post("/api/v1/runs/run-beta/stop").json()["state"], "stopped")
        # terminal state refuses further transitions with 409
        res = self.client.post("/api/v1/runs/run-beta/start")
        self.assertEqual(res.status_code, 409)
        # idempotency: same key replays recorded outcome
        self.client.post("/api/v1/runs", json={"run_id": "run-gamma", "target": "test-target"})
        r1 = self.client.post("/api/v1/runs/run-gamma/start", headers={"Idempotency-Key": "g1"})
        r2 = self.client.post("/api/v1/runs/run-gamma/start", headers={"Idempotency-Key": "g1"})
        self.assertEqual(r1.json()["state"], r2.json()["state"])

    def test_illegal_transition(self) -> None:
        self.client.post("/api/v1/runs", json={"run_id": "run-delta", "target": "test-target"})
        res = self.client.post("/api/v1/runs/run-delta/pause")  # created -> paused is illegal
        self.assertEqual(res.status_code, 409)

    def test_run_documents_validates(self) -> None:
        res = self.client.get("/api/v1/runs/run-one/documents")
        self.assertEqual(res.status_code, 404)  # discovered runs have no state record yet
        self.client.post("/api/v1/runs", json={"run_id": "run-one", "target": "test-target"})
        res = self.client.get("/api/v1/runs/run-one/documents")
        body = res.json()
        self.assertEqual(body["total_valid"], 2)
        self.assertEqual(body["total_invalid"], 1)
        self.assertEqual(len(body["documents"]), 2)

    def test_progress(self) -> None:
        self.client.post("/api/v1/runs", json={"run_id": "run-eps", "target": "test-target"})
        res = self.client.post("/api/v1/runs/run-eps/progress", json={"documents": 42, "notes": "mid-dig"})
        self.assertEqual(res.json()["progress"]["documents"], 42)
        got = self.client.get("/api/v1/runs/run-eps/progress").json()
        self.assertEqual(got["progress"]["notes"], "mid-dig")

    def test_document_submission_validation_gate(self) -> None:
        res = self.client.post("/api/v1/documents", json={"document": {"dtype": "org"}})
        self.assertEqual(res.status_code, 422)
        self.assertIn("invalid_document_schema", res.json()["detail"])

    def test_runs_listing_includes_discovered(self) -> None:
        self.client.post("/api/v1/runs", json={"run_id": "run-one", "target": "test-target"})
        body = self.client.get("/api/v1/runs").json()
        ids = {r["run_id"] for r in body["runs"]}
        self.assertIn("run-one", ids)
        rec = next(r for r in body["runs"] if r["run_id"] == "run-one")
        self.assertEqual(rec["target"], "test-target")
        self.assertTrue(rec["artifact"].endswith(".jsonl"))

    def test_no_internal_secrets_in_responses(self) -> None:
        self.client.post("/api/v1/runs", json={"run_id": "run-zeta", "target": "test-target"})
        for path in ("/health", "/readyz", "/api/v1/runs", "/api/v1/runs/run-zeta"):
            body = self.client.get(path).text
            self.assertNotIn("authorization", body.lower())
            self.assertNotIn("password", body.lower())
            self.assertNotIn("token", body.lower().replace("idempotency", ""))


if __name__ == "__main__":
    unittest.main()
