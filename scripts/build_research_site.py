#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import read_transport
from starintel_doc.validation import validate_document
from starintel_site.builder import build_site
from starintel_site.model import slug


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def normalize_document(path: Path) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{path}: expected exactly one non-empty NDJSON line")
    document = json.loads(lines[0])
    validate_document(document)
    return document


def infer_target(dataset: str, mappings: dict[str, str]) -> str:
    configured = mappings.get(dataset)
    if configured:
        return slug(configured)
    candidate = re.sub(r"-20\d{2}(?:-\d{2}-\d{2})?$", "", slug(dataset))
    return candidate or slug(dataset)


def filter_excluded(workspace: Path, config: dict[str, Any]) -> None:
    raw_ids = config.get("excluded_document_ids", [])
    if not isinstance(raw_ids, list):
        raise ValueError("site-config.json: excluded_document_ids must be a list")
    excluded = {str(value) for value in raw_ids}
    if not excluded:
        return
    paths = list(workspace.glob("*/*/starintel-documents.jsonl"))
    paths += list(workspace.glob("*/*/starintel-documents.jsonl.gz.b64"))
    paths += list(workspace.glob("*/*/starintel-documents.jsonl.gz.b64.parts"))
    handled: set[Path] = set()
    for path in sorted(paths):
        if path.parent in handled:
            continue
        handled.add(path.parent)
        preferred = path.parent / "starintel-documents.jsonl"
        selected = preferred if preferred.exists() else path
        documents = [json.loads(line) for line in read_transport(selected).splitlines() if line.strip()]
        kept = [document for document in documents if str(document.get("_id")) not in excluded]
        if kept:
            preferred.write_text(
                "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n" for document in kept),
                encoding="utf-8",
            )
        elif preferred.exists():
            preferred.unlink()
        for candidate in path.parent.glob("starintel-documents.jsonl.gz.b64*"):
            candidate.unlink()


def materialize_input(digs_root: Path, db_root: Path, workspace: Path, config: dict[str, Any]) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    if digs_root.exists():
        shutil.copytree(digs_root, workspace, dirs_exist_ok=True)
    filter_excluded(workspace, config)

    mappings = config.get("database_targets", {})
    if not isinstance(mappings, dict):
        raise ValueError("site-config.json: database_targets must be an object")
    normalized_mappings = {str(key): str(value) for key, value in mappings.items()}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    if db_root.exists():
        for path in sorted(db_root.glob("*/*.ndjson")):
            document = normalize_document(path)
            dataset = str(document.get("dataset") or "database")
            target = infer_target(dataset, normalized_mappings)
            grouped[(target, slug(dataset))].append(document)
    for (target, dataset), documents in grouped.items():
        packet = workspace / target / f"db-{dataset}" / "starintel-documents.jsonl"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(
            "".join(
                json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
                for document in sorted(documents, key=lambda item: str(item.get("_id", "")))
            ),
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static StarIntel v0.9.0 research explorer.")
    parser.add_argument("--input", type=Path, default=Path("digs"))
    parser.add_argument("--db", type=Path, default=Path("db"))
    parser.add_argument("--output", type=Path, default=Path("_site"))
    parser.add_argument("--org-output", type=Path, default=Path(".generated/org"))
    parser.add_argument("--workspace", type=Path, default=Path(".generated/site-input"))
    parser.add_argument("--config", type=Path, default=Path("site-config.json"))
    parser.add_argument("--assets", type=Path, default=Path("site-assets"))
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        materialize_input(args.input, args.db, args.workspace, config)
        build_site(args.workspace, args.output, args.org_output, args.config, args.assets)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Built explorer at {args.output} and Org corpus at {args.org_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
