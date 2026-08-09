from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .store import LocatedDocument


TARGET_DTYPES = {"target", "investigation-target"}


def _state_key(located: LocatedDocument) -> tuple[str, int, str, int]:
    document = located.document
    workflow = document.get("workflow", {})
    timestamp = str(
        document.get("date_updated")
        or workflow.get("completed_at")
        or document.get("date_added")
        or ""
    )
    version = document.get("version", 0)
    if isinstance(version, bool) or not isinstance(version, int):
        version = 0
    return timestamp, version, located.path.as_posix(), located.line


def _ids(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    return ()


def _superseded_ids(document: dict[str, Any]) -> tuple[str, ...]:
    lineage = document.get("lineage", {})
    return _ids(lineage.get("supersedes")) + _ids(lineage.get("replaces"))


def resolve_latest_target_states(
    documents: Iterable[LocatedDocument],
) -> list[LocatedDocument]:
    """Resolve target state by document identity and explicit lineage.

    ``data.target_id`` identifies the research subject in existing packets and is
    not a safe queue-state key. Target-state updates therefore supersede the
    prior queue document explicitly through ``lineage.supersedes``/``replaces``.
    Duplicate copies of the same document ID are resolved by timestamp/version.
    """

    values = list(documents)
    latest_by_id: dict[str, LocatedDocument] = {}

    for located in values:
        document = located.document
        if document.get("dtype") not in TARGET_DTYPES:
            continue
        document_id = str(document.get("_id", ""))
        if not document_id:
            continue
        current = latest_by_id.get(document_id)
        if current is None or _state_key(located) > _state_key(current):
            latest_by_id[document_id] = located

    superseded: set[str] = set()
    for located in latest_by_id.values():
        superseded.update(_superseded_ids(located.document))

    resolved: list[LocatedDocument] = []
    for located in values:
        document = located.document
        if document.get("dtype") not in TARGET_DTYPES:
            resolved.append(located)
            continue

        document_id = str(document.get("_id", ""))
        if not document_id:
            resolved.append(located)
            continue
        if latest_by_id.get(document_id) is not located:
            continue
        if document_id in superseded:
            continue
        resolved.append(located)

    return resolved
