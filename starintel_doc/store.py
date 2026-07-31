from __future__ import annotations

import base64
import gzip
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from .migration import migrate_document
from .schema_org_migration import enrich_schema_org
from .validation import ValidationError, validate_document


@dataclass(frozen=True, slots=True)
class LocatedDocument:
    document: dict[str, Any]
    path: Path
    line: int = 1
    surface: str = "db"


def compact(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def read_transport(path: Path) -> str:
    if path.name.endswith(".parts"):
        names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        encoded = "".join((path.parent / name).read_text(encoding="utf-8").strip() for name in names)
        return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    if path.name.endswith(".gz.b64"):
        return gzip.decompress(base64.b64decode(path.read_bytes())).decode("utf-8")
    return path.read_text(encoding="utf-8")


def packet_paths(root: Path) -> list[Path]:
    paths = list(root.glob("digs/*/*/starintel-documents.jsonl"))
    paths += list(root.glob("digs/*/*/starintel-documents.jsonl.gz.b64"))
    paths += list(root.glob("digs/*/*/starintel-documents.jsonl.gz.b64.parts"))
    return sorted(paths)


def iter_jsonl(path: Path, *, surface: str) -> Iterator[LocatedDocument]:
    for number, raw in enumerate(read_transport(path).splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{number}: expected JSON object")
        yield LocatedDocument(value, path, number, surface)


def iter_db(root: Path) -> Iterator[LocatedDocument]:
    db = root / "db"
    if not db.is_dir():
        return
    for path in sorted(db.glob("*/*.ndjson")):
        data = path.read_bytes()
        if not data.endswith(b"\n"):
            raise ValueError(f"{path}: missing terminating newline")
        lines = data.decode("utf-8").splitlines()
        if len(lines) != 1 or not lines[0].strip():
            raise ValueError(f"{path}: expected exactly one non-empty NDJSON line")
        value = json.loads(lines[0])
        if not isinstance(value, dict):
            raise ValueError(f"{path}: expected JSON object")
        yield LocatedDocument(value, path, 1, "db")


def iter_corpus(root: Path, *, include_db: bool = True, include_packets: bool = True) -> Iterator[LocatedDocument]:
    if include_db:
        yield from iter_db(root)
    if include_packets:
        for path in packet_paths(root):
            yield from iter_jsonl(path, surface="packet")


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)


def search_documents(
    documents: Iterable[LocatedDocument],
    *,
    query: str = "",
    dtypes: set[str] | None = None,
    dataset: str = "",
    predicate: str = "",
    doc_id: str = "",
    source: str = "",
    min_confidence: float | None = None,
) -> list[LocatedDocument]:
    terms = [term.lower() for term in query.split() if term.strip()]
    results: list[LocatedDocument] = []
    for located in documents:
        doc = located.document
        if dtypes and doc.get("dtype") not in dtypes:
            continue
        if dataset and dataset.lower() not in str(doc.get("dataset", "")).lower():
            continue
        if doc_id and doc_id.lower() not in str(doc.get("_id", "")).lower():
            continue
        if predicate:
            actual = str(doc.get("data", {}).get("predicate", ""))
            if predicate.lower() not in actual.lower():
                continue
        if source:
            source_text = " ".join(_strings(doc.get("sources", []))).lower()
            if source.lower() not in source_text:
                continue
        if min_confidence is not None:
            raw = doc.get("assessment", {}).get("confidence")
            if not isinstance(raw, (int, float)) or raw < min_confidence:
                continue
        haystack = "\n".join(_strings(doc)).lower()
        if terms and not all(term in haystack for term in terms):
            continue
        results.append(located)
    return results


def validate_repository(root: Path, *, require_v090: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    ids_by_surface: dict[str, dict[str, Path]] = {"db": {}, "packet": {}}
    located_docs: list[LocatedDocument] = []
    try:
        located_docs = list(iter_corpus(root))
    except Exception as exc:
        errors.append(str(exc))

    for located in located_docs:
        doc = located.document
        label = f"{located.path}:{located.line}"
        try:
            if require_v090:
                validate_document(doc)
            dtype = str(doc.get("dtype", ""))
            doc_id = str(doc.get("_id", ""))
            counts[dtype] += 1
            if located.surface == "db":
                expected_dtype = located.path.parent.name
                expected_id = located.path.name.removesuffix(".ndjson")
                if dtype != expected_dtype:
                    errors.append(f"{label}: dtype={dtype!r}, directory={expected_dtype!r}")
                if doc_id != expected_id:
                    errors.append(f"{label}: _id={doc_id!r}, filename={expected_id!r}")
            seen = ids_by_surface[located.surface]
            if doc_id in seen and located.surface == "db":
                errors.append(f"{label}: duplicate normalized _id also at {seen[doc_id]}")
            else:
                seen[doc_id] = located.path
        except (ValidationError, ValueError, TypeError) as exc:
            errors.append(f"{label}: {exc}")

    db_ids = set(ids_by_surface["db"])
    for located in located_docs:
        if located.surface != "db" or located.document.get("dtype") != "relation":
            continue
        data = located.document.get("data", {})
        for endpoint in ("subject", "object"):
            value = data.get(endpoint)
            values = value if isinstance(value, list) else [value]
            for item in values:
                endpoint_id = item.get("id") if isinstance(item, dict) else item
                if isinstance(endpoint_id, str) and endpoint_id and endpoint_id not in db_ids:
                    errors.append(f"{located.path}: unresolved relation {endpoint}={endpoint_id!r}")

    return {
        "ok": not errors,
        "errors": errors,
        "counts": dict(sorted(counts.items())),
        "documents": len(located_docs),
    }


def _write_packet(path: Path, docs: list[dict[str, Any]]) -> None:
    canonical = path.parent / "starintel-documents.jsonl"
    payload = "".join(compact(doc) + "\n" for doc in docs)
    canonical.write_text(payload, encoding="utf-8")
    for candidate in path.parent.glob("starintel-documents.jsonl.gz.b64*"):
        candidate.unlink()


def migrate_repository(root: Path, *, write: bool = False) -> dict[str, Any]:
    changed: list[str] = []
    counts: Counter[str] = Counter()
    migrated_total = 0

    db_items = list(iter_db(root))
    for located in db_items:
        migrated = enrich_schema_org(
            migrate_document(located.document, original_path=str(located.path.relative_to(root)))
        )
        validate_document(migrated)
        target = root / "db" / migrated["dtype"] / f"{migrated['_id']}.ndjson"
        payload = compact(migrated) + "\n"
        old_payload = located.path.read_text(encoding="utf-8")
        if target != located.path or payload != old_payload:
            changed.append(str(target.relative_to(root)))
            if write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(payload, encoding="utf-8")
                if target != located.path:
                    located.path.unlink()
        counts[migrated["dtype"]] += 1
        migrated_total += 1

    handled_packet_dirs: set[Path] = set()
    for path in packet_paths(root):
        if path.parent in handled_packet_dirs:
            continue
        handled_packet_dirs.add(path.parent)
        source_path = next(
            (candidate for candidate in [
                path.parent / "starintel-documents.jsonl",
                path.parent / "starintel-documents.jsonl.gz.b64",
                path.parent / "starintel-documents.jsonl.gz.b64.parts",
            ] if candidate.exists()),
            path,
        )
        docs: list[dict[str, Any]] = []
        seen: set[str] = set()
        for located in iter_jsonl(source_path, surface="packet"):
            migrated = enrich_schema_org(
                migrate_document(located.document, original_path=str(source_path.relative_to(root)))
            )
            validate_document(migrated)
            if migrated["_id"] in seen:
                raise ValueError(f"{source_path}: duplicate _id {migrated['_id']}")
            seen.add(migrated["_id"])
            docs.append(migrated)
            counts[migrated["dtype"]] += 1
            migrated_total += 1
        canonical = source_path.parent / "starintel-documents.jsonl"
        new_payload = "".join(compact(doc) + "\n" for doc in docs)
        current_payload = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
        transport_exists = any(source_path.parent.glob("starintel-documents.jsonl.gz.b64*"))
        if new_payload != current_payload or transport_exists:
            changed.append(str(canonical.relative_to(root)))
            if write:
                _write_packet(source_path, docs)

    digest = hashlib.sha256()
    for located in sorted(iter_corpus(root), key=lambda item: (str(item.path), item.line)) if write else []:
        digest.update(compact(located.document).encode("utf-8"))
        digest.update(b"\n")

    manifest = {
        "schema_version": "0.9.0",
        "migration": "starintel_doc v0.9.0 canonical envelope with Schema.org JSON-LD metadata",
        "record_count": migrated_total,
        "counts_by_dtype": dict(sorted(counts.items())),
        "changed_paths": sorted(set(changed)),
        "content_sha256": digest.hexdigest() if write else "",
    }
    if write:
        manifest_path = root / "manifests" / "starintel-v0.9.0-migration.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        changed.append(str(manifest_path.relative_to(root)))
    manifest["changed_paths"] = sorted(set(changed))
    return manifest
