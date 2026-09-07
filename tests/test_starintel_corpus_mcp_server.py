from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.starintel_corpus_mcp_server import (
    TOOLS,
    ToolError,
    optional_limit,
    require_doc_id,
    require_query,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SCRIPT = REPO_ROOT / "agents" / "starintel_corpus_mcp_server.py"
UNREACHABLE_URL = "http://127.0.0.1:1"

EXAMPLE_DOCUMENT = {
    "_id": "starintel:org:example-corp",
    "dtype": "org",
    "dataset": "example-fixture",
    "schema_version": "0.9.0",
    "version": 1,
    "title": "Example Corp",
    "summary": "Example Corp makes example widgets in Exampleville.",
    "data": {"name": "Example Corp"},
    "sources": [],
    "evidence": [],
    "uncertainty": [],
    "lineage": [],
    "assessment": {},
    "extensions": {},
}

PACKET_DOCUMENT = {
    "_id": "starintel:person:fixture-person",
    "dtype": "person",
    "dataset": "example-fixture",
    "schema_version": "0.9.0",
    "version": 1,
    "title": "Fixture Person",
    "summary": "Fixture Person directs Example Corp.",
    "data": {"name": "Fixture Person"},
    "sources": [],
    "evidence": [],
    "uncertainty": [],
    "lineage": [],
    "assessment": {},
    "extensions": {},
}


def compact(document: dict) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_fixture_corpus(root: Path) -> None:
    db_dir = root / "db" / "org"
    db_dir.mkdir(parents=True)
    (db_dir / "starintel:org:example-corp.ndjson").write_text(
        compact(EXAMPLE_DOCUMENT) + "\n", encoding="utf-8")
    packet_dir = root / "digs" / "example" / "2026-09-06-fixture"
    packet_dir.mkdir(parents=True)
    (packet_dir / "starintel-documents.jsonl").write_text(
        compact(PACKET_DOCUMENT) + "\n", encoding="utf-8")


class McpSession:
    def __init__(self, root: Path, env: dict[str, str]) -> None:
        process_env = dict(os.environ)
        process_env.update(env)
        self._process = subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT), "--root", str(root)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=process_env,
            text=True,
        )

    def request(self, payload: dict) -> dict:
        assert self._process.stdin is not None
        assert self._process.stdout is not None
        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()
        line = self._process.stdout.readline()
        assert line, "server closed stdout before answering"
        return json.loads(line)

    def notify(self, payload: dict) -> None:
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(payload) + "\n")
        self._process.stdin.flush()

    def close(self) -> None:
        if self._process.stdin is not None:
            self._process.stdin.close()
        self._process.wait(timeout=30)
        for stream in (self._process.stdout, self._process.stderr):
            if stream is not None:
                stream.close()

    def call(self, request_id: int, name: str, arguments: dict) -> dict:
        response = self.request(
            {"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
             "params": {"name": name, "arguments": arguments}})
        result = response["result"]
        assert result["content"][0]["type"] == "text"
        payload = json.loads(result["content"][0]["text"])
        return {"is_error": result.get("isError", False), "payload": payload}


class FakeAPIHandler(BaseHTTPRequestHandler):
    server_document = dict(EXAMPLE_DOCUMENT)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        path, _, query = self.path.partition("?")
        if path == "/health":
            self._send({"status": "ok"})
            return
        if path == "/search":
            params = dict(
                pair.partition("=")[::2]
                for pair in query.split("&")
                if "=" in pair
            )
            if params.get("q") == "example" and params.get("limit") == "10":
                self._send({"results": [FakeAPIHandler.server_document]})
            else:
                self._send({"results": []})
            return
        if path.startswith("/document/"):
            doc_id = path[len("/document/"):]
            if doc_id == FakeAPIHandler.server_document["_id"]:
                self._send(FakeAPIHandler.server_document)
            else:
                self.send_response(404)
                self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def _send(self, body: dict) -> None:
        raw = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args: object) -> None:
        pass


class LocalCorpusToolTests(unittest.TestCase):
    def test_stdio_handshake_and_tool_inventory(self) -> None:
        with TemporaryDirectory() as tmp:
            session = McpSession(Path(tmp), {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                response = session.request(
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2025-11-25",
                                "capabilities": {},
                                "clientInfo": {"name": "t", "version": "0"}}})
                result = response["result"]
                self.assertEqual(result["protocolVersion"], "2025-11-25")
                self.assertEqual(result["capabilities"], {"tools": {}})
                self.assertEqual(result["serverInfo"]["name"], "starintel-corpus")
                session.notify({"jsonrpc": "2.0", "method": "notifications/initialized"})
                listing = session.request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
                tools = listing["result"]["tools"]
                self.assertEqual(
                    sorted(tool["name"] for tool in tools),
                    ["starintel_get_document", "starintel_health", "starintel_search"])
                for tool in tools:
                    self.assertIsInstance(tool["inputSchema"], dict)
                    self.assertEqual(tool["inputSchema"]["type"], "object")
            finally:
                session.close()

    def test_unknown_method_answers_jsonrpc_error_for_protocol_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            session = McpSession(Path(tmp), {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                response = session.request(
                    {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {}})
                self.assertEqual(response["id"], 1)
                self.assertEqual(response["error"]["code"], -32601)
            finally:
                session.close()

    def test_search_and_get_document_over_the_local_corpus(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_fixture_corpus(root)
            session = McpSession(root, {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                outcome = session.call(1, "starintel_search",
                                       {"query": "example widgets", "limit": 5})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "local")
                self.assertEqual(outcome["payload"]["count"], 1)
                result = outcome["payload"]["results"][0]
                self.assertEqual(result["_id"], "starintel:org:example-corp")
                self.assertEqual(result["dtype"], "org")
                self.assertEqual(result["surface"], "db")

                outcome = session.call(2, "starintel_get_document",
                                       {"doc_id": "starintel:org:example-corp"})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "local")
                self.assertTrue(outcome["payload"]["found"])
                self.assertEqual(outcome["payload"]["document"]["_id"],
                                 "starintel:org:example-corp")

                outcome = session.call(3, "starintel_get_document",
                                       {"doc_id": "starintel:org:missing"})
                self.assertFalse(outcome["is_error"])
                self.assertFalse(outcome["payload"]["found"])

                outcome = session.call(4, "starintel_health", {})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "local")
                self.assertFalse(outcome["payload"]["server"]["reachable"])
                self.assertTrue(outcome["payload"]["local"]["available"])
                self.assertEqual(outcome["payload"]["local"]["db_documents"], 1)
            finally:
                session.close()

    def test_packet_surface_documents_are_searchable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_fixture_corpus(root)
            session = McpSession(root, {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                outcome = session.call(1, "starintel_search",
                                       {"query": "Fixture Person directs"})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["count"], 1)
                self.assertEqual(outcome["payload"]["results"][0]["surface"], "packet")
            finally:
                session.close()

    def test_invalid_arguments_are_tool_errors_not_crashes(self) -> None:
        with TemporaryDirectory() as tmp:
            session = McpSession(Path(tmp), {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                outcome = session.call(1, "starintel_search", {"query": ""})
                self.assertTrue(outcome["is_error"])
                outcome = session.call(2, "starintel_search", {"query": "x", "limit": 0})
                self.assertTrue(outcome["is_error"])
                outcome = session.call(3, "starintel_search",
                                       {"query": "x", "limit": "ten"})
                self.assertTrue(outcome["is_error"])
                outcome = session.call(4, "starintel_get_document", {"doc_id": "../secrets"})
                self.assertTrue(outcome["is_error"])
                outcome = session.call(5, "no_such_tool", {})
                self.assertTrue(outcome["is_error"])
                # The process stays alive and keeps answering afterwards.
                outcome = session.call(6, "starintel_health", {})
                self.assertFalse(outcome["is_error"])
            finally:
                session.close()

    def test_missing_local_corpus_and_unreachable_server_is_a_tool_error(self) -> None:
        with TemporaryDirectory() as tmp:
            session = McpSession(Path(tmp), {"STARINTEL_SERVER_URL": UNREACHABLE_URL})
            try:
                outcome = session.call(1, "starintel_search", {"query": "anything"})
                self.assertTrue(outcome["is_error"])
                self.assertIn("no StarIntel corpus backend", outcome["payload"]["error"])
            finally:
                session.close()


class ServerAPIBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), FakeAPIHandler)
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=10)

    def test_server_backend_answers_and_404_is_definitive(self) -> None:
        url = f"http://127.0.0.1:{self._port}"
        with TemporaryDirectory() as tmp:
            session = McpSession(Path(tmp), {"STARINTEL_SERVER_URL": url})
            try:
                outcome = session.call(1, "starintel_search",
                                       {"query": "example", "limit": 10})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "server")
                self.assertEqual(outcome["payload"]["count"], 1)
                self.assertEqual(outcome["payload"]["results"][0]["_id"],
                                 "starintel:org:example-corp")

                outcome = session.call(2, "starintel_get_document",
                                       {"doc_id": "starintel:org:example-corp"})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "server")
                self.assertEqual(outcome["payload"]["document"]["_id"],
                                 "starintel:org:example-corp")

                # A connected server answering 404 is definitive: the empty
                # local corpus must not be consulted as a fallback.
                outcome = session.call(3, "starintel_get_document",
                                       {"doc_id": "starintel:org:missing"})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "server")
                self.assertFalse(outcome["payload"]["found"])

                outcome = session.call(4, "starintel_health", {})
                self.assertFalse(outcome["is_error"])
                self.assertEqual(outcome["payload"]["backend"], "server")
                self.assertTrue(outcome["payload"]["server"]["reachable"])
            finally:
                session.close()


class ArgumentValidatorTests(unittest.TestCase):
    def test_query_must_be_a_non_empty_string(self) -> None:
        self.assertEqual(require_query({"query": " flock safety "}), "flock safety")
        for bad in ("", "   ", 42, None):
            with self.assertRaises(ToolError):
                require_query({"query": bad})

    def test_limit_defaults_and_bounds(self) -> None:
        self.assertEqual(optional_limit({}), 10)
        self.assertEqual(optional_limit({"limit": 1}), 1)
        self.assertEqual(optional_limit({"limit": 20}), 20)
        for bad in (0, 21, -1, "10", 3.5, True):
            with self.assertRaises(ToolError):
                optional_limit({"limit": bad})

    def test_doc_id_rejects_path_traversal(self) -> None:
        self.assertEqual(require_doc_id({"doc_id": " starintel:org:x "}),
                         "starintel:org:x")
        for bad in ("", "  ", "../secrets", "db/../x", "a/b", "a\\b"):
            with self.assertRaises(ToolError):
                require_doc_id({"doc_id": bad})

    def test_wire_tool_inventory_matches_dispatched_names(self) -> None:
        self.assertEqual(
            sorted(tool["name"] for tool in TOOLS),
            ["starintel_get_document", "starintel_health", "starintel_search"])


if __name__ == "__main__":
    unittest.main()
