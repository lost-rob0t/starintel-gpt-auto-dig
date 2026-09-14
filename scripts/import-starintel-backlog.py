#!/usr/bin/env python3
"""Import the canonical Auto-Dig corpus in resumable 10k outer chunks.

Each outer chunk is subdivided into server-safe batches.  The server currently
caps /documents/bulk at 500 documents, so the default 10,000-document chunk is
20 confirmed 500-document submissions.  A checkpoint is emitted after every
successful server batch.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "scripts" / "import-starintel-documents.py"
DEFAULT_CORE = ROOT / "bin" / "starintel-ingest-core"
DEFAULT_CHUNK_SIZE = 10_000
DEFAULT_BATCH_SIZE = 500
MAX_BATCH_SIZE = 500


def load_importer():
    spec = importlib.util.spec_from_file_location("starintel_import_documents", IMPORTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {IMPORTER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def nonnegative_int(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=positive_int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--batch-size", type=positive_int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--start-offset", type=nonnegative_int, default=0)
    parser.add_argument(
        "--max-documents",
        type=nonnegative_int,
        default=0,
        help="0 imports through the end of the canonical corpus",
    )
    parser.add_argument("--core", type=Path, default=DEFAULT_CORE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.batch_size > MAX_BATCH_SIZE:
        parser.error(f"--batch-size may not exceed {MAX_BATCH_SIZE}")
    return args


def selected_window(total: int, start_offset: int, max_documents: int) -> tuple[int, int]:
    start = min(start_offset, total)
    stop = total if max_documents == 0 else min(total, start + max_documents)
    return start, stop


def chunk_bounds(start: int, stop: int, chunk_size: int) -> Iterator[tuple[int, int, int]]:
    chunk_no = 1
    cursor = start
    while cursor < stop:
        past_last = min(cursor + chunk_size, stop)
        yield chunk_no, cursor, past_last
        chunk_no += 1
        cursor = past_last


def batch_bounds(start: int, stop: int, batch_size: int) -> Iterator[tuple[int, int]]:
    cursor = start
    while cursor < stop:
        past_last = min(cursor + batch_size, stop)
        yield cursor, past_last
        cursor = past_last


def emit(payload: dict) -> None:
    print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)


def run_batch(core: Path, records, first: int, past_last: int, batch_size: int) -> int:
    command = [str(core), "--workers", "1", "--batch-size", str(batch_size)]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        stdin=subprocess.PIPE,
        text=True,
    )
    assert process.stdin is not None
    try:
        for record in records[first:past_last]:
            process.stdin.write(
                json.dumps(record.document, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
    finally:
        process.stdin.close()
    return process.wait()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    importer = load_importer()
    root = importer.repo_root(ROOT)
    records = importer.collect_all_documents(root)
    records.sort(key=lambda record: record.document_id)

    start, stop = selected_window(len(records), args.start_offset, args.max_documents)
    chunks = list(chunk_bounds(start, stop, args.chunk_size))
    total_batches = sum(
        (chunk_stop - chunk_start + args.batch_size - 1) // args.batch_size
        for _chunk_no, chunk_start, chunk_stop in chunks
    )

    emit(
        {
            "status": "planned",
            "corpus_documents": len(records),
            "start_offset": start,
            "stop_offset": stop,
            "selected_documents": stop - start,
            "chunk_size": args.chunk_size,
            "chunks": len(chunks),
            "batch_size": args.batch_size,
            "server_batches": total_batches,
            "dry_run": args.dry_run,
        }
    )
    if args.dry_run or start == stop:
        return 0

    if not args.core.is_file():
        emit({"status": "failed", "error": f"ingest core not found: {args.core}"})
        return 2
    if not os.environ.get("STAR_SERVER_API_KEY", "").strip():
        emit({"status": "failed", "error": "STAR_SERVER_API_KEY is required"})
        return 2

    confirmed_offset = start
    completed_batches = 0
    for chunk_no, chunk_start, chunk_stop in chunks:
        emit(
            {
                "status": "chunk-starting",
                "chunk": chunk_no,
                "start_offset": chunk_start,
                "stop_offset": chunk_stop,
                "documents": chunk_stop - chunk_start,
            }
        )
        for batch_start, batch_stop in batch_bounds(chunk_start, chunk_stop, args.batch_size):
            rc = run_batch(args.core, records, batch_start, batch_stop, args.batch_size)
            if rc != 0:
                emit(
                    {
                        "status": "failed",
                        "exit_code": rc,
                        "confirmed_offset": confirmed_offset,
                        "failed_start_offset": batch_start,
                        "failed_stop_offset": batch_stop,
                        "note": "A failed POST can be ambiguous; inspect the ingest-core log before replaying this batch.",
                    }
                )
                return rc
            confirmed_offset = batch_stop
            completed_batches += 1
            emit(
                {
                    "status": "checkpoint",
                    "confirmed_offset": confirmed_offset,
                    "completed_server_batches": completed_batches,
                    "total_server_batches": total_batches,
                }
            )
        emit({"status": "chunk-completed", "chunk": chunk_no, "confirmed_offset": confirmed_offset})

    emit(
        {
            "status": "completed",
            "imported_documents": confirmed_offset - start,
            "confirmed_offset": confirmed_offset,
            "server_batches": completed_batches,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
