#!/usr/bin/env python3
"""Resolve canonical Auto-Dig documents and stream them as JSONL.

This intentionally contains no HTTP client.  It reuses the existing, well-tested
canonical/diff resolution logic while the Nim ingest core owns network I/O and
parallelism.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_IMPORTER = ROOT / "scripts" / "import-starintel-documents.py"


def load_importer():
    spec = importlib.util.spec_from_file_location("starintel_import_documents", LEGACY_IMPORTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LEGACY_IMPORTER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve canonical Auto-Dig documents and emit JSONL for the Nim ingest core."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diff", metavar="BASE", help="Emit logical document IDs newly introduced since BASE.")
    mode.add_argument("--all", action="store_true", help="Emit the full canonical corpus.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    importer = load_importer()
    root = importer.repo_root(ROOT)

    if args.diff:
        records = importer.collect_new_documents(root, args.diff)
        mode = f"diff:{args.diff}"
    else:
        records = importer.collect_all_documents(root)
        mode = "all"

    records.sort(key=lambda record: record.document_id)
    print(
        json.dumps({"mode": mode, "documents": len(records)}, sort_keys=True),
        file=sys.stderr,
    )
    for record in records:
        print(json.dumps(record.document, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
