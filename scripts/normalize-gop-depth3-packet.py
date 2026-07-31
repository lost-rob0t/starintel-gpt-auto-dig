#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

UNDECLARED_ORG_FIELDS = frozenset({"connected_organization_id", "fec_committee_id"})


def normalize_document(document: dict[str, Any]) -> tuple[dict[str, Any], int]:
    if document.get("dtype") != "org":
        return document, 0

    data = document.get("data")
    if not isinstance(data, dict):
        return document, 0

    removed = 0
    for field in UNDECLARED_ORG_FIELDS:
        if field in data:
            del data[field]
            removed += 1
    return document, removed


def iter_ndjson_paths(inputs: Iterable[Path]) -> Iterable[Path]:
    for input_path in inputs:
        if input_path.is_dir():
            yield from sorted(input_path.rglob("*.ndjson"))
        else:
            yield input_path


def normalize_ndjson(path: Path) -> tuple[int, int]:
    documents: list[dict[str, Any]] = []
    removed = 0

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        document = json.loads(line)
        if not isinstance(document, dict):
            raise ValueError(f"{path}:{line_number}: document must be an object")
        document, count = normalize_document(document)
        documents.append(document)
        removed += count

    if removed:
        payload = "".join(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
            for document in documents
        )
        path.write_text(payload, encoding="utf-8")
    return len(documents), removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize GOP recursion StarIntel NDJSON fields.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    files = 0
    documents = 0
    removed = 0
    for path in iter_ndjson_paths(args.paths):
        file_documents, file_removed = normalize_ndjson(path)
        files += 1
        documents += file_documents
        removed += file_removed

    print(
        f"normalized {documents} documents across {files} files; "
        f"removed {removed} undeclared organization fields"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
