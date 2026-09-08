#!/usr/bin/env python3
"""Fast StarIntel v0.9 document importer.

Streams StarIntel documents (db/ trees, NDJSON files, digs/ packets) into a
StarIntel server as quickly as is safely possible. Correctness never
overrides speed: every document is validated against v0.9 before submit,
result categories are tracked separately, and checkpoints make runs
idempotent and resumable.

    python3 scripts/import_starintel.py \
        --input db/ \
        --server http://127.0.0.1:5000 \
        --workers 8 --batch-size 200 \
        --checkpoint /tmp/import-checkpoint.jsonl \
        --resume \
        --summary /tmp/import-summary.json

Categories:
    accepted   server acknowledged the document (queue ack)
    duplicate  document already imported in this checkpoint (with --resume)
    invalid    failed local v0.9 validation (never sent)
    failed     server rejected permanently (4xx other than 429/408)
    transient  server/temporary failure after bounded retries

The summary is machine-readable; benchmark numbers come only from real runs.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from backend.server_client import StarIntelClient, StarIntelServerError  # noqa: E402
from backend.validation import DocumentValidationError, validate_v09_line  # noqa: E402

BULK_INLINE_LIMIT = 10  # server inline-mode threshold; batches above it run as async jobs


@dataclass
class Counters:
    attempted: int = 0
    accepted: int = 0
    duplicate: int = 0
    invalid: int = 0
    failed: int = 0
    transient: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def bump(self, key: str, n: int = 1) -> None:
        with self.lock:
            setattr(self, key, getattr(self, key) + n)

    def as_dict(self, elapsed: float) -> dict[str, float | int]:
        with self.lock:
            base = {k: getattr(self, k) for k in
                    ("attempted", "accepted", "duplicate", "invalid", "failed", "transient")}
        base["elapsed_seconds"] = round(elapsed, 3)
        base["documents_per_second"] = round(base["attempted"] / elapsed, 1) if elapsed > 0 else 0.0
        return base


def iter_source_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files: list[Path] = []
    for child in sorted(input_path.iterdir()):
        if child.is_dir():
            files.extend(sorted(p for p in child.glob("*.ndjson") if p.is_file()))
        elif child.suffix == ".ndjson" and child.is_file():
            files.append(child)
    return files


def read_docs(files: list[Path]) -> Iterator[tuple[str, str, dict | None, str | None]]:
    """Yield (source, line, parsed_doc_or_None, error_or_None) without loading files into RAM."""
    for path in files:
        with path.open(encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield f"{path}:{lineno}", stripped, json.loads(stripped), None
                except json.JSONDecodeError as exc:
                    yield f"{path}:{lineno}", stripped, None, f"invalid JSON: {exc}"


class Checkpoint:
    """Append-only JSONL of imported document ids; resumable and crash-safe."""

    def __init__(self, path: Path | None, resume: bool) -> None:
        self.path = path
        self._ids: set[str] = set()
        self._lock = threading.Lock()
        self._handle = None
        if path and resume and path.is_file():
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        self._ids.add(json.loads(stripped)["id"])
        if path and not resume and path.exists():
            path.unlink()
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = path.open("a", encoding="utf-8")

    def seen(self, doc_id: str) -> bool:
        with self._lock:
            return doc_id in self._ids

    def record(self, doc_id: str) -> None:
        with self._lock:
            self._ids.add(doc_id)
            if self._handle:
                self._handle.write(json.dumps({"id": doc_id, "at": time.time()}) + "\n")

    def close(self) -> None:
        if self._handle:
            self._handle.close()

    def __len__(self) -> int:
        return len(self._ids)


def batcher(items: Iterator[tuple[str, dict]], size: int, out: Queue, stop: threading.Event, workers: int) -> None:
    buf: list[tuple[str, dict]] = []
    for item in items:
        if stop.is_set():
            break
        buf.append(item)
        if len(buf) >= size:
            out.put(buf)
            buf = []
    if buf and not stop.is_set():
        out.put(buf)
    for _ in range(workers):
        out.put(None)  # one sentinel per worker


def submit_worker(
    client: StarIntelClient,
    queue: Queue,
    counters: Counters,
    checkpoint: Checkpoint,
    retries: int,
    timeout: float,
    stop: threading.Event,
) -> None:
    while True:
        try:
            batch = queue.get(timeout=0.5)
        except Empty:
            if stop.is_set():
                return
            continue
        if batch is None:
            queue.task_done()
            return
        docs = batch
        attempt = 0
        while True:
            try:
                result = client.submit_bulk([d for _, d in docs])
                counters.bump("accepted", result.accepted)
                counters.bump("failed", result.failed)
                for entry, doc in docs:
                    checkpoint.record(str(doc.get("_id", entry)))
                break
            except StarIntelServerError as exc:
                status = exc.status or 0
                permanent = 400 <= status < 500 and status not in (408, 429)
                if permanent or attempt >= retries:
                    counters.bump("transient" if not permanent else "failed", len(docs))
                    break
                attempt += 1
                time.sleep(min(0.25 * (2**attempt), 5.0))
            except DocumentValidationError:
                counters.bump("invalid", len(docs))
                break
        queue.task_done()
        if stop.is_set():
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="db/ directory, digs packet dir, or single .ndjson file")
    parser.add_argument("--server", default=None, help="StarIntel server base URL (or STARINTEL_SERVER_URL)")
    parser.add_argument("--token", default=None, help="bearer token (prefer STARINTEL_TOKEN env)")
    parser.add_argument("--workers", type=int, default=8, help="concurrent batch submitters")
    parser.add_argument("--batch-size", type=int, default=BULK_INLINE_LIMIT, help=f"documents per bulk request (inline limit {BULK_INLINE_LIMIT}; larger batches run as tracked async jobs)")
    parser.add_argument("--timeout", type=float, default=30.0, help="per-request timeout seconds")
    parser.add_argument("--retry", type=int, default=3, help="bounded retries per batch")
    parser.add_argument("--checkpoint", type=str, default=None, help="checkpoint JSONL path")
    parser.add_argument("--resume", action="store_true", help="skip ids present in the checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="plan only: count files and documents, submit nothing")
    parser.add_argument("--validate-only", action="store_true", help="validate every document, submit nothing")
    parser.add_argument("--limit", type=int, default=None, help="stop after N valid documents")
    parser.add_argument("--dtypes", type=str, default=None, help="comma-separated dtype filter")
    parser.add_argument("--summary", type=str, default=None, help="write machine-readable summary JSON here")
    args = parser.parse_args(argv)

    batch_size = min(args.batch_size, 200)
    if batch_size < 1 or args.workers < 1:
        parser.error("batch-size and workers must be >= 1")
    server = args.server or "http://127.0.0.1:5000"

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"input does not exist: {input_path}")
    files = iter_source_files(input_path)
    if args.dtypes:
        allowed = {d.strip() for d in args.dtypes.split(",")}
        files = [f for f in files if f.parent.name in allowed or f.name in allowed]
    if not files:
        print(json.dumps({"error": "no .ndjson source files found"}))
        return 2

    if args.dry_run:
        plan = {"files": len(files), "input": str(input_path), "server": server,
                "batch_size": batch_size, "workers": args.workers, "mode": "dry-run"}
        print(json.dumps(plan))
        return 0

    counters = Counters()
    stop = threading.Event()
    original_sigint = signal.getsignal(signal.SIGINT)

    def request_stop(_sig, _frm):  # pragma: no cover - interactive path
        stop.set()
        signal.signal(signal.SIGINT, original_sigint)

    signal.signal(signal.SIGINT, request_stop)

    checkpoint = Checkpoint(Path(args.checkpoint) if args.checkpoint else None, args.resume)
    started = time.monotonic()

    try:
        if args.validate_only:
            for source, _line, doc, error in read_docs(files):
                if stop.is_set():
                    break
                counters.bump("attempted")
                if error or doc is None:
                    counters.bump("invalid")
                    print(f"INVALID {source}: {error}", file=sys.stderr)
                    continue
                try:
                    validate_v09_line(json.dumps(doc))
                    counters.bump("accepted")
                except DocumentValidationError as exc:
                    counters.bump("invalid")
                    print(f"INVALID {source}: {exc}", file=sys.stderr)
                if args.limit and counters.attempted >= args.limit:
                    break
        else:
            client = StarIntelClient(server, args.token or os.environ.get("STARINTEL_TOKEN"), args.timeout)
            queue: Queue = Queue(maxsize=args.workers * 2)
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                for _ in range(args.workers):
                    pool.submit(submit_worker, client, queue, counters, checkpoint, args.retry, args.timeout, stop)

                def filtered():
                    sent = 0
                    for source, _line, doc, error in read_docs(files):
                        if stop.is_set() or (args.limit and sent >= args.limit):
                            break
                        if error or doc is None:
                            counters.bump("invalid")
                            counters.bump("attempted")
                            continue
                        doc_id = str(doc.get("_id", ""))
                        if not doc_id:
                            counters.bump("invalid")
                            counters.bump("attempted")
                            continue
                        counters.bump("attempted")
                        if args.resume and checkpoint.seen(doc_id):
                            counters.bump("duplicate")
                            continue
                        sent += 1
                        yield source, doc

                producer = threading.Thread(
                    target=batcher, args=(filtered(), batch_size, queue, stop, args.workers), daemon=True
                )
                producer.start()
                producer.join()
                # Wait for workers to consume every batch and sentinel.
                queue.join()
                client.close()
    finally:
        elapsed = time.monotonic() - started
        checkpoint.close()

    summary = counters.as_dict(elapsed)
    summary["input"] = str(input_path)
    summary["server"] = server
    summary["mode"] = "validate-only" if args.validate_only else "import"
    summary["checkpoint_ids"] = len(checkpoint)
    print(json.dumps(summary, indent=2))
    if args.summary:
        Path(args.summary).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["invalid"] == 0 and summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
