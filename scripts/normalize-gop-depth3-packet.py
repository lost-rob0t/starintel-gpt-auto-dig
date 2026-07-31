#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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


def normalize_packet(path: Path) -> tuple[int, int]:
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

    payload = "".join(
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        for document in documents
    )
    path.write_text(payload, encoding="utf-8")
    return len(documents), removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize generated GOP depth-3 StarIntel packet fields.")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()

    documents, removed = normalize_packet(args.packet)
    print(f"normalized {documents} documents; removed {removed} undeclared organization fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
