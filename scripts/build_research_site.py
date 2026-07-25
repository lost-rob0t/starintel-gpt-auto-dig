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
    if not isinstance(document, dict):
        raise ValueError(f"{path}: expected JSON object")

    source = document.get("source")
    if "sources" not in document:
        document["sources"] = [source] if source else []
    if not isinstance(document["sources"], list):
        raise ValueError(f"{path}: sources must be a list")

    if document.get("dtype") == "relation":
        subject = document.get("subject")
        object_ = document.get("object")
        predicate = document.get("predicate")
        if isinstance(subject, str):
            document["subject_ref"] = subject
            document["subject"] = {"entity_id": subject}
        if isinstance(object_, str):
            document["object_ref"] = object_
        if isinstance(predicate, str) and isinstance(object_, str):
            document.setdefault("predicates", []).append(
                {"predicate": predicate, "object": {"entity_id": object_}}
            )

    return document


def infer_target(dataset: str, mappings: dict[str, str]) -> str:
    configured = mappings.get(dataset)
    if configured:
        return slug(configured)
    candidate = re.sub(r"-20\d{2}(?:-\d{2}-\d{2})?$", "", slug(dataset))
    return candidate or slug(dataset)


def materialize_input(
    digs_root: Path,
    db_root: Path,
    workspace: Path,
    config: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    if digs_root.exists():
        shutil.copytree(digs_root, workspace, dirs_exist_ok=True)

    mappings = config.get("database_targets", {})
    if not isinstance(mappings, dict):
        raise ValueError("site-config.json: database_targets must be an object")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if db_root.exists():
        for path in sorted(db_root.glob("*/*.ndjson")):
            document = normalize_document(path)
            dataset = str(document.get("dataset") or "database")
            target = infer_target(dataset, {str(k): str(v) for k, v in mappings.items()})
            grouped[(target, slug(dataset))].append(document)
            by_target[target].append(document)

    for (target, dataset), documents in grouped.items():
        packet = workspace / target / f"db-{dataset}" / "starintel-documents.jsonl"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(
            "".join(
                json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
                for document in sorted(documents, key=lambda item: str(item.get("_id", "")))
            ),
            encoding="utf-8",
        )

    return by_target


def add_relation_edges(output: Path, by_target: dict[str, list[dict[str, Any]]]) -> None:
    for target, documents in by_target.items():
        path = output / target / "graph.json"
        if not path.exists():
            continue
        graph = json.loads(path.read_text(encoding="utf-8"))
        nodes = {str(node.get("id")) for node in graph.get("nodes", [])}
        keys = {
            (str(edge.get("source")), str(edge.get("target")), str(edge.get("label")))
            for edge in graph.get("edges", [])
        }
        for document in documents:
            if document.get("dtype") != "relation":
                continue
            subject = document.get("subject_ref")
            object_ = document.get("object_ref")
            predicate = document.get("predicate")
            if not all(isinstance(value, str) for value in (subject, object_, predicate)):
                continue
            if subject not in nodes or object_ not in nodes:
                continue
            key = (subject, object_, predicate)
            if key in keys:
                continue
            keys.add(key)
            graph.setdefault("edges", []).append(
                {"source": subject, "target": object_, "label": predicate.replace("_", " ")}
            )
        path.write_text(
            json.dumps(graph, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static StarIntel research explorer.")
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
        database = materialize_input(args.input, args.db, args.workspace, config)
        build_site(args.workspace, args.output, args.org_output, args.config, args.assets)
        add_relation_edges(args.output, database)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Built explorer at {args.output} and Org corpus at {args.org_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
