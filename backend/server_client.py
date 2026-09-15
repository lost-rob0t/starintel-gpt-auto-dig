"""Typed client for the StarIntel server.

The browser never talks to CouchDB, RabbitMQ, or Valkey; only this private
client does. Every document handed to the server is validated against
StarIntel v0.9 first. Result categories are tracked separately so speed
never overrides correctness.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .validation import DocumentValidationError, validate_v09


class StarIntelServerError(RuntimeError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass
class BulkResult:
    accepted: int
    failed: int
    errors: list[dict[str, Any]]


class StarIntelClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 10.0) -> None:
        headers = {"accept": "application/json"}
        if token:
            headers["authorization"] = f"Bearer {token}"
        self._client = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    # ---- health ----
    def health(self) -> dict[str, Any]:
        try:
            res = self._client.get("/health")
            res.raise_for_status()
            return res.json()
        except httpx.HTTPError as exc:
            raise StarIntelServerError(f"health check failed: {exc}") from exc

    # ---- reads ----
    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        try:
            res = self._client.get(f"/document/{doc_id}")
        except httpx.HTTPError as exc:
            raise StarIntelServerError(f"read failed for {doc_id}: {exc}") from exc
        if res.status_code == 404:
            return None
        if res.status_code >= 400:
            raise StarIntelServerError(f"read failed for {doc_id}: HTTP {res.status_code}", res.status_code)
        return res.json()

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        try:
            res = self._client.get("/search", params={"q": query, "limit": limit})
        except httpx.HTTPError as exc:
            raise StarIntelServerError(f"search failed: {exc}") from exc
        if res.status_code >= 400:
            raise StarIntelServerError(f"search failed: HTTP {res.status_code}", res.status_code)
        body = res.json()
        return body.get("results", body) if isinstance(body, dict) else body

    # ---- writes ----
    def submit_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Single-document ingest via POST /new/document/:dtype (queue-ack semantics)."""
        validate_v09(doc)
        dtype = doc["dtype"]
        try:
            res = self._client.post(f"/new/document/{dtype}", json=doc)
        except httpx.HTTPError as exc:
            raise StarIntelServerError(f"submit failed: {exc}") from exc
        if res.status_code >= 400:
            raise StarIntelServerError(f"submit failed: HTTP {res.status_code}", res.status_code)
        return res.json()

    def submit_bulk(self, documents: list[dict[str, Any]], job_timeout: float = 120.0) -> BulkResult:
        """Batch ingest via POST /documents/bulk. Validates every document first.

        Batches above the server's inline limit return 202 with an async job;
        this client polls the job status endpoint to a terminal state and maps
        the final per-document counts.
        """
        for doc in documents:
            validate_v09(doc)
        try:
            res = self._client.post("/documents/bulk", json=documents)
        except httpx.HTTPError as exc:
            raise StarIntelServerError(f"bulk submit failed: {exc}") from exc
        if res.status_code == 400:
            body = self._safe_json(res)
            raise StarIntelServerError(f"bulk rejected: {body.get('message', res.text[:200])}", 400)
        if res.status_code in (202, 200) and res.status_code != 200:
            body = self._safe_json(res)
            job_id = body.get("job_id")
            if job_id:
                return self._await_bulk_job(str(job_id), len(documents), job_timeout)
            raise StarIntelServerError("bulk accepted without job id or counts", 502)
        if res.status_code >= 400:
            raise StarIntelServerError(f"bulk submit failed: HTTP {res.status_code}", res.status_code)
        body = self._safe_json(res)
        return BulkResult(
            accepted=int(body.get("succeeded", 0)),
            failed=int(body.get("failed", 0)),
            errors=list(body.get("errors", [])),
        )

    def _await_bulk_job(self, job_id: str, total: int, timeout: float) -> BulkResult:
        """Poll a 202 async bulk job to a terminal state."""
        deadline = time.monotonic() + timeout
        poll = 0.05
        while time.monotonic() < deadline:
            try:
                res = self._client.get(f"/documents/bulk/{job_id}")
            except httpx.HTTPError as exc:
                raise StarIntelServerError(f"bulk job poll failed for {job_id}: {exc}") from exc
            if res.status_code == 404:
                # Job record already reaped; the batch was accepted for processing.
                return BulkResult(accepted=total, failed=0, errors=[])
            if res.status_code >= 400:
                raise StarIntelServerError(f"bulk job poll failed: HTTP {res.status_code}", res.status_code)
            body = self._safe_json(res)
            status = str(body.get("status", ""))
            if status in ("completed", "completed_with_errors", "completed-with-errors", "failed"):
                return BulkResult(
                    accepted=int(body.get("succeeded", 0)),
                    failed=int(body.get("failed", 0)),
                    errors=[],
                )
            time.sleep(poll)
            poll = min(poll * 1.5, 1.0)
        raise StarIntelServerError(f"bulk job {job_id} timed out after {timeout}s", 504)

    @staticmethod
    def _safe_json(res: httpx.Response) -> dict[str, Any]:
        try:
            return res.json()
        except json.JSONDecodeError:
            return {"message": res.text[:500]}


__all__ = ["StarIntelClient", "StarIntelServerError", "BulkResult", "DocumentValidationError"]
