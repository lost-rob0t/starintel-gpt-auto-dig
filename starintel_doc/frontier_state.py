from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .store import LocatedDocument


TARGET_DTYPES = {"target", "investigation-target"}


def _target_id(document: dict[str, Any]) -> str:
    data = document.get("data", {})
    value = data.get("target_id", data.get("target", document.get("_id", "")))
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "document_id", "entity_id"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return item
    return str(document.get("_id", ""))


def _state_key(located: LocatedDocument) -> tuple[str, int, str, str, int]:
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
    return (
        timestamp,
        version,
        str(document.get("_id", "")),
        located.path.as_posix(),
        located.line,
    )


def resolve_latest_target_states(
    documents: Iterable[LocatedDocument],
) -> list[LocatedDocument]:
    """Keep only the newest state record for each logical target.

    StarIntel research can emit a later target-state record with a new document ID
    while preserving the original ``data.target_id``.  The frontier must resolve
    that event stream before terminal-state filtering; otherwise an old ``queued``
    record remains actionable even after a later ``completed``/``superseded``
    record closes the same target.
    """

    values = list(documents)
    latest: dict[str, LocatedDocument] = {}

    for located in values:
        document = located.document
        if document.get("dtype") not in TARGET_DTYPES:
            continue
        target_id = _target_id(document)
        current = latest.get(target_id)
        if current is None or _state_key(located) > _state_key(current):
            latest[target_id] = located

    resolved: list[LocatedDocument] = []
    for located in values:
        document = located.document
        if document.get("dtype") not in TARGET_DTYPES:
            resolved.append(located)
            continue
        target_id = _target_id(document)
        if latest.get(target_id) is located:
            resolved.append(located)

    return resolved
