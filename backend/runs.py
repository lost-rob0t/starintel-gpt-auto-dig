"""Durable, restartable run state for the Auto Dig backend.

Auto Dig research is executed by agent actors; this backend owns the
coordination surface: run records, lifecycle state, and progress, persisted
as JSON on disk so the process can restart without losing state.

Lifecycle (fail closed):
    created -> running -> paused -> running -> completed
                                  \-> stopped
    any -> failed
Illegal transitions are rejected with 409.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import BackendConfig
from .validation import DocumentValidationError, validate_v09, validate_v09_line

RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "created": {"running", "stopped", "failed"},
    "running": {"paused", "completed", "stopped", "failed"},
    "paused": {"running", "stopped", "failed"},
    "stopped": set(),
    "completed": set(),
    "failed": set(),
}

TERMINAL_STATES = {"stopped", "completed", "failed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunError(ValueError):
    """Typed run error carrying an HTTP status."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


class RunStore:
    def __init__(self, cfg: BackendConfig) -> None:
        self.cfg = cfg
        self.cfg.runs_state_root.mkdir(parents=True, exist_ok=True)

    # ---- persistence ----
    def _path(self, run_id: str) -> Path:
        if not RUN_ID_RE.match(run_id):
            raise RunError("run_id must match ^[a-z0-9][a-z0-9-]{0,79}$", 400)
        return self.cfg.resolve_state_path(run_id)

    def _read(self, run_id: str) -> dict[str, Any] | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, record: dict[str, Any]) -> None:
        path = self._path(record["run_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(record, handle, sort_keys=True, indent=2)
                handle.write("\n")
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ---- discovery ----
    def discovered_runs(self) -> list[dict[str, Any]]:
        """Runs present as digs/<target>/<run>/ artifacts on disk."""
        out: list[dict[str, Any]] = []
        digs = self.cfg.digs_root
        if not digs.is_dir():
            return out
        for target in sorted(p for p in digs.iterdir() if p.is_dir()):
            for run in sorted(p for p in target.iterdir() if p.is_dir()):
                jsonl = run / "starintel-documents.jsonl"
                if not jsonl.is_file():
                    continue
                out.append(
                    {
                        "run_id": run.name,
                        "target": target.name,
                        "path": str(run.relative_to(self.cfg.root)),
                        "artifact": str(jsonl.relative_to(self.cfg.root)),
                    }
                )
        return out

    # ---- operations ----
    def create_run(self, run_id: str, target: str, description: str = "") -> dict[str, Any]:
        record = self._read(run_id)
        if record is not None:
            # Idempotent create: returning the existing record is correct.
            return record
        artifact = self.cfg.digs_root / target / run_id / "starintel-documents.jsonl"
        record = {
            "run_id": run_id,
            "target": target,
            "description": description,
            "state": "created",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "artifact": str(artifact.relative_to(self.cfg.root)),
            "history": [{"state": "created", "at": utc_now()}],
            "progress": {"documents": 0, "notes": ""},
        }
        self._write(record)
        return record

    def get_run(self, run_id: str) -> dict[str, Any]:
        record = self._read(run_id)
        if record is None:
            raise RunError(f"run not found: {run_id}", 404)
        return record

    def transition(self, run_id: str, action: str, idempotency_key: str | None = None) -> dict[str, Any]:
        record = self.get_run(run_id)
        current: str = record["state"]
        target_state = {"start": "running", "pause": "paused", "resume": "running", "stop": "stopped"}.get(action)
        if target_state is None:
            raise RunError(f"unknown action: {action}", 400)
        if idempotency_key and record.get("last_idempotency_key") == idempotency_key:
            return record
        if current in TERMINAL_STATES:
            raise RunError(f"run {run_id} is terminal ({current}); transition refused", 409)
        if target_state not in ALLOWED_TRANSITIONS.get(current, set()):
            raise RunError(f"illegal transition {current} -> {target_state}", 409)
        record["state"] = target_state
        record["updated_at"] = utc_now()
        record.setdefault("history", []).append({"state": target_state, "at": record["updated_at"]})
        if idempotency_key:
            record["last_idempotency_key"] = idempotency_key
        self._write(record)
        return record

    def record_progress(self, run_id: str, documents: int | None = None, notes: str = "") -> dict[str, Any]:
        record = self.get_run(run_id)
        progress = record.setdefault("progress", {"documents": 0, "notes": ""})
        if documents is not None:
            if documents < 0:
                raise RunError("documents count must be >= 0", 400)
            progress["documents"] = documents
        if notes:
            progress["notes"] = notes[:4000]
        record["updated_at"] = utc_now()
        self._write(record)
        return record

    def mark_failed(self, run_id: str, reason: str) -> dict[str, Any]:
        record = self.get_run(run_id)
        if record["state"] in TERMINAL_STATES:
            return record
        record["state"] = "failed"
        record["updated_at"] = utc_now()
        record.setdefault("history", []).append({"state": "failed", "at": record["updated_at"], "reason": reason[:500]})
        self._write(record)
        return record

    def list_runs(self) -> list[dict[str, Any]]:
        by_id: dict[str, dict[str, Any]] = {}
        for discovered in self.discovered_runs():
            by_id[discovered["run_id"]] = {**discovered, "state": "on-disk", "source": "discovered"}
        for path in sorted(self.cfg.runs_state_root.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            run_id = record.get("run_id")
            if not run_id:
                continue
            merged = {**by_id.get(run_id, {}), **record}
            merged["run_id"] = run_id
            merged["source"] = "discovered" if run_id in by_id else "state"
            by_id[run_id] = merged
        return sorted(by_id.values(), key=lambda r: r.get("updated_at", ""), reverse=True)

    # ---- documents ----
    def run_documents(self, run_id: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        record = self.get_run(run_id)
        artifact = self.cfg.root / str(record.get("artifact", ""))
        if not artifact.is_file():
            return {"run_id": run_id, "total_valid": 0, "total_invalid": 0, "documents": [], "truncated": False}
        documents: list[dict[str, Any]] = []
        total_valid = 0
        total_invalid = 0
        with artifact.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    doc = validate_v09_line(line)
                except DocumentValidationError:
                    total_invalid += 1
                    continue
                total_valid += 1
                if offset and total_valid <= offset:
                    continue
                if len(documents) < limit:
                    documents.append(doc)
        return {
            "run_id": run_id,
            "total_valid": total_valid,
            "total_invalid": total_invalid,
            "documents": documents,
            "truncated": total_valid > offset + len(documents),
        }
