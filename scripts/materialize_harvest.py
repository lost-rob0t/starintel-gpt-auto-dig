#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.model import Document


def compact(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def safe_packet_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "digs":
        raise ValueError("harvest output must be a relative path below digs/")
    if path.name != "starintel-documents.jsonl":
        raise ValueError("harvest output must end in starintel-documents.jsonl")
    return path


def materialize(manifest_path: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset = manifest["dataset"]
    output = safe_packet_path(manifest["output"])
    documents = manifest["documents"]
    if not isinstance(documents, list) or not documents:
        raise ValueError("manifest documents must be a non-empty list")

    seen: set[str] = set()
    rendered: list[str] = []
    for item in documents:
        metadata = dict(item.get("metadata", {}))
        document = Document.create(
            item["dtype"],
            dataset,
            doc_id=item["id"],
            title=item.get("title", ""),
            summary=item.get("summary", ""),
            data=item.get("data", {}),
            **metadata,
        ).to_dict()
        if document["_id"] in seen:
            raise ValueError(f"duplicate document id: {document['_id']}")
        seen.add(document["_id"])
        rendered.append(compact(document))

    target = ROOT / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(rendered) + "\n", encoding="utf-8")
    print(target.relative_to(ROOT))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize a validated Auto-Dig harvest packet")
    parser.add_argument("manifest")
    args = parser.parse_args(argv)
    try:
        materialize(Path(args.manifest))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
