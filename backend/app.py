"""Auto Dig typed backend API.

Versioned surface under /api/v1. Mutations are idempotent where retries can
happen. Validation is strict StarIntel v0.9; invalid documents are rejected
with typed 422s and never reach persistence.

    capabilities, runs (list/get/create/start/pause/resume/stop),
    progress, results/documents, health, readiness
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .config import BackendConfig, load_config
from .runs import RunStore, RunError, utc_now
from .validation import DocumentValidationError, validate_v09
from .server_client import StarIntelClient, StarIntelServerError

API = "/api/v1"
SCHEMA_VERSION = "0.9.0"
BACKEND_VERSION = "0.1.0"


class CreateRunBody(BaseModel):
    run_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    target: str = Field(min_length=1, max_length=80)
    description: str = ""


class ProgressBody(BaseModel):
    documents: int | None = Field(default=None, ge=0)
    notes: str = Field(default="", max_length=4000)


class DocumentInBody(BaseModel):
    document: dict[str, Any]


def dtypes() -> list[str]:
    try:
        from starintel_doc import TYPE_FIELDS

        return sorted(TYPE_FIELDS.keys())
    except Exception:
        return []


def create_app(cfg: BackendConfig | None = None) -> FastAPI:
    cfg = cfg or load_config()
    store = RunStore(cfg)
    app = FastAPI(
        title="StarIntel Auto Dig Backend",
        version=BACKEND_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    def guard(exc: RunError) -> HTTPException:
        return HTTPException(status_code=exc.status, detail=str(exc))

    @app.get(f"{API}/capabilities")
    def capabilities() -> dict[str, Any]:
        return {
            "backend": "starintel-auto-dig",
            "backend_version": BACKEND_VERSION,
            "schema_version": SCHEMA_VERSION,
            "dtypes": dtypes(),
            "run_root": str(cfg.digs_root.relative_to(cfg.root)) if cfg.digs_root.exists() else "digs",
            "actions": ["start", "pause", "resume", "stop"],
            "ingest": ["submit_document", "submit_bulk"],
        }

    @app.get(f"{API}/runs")
    def list_runs() -> dict[str, Any]:
        return {"runs": store.list_runs(), "count": len(store.list_runs())}

    @app.post(f"{API}/runs", status_code=201)
    def create_run(body: CreateRunBody, idempotency_key: str | None = Header(default=None)) -> dict[str, Any]:
        try:
            record = store.create_run(body.run_id, body.target, body.description)
            if idempotency_key:
                record.setdefault("idempotency_keys", [])
                if idempotency_key not in record["idempotency_keys"]:
                    record["idempotency_keys"].append(idempotency_key)
                    store._write(record)  # noqa: SLF001 - same-module state owner
            return record
        except RunError as exc:
            raise guard(exc) from exc

    @app.get(f"{API}/runs/{{run_id}}")
    def get_run(run_id: str) -> dict[str, Any]:
        try:
            return store.get_run(run_id)
        except RunError as exc:
            raise guard(exc) from exc

    @app.post(f"{API}/runs/{{run_id}}/progress")
    def record_progress(run_id: str, body: ProgressBody) -> dict[str, Any]:
        try:
            record = store.record_progress(run_id, body.documents, body.notes)
            return {"run_id": run_id, "state": record["state"], "progress": record["progress"]}
        except RunError as exc:
            raise guard(exc) from exc

    @app.get(f"{API}/runs/{{run_id}}/progress")
    def run_progress(run_id: str) -> dict[str, Any]:
        try:
            record = store.get_run(run_id)
            return {
                "run_id": run_id,
                "state": record["state"],
                "progress": record.get("progress", {}),
                "updated_at": record["updated_at"],
            }
        except RunError as exc:
            raise guard(exc) from exc

    @app.post(f"{API}/runs/{{run_id}}/{{action}}")
    def run_action(
        run_id: str,
        action: Literal["start", "pause", "resume", "stop"],
        idempotency_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        try:
            return store.transition(run_id, action, idempotency_key)
        except RunError as exc:
            raise guard(exc) from exc

    @app.get(f"{API}/runs/{{run_id}}/documents")
    def run_documents(
        run_id: str,
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        try:
            return store.run_documents(run_id, limit, offset)
        except RunError as exc:
            raise guard(exc) from exc

    @app.post(f"{API}/documents", status_code=202)
    def submit_document(body: DocumentInBody) -> dict[str, Any]:
        """Validate and forward one document to the StarIntel server."""
        try:
            validate_v09(body.document)
        except DocumentValidationError as exc:
            raise HTTPException(status_code=422, detail=f"invalid_document_schema: {exc}") from exc
        client = StarIntelClient(cfg.server_url, cfg.server_token, cfg.server_timeout)
        try:
            result = client.submit_document(body.document)
        except (StarIntelServerError, DocumentValidationError) as exc:
            raise HTTPException(status_code=502, detail=f"server_unavailable: {exc}") from exc
        finally:
            client.close()
        return {"accepted": True, "result": result}

    @app.get(f"{API}/search")
    def search(query: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
        client = StarIntelClient(cfg.server_url, cfg.server_token, cfg.server_timeout)
        try:
            return {"results": client.search(query, limit)}
        except StarIntelServerError as exc:
            raise HTTPException(status_code=502, detail=f"server_unavailable: {exc}") from exc
        finally:
            client.close()

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "version": BACKEND_VERSION, "at": utc_now()}

    @app.get("/readyz")
    def readyz() -> dict[str, Any]:
        checks: dict[str, str] = {}
        checks["corpus"] = "ok" if (cfg.db_root / "document").is_dir() else "missing"
        checks["digs"] = "ok" if cfg.digs_root.is_dir() else "missing"
        try:
            client = StarIntelClient(cfg.server_url, cfg.server_token, cfg.server_timeout)
            client.health()
            checks["starintel_server"] = "ok"
        except Exception:
            checks["starintel_server"] = "unavailable"
        status = "ready" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": status, "checks": checks, "at": utc_now()}

    return app


app = create_app()
