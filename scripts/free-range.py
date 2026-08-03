#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.free_range import (
    load_frontier_documents,
    plan_free_range,
    render_jsonl,
    render_markdown,
)
from starintel_doc.store import search_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="free-range",
        description="Plan balanced multi-actor research missions from the StarIntel frontier.",
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--query", default="")
    parser.add_argument("--dtype", action="append")
    parser.add_argument("--dataset")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-per-dataset", type=int, default=3)
    parser.add_argument("--max-per-type", type=int, default=5)
    parser.add_argument("--include-blocked", action="store_true")
    parser.add_argument("--queue-only", action="store_true")
    parser.add_argument("--format", choices=("jsonl", "markdown"), default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--db-only", action="store_true")
    parser.add_argument("--packets-only", action="store_true")
    parser.add_argument("--strict-packets", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    documents, warnings = load_frontier_documents(
        root,
        include_db=not args.packets_only,
        include_packets=not args.db_only,
        strict_packets=args.strict_packets,
    )
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if args.query or args.dtype or args.dataset:
        documents = search_documents(
            documents,
            query=args.query,
            dtypes=set(args.dtype) if args.dtype else None,
            dataset=args.dataset or "",
        )

    missions = plan_free_range(
        documents,
        limit=args.limit,
        batch_size=args.batch_size,
        max_per_dataset=args.max_per_dataset,
        max_per_type=args.max_per_type,
        include_blocked=args.include_blocked,
        discover=not args.queue_only,
    )
    payload = render_markdown(missions) if args.format == "markdown" else render_jsonl(missions)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
