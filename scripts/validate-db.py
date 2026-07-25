#!/usr/bin/env python3
"""Validate the Git-backed StarIntel document database."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db"


def load_one(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data.endswith(b"\n"):
        raise ValueError(f"{path}: missing terminating newline")
    text = data.decode("utf-8")
    lines = text.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        raise ValueError(f"{path}: expected exactly one non-empty NDJSON line")
    record = json.loads(lines[0])
    if not isinstance(record, dict):
        raise ValueError(f"{path}: expected JSON object")
    return record


def main() -> int:
    if not DB.is_dir():
        raise SystemExit("db/ does not exist")

    ids: dict[str, Path] = {}
    counts: Counter[str] = Counter()
    errors: list[str] = []

    for path in sorted(DB.glob("*/*.ndjson")):
        try:
            record = load_one(path)
            dtype = str(record.get("dtype", ""))
            doc_id = str(record.get("_id", ""))
            expected_dtype = path.parent.name
            expected_id = path.name.removesuffix(".ndjson")

            if dtype != expected_dtype:
                errors.append(f"{path}: dtype={dtype!r}, directory={expected_dtype!r}")
            if doc_id != expected_id:
                errors.append(f"{path}: _id={doc_id!r}, filename={expected_id!r}")
            if not doc_id:
                errors.append(f"{path}: missing _id")
            if doc_id in ids:
                errors.append(f"{path}: duplicate _id also present at {ids[doc_id]}")
            else:
                ids[doc_id] = path
            counts[dtype] += 1
        except Exception as exc:
            errors.append(str(exc))

    if not ids:
        errors.append("db/ contains no documents")

    relation_errors = 0
    for path in sorted((DB / "relation").glob("*.ndjson")) if (DB / "relation").is_dir() else []:
        try:
            record = load_one(path)
            for endpoint in ("subject", "object"):
                value = record.get(endpoint)
                if value not in ids:
                    errors.append(f"{path}: unresolved relation {endpoint}={value!r}")
                    relation_errors += 1
        except Exception as exc:
            errors.append(str(exc))

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1

    print(f"validated {len(ids)} documents")
    for dtype, count in sorted(counts.items()):
        print(f"{dtype}: {count}")
    print(f"relation endpoint errors: {relation_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
