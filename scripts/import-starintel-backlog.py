#!/usr/bin/env python3
"""Import the canonical Auto-Dig corpus in resumable 10k outer chunks.

The server accepts at most 500 documents per /documents/bulk request, but the
live ingest host also has an nginx request-body ceiling. Initial batches start
at --batch-size (default 500). A clean HTTP 413 rejection is safe to retry, so
this wrapper bisects only that rejected range until it fits.

Two append-only ledgers are authoritative:
- canonical-import.jsonl: exact source commit and every confirmed imported ID.
- failed-import.jsonl: corpus conflicts, recovered 413 splits, and terminal or
  ambiguous failures with exact IDs.

Canonical resolution is fail-soft by logical ID. Existing repository
precedence rules apply; unresolved same-precedence conflicts are quarantined
rather than chosen arbitrarily.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from collections import defaultdict
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
LEDGER_VERSION = 2


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
        handle.write(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
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


def resolve_backlog_records(importer, root: Path):
    """Resolve every logical ID independently and quarantine only conflicts."""
    candidates = defaultdict(list)
    carrier_errors: list[dict] = []
    raw_records = 0

    for path in importer.current_document_paths(root):
        relative = path.relative_to(root).as_posix()
        try:
            parsed = importer.parse_jsonl(path.read_text(encoding="utf-8"), relative)
        except (OSError, UnicodeError, ValueError) as exc:
            carrier_errors.append(
                {
                    "record_type": "source-read-error",
                    "status": "skipped-source",
                    "source": relative,
                    "error": str(exc),
                }
            )
            continue

        raw_records += len(parsed)
        for record in parsed:
            candidates[record.document_id].append(record)

    resolved = []
    conflicts: list[dict] = list(carrier_errors)
    for document_id in sorted(candidates):
        records = candidates[document_id]
        try:
            merged = importer.merge_records(records, prefer_db=True)
            selected = merged.get(document_id)
            if selected is None:
                raise ValueError("canonical resolver returned no record")
            resolved.append(selected)
        except ValueError as exc:
            conflicts.append(
                {
                    "record_type": "canonical-conflict",
                    "status": "skipped-conflict",
                    "document_id": document_id,
                    "sources": sorted(record.source for record in records),
                    "candidate_count": len(records),
                    "error": str(exc),
                    "replay_requires_review": True,
                }
            )

    resolved.sort(key=lambda record: record.document_id)
    return resolved, conflicts, raw_records, len(candidates)


def batch_input(records, first: int, past_last: int) -> str:
    return "".join(
        json.dumps(
            record.document,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
        for record in records[first:past_last]
    )


def run_batch(core: Path, records, first: int, past_last: int) -> tuple[int, str]:
    """Run one core invocation containing exactly one server batch."""
    count = past_last - first
    command = [
        str(core),
        "--workers",
        "1",
        "--batch-size",
        str(count),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        input=batch_input(records, first, past_last),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)

    return result.returncode, result.stdout + "\n" + result.stderr


def request_too_large(output: str) -> bool:
    lowered = output.lower()
    return (
        "http 413" in lowered
        or "413 request entity too large" in lowered
        or "request entity too large" in lowered
    )


def common_event(run_id: str, source_commit: str) -> dict:
    return {
        "ledger_version": LEDGER_VERSION,
        "timestamp": utc_now(),
        "run_id": run_id,
        "source_commit": source_commit,
    }


def record_confirmed_batch(
    *,
    import_log: Path,
    records,
    first: int,
    past_last: int,
    chunk_no: int,
    run_id: str,
    source_commit: str,
    adaptive_depth: int,
) -> None:
    append_jsonl(
        import_log,
        {
            **common_event(run_id, source_commit),
            "record_type": "batch-import",
            "status": "confirmed",
            "chunk": chunk_no,
            "batch_start_offset": first,
            "batch_stop_offset": past_last,
            "confirmed_offset": past_last,
            "document_count": past_last - first,
            "document_ids": [record.document_id for record in records[first:past_last]],
            "adaptive_depth": adaptive_depth,
        },
    )


def ingest_range(
    *,
    core: Path,
    records,
    first: int,
    past_last: int,
    chunk_no: int,
    import_log: Path,
    failed_log: Path,
    run_id: str,
    source_commit: str,
    state: dict[str, int],
    adaptive_depth: int = 0,
) -> bool:
    """Ingest all canonical documents through the authorized bulk route.

    The server requires ``targets:dispatch`` and resource grants for every
    target in a bulk request before publishing any document in that batch.
    Target actor metadata is optional in the canonical schema.
    """

    rc, output = run_batch(core, records, first, past_last)
    document_ids = [record.document_id for record in records[first:past_last]]

    if rc == 0:
        record_confirmed_batch(
            import_log=import_log,
            records=records,
            first=first,
            past_last=past_last,
            chunk_no=chunk_no,
            run_id=run_id,
            source_commit=source_commit,
            adaptive_depth=adaptive_depth,
        )
        state["confirmed_offset"] = past_last
        state["completed_batches"] += 1
        state["imported_documents"] += past_last - first
        emit(
            {
                "status": "checkpoint",
                "confirmed_offset": past_last,
                "completed_server_batches": state["completed_batches"],
                "imported_documents": state["imported_documents"],
                "last_batch_documents": past_last - first,
                "adaptive_depth": adaptive_depth,
            }
        )
        return True

    if request_too_large(output):
        append_jsonl(
            failed_log,
            {
                **common_event(run_id, source_commit),
                "record_type": "ingress-413",
                "status": "recovered-by-split" if past_last - first > 1 else "terminal",
                "chunk": chunk_no,
                "http_status": 413,
                "failed_start_offset": first,
                "failed_stop_offset": past_last,
                "document_count": past_last - first,
                "document_ids": document_ids,
                "replay_requires_review": False,
                "adaptive_depth": adaptive_depth,
            },
        )

        if past_last - first == 1:
            emit(
                {
                    "status": "failed",
                    "reason": "single-document-http-413",
                    "document_id": document_ids[0],
                    "confirmed_offset": state["confirmed_offset"],
                }
            )
            return False

        midpoint = first + ((past_last - first) // 2)
        emit(
            {
                "status": "batch-splitting",
                "reason": "http-413",
                "start_offset": first,
                "stop_offset": past_last,
                "documents": past_last - first,
                "split_at": midpoint,
                "left_documents": midpoint - first,
                "right_documents": past_last - midpoint,
                "adaptive_depth": adaptive_depth,
            }
        )
        if not ingest_range(
            core=core,
            records=records,
            first=first,
            past_last=midpoint,
            chunk_no=chunk_no,
            import_log=import_log,
            failed_log=failed_log,
            run_id=run_id,
            source_commit=source_commit,
            state=state,
            adaptive_depth=adaptive_depth + 1,
        ):
            return False
        return ingest_range(
            core=core,
            records=records,
            first=midpoint,
            past_last=past_last,
            chunk_no=chunk_no,
            import_log=import_log,
            failed_log=failed_log,
            run_id=run_id,
            source_commit=source_commit,
            state=state,
            adaptive_depth=adaptive_depth + 1,
        )

    failure = {
        **common_event(run_id, source_commit),
        "record_type": "batch-failure",
        "status": "failed-or-ambiguous",
        "chunk": chunk_no,
        "exit_code": rc,
        "confirmed_offset": state["confirmed_offset"],
        "failed_start_offset": first,
        "failed_stop_offset": past_last,
        "document_count": past_last - first,
        "document_ids": document_ids,
        "replay_requires_review": True,
        "adaptive_depth": adaptive_depth,
        "note": "Non-413 POST failures can be ambiguous; inspect the ingest-core log before replaying this range.",
    }
    append_jsonl(failed_log, failure)
    emit(
        {
            "status": "failed-or-ambiguous",
            "confirmed_offset": state["confirmed_offset"],
            "failed_start_offset": first,
            "failed_stop_offset": past_last,
            "documents": past_last - first,
        }
    )
    return False


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    importer = load_importer()
    root = importer.repo_root(ROOT)
    source_commit = git_head(root)
    run_id = os.environ.get("GITHUB_RUN_ID") or f"local-{os.getpid()}"
    import_log = args.log_dir / "canonical-import.jsonl"
    failed_log = args.log_dir / "failed-import.jsonl"

    records, conflicts, raw_records, raw_unique_ids = resolve_backlog_records(importer, root)
    for conflict in conflicts:
        event = {**common_event(run_id, source_commit), **conflict}
        append_jsonl(failed_log, event)
        emit(
            {
                "status": event["status"],
                "record_type": event["record_type"],
                "document_id": event.get("document_id"),
                "source": event.get("source"),
            }
        )

    start_offset = args.start_offset
    if args.resume_from_log:
        resumed = highest_confirmed_offset(import_log, source_commit)
        if resumed is not None:
            start_offset = max(start_offset, resumed)

    start, stop = selected_window(len(records), start_offset, args.max_documents)
    chunks = list(chunk_bounds(start, stop, args.chunk_size))
    nominal_batches = sum(
        (chunk_stop - chunk_start + args.batch_size - 1) // args.batch_size
        for _chunk_no, chunk_start, chunk_stop in chunks
    )

    plan = {
        **common_event(run_id, source_commit),
        "record_type": "run-plan",
        "status": "planned",
        "raw_candidate_records": raw_records,
        "raw_unique_ids": raw_unique_ids,
        "canonical_documents": len(records),
        "quarantined_conflicts": len(conflicts),
        "start_offset": start,
        "stop_offset": stop,
        "selected_documents": stop - start,
        "chunk_size": args.chunk_size,
        "chunks": len(chunks),
        "initial_batch_size": args.batch_size,
        "max_batch_size": MAX_BATCH_SIZE,
        "nominal_server_batches": nominal_batches,
        "adaptive_http_413_split": True,
        "dry_run": args.dry_run,
    }
    emit(plan)
    append_jsonl(import_log, plan)

    if args.dry_run or start == stop:
        return 0

    if not args.core.is_file():
        failure = {
            **common_event(run_id, source_commit),
            "record_type": "run-failure",
            "status": "failed",
            "confirmed_offset": start,
            "error": f"ingest core not found: {args.core}",
        }
        emit(failure)
        append_jsonl(failed_log, failure)
        return 2

    if not os.environ.get("STAR_SERVER_API_KEY", "").strip():
        failure = {
            **common_event(run_id, source_commit),
            "record_type": "run-failure",
            "status": "failed",
            "confirmed_offset": start,
            "error": "STAR_SERVER_API_KEY is required",
        }
        emit(failure)
        append_jsonl(failed_log, failure)
        return 2

    state = {"confirmed_offset": start, "completed_batches": 0, "imported_documents": 0}

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
        for first, past_last in batch_bounds(chunk_start, chunk_stop, args.batch_size):
            if not ingest_range(
                core=args.core,
                records=records,
                first=first,
                past_last=past_last,
                chunk_no=chunk_no,
                import_log=import_log,
                failed_log=failed_log,
                run_id=run_id,
                source_commit=source_commit,
                state=state,
            ):
                return 1

        emit(
            {
                "status": "chunk-completed",
                "chunk": chunk_no,
                "confirmed_offset": state["confirmed_offset"],
                "imported_documents": state["imported_documents"],
            }
        )

    completed = {
        **common_event(run_id, source_commit),
        "record_type": "run-complete",
        "status": "completed",
        "start_offset": start,
        "confirmed_offset": state["confirmed_offset"],
        "imported_documents": state["imported_documents"],
        "quarantined_conflicts": len(conflicts),
        "server_batches": state["completed_batches"],
    }
    append_jsonl(import_log, completed)
    emit(completed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
