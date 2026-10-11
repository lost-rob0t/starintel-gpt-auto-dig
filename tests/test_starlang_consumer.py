"""Exercise the public document API and the actual outbound HTTP boundary."""
import json
import subprocess
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

import httpx
import starintel_doc as runtime
from backend.server_client import StarIntelClient
from backend.validation import DocumentValidationError
from starintel_doc.writer import write_db_document

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = {"id": "fixture:person", "dtype": "person", "dataset": "test", "schemaVersion": "0.10.1"}
NESTED = {"_id": "fixture:person", "dtype": "person", "dataset": "test", "schema_version": "0.10.1", "version": 1,
          "date_added": "2026-10-03T00:00:00Z", "date_updated": "2026-10-03T00:00:00Z", "sources": [], "evidence": [], "data": {}}

class StarLangConsumerTests(unittest.TestCase):
    def test_actual_backend_route_accepts_generated_and_rejects_nested(self):
        from backend.app import create_app
        from backend.config import BackendConfig
        with tempfile.TemporaryDirectory() as temp:
            client = TestClient(create_app(BackendConfig(root=Path(temp), state_dir=Path(temp) / "state")))
            with patch("backend.app.StarIntelClient") as server:
                server.return_value.submit_document.return_value = {"queued": True}
                self.assertEqual(client.post("/api/v1/documents", json={"document": CANONICAL}).status_code, 202)
                server.return_value.submit_document.assert_called_once_with(CANONICAL)
            with patch("backend.app.StarIntelClient") as server:
                self.assertEqual(client.post("/api/v1/documents", json={"document": NESTED}).status_code, 422)
                server.assert_not_called()
    def test_public_default_is_generated_contract(self):
        self.assertEqual(runtime.SCHEMA_VERSION, "0.10.1")
        self.assertEqual(runtime.Document.from_dict(CANONICAL).to_dict(), CANONICAL)
        self.assertEqual(runtime.validate_document(CANONICAL), CANONICAL)
        self.assertIn("wireless-network", runtime.DOCUMENT_TYPES)
        self.assertNotIn("operation", runtime.DOCUMENT_TYPES)
        with self.assertRaises(ValueError):
            runtime.validate_document(NESTED)

    def test_public_conformance_adapter_uses_the_generated_wire_shape(self):
        from conformance.adapter import handle
        self.assertEqual(handle({"command": "roundtrip", "document": CANONICAL})["document"], CANONICAL)
        with self.assertRaises(ValueError):
            handle({"command": "roundtrip", "document": NESTED})

    def test_outbound_validates_before_network(self):
        client = StarIntelClient("https://server.example")
        calls = []
        client._client = httpx.Client(transport=httpx.MockTransport(
            lambda request: calls.append(json.loads(request.content)) or httpx.Response(202, json={"accepted": True})),
            base_url="https://server.example")
        try:
            client.submit_document(CANONICAL)
            with self.assertRaises(DocumentValidationError):
                client.submit_document(NESTED)
            with self.assertRaises(DocumentValidationError):
                client.submit_bulk([CANONICAL, NESTED])
            self.assertEqual(calls, [CANONICAL])
        finally:
            client.close()

    def test_canonical_transactional_writer_and_corpus_gate(self):
        from starintel_doc.store import validate_repository
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_db_document(root, CANONICAL)
            self.assertEqual(path, root / "db/person/fixture:person.ndjson")
            self.assertEqual(json.loads(path.read_text()), CANONICAL)
            self.assertTrue(validate_repository(root)["ok"])
            relation = {"id": "fixture:relation", "dtype": "relation", "dataset": "test", "schemaVersion": "0.10.1",
                        "source": {"id": CANONICAL["id"], "schema": "person"},
                        "destination": {"id": "fixture:missing", "schema": "person"}, "predicate": "knows"}
            with self.assertRaises(ValueError):
                write_db_document(root, relation)
            self.assertFalse((root / "db/relation/fixture:relation.ndjson").exists())
            (root / "schemas").mkdir()
            shutil.copy2(ROOT / "schemas/starintel-doc-v0.10.1.schema.json", root / "schemas")
            checked = subprocess.run([str(ROOT / "bin/starintel-validate"), "--root", str(root)], text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_cli_inventory_and_release_have_one_authority(self):
        result = subprocess.run([sys.executable, "scripts/starintel.py", "types"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(len(result.stdout.splitlines()), 60)
        state = json.loads(subprocess.check_output([sys.executable, "scripts/schema-release.py", "current", "--json"], cwd=ROOT))
        self.assertEqual(state["canonical_repository"], "lost-rob0t/star-lang")
        self.assertEqual(state["release_version"], "0.10.1")
        result = subprocess.run([sys.executable, "scripts/schema-release.py", "bump", "--to", "0.10.2"], cwd=ROOT, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"StarLang", result.stderr)
