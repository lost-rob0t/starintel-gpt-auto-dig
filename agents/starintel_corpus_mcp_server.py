#!/usr/bin/env python3
"""StarIntel corpus MCP stdio server for the Auto-Dig harness.

Speaks MCP 2025-11-25 over newline-delimited JSON-RPC 2.0 on stdio and
exposes exactly three read-only tools over the StarIntel corpus:

  - starintel_search(query, limit)
  - starintel_get_document(doc_id)
  - starintel_health()

The preferred backend is the StarIntel server API
(STARINTEL_SERVER_URL, authenticated with STARINTEL_TOKEN when present).
When the API is not reachable, the tools fall back to the on-disk corpus
(starintel_doc.store over the repository root) with the same result
shapes, so both backends produce interchangeable results.

This process is started only by the trusted host policy in
agents/auto_dig_mcp_tools.pl. It never writes, executes anything, or
logs secrets; every capability it exposes is read-only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2025-11-25"
SERVER_NAME = "starintel-corpus"
SERVER_VERSION = "0.9.0"
DEFAULT_SERVER_URL = "http://127.0.0.1:5000"
API_TIMEOUT_SECONDS = 5.0
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 20

REPO_ROOT = Path(__file__).resolve().parents[1]

IDENTITY_KEYS = ("_id", "dtype", "dataset", "title", "summary")


class ToolError(Exception):
    """Raised for invalid tool arguments or unavailable backends."""


class ServerAPIError(Exception):
    """Transport-level failure while talking to the StarIntel server API."""


class HTTPStatusError(ServerAPIError):
    """The StarIntel server API answered with a non-2xx status."""

    def __init__(self, code: int) -> None:
        super().__init__(f"StarIntel server answered HTTP {code}")
        self.code = code


# ---------------------------------------------------------------------------
# StarIntel server API backend
# ---------------------------------------------------------------------------


class StarIntelServerAPI:
    def __init__(self, base_url: str, token: str | None,
                 timeout: float = API_TIMEOUT_SECONDS) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = ""
        if params:
            pairs = [
                f"{key}={urllib.request.quote(str(value), safe='')}"
                for key, value in params.items()
            ]
            query = "?" + "&".join(pairs)
        url = f"{self._base_url}{path}{query}"
        headers = {"accept": "application/json"}
        if self._token:
            headers["authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise HTTPStatusError(exc.code) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ServerAPIError(f"StarIntel server unreachable: {exc}") from exc
        if not body.strip():
            return {}
        try:
            return json.loads(body)
        except ValueError as exc:
            raise ServerAPIError(f"StarIntel server returned invalid JSON: {exc}") from exc

    def health(self) -> dict[str, Any]:
        self._request("/health")
        return {"status": "ok"}

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        body = self._request("/search", params={"q": query, "limit": limit})
        if isinstance(body, dict):
            results = body.get("results", [])
        elif isinstance(body, list):
            results = body
        else:
            raise ServerAPIError("StarIntel server search returned an unsupported body")
        if not isinstance(results, list):
            raise ServerAPIError("StarIntel server search results are not a list")
        return [item for item in results if isinstance(item, dict)]

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        try:
            body = self._request(f"/document/{urllib.request.quote(doc_id, safe=':')}")
        except HTTPStatusError as exc:
            if exc.code == 404:
                return None
            raise
        if not isinstance(body, dict):
            raise ServerAPIError("StarIntel server document body is not an object")
        return body


# ---------------------------------------------------------------------------
# On-disk corpus fallback backend
# ---------------------------------------------------------------------------


class LocalCorpus:
    def __init__(self, root: Path) -> None:
        self._root = root

    def available(self) -> bool:
        return (self._root / "db").is_dir() or (self._root / "digs").is_dir()

    def _store(self):
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        try:
            from starintel_doc import store
        except ImportError as exc:  # pragma: no cover - depends on checkout layout
            raise ToolError(f"local corpus backend unavailable: {exc}") from exc
        return store

    def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        store = self._store()
        documents = store.iter_corpus(self._root, include_db=True, include_packets=True)
        matches = store.search_documents(documents, query=query)[:limit]
        return [self._located_summary(item) for item in matches]

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        store = self._store()
        documents = store.iter_corpus(self._root, include_db=True, include_packets=True)
        for item in store.search_documents(documents, doc_id=doc_id):
            if item.document.get("_id") == doc_id:
                return item.document
        return None

    def stats(self) -> dict[str, Any]:
        db_documents = 0
        db_root = self._root / "db"
        if db_root.is_dir():
            for path in db_root.rglob("*.ndjson"):
                if path.is_file():
                    db_documents += 1
        try:
            packets = len(self._store().packet_paths(self._root))
        except ToolError:
            packets = 0
        return {"available": self.available(),
                "db_documents": db_documents,
                "packets": packets}

    @staticmethod
    def _located_summary(item) -> dict[str, Any]:
        summary = summarize_document(item.document)
        summary["path"] = str(item.path)
        summary["line"] = item.line
        summary["surface"] = item.surface
        return summary


def summarize_document(document: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in IDENTITY_KEYS:
        value = document.get(key, "")
        summary[key] = value if isinstance(value, str) else ""
    return summary


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


class CorpusTools:
    def __init__(self, server_api: StarIntelServerAPI, local: LocalCorpus) -> None:
        self._api = server_api
        self._local = local

    def search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = require_query(arguments)
        limit = optional_limit(arguments)
        backend = "server"
        results: list[dict[str, Any]] | None = None
        server_error: str | None = None
        try:
            results = [summarize_document(item) for item in self._api.search(query, limit)]
        except ServerAPIError as exc:
            server_error = str(exc)
            backend = "local"
        if results is None:
            results = self._local_results(query, limit)
        return {"backend": backend,
                "query": query,
                "limit": limit,
                "server_error": server_error,
                "count": len(results),
                "results": results}

    def get_document(self, arguments: dict[str, Any]) -> dict[str, Any]:
        doc_id = require_doc_id(arguments)
        try:
            document = self._api.get_document(doc_id)
            backend = "server"
        except ServerAPIError:
            backend = "local"
            document = self._local_document(doc_id)
        if document is None:
            return {"backend": backend, "found": False, "doc_id": doc_id}
        return {"backend": backend, "found": True, "doc_id": doc_id,
                "document": document}

    def health(self) -> dict[str, Any]:
        try:
            server_status = {"reachable": True, **self._api.health()}
        except ServerAPIError as exc:
            server_status = {"reachable": False, "error": str(exc)}
        local_stats = self._local.stats() if self._local.available() else {
            "available": False, "db_documents": 0, "packets": 0}
        backend = "server" if server_status.get("reachable") else "local"
        return {"status": "ok",
                "backend": backend,
                "server": server_status,
                "local": local_stats}

    def _local_results(self, query: str, limit: int) -> list[dict[str, Any]]:
        self._require_local()
        return self._local.search(query, limit)

    def _local_document(self, doc_id: str) -> dict[str, Any] | None:
        self._require_local()
        return self._local.get_document(doc_id)

    def _require_local(self) -> None:
        if not self._local.available():
            raise ToolError("no StarIntel corpus backend is available: "
                            "the server API is unreachable and the on-disk "
                            "corpus is missing")


def require_query(arguments: dict[str, Any]) -> str:
    query = arguments.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ToolError("query must be a non-empty string")
    return query.strip()


def optional_limit(arguments: dict[str, Any]) -> int:
    raw = arguments.get("limit")
    if raw is None:
        return DEFAULT_SEARCH_LIMIT
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ToolError("limit must be an integer")
    if not 1 <= raw <= MAX_SEARCH_LIMIT:
        raise ToolError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}")
    return raw


def require_doc_id(arguments: dict[str, Any]) -> str:
    doc_id = arguments.get("doc_id")
    if not isinstance(doc_id, str) or not doc_id.strip():
        raise ToolError("doc_id must be a non-empty string")
    if "/" in doc_id or "\\" in doc_id or ".." in doc_id:
        raise ToolError("doc_id must not contain path separators")
    return doc_id.strip()


# ---------------------------------------------------------------------------
# MCP 2025-11-25 wire surface
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "starintel_search",
        "description": (
            "Search the StarIntel corpus of already-materialized documents "
            "(canonical DB records and research packet records) for a "
            "subject. Consult this before creating new identities so "
            "existing StarIntel _id values are reused instead of "
            "duplicated. Returns matching records with their _id, dtype, "
            "dataset, title, and summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms matched across StarIntel documents.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_SEARCH_LIMIT,
                    "description": "Maximum results to return (default 10).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "starintel_get_document",
        "description": (
            "Fetch one complete StarIntel v0.9 document by its exact _id "
            "(for example starintel:org:flock-safety). Returns the full "
            "document, or found:false when no such document exists."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Exact StarIntel document _id.",
                },
            },
            "required": ["doc_id"],
        },
    },
    {
        "name": "starintel_health",
        "description": (
            "Report StarIntel corpus availability: whether the StarIntel "
            "server API is reachable and whether the on-disk corpus "
            "fallback is available. Takes no arguments."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def call_tool(tools: CorpusTools, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "starintel_search":
        return tools.search(arguments)
    if name == "starintel_get_document":
        return tools.get_document(arguments)
    if name == "starintel_health":
        return tools.health()
    raise ToolError(f"unknown tool: {name}")


def handle_request(tools: CorpusTools, message: dict[str, Any]) -> dict[str, Any]:
    method = message.get("method", "")
    request_id = message.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": initialize_result()}
    if method == "notifications/initialized" or request_id is None:
        # Notifications never get a response; a response line here would
        # desynchronize the client's next exchange.
        return {}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict):
            return error_response(request_id, -32602, "tools/call params must be an object")
        name = params.get("name")
        raw_arguments = params.get("arguments", {})
        if not isinstance(name, str) or not name:
            return error_response(request_id, -32602, "tools/call name must be a string")
        if not isinstance(raw_arguments, dict):
            return error_response(request_id, -32602, "tools/call arguments must be an object")
        try:
            payload = call_tool(tools, name, raw_arguments)
        except ToolError as exc:
            return {"jsonrpc": "2.0", "id": request_id,
                    "result": {"content": [text_content({"error": str(exc)})],
                               "isError": True}}
        return {"jsonrpc": "2.0", "id": request_id,
                "result": {"content": [text_content(payload)], "isError": False}}
    # Unknown methods answer with a JSON-RPC error: this is what makes the
    # pinned runtime's 2026-07-28 server/discover probe fail fast so the
    # client falls back to this 2025-11-25 protocol.
    return error_response(request_id, -32601, f"Method not found: {method}")


def text_content(payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": "text",
            "text": json.dumps(payload, ensure_ascii=False, sort_keys=True)}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": code, "message": message}}


def serve(in_stream: Any, out_stream: Any, tools: CorpusTools) -> None:
    while True:
        line = in_stream.readline()
        if not line:
            return
        stripped = line.strip()
        if not stripped:
            continue
        try:
            message = json.loads(stripped)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        response = handle_request(tools, message)
        if not response:
            continue
        out_stream.write(json.dumps(response, ensure_ascii=False, sort_keys=True))
        out_stream.write("\n")
        out_stream.flush()


def build_tools(root: Path, server_url: str, token: str | None) -> CorpusTools:
    api = StarIntelServerAPI(server_url, token)
    local = LocalCorpus(root)
    return CorpusTools(api, local)


def resolve_root(argument_root: str | None) -> Path:
    if argument_root:
        return Path(argument_root).resolve()
    return REPO_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="StarIntel corpus read-only MCP stdio server for Auto-Dig")
    parser.add_argument("--root", default=None,
                        help="corpus root for the on-disk fallback backend")
    args = parser.parse_args(argv)
    root = resolve_root(args.root)
    server_url = (os.environ.get("STARINTEL_SERVER_URL") or "").strip() or DEFAULT_SERVER_URL
    token = (os.environ.get("STARINTEL_TOKEN") or "").strip() or None
    tools = build_tools(root, server_url, token)
    try:
        serve(sys.stdin, sys.stdout, tools)
    except BrokenPipeError:  # pragma: no cover - client teardown race
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
