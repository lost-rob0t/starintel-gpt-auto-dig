from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import importlib.util

_spec_path = (Path(__file__).resolve().parents[1] /
              "scripts" / "serve-spec.py")
_spec_spec = importlib.util.spec_from_file_location("serve_spec", _spec_path)
serve_spec = importlib.util.module_from_spec(_spec_spec)
_spec_spec.loader.exec_module(serve_spec)

ROOT = Path(__file__).resolve().parents[1]


class SpecServingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = serve_spec.SpecRegistry(ROOT, "https://spec.example")
        assert "0.10.1" in cls.registry.releases
        handler = type("Bound", (serve_spec.SpecHandler,),
                       {"registry": cls.registry})
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(
                f"http://127.0.0.1:{self.port}{path}", timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read()

    def test_index_lists_releases(self):
        status, _, body = self.get("/releases")
        self.assertEqual(status, 200)
        index = json.loads(body)
        self.assertIn("0.10.1", index["releases"])
        self.assertTrue(index["served_commit"])

    def test_schema_by_version_and_by_id_shape(self):
        status, _, body = self.get("/schema/0.10.1")
        self.assertEqual(status, 200)
        schema = json.loads(body)
        self.assertTrue(schema["title"].startswith("StarIntel Document"))
        status_id, _, _ = self.get(
            "/schema/starintel-doc-v0.10.1.schema.json")
        self.assertEqual(status_id, 200)

    def test_star_export_served_with_digest(self):
        status, headers, body = self.get("/star/0.10.1")
        self.assertEqual(status, 200)
        self.assertIn(b"org.starintel/core@1", body)
        self.assertEqual(headers.get("Cache-Control"),
                         "public, max-age=31536000, immutable")

    def test_lock_pins_canonical_commit_and_digests(self):
        status, _, body = self.get("/lock/0.10.1")
        self.assertEqual(status, 200)
        lock = json.loads(body)
        self.assertEqual(lock["release_version"], "0.10.1")
        self.assertEqual(lock["canonical_repository"],
                         "lost-rob0t/starintel-gpt-auto-dig")
        self.assertTrue(lock["canonical_commit"])
        self.assertTrue(lock["star_import_digest"].startswith("sha256:"))
        self.assertTrue(lock["http"]["star"].endswith("/star/0.10.1"))

    def test_sums_match_served_artifacts(self):
        _, _, sums = self.get("/sha256/0.10.1")
        entries = {parts[1]: parts[0] for parts in (line.split() for line in sums.decode().splitlines())}
        _, _, star = self.get("/star/0.10.1")
        import hashlib
        self.assertEqual(hashlib.sha256(star).hexdigest(),
                         entries["starintel-core-0.10.1.star"])

    def test_unknown_release_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get("/lock/0.0.0")
        self.assertEqual(caught.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
