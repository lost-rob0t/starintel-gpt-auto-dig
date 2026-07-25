#!/usr/bin/env python3
"""Split a StarIntel JSONL stream into db/<dtype>/<_id>.ndjson."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def safe_component(value: str, field: str) -> str:
    if not value or value in {".", ".."}:
        raise ValueError(f"{field} is empty or unsafe: {value!r}")
    if "/" in value or "\\" in value or "\x00" in value:
        raise ValueError(f"{field} contains a path separator or NUL: {value!r}")
    return value


def compact(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"


def import_jsonl(source: Path, root: Path) -> tuple[int, int]:
    seen: set[str] = set()
    created = 0
    replaced = 0

    for number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        record = json.loads(raw)
        if not isinstance(record, dict):
            raise ValueError(f"line {number}: expected an object")

        dtype = safe_component(str(record.get("dtype", "")), "dtype")
        doc_id = safe_component(str(record.get("_id", "")), "_id")
        if doc_id in seen:
            raise ValueError(f"line {number}: duplicate _id {doc_id!r}")
        seen.add(doc_id)

        target = root / "db" / dtype / f"{doc_id}.ndjson"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = compact(record)

        if target.exists():
            if target.read_text(encoding="utf-8") == payload:
                continue
            replaced += 1
        else:
            created += 1

        target.write_text(payload, encoding="utf-8")

    return created, replaced


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    created, replaced = import_jsonl(args.source.resolve(), args.root.resolve())
    print(f"created={created} replaced={replaced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
