#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, TextIO

GRAPH_DTYPES = {
    "person",
    "org",
    "relation",
    "event",
    "claim",
    "analysis",
    "concept",
    "education",
    "employment",
}


def compact_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def clip(value: Any, limit: int) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit] + "…"


def record_summary(document: dict[str, Any], limit: int) -> str:
    value = document.get("summary") or document.get("description")
    data = document.get("data")
    if not value and isinstance(data, dict):
        for key in ("description", "definition", "claim", "bio", "business", "mission"):
            value = data.get(key)
            if value:
                break
    if not value:
        value = document.get("title") or document.get("_id") or ""
    return clip(value, limit)


def selected_surface_ids(site: Path, limit: int) -> dict[str, list[Path]]:
    by_id: dict[str, list[Path]] = defaultdict(list)
    for preview in sorted(site.glob("*/documents.json")):
        rows = json.loads(preview.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError(f"document preview must be an array: {preview}")
        destination = preview.parent / "quasar-documents.json"
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            record_id = row.get("id")
            if isinstance(record_id, str) and record_id:
                by_id[record_id].append(destination)
    return by_id


class JsonArrayWriter:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.stream: TextIO = path.open("w", encoding="utf-8")
        self.stream.write("[")
        self.first = True
        self.count = 0

    def write_raw(self, raw: str) -> None:
        if not self.first:
            self.stream.write(",")
        self.first = False
        self.stream.write(raw.rstrip("\r\n"))
        self.count += 1

    def close(self) -> None:
        self.stream.write("]\n")
        self.stream.close()


def prepare(site: Path, bulk: Path, summary_limit: int, quasar_limit: int, root_limit: int) -> dict[str, int]:
    corpus = bulk / "starintel-complete-corpus.jsonl"
    if not corpus.is_file():
        raise FileNotFoundError(corpus)

    index_path = site / "search-index.json"
    config = json.loads(index_path.read_text(encoding="utf-8"))
    if config.get("format") != "starintel-pages-static-index-v1":
        raise ValueError(f"unexpected browser index transport: {config.get('format')!r}")

    fields = list(config.get("records", {}).get("fields", []))
    if "summary" not in fields:
        fields.append("summary")
    config["records"]["fields"] = fields

    surface_ids = selected_surface_ids(site, quasar_limit)
    destination_paths = sorted({path for paths in surface_ids.values() for path in paths})
    writers = {path: JsonArrayWriter(path) for path in destination_paths}
    root_writer = JsonArrayWriter(site / "quasar-documents.json")

    hydrated = 0
    records = 0
    try:
        with corpus.open("r", encoding="utf-8") as corpus_stream:
            for segment in config["records"]["pages"]:
                page_path = site / segment["url"]
                rows = json.loads(page_path.read_text(encoding="utf-8"))
                if not isinstance(rows, list) or not rows:
                    raise ValueError(f"record metadata page must be a non-empty array: {page_path}")

                for row in rows:
                    raw = corpus_stream.readline()
                    if not raw:
                        raise ValueError("canonical corpus ended before record index")
                    document = json.loads(raw)
                    record_id = str(document.get("_id") or "")
                    if len(row) < 2 or str(row[1]) != record_id:
                        raise ValueError(
                            f"record/corpus ordering mismatch: index={row[1] if len(row) > 1 else None!r} corpus={record_id!r}"
                        )

                    dtype = str(document.get("dtype") or "")
                    summary = record_summary(document, summary_limit) if dtype in GRAPH_DTYPES else ""
                    if len(row) >= 8:
                        row[7] = summary
                    else:
                        row.append(summary)
                    hydrated += int(bool(summary))

                    for destination in surface_ids.get(record_id, ()):
                        writers[destination].write_raw(raw)

                    if root_writer.count < root_limit and dtype in GRAPH_DTYPES:
                        root_writer.write_raw(raw)
                    records += 1

                payload = compact_json(rows) + b"\n"
                page_path.write_bytes(payload)
                segment["length"] = len(payload)
                segment["sha256"] = sha256(payload)
                segment["first_id"] = str(rows[0][1])
                segment["last_id"] = str(rows[-1][1])

            if corpus_stream.readline():
                raise ValueError("canonical corpus contains records missing from record index")
    finally:
        root_writer.close()
        for writer in writers.values():
            writer.close()

    index_path.write_bytes(compact_json(config) + b"\n")
    return {
        "records": records,
        "hydrated_summaries": hydrated,
        "quasar_surfaces": len(writers) + 1,
        "quasar_documents": root_writer.count + sum(writer.count for writer in writers.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hydrate bounded Pages metadata and materialize same-origin Quasar working sets"
    )
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--bulk", type=Path, required=True)
    parser.add_argument("--summary-limit", type=int, default=180)
    parser.add_argument("--quasar-limit", type=int, default=500)
    parser.add_argument("--root-limit", type=int, default=2000)
    args = parser.parse_args()
    if args.summary_limit < 1 or args.quasar_limit < 1 or args.root_limit < 1:
        parser.error("limits must be positive")

    result = prepare(
        args.site,
        args.bulk,
        args.summary_limit,
        args.quasar_limit,
        args.root_limit,
    )
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
