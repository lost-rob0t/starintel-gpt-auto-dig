#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.linking import RecordResolutionError, create_relation_document
from starintel_doc.store import compact


def json_object(value: str, label: str) -> dict[str, Any]:
    if not value:
        return {}
    text = value
    if value.startswith("@"):
        text = Path(value[1:]).read_text(encoding="utf-8")
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve two canonical StarIntel records and emit one validated relation "
            "document for later import"
        )
    )
    parser.add_argument("subject")
    parser.add_argument("predicate")
    parser.add_argument("object")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--id", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--confidence", type=float, default=1.0)
    parser.add_argument("--qualifiers", default="{}")
    parser.add_argument("--note", default="")
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--undirected", action="store_true")
    parser.add_argument(
        "--include-packets",
        action="store_true",
        help="allow endpoint resolution from dig packets; omit for DB-only linking",
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--output",
        help="write validated JSONL outside db/; omit to print to stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        document = create_relation_document(
            root,
            dataset=args.dataset,
            subject_query=args.subject,
            predicate=args.predicate,
            object_query=args.object,
            doc_id=args.id,
            title=args.title,
            summary=args.summary,
            directed=not args.undirected,
            confidence=args.confidence,
            qualifiers=json_object(args.qualifiers, "--qualifiers"),
            note=args.note,
            source_ids=args.source_id,
            include_packets=args.include_packets,
        )
        payload = compact(document) + "\n"
        if args.output:
            output = Path(args.output).resolve()
            db_root = (root / "db").resolve()
            if output == db_root or db_root in output.parents:
                raise ValueError(
                    "--output may not target db/; emit JSONL and import it with "
                    "scripts/starintel.py import"
                )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
            print(output)
        else:
            print(payload, end="")
        return 0
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        RecordResolutionError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
