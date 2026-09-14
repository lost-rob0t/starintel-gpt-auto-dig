#!/usr/bin/env python3
"""Import the canonical Auto-Dig corpus in resumable 10k outer chunks.

Each outer chunk is subdivided into server-safe batches. The server currently
caps /documents/bulk at 500 documents, so the default 10,000-document chunk is
20 confirmed 500-document submissions.

The importer writes two append-only JSONL ledgers:
- canonical-import.jsonl records the exact source commit and every confirmed ID.
- failed-import.jsonl records any failed/ambiguous batch and its exact IDs.

The last confirmed offset in canonical-import.jsonl is safe to use as
--start-offset for a later continuation. Failed POSTs are logged separately
because a transport/server failure can be ambiguous and must not be blindly
replayed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "scripts" / "import-starintel-documents.py"
DEFAULT_CORE = ROOT / "bin" / "starintel-ingest-core"
DEFAULT_CHUNK_SIZE = 10_000
DEFAULT_BATCH_SIZE = 500
MAX_BATCH_SIZE = 500
DEFAULT_LOG_DIR = ROOT / ".artifacts" / "backlog-import"
LEDGER_VERSION = 1


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
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument(
        "--resume-from-log",
        action="store_true",
        help="resume at the highest confirmed offset in canonical-import.jsonl",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.batch_size > MAX_BATCH_SIZE:
        parser.error(f"--batch-size may not exceed {MAX_BATCH_SIZE}")
    return args


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


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


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def highest_confirmed_offset(path: Path, source_commit: str) -> int | None:
    if not path.is_file():
        return None
    confirmed: int | None = None
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
        if event.get("source_commit") != source_commit:
            continue
        value = event.get("confirmed_offset")
        if isinstance(value, int) and value >= 0:
            confirmed = value if confirmed is None else max(confirmed, value)
    return confirmed


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
    source_commit = git_head(root)
    run_id = os.environ.get("GITHUB_RUN_ID") or f"local-{os.getpid()}"
    import_log = args.log_dir / "canonical-import.jsonl"
    failed_log = args.log_dir / "failed-import.jsonl"

    records = importer.collect_all_documents(root)
    records.sort(key=lambda record: record.document_id)

    start_offset = args.start_offset
    if args.resume_from_log:
        resumed = highest_confirmed_offset(import_log, source_commit)
        if resumed is not None:
            start_offset = max(start_offset, resumed)

    start, stop = selected_window(len(records), start_offset, args.max_documents)
    chunks = list(chunk_bounds(start, stop, args.chunk_size))
    total_batches = sum(
        (chunk_stop - chunk_start + args.batch_size - 1) // args.batch_size
        for _chunk_no, chunk_start, chunk_stop in chunks
    )

    plan = {
        "ledger_version": LEDGER_VERSION,
        "record_type": "run-plan",
        "status": "planned",
        "timestamp": utc_now(),
        "run_id": run_id,
        "source_commit": source_commit,
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
    emit(plan)
    append_jsonl(import_log, plan)

    if args.dry_run or start == stop:
        return 0

    if not args.core.is_file():
        failure = {
            "ledger_version": LEDGER_VERSION,
            "record_type": "run-failure",
            "status": "failed",
            "timestamp": utc_now(),
            "run_id": run_id,
            "source_commit": source_commit,
            "confirmed_offset": start,
            "error": f"ingest core not found: {args.core}",
        }
        emit(failure)
        append_jsonl(failed_log, failure)
        return 2
    if not os.environ.get("STAR_SERVER_API_KEY", "").strip():
        failure = {
            "ledger_version": LEDGER_VERSION,
            "record_type": "run-failure",
            "status": "failed",
            "timestamp": utc_now(),
            "run_id": run_id,
            "source_commit": source_commit,
            "confirmed_offset": start,
            "error": "STAR_SERVER_API_KEY is required",
        }
        emit(failure)
        append_jsonl(failed_log, failure)
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
            document_ids = [record.document_id for record in records[batch_start:batch_stop]]
            rc = run_batch(args.core, records, batch_start, batch_stop, args.batch_size)
            if rc != 0:
                failure = {
                    "ledger_version": LEDGER_VERSION,
                    "record_type": "batch-failure",
                    "status": "failed-or-ambiguous",
                    "timestamp": utc_now(),
                    "run_id": run_id,
                    "source_commit": source_commit,
                    "chunk": chunk_no,
                    "exit_code": rc,
                    "confirmed_offset": confirmed_offset,
                    "failed_start_offset": batch_start,
                    "failed_stop_offset": batch_stop,
                    "document_ids": document_ids,
                    "replay_requires_review": True,
                    "note": "A failed POST can be ambiguous; inspect the ingest-core log before replaying this batch.",
                }
                emit(failure)
                append_jsonl(failed_log, failure)
                return rc

            confirmed_offset = batch_stop
            completed_batches += 1
            imported = {
                "ledger_version": LEDGER_VERSION,
                "record_type": "batch-import",
                "status": "confirmed",
                "timestamp": utc_now(),
                "run_id": run_id,
                "source_commit": source_commit,
                "chunk": chunk_no,
                "batch_start_offset": batch_start,
                "batch_stop_offset": batch_stop,
                "confirmed_offset": confirmed_offset,
                "document_count": batch_stop - batch_start,
                "document_ids": document_ids,
            }
            append_jsonl(import_log, imported)
            emit(
                {
                    "status": "checkpoint",
                    "confirmed_offset": confirmed_offset,
                    "completed_server_batches": completed_batches,
                    "total_server_batches": total_batches,
                }
            )
        emit({"status": "chunk-completed", "chunk": chunk_no, "confirmed_offset": confirmed_offset})

    completed = {
        "ledger_version": LEDGER_VERSION,
        "record_type": "run-complete",
        "status": "completed",
        "timestamp": utc_now(),
        "run_id": run_id,
        "source_commit": source_commit,
        "start_offset": start,
        "confirmed_offset": confirmed_offset,
        "imported_documents": confirmed_offset - start,
        "server_batches": completed_batches,
    }
    append_jsonl(import_log, completed)
    emit(completed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
