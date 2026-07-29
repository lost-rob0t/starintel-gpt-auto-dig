from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .model import Document, stable_id
from .store import LocatedDocument, iter_corpus

_WORD_RE = re.compile(r"[a-z0-9]+")


class RecordResolutionError(ValueError):
    """Base class for record-resolution failures."""


class RecordNotFoundError(RecordResolutionError):
    """Raised when no record matches a query."""


class AmbiguousRecordError(RecordResolutionError):
    """Raised when a query has multiple equally strong matches."""


@dataclass(frozen=True, slots=True)
class RecordMatch:
    located: LocatedDocument
    score: int
    matched_field: str
    matched_value: str

    @property
    def document(self) -> dict[str, Any]:
        return self.located.document

    def to_dict(self, root: Path | None = None) -> dict[str, Any]:
        path = self.located.path
        if root is not None:
            try:
                path = path.relative_to(root)
            except ValueError:
                pass
        document = self.document
        return {
            "_id": document.get("_id", ""),
            "dtype": document.get("dtype", ""),
            "dataset": document.get("dataset", ""),
            "title": document.get("title", ""),
            "aliases": document.get("aliases", []),
            "score": self.score,
            "matched_field": self.matched_field,
            "matched_value": self.matched_value,
            "surface": self.located.surface,
            "path": str(path),
            "line": self.located.line,
        }


def normalize(value: str) -> str:
    return " ".join(_WORD_RE.findall(value.casefold()))


def _iter_strings(value: Any, prefix: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield prefix, value
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_strings(item, child)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_strings(item, child)


def _identity_fields(document: dict[str, Any]) -> list[tuple[str, str]]:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    values: list[tuple[str, str]] = [
        ("_id", str(document.get("_id", ""))),
        ("title", str(document.get("title", ""))),
    ]
    for index, alias in enumerate(document.get("aliases", [])):
        if isinstance(alias, str):
            values.append((f"aliases[{index}]", alias))
    for key in (
        "name",
        "display_name",
        "legal_name",
        "short_name",
        "full_name",
        "preferred_name",
        "target",
        "target_id",
    ):
        value = data.get(key)
        if isinstance(value, str):
            values.append((f"data.{key}", value))
    for key in ("former_names", "aliases"):
        values_list = data.get(key)
        if isinstance(values_list, list):
            for index, value in enumerate(values_list):
                if isinstance(value, str):
                    values.append((f"data.{key}[{index}]", value))
    return [(field, value) for field, value in values if value.strip()]


def _surface_priority(located: LocatedDocument) -> int:
    return 2 if located.surface == "db" else 1


def _version(document: dict[str, Any]) -> int:
    value = document.get("version", 0)
    return value if isinstance(value, int) else 0


def canonical_documents(documents: Iterable[LocatedDocument]) -> list[LocatedDocument]:
    """Deduplicate by _id, preferring normalized DB records and newer versions."""
    selected: dict[str, LocatedDocument] = {}
    anonymous: list[LocatedDocument] = []
    for located in documents:
        doc_id = located.document.get("_id")
        if not isinstance(doc_id, str) or not doc_id:
            anonymous.append(located)
            continue
        current = selected.get(doc_id)
        if current is None:
            selected[doc_id] = located
            continue
        candidate_key = (
            _surface_priority(located),
            _version(located.document),
            str(located.document.get("date_updated", "")),
            -located.line,
        )
        current_key = (
            _surface_priority(current),
            _version(current.document),
            str(current.document.get("date_updated", "")),
            -current.line,
        )
        if candidate_key > current_key:
            selected[doc_id] = located
    return sorted(
        [*selected.values(), *anonymous],
        key=lambda item: (
            str(item.document.get("dtype", "")),
            str(item.document.get("title", "")),
            str(item.document.get("_id", "")),
        ),
    )


def _match_score(query: str, document: dict[str, Any]) -> tuple[int, str, str]:
    normalized_query = normalize(query)
    if not normalized_query:
        return 1, "*", "*"
    query_tokens = set(normalized_query.split())

    best = (0, "", "")
    for field, raw_value in _identity_fields(document):
        value = normalize(raw_value)
        if not value:
            continue
        if field == "_id" and raw_value.casefold() == query.casefold():
            candidate = (1000, field, raw_value)
        elif value == normalized_query:
            candidate = (950, field, raw_value)
        elif value.startswith(normalized_query):
            candidate = (850, field, raw_value)
        elif normalized_query in value:
            candidate = (750, field, raw_value)
        elif query_tokens and query_tokens.issubset(set(value.split())):
            candidate = (700, field, raw_value)
        else:
            candidate = (0, "", "")
        if candidate > best:
            best = candidate

    if best[0]:
        return best

    flattened = [(field, value) for field, value in _iter_strings(document)]
    normalized_values = [(field, normalize(value), value) for field, value in flattened]
    joined = " ".join(value for _, value, _ in normalized_values if value)
    if normalized_query in joined:
        return 500, "document", query
    if query_tokens and query_tokens.issubset(set(joined.split())):
        return 400, "document", query
    return 0, "", ""


def search_records(
    root: Path,
    query: str,
    *,
    dtypes: set[str] | None = None,
    dataset: str = "",
    limit: int = 20,
    include_packets: bool = True,
) -> list[RecordMatch]:
    records = canonical_documents(
        iter_corpus(root, include_db=True, include_packets=include_packets)
    )
    matches: list[RecordMatch] = []
    for located in records:
        document = located.document
        if dtypes and str(document.get("dtype", "")) not in dtypes:
            continue
        if dataset and dataset.casefold() not in str(document.get("dataset", "")).casefold():
            continue
        score, field, value = _match_score(query, document)
        if score <= 0:
            continue
        matches.append(RecordMatch(located, score, field, value))
    matches.sort(
        key=lambda item: (
            -item.score,
            -_surface_priority(item.located),
            str(item.document.get("dtype", "")),
            str(item.document.get("title", "")),
            str(item.document.get("_id", "")),
        )
    )
    return matches[:limit] if limit > 0 else matches


def resolve_record(
    root: Path,
    query: str,
    *,
    dtypes: set[str] | None = None,
    dataset: str = "",
    include_packets: bool = True,
) -> RecordMatch:
    matches = search_records(
        root,
        query,
        dtypes=dtypes,
        dataset=dataset,
        limit=50,
        include_packets=include_packets,
    )
    if not matches:
        raise RecordNotFoundError(f"no StarIntel record matches {query!r}")
    top_score = matches[0].score
    tied = [match for match in matches if match.score == top_score]
    if len(tied) > 1:
        ids = ", ".join(str(match.document.get("_id", "")) for match in tied[:10])
        raise AmbiguousRecordError(
            f"ambiguous StarIntel record {query!r}; top matches: {ids}"
        )
    return matches[0]


def _endpoint_id(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "document_id", "entity_id"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
    return ""


def relation_neighbors(
    root: Path,
    query: str,
    *,
    dataset: str = "",
    direction: str = "both",
    limit: int = 100,
    include_packets: bool = True,
) -> tuple[RecordMatch, list[LocatedDocument]]:
    if direction not in {"both", "in", "out"}:
        raise ValueError("direction must be one of: both, in, out")
    resolved = resolve_record(
        root,
        query,
        dataset=dataset,
        include_packets=include_packets,
    )
    record_id = str(resolved.document["_id"])
    relations: list[LocatedDocument] = []
    for located in canonical_documents(
        iter_corpus(root, include_db=True, include_packets=include_packets)
    ):
        document = located.document
        if document.get("dtype") != "relation":
            continue
        if dataset and dataset.casefold() not in str(document.get("dataset", "")).casefold():
            continue
        data = document.get("data")
        if not isinstance(data, dict):
            continue
        subject = _endpoint_id(data.get("subject"))
        raw_object = data.get("object")
        objects = raw_object if isinstance(raw_object, list) else [raw_object]
        object_ids = {_endpoint_id(item) for item in objects}
        outbound = subject == record_id
        inbound = record_id in object_ids
        matches_direction = (
            (direction == "both" and (outbound or inbound))
            or (direction == "out" and outbound)
            or (direction == "in" and inbound)
        )
        if matches_direction:
            relations.append(located)
    relations.sort(
        key=lambda item: (
            str(item.document.get("data", {}).get("predicate", "")),
            str(item.document.get("_id", "")),
        )
    )
    return resolved, relations[:limit] if limit > 0 else relations


def create_relation_document(
    root: Path,
    *,
    dataset: str,
    subject_query: str,
    predicate: str,
    object_query: str,
    doc_id: str = "",
    title: str = "",
    summary: str = "",
    directed: bool = True,
    confidence: float = 1.0,
    qualifiers: dict[str, Any] | None = None,
    note: str = "",
    source_ids: Sequence[str] = (),
    include_packets: bool = True,
) -> dict[str, Any]:
    if not predicate.strip():
        raise ValueError("predicate must not be empty")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    subject = resolve_record(
        root,
        subject_query,
        include_packets=include_packets,
    )
    object_match = resolve_record(
        root,
        object_query,
        include_packets=include_packets,
    )
    subject_id = str(subject.document["_id"])
    object_id = str(object_match.document["_id"])
    relation_id = doc_id or stable_id(
        "relation",
        dataset,
        subject_id,
        predicate,
        object_id,
    )
    relation_title = title or (
        f"{subject.document.get('title') or subject_id} "
        f"{predicate.replace('_', ' ')} "
        f"{object_match.document.get('title') or object_id}"
    )
    relation_summary = summary or (
        f"Validated link from {subject_id} to {object_id} using predicate {predicate}."
    )
    sources = [{"source_id": source_id} for source_id in source_ids if source_id]
    document = Document.create(
        "relation",
        dataset,
        doc_id=relation_id,
        title=relation_title,
        summary=relation_summary,
        data={
            "subject": subject_id,
            "predicate": predicate,
            "object": object_id,
            "directed": directed,
            "confidence": confidence,
            "qualifiers": qualifiers or {},
            "note": note,
        },
        sources=sources,
        related_ids=[subject_id, object_id],
        assessment={"confidence": confidence},
        verification={"status": "draft-linked", "verified": False},
        provenance={
            "tool": "scripts/create-db-link.py",
            "method": "deterministic canonical-ID resolution",
        },
        handling={
            "visibility": "public",
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
        },
    ).to_dict()
    return document
