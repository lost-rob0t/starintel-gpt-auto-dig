from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .store import compact, validate_repository
from .validation import validate_document


class DatabaseWriteError(ValueError):
    """Raised when a canonical database write would violate repository invariants."""


def canonical_db_path(root: Path, document: dict[str, Any]) -> Path:
    """Return the only valid normalized DB path for a validated document."""
    validate_document(document)
    dtype = document["dtype"]
    doc_id = document["_id"]
    if not isinstance(doc_id, str) or not doc_id:
        raise DatabaseWriteError("document _id must be a non-empty string")
    if "/" in doc_id or "\\" in doc_id or doc_id in {".", ".."}:
        raise DatabaseWriteError(f"document _id cannot contain path separators: {doc_id!r}")
    return root.resolve() / "db" / dtype / f"{doc_id}.ndjson"


def _restore(target: Path, previous: bytes | None) -> None:
    if previous is None:
        target.unlink(missing_ok=True)
        return
    rollback = target.with_name(f".{target.name}.rollback")
    rollback.write_bytes(previous)
    os.replace(rollback, target)


def write_db_document(
    root: Path,
    document: dict[str, Any],
    *,
    replace: bool = False,
    validate_corpus: bool = True,
) -> Path:
    """Atomically write one document to db/<dtype>/<_id>.ndjson.

    The document is validated before writing. The complete repository is validated
    after writing, and the write is rolled back if any schema, path, duplicate-ID,
    or relation-endpoint invariant fails.
    """
    validate_document(document)
    target = canonical_db_path(root, document)
    payload = (compact(document) + "\n").encode("utf-8")
    previous = target.read_bytes() if target.exists() else None

    if previous == payload:
        return target
    if previous is not None and not replace:
        raise DatabaseWriteError(
            f"{target}: already exists with different content; pass replace=True for an intentional update"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, target)

    if validate_corpus:
        result = validate_repository(root.resolve(), require_v090=True)
        if not result["ok"]:
            _restore(target, previous)
            details = "\n".join(result["errors"])
            raise DatabaseWriteError(f"repository validation failed; write rolled back:\n{details}")

    return target
