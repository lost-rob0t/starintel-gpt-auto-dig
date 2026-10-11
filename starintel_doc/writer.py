from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from .store import LocatedDocument, compact, validate_repository
from .storage_validation import validate_stored_document as validate_document, document_id


class DatabaseWriteError(ValueError):
    """Raised when a canonical database write would violate repository invariants."""


def canonical_db_path(root: Path, document: dict[str, Any]) -> Path:
    """Return the only valid normalized DB path for a validated document."""
    validate_document(document)
    dtype = document["dtype"]
    doc_id = document_id(document)
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


def write_db_documents(
    root: Path, documents: Iterable[dict[str, Any]], *, replace: bool = False,
) -> list[Path]:
    """Validate a complete batch, then persist it with rollback on failure.

    Relations may precede their endpoints. Duplicate IDs and replacement
    conflicts are rejected before any record is changed. This is rollback on
    in-process failures, not crash-safe multi-file filesystem atomicity.
    """
    root = root.resolve()
    pending = []
    updates = []
    seen = set()
    for document in documents:
        target = canonical_db_path(root, document)
        doc_id = document_id(document)
        if doc_id in seen:
            raise DatabaseWriteError(f"duplicate document id in batch: {doc_id!r}")
        seen.add(doc_id)
        payload = (compact(document) + "\n").encode("utf-8")
        previous = target.read_bytes() if target.exists() else None
        if previous is not None and previous != payload and not replace:
            raise DatabaseWriteError(f"{target}: already exists with different content; pass replace=True for an intentional update")
        pending.append(LocatedDocument(document, target))
        if previous != payload:
            updates.append((target, payload, previous))

    result = validate_repository(root, pending_documents=pending)
    if not result["ok"]:
        raise DatabaseWriteError("repository validation failed before batch write:\n" + "\n".join(result["errors"]))

    written = []
    temporary = None
    try:
        for target, payload, previous in updates:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.tmp")
            temporary.write_bytes(payload)
            os.replace(temporary, target)
            written.append((target, previous))
        result = validate_repository(root)
        if not result["ok"]:
            raise DatabaseWriteError("repository validation failed after batch write:\n" + "\n".join(result["errors"]))
    except BaseException:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        for target, previous in reversed(written):
            _restore(target, previous)
        raise
    return [item.path for item in pending]


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
