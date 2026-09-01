#!/usr/bin/env python3
"""Import canonical Auto-Dig StarIntel documents into the ingest server."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urljoin


DEFAULT_SERVER_URL = "https://ingest.starintel.actor"
DEFAULT_BATCH_SIZE = 250
MAX_BATCH_SIZE = 500
TRANSIENT_HTTP_STATUS = {429, 502, 503, 504}
TERMINAL_JOB_STATUS = {"completed", "completed-with-errors", "failed"}
DOC_PACKET_NAME = "starintel-documents.jsonl"


@dataclass(frozen=True)
class DocumentRecord:
    document: dict
    source: str

    @property
    def document_id(self) -> str:
        return self.document["_id"]


def run_git(root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return result.stdout


def repo_root(path: Path | None = None) -> Path:
    start = path or Path.cwd()
    return Path(run_git(start, "rev-parse", "--show-toplevel").strip())


def is_document_carrier(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith("db/")
        and normalized.endswith(".ndjson")
        or normalized.startswith("digs/")
        and normalized.endswith("/" + DOC_PACKET_NAME)
    )


def parse_jsonl(text: str, source: str) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            document = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise ValueError(f"{source}:{line_number}: document must be a JSON object")
        document_id = document.get("_id")
        dtype = document.get("dtype")
        if not isinstance(document_id, str) or not document_id:
            raise ValueError(f"{source}:{line_number}: document is missing non-empty _id")
        if not isinstance(dtype, str) or not dtype:
            raise ValueError(f"{source}:{line_number}: document {document_id!r} is missing dtype")
        records.append(DocumentRecord(document=document, source=f"{source}:{line_number}"))
    return records


def canonical_document(document: dict) -> str:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def integer_version(document: dict) -> int | None:
    version = document.get("version")
    if isinstance(version, bool):
        return None
    if isinstance(version, int):
        return version
    return None


def db_source(record: DocumentRecord) -> bool:
    return record.source.startswith("db/")


def merge_records(
    records: Iterable[DocumentRecord],
    *,
    prefer_db: bool = False,
) -> dict[str, DocumentRecord]:
    merged: dict[str, DocumentRecord] = {}
    for record in records:
        previous = merged.get(record.document_id)
        if previous is None:
            merged[record.document_id] = record
            continue
        if canonical_document(previous.document) == canonical_document(record.document):
            continue
        if prefer_db and db_source(previous) != db_source(record):
            if db_source(record):
                merged[record.document_id] = record
            continue
        old_version = integer_version(previous.document)
        new_version = integer_version(record.document)
        if old_version is not None and new_version is not None and old_version != new_version:
            if new_version > old_version:
                merged[record.document_id] = record
            continue
        raise ValueError(
            f"conflicting duplicate _id {record.document_id!r}: "
            f"{previous.source} vs {record.source}"
        )
    return merged


def current_document_paths(root: Path) -> Iterator[Path]:
    db = root / "db"
    if db.is_dir():
        yield from sorted(db.rglob("*.ndjson"))
    digs = root / "digs"
    if digs.is_dir():
        yield from sorted(digs.rglob(DOC_PACKET_NAME))


def collect_all_documents(root: Path) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    for path in current_document_paths(root):
        relative = path.relative_to(root).as_posix()
        records.extend(parse_jsonl(path.read_text(encoding="utf-8"), relative))
    return list(merge_records(records, prefer_db=True).values())


def git_show_text(root: Path, ref: str, path: str) -> str:
    return run_git(root, "show", f"{ref}:{path}")


def changed_document_paths(root: Path, base: str) -> tuple[set[str], set[str]]:
    output = run_git(
        root,
        "diff",
        "--name-status",
        "-M",
        "--find-renames",
        f"{base}..HEAD",
        "--",
        "db",
        "digs",
    )
    base_paths: set[str] = set()
    current_paths: set[str] = set()

    for raw_line in output.splitlines():
        if not raw_line:
            continue
        fields = raw_line.split("\t")
        status = fields[0]
        code = status[0]

        if code in {"R", "C"}:
            if len(fields) != 3:
                raise ValueError(f"unexpected git diff line: {raw_line!r}")
            old_path, new_path = fields[1], fields[2]
            if is_document_carrier(old_path):
                base_paths.add(old_path)
            if is_document_carrier(new_path):
                current_paths.add(new_path)
            continue

        if len(fields) != 2:
            raise ValueError(f"unexpected git diff line: {raw_line!r}")
        path = fields[1]
        if not is_document_carrier(path):
            continue
        if code != "A":
            base_paths.add(path)
        if code != "D":
            current_paths.add(path)

    return base_paths, current_paths


def collect_new_documents(root: Path, base: str) -> list[DocumentRecord]:
    run_git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    base_paths, current_paths = changed_document_paths(root, base)

    base_records: list[DocumentRecord] = []
    for path in sorted(base_paths):
        base_records.extend(parse_jsonl(git_show_text(root, base, path), f"{base}:{path}"))

    current_records: list[DocumentRecord] = []
    for relative in sorted(current_paths):
        path = root / relative
        if path.is_file():
            current_records.extend(parse_jsonl(path.read_text(encoding="utf-8"), relative))

    base_by_id = merge_records(base_records)
    current_by_id = merge_records(current_records)
    return [
        record
        for document_id, record in current_by_id.items()
        if document_id not in base_by_id
    ]


class IngestClient:
    def __init__(
        self,
        server_url: str,
        api_key: str,
        *,
        timeout: float = 30.0,
        retries: int = 4,
        poll_interval: float = 1.0,
        poll_timeout: float = 180.0,
    ) -> None:
        self.server_url = server_url.rstrip("/") + "/"
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def request_json(self, method: str, path: str, payload: object | None = None) -> dict:
        url = urljoin(self.server_url, path.lstrip("/"))
        body = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "starintel-auto-dig-ingest/1",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"

        for attempt in range(self.retries + 1):
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    if not raw:
                        return {}
                    parsed = json.loads(raw)
                    if not isinstance(parsed, dict):
                        raise RuntimeError(f"{method} {url} returned non-object JSON")
                    return parsed
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="replace")
                if exc.code in TRANSIENT_HTTP_STATUS and attempt < self.retries:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise RuntimeError(
                    f"{method} {url} failed with HTTP {exc.code}: {raw[:1000]}"
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc

        raise AssertionError("unreachable")

    def wait_for_job(self, status_url: str) -> dict:
        deadline = time.monotonic() + self.poll_timeout
        while True:
            response = self.request_json("GET", status_url)
            status = str(response.get("status", "")).lower()
            if status in TERMINAL_JOB_STATUS:
                failed = int(response.get("failed", 0) or 0)
                if status != "completed" or failed:
                    raise RuntimeError(
                        "bulk ingest job failed: "
                        + json.dumps(response, ensure_ascii=False, sort_keys=True)
                    )
                return response
            if time.monotonic() >= deadline:
                raise RuntimeError(f"timed out waiting for bulk ingest job {status_url}")
            time.sleep(self.poll_interval)

    def upload_batch(self, documents: list[dict]) -> dict:
        response = self.request_json("POST", "/documents/bulk", documents)
        status_url = response.get("status_url")
        if response.get("status") == "accepted" and isinstance(status_url, str):
            return self.wait_for_job(status_url)

        failed = int(response.get("failed", 0) or 0)
        if failed:
            raise RuntimeError(
                "bulk ingest reported failures: "
                + json.dumps(response, ensure_ascii=False, sort_keys=True)
            )
        return response


def batched(items: list[DocumentRecord], size: int) -> Iterator[list[DocumentRecord]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import canonical Auto-Dig StarIntel documents into the ingest server."
    )
    parser.add_argument(
        "--diff",
        metavar="BASE",
        help="Import only logical document IDs newly introduced since BASE.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import the full canonical corpus (default when --diff is omitted).",
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("STAR_INGEST_URL", DEFAULT_SERVER_URL),
        help="Ingest server base URL (default: %(default)s).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Documents per request (1-{MAX_BATCH_SIZE}, default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--poll-timeout",
        type=float,
        default=180.0,
        help="Maximum seconds to wait for an asynchronous bulk job.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve documents and print a summary without contacting the server.",
    )
    args = parser.parse_args(argv)
    if args.diff and args.all:
        parser.error("--diff and --all are mutually exclusive")
    if not 1 <= args.batch_size <= MAX_BATCH_SIZE:
        parser.error(f"--batch-size must be between 1 and {MAX_BATCH_SIZE}")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = repo_root()

    if args.diff:
        records = collect_new_documents(root, args.diff)
        mode = f"diff:{args.diff}"
    else:
        records = collect_all_documents(root)
        mode = "all"

    records.sort(key=lambda record: record.document_id)
    summary = {
        "mode": mode,
        "documents": len(records),
        "server_url": args.server_url,
    }
    print(json.dumps(summary, sort_keys=True))

    if not records or args.dry_run:
        return 0

    api_key = os.environ.get("STAR_SERVER_API_KEY")
    if not api_key:
        print("STAR_SERVER_API_KEY is required", file=sys.stderr)
        return 2

    client = IngestClient(
        args.server_url,
        api_key,
        timeout=args.timeout,
        poll_timeout=args.poll_timeout,
    )

    uploaded = 0
    for batch_number, batch in enumerate(batched(records, args.batch_size), start=1):
        response = client.upload_batch([record.document for record in batch])
        uploaded += len(batch)
        print(
            json.dumps(
                {
                    "batch": batch_number,
                    "batch_documents": len(batch),
                    "uploaded": uploaded,
                    "total": len(records),
                    "server_status": response.get("status", "inline"),
                },
                sort_keys=True,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
