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

from starintel_doc.model import Document
from starintel_doc.spec import TYPE_FIELDS
from starintel_doc.writer import write_db_document


def json_object(value: str, label: str) -> dict[str, Any]:
    if not value:
        return {}
    if value.startswith("@"):
        text = Path(value[1:]).read_text(encoding="utf-8")
    else:
        text = value
        try:
            candidate = Path(value)
            if len(value) < 4096 and candidate.is_file():
                text = candidate.read_text(encoding="utf-8")
        except OSError:
            text = value
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, validate, and atomically write one canonical StarIntel DB document"
    )
    parser.add_argument("dtype", choices=sorted(TYPE_FIELDS))
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--id", required=True, help="stable StarIntel _id; becomes the literal filename")
    parser.add_argument("--title", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--data", default="{}", help="JSON object or @path containing dtype-specific data")
    parser.add_argument("--metadata", default="{}", help="JSON object or @path containing common envelope metadata")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--replace", action="store_true", help="allow an intentional update to an existing _id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.root).resolve()
        document = Document.create(
            args.dtype,
            args.dataset,
            doc_id=args.id,
            title=args.title,
            summary=args.summary,
            data=json_object(args.data, "--data"),
            **json_object(args.metadata, "--metadata"),
        ).to_dict()
        target = write_db_document(
            root,
            document,
            replace=args.replace,
            validate_corpus=True,
        )
        print(target.relative_to(root))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
