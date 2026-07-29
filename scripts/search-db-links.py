#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.linking import (
    RecordResolutionError,
    relation_neighbors,
    resolve_record,
    search_records,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search, resolve, and traverse canonical StarIntel DB links"
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=str(ROOT))
    common.add_argument("--dataset", default="")
    common.add_argument("--db-only", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser(
        "search",
        parents=[common],
        help="rank matching canonical records",
    )
    search.add_argument("query")
    search.add_argument("--dtype", action="append")
    search.add_argument("--limit", type=int, default=20)

    resolve = sub.add_parser(
        "resolve",
        parents=[common],
        help="resolve exactly one canonical record",
    )
    resolve.add_argument("query")
    resolve.add_argument("--dtype", action="append")

    neighbors = sub.add_parser(
        "neighbors",
        parents=[common],
        help="list relations touching one record",
    )
    neighbors.add_argument("query")
    neighbors.add_argument("--direction", choices=("both", "in", "out"), default="both")
    neighbors.add_argument("--limit", type=int, default=100)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    include_packets = not args.db_only
    try:
        if args.command == "search":
            matches = search_records(
                root,
                args.query,
                dtypes=set(args.dtype) if args.dtype else None,
                dataset=args.dataset,
                limit=args.limit,
                include_packets=include_packets,
            )
            for match in matches:
                print(json.dumps(match.to_dict(root), ensure_ascii=False, sort_keys=True))
            return 0 if matches else 1

        if args.command == "resolve":
            match = resolve_record(
                root,
                args.query,
                dtypes=set(args.dtype) if args.dtype else None,
                dataset=args.dataset,
                include_packets=include_packets,
            )
            print(json.dumps(match.to_dict(root), ensure_ascii=False, sort_keys=True))
            return 0

        resolved, relations = relation_neighbors(
            root,
            args.query,
            dataset=args.dataset,
            direction=args.direction,
            limit=args.limit,
            include_packets=include_packets,
        )
        payload = {
            "record": resolved.to_dict(root),
            "relations": [
                {
                    "_id": item.document.get("_id", ""),
                    "predicate": item.document.get("data", {}).get("predicate", ""),
                    "subject": item.document.get("data", {}).get("subject"),
                    "object": item.document.get("data", {}).get("object"),
                    "dataset": item.document.get("dataset", ""),
                    "surface": item.surface,
                    "path": str(item.path.relative_to(root)),
                    "line": item.line,
                }
                for item in relations
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, RecordResolutionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
