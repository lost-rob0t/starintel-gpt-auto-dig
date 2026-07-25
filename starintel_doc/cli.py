from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .migration import migrate_document
from .model import Document
from .selectors import candidate_documents, select_candidates
from .spec import SCHEMA_VERSION, TYPE_FIELDS, document_schema
from .store import (
    LocatedDocument,
    compact,
    iter_corpus,
    migrate_repository,
    search_documents,
    validate_repository,
)
from .validation import validate_document


def _json_object(value: str, label: str) -> dict[str, Any]:
    if not value:
        return {}
    path = Path(value)
    text = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _emit(value: Any, *, pretty: bool = False) -> None:
    if isinstance(value, list):
        for item in value:
            print(json.dumps(item, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True, separators=None if pretty else (",", ":")))
        return
    print(json.dumps(value, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True, separators=None if pretty else (",", ":")))


def cmd_types(_: argparse.Namespace) -> int:
    for dtype in sorted(TYPE_FIELDS):
        print(dtype)
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    schema = document_schema(args.dtype or None)
    payload = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    data = _json_object(args.data, "--data")
    metadata = _json_object(args.metadata, "--metadata")
    document = Document.create(
        args.dtype,
        args.dataset,
        doc_id=args.id or None,
        title=args.title,
        summary=args.summary,
        data=data,
        **metadata,
    ).to_dict()
    payload = json.dumps(document, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True, separators=None if args.pretty else (",", ":")) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    result = validate_repository(root, require_v090=not args.allow_legacy)
    if args.json:
        _emit(result, pretty=True)
    else:
        print(f"documents={result['documents']} ok={str(result['ok']).lower()} schema={SCHEMA_VERSION}")
        for dtype, count in result["counts"].items():
            print(f"{dtype}: {count}")
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


def cmd_migrate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    result = migrate_repository(root, write=args.write)
    _emit(result, pretty=True)
    if args.write:
        validation = validate_repository(root, require_v090=True)
        if not validation["ok"]:
            for error in validation["errors"]:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
    return 0


def cmd_migrate_one(args: argparse.Namespace) -> int:
    source = Path(args.source)
    raw = json.loads(source.read_text(encoding="utf-8") if source.exists() else args.source)
    migrated = migrate_document(raw, original_path=str(source) if source.exists() else "stdin")
    _emit(migrated, pretty=args.pretty)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    documents = iter_corpus(root, include_db=not args.packets_only, include_packets=not args.db_only)
    results = search_documents(
        documents,
        query=args.query,
        dtypes=set(args.dtype) if args.dtype else None,
        dataset=args.dataset,
        predicate=args.predicate,
        doc_id=args.id,
        source=args.source,
        min_confidence=args.min_confidence,
    )
    for located in results[: args.limit if args.limit > 0 else None]:
        if args.with_location:
            value = {
                "path": str(located.path.relative_to(root)),
                "line": located.line,
                "surface": located.surface,
                "document": located.document,
            }
        else:
            value = located.document
        print(compact(value))
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    documents = list(iter_corpus(root, include_db=not args.packets_only, include_packets=not args.db_only))
    if args.query or args.dtype or args.dataset:
        documents = search_documents(
            documents,
            query=args.query,
            dtypes=set(args.dtype) if args.dtype else None,
            dataset=args.dataset,
        )
    candidates = select_candidates(documents, limit=args.limit)
    if args.emit_documents:
        docs = candidate_documents(
            candidates,
            dataset=args.output_dataset or args.dataset or "star-intel-auto-dig",
            root_target_id=args.root_target_id,
            depth=args.depth,
            max_depth=args.max_depth,
        )
        payload = "".join(compact(doc) + "\n" for doc in docs)
    else:
        payload = "".join(
            compact(
                {
                    "target_id": item.target_id,
                    "target_type": item.target_type,
                    "score": item.score,
                    "reasons": list(item.reasons),
                    "seed_ids": list(item.seed_ids),
                }
            )
            + "\n"
            for item in candidates
        )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    source = Path(args.source)
    root = Path(args.root).resolve()
    created = replaced = unchanged = 0
    seen: set[str] = set()
    for number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if args.migrate:
            value = migrate_document(value, original_path=f"{source}:{number}")
        validate_document(value)
        doc_id = value["_id"]
        if doc_id in seen:
            raise ValueError(f"{source}:{number}: duplicate _id {doc_id!r}")
        seen.add(doc_id)
        target = root / "db" / value["dtype"] / f"{doc_id}.ndjson"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = compact(value) + "\n"
        if target.exists():
            if target.read_text(encoding="utf-8") == payload:
                unchanged += 1
                continue
            if not args.replace:
                raise ValueError(f"{target}: exists; pass --replace for an intentional update")
            replaced += 1
        else:
            created += 1
        target.write_text(payload, encoding="utf-8")
    _emit({"created": created, "replaced": replaced, "unchanged": unchanged}, pretty=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="starintel", description="Canonical StarIntel v0.9.0 document tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("types", help="list canonical document types")
    p.set_defaults(func=cmd_types)

    p = sub.add_parser("schema", help="export the canonical JSON Schema")
    p.add_argument("--dtype", choices=sorted(TYPE_FIELDS))
    p.add_argument("--output")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("create", help="create one schema-valid document")
    p.add_argument("dtype", choices=sorted(TYPE_FIELDS))
    p.add_argument("--dataset", required=True)
    p.add_argument("--id", default="")
    p.add_argument("--title", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--data", default="{}", help="JSON object or path containing dtype-specific data")
    p.add_argument("--metadata", default="{}", help="JSON object or path containing declared common metadata")
    p.add_argument("--output")
    p.add_argument("--pretty", action="store_true")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("validate", help="validate db/ and digs/ against v0.9.0")
    p.add_argument("--root", default=".")
    p.add_argument("--allow-legacy", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("migrate", help="migrate every DB and packet record to v0.9.0")
    p.add_argument("--root", default=".")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("migrate-one", help="migrate one JSON object")
    p.add_argument("source", help="JSON object or path")
    p.add_argument("--pretty", action="store_true")
    p.set_defaults(func=cmd_migrate_one)

    p = sub.add_parser("search", help="search the JSON DB and dig packets")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--root", default=".")
    p.add_argument("--dtype", action="append", choices=sorted(TYPE_FIELDS))
    p.add_argument("--dataset", default="")
    p.add_argument("--predicate", default="")
    p.add_argument("--id", default="")
    p.add_argument("--source", default="")
    p.add_argument("--min-confidence", type=float)
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--db-only", action="store_true")
    p.add_argument("--packets-only", action="store_true")
    p.add_argument("--with-location", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("select-targets", help="rank entities for recursive auto-dig")
    p.add_argument("--root", default=".")
    p.add_argument("--query", default="")
    p.add_argument("--dtype", action="append", choices=sorted(TYPE_FIELDS))
    p.add_argument("--dataset", default="")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--root-target-id", default="")
    p.add_argument("--output-dataset", default="")
    p.add_argument("--emit-documents", action="store_true")
    p.add_argument("--output")
    p.add_argument("--db-only", action="store_true")
    p.add_argument("--packets-only", action="store_true")
    p.set_defaults(func=cmd_select)

    p = sub.add_parser("import", help="import validated JSONL into db/<dtype>/<_id>.ndjson")
    p.add_argument("source")
    p.add_argument("--root", default=".")
    p.add_argument("--replace", action="store_true")
    p.add_argument("--migrate", action="store_true")
    p.set_defaults(func=cmd_import)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2
