#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def key(record: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(record.get("source") or ""),
        str(record.get("booking_id") or ""),
        str(record.get("booking_date") or ""),
        str(record.get("name") or "").casefold().strip(),
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    output: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{line_number}: expected object")
            output.append(value)
    return output


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sources": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected object")
    return value


def merge(root: Path, extra: Path) -> int:
    primary_records = load_jsonl(root / "records.jsonl")
    extra_records = load_jsonl(extra / "records.jsonl")
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for record in primary_records + extra_records:
        merged[key(record)] = record
    records = sorted(
        merged.values(),
        key=lambda record: (
            str(record.get("locality") or ""),
            str(record.get("name") or "").casefold(),
            str(record.get("booking_date") or ""),
        ),
    )
    with (root / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    primary_summary = load_summary(root / "summary.json")
    extra_summary = load_summary(extra / "summary.json")
    primary_summary["record_count"] = len(records)
    primary_summary["sources"] = list(primary_summary.get("sources") or []) + list(extra_summary.get("sources") or [])
    primary_summary["component_record_counts"] = {
        "primary": len(primary_records),
        "expanded": len(extra_records),
    }
    (root / "summary.json").write_text(json.dumps(primary_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge primary and expanded violent-offender locality grabs")
    parser.add_argument("--root", type=Path, default=Path("artifacts/violent-offender-localities"))
    parser.add_argument("--extra", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    extra = args.extra or args.root / "expanded"
    count = merge(args.root, extra)
    print(f"merged_records={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
