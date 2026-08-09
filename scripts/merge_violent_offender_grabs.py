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


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    booking_id = str(record.get("booking_id") or "").casefold().strip()
    case_numbers = record.get("case_numbers") or []
    if isinstance(case_numbers, list):
        record["case_numbers"] = [
            value
            for value in case_numbers
            if str(value).casefold().strip() != booking_id
        ]
    return record


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
            output.append(normalize_record(value))
    return output


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sources": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: expected object")
    return value


def source_score(source: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        1 if source.get("error") is None else 0,
        int(source.get("records") or 0),
        int(source.get("candidates_seen") or 0),
        int(source.get("pages_fetched") or 0),
    )


def coalesce_sources(groups: list[tuple[str, list[dict[str, Any]], dict[str, Any]]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    unnamed: list[dict[str, Any]] = []
    for _, _, component_summary in groups:
        for source in list(component_summary.get("sources") or []):
            if not isinstance(source, dict):
                continue
            name = str(source.get("source") or "").strip()
            if not name:
                unnamed.append(source)
                continue
            existing = best.get(name)
            if existing is None or source_score(source) >= source_score(existing):
                best[name] = source
    return sorted(best.values(), key=lambda source: str(source.get("source") or "")) + unnamed


def merge(root: Path, components: list[Path]) -> int:
    groups: list[tuple[str, list[dict[str, Any]], dict[str, Any]]] = [
        ("primary", load_jsonl(root / "records.jsonl"), load_summary(root / "summary.json"))
    ]
    for component in components:
        groups.append((component.name, load_jsonl(component / "records.jsonl"), load_summary(component / "summary.json")))

    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for _, records, _ in groups:
        for record in records:
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

    summary = groups[0][2]
    summary["record_count"] = len(records)
    summary["sources"] = coalesce_sources(groups)
    summary["component_record_counts"] = {
        name: len(group_records)
        for name, group_records, _ in groups
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge violent-offender locality scraper output groups")
    parser.add_argument("--root", type=Path, default=Path("artifacts/violent-offender-localities"))
    parser.add_argument("--component", action="append", type=Path, dest="components")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    components = args.components or [args.root / "expanded", args.root / "high-yield"]
    count = merge(args.root, components)
    print(f"merged_records={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
