#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.integrity_site import publish_site_seal
from starintel_doc.store import read_transport
from starintel_doc.validation import validate_document
from starintel_site.builder import build_site
from starintel_site.model import slug
from starintel_site.people import build_people_directory


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


def normalize_legacy_fec_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def coalesce_legacy_fec_employment_collisions(
    documents: list[dict[str, Any]], path: Path
) -> list[dict[str, Any]]:
    """Merge only known legacy DNC/FEC employment-ID collisions.

    The legacy generator aggregated by normalized occupation but generated IDs from
    a display title that could fall back to the employer. Blank occupations and an
    occupation equal to the employer could therefore emit records with the same ID.
    Display titles may also differ cosmetically while normalizing to the same ID
    input. Preserve aggregate evidence and raw title variants while keeping all
    unrelated or semantically different duplicate IDs fatal.
    """

    merged: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    exact_fields = ("person_id", "organization_id", "employment_type")

    for document in documents:
        doc_id = str(document.get("_id", ""))
        existing = by_id.get(doc_id)
        if existing is None:
            by_id[doc_id] = document
            merged.append(document)
            continue

        legacy_collision = (
            document.get("dataset") == "dnc"
            and document.get("dtype") == "employment"
            and doc_id.startswith("starintel:employment:fec-reported-")
            and existing.get("dataset") == "dnc"
            and existing.get("dtype") == "employment"
        )
        if not legacy_collision:
            raise ValueError(f"{path}: duplicate _id {doc_id}")

        existing_data = existing.get("data", {})
        incoming_data = document.get("data", {})
        exact_match = all(existing_data.get(field) == incoming_data.get(field) for field in exact_fields)
        title_match = normalize_legacy_fec_text(existing_data.get("title")) == normalize_legacy_fec_text(
            incoming_data.get("title")
        )
        if not exact_match or not title_match:
            raise ValueError(f"{path}: non-equivalent legacy FEC collision for {doc_id}")

        existing_reporting = existing.setdefault("extensions", {}).setdefault("fec_reporting", {})
        incoming_reporting = document.get("extensions", {}).get("fec_reporting", {})
        existing_reporting["row_count"] = int(existing_reporting.get("row_count", 0)) + int(
            incoming_reporting.get("row_count", 0)
        )

        first_dates = [
            value
            for value in (
                existing_reporting.get("first_transaction_date"),
                incoming_reporting.get("first_transaction_date"),
            )
            if isinstance(value, str) and value
        ]
        last_dates = [
            value
            for value in (
                existing_reporting.get("last_transaction_date"),
                incoming_reporting.get("last_transaction_date"),
            )
            if isinstance(value, str) and value
        ]
        if first_dates:
            existing_reporting["first_transaction_date"] = min(first_dates)
        if last_dates:
            existing_reporting["last_transaction_date"] = max(last_dates)
        existing_reporting["legacy_collision_merged_documents"] = int(
            existing_reporting.get("legacy_collision_merged_documents", 1)
        ) + 1

        raw_titles = {
            str(title)
            for title in existing_reporting.get("legacy_collision_raw_titles", [])
            if str(title).strip()
        }
        for title in (existing_data.get("title"), incoming_data.get("title")):
            if title is not None and str(title).strip():
                raw_titles.add(str(title))
        if raw_titles:
            existing_reporting["legacy_collision_raw_titles"] = sorted(raw_titles)

        source_keys = {
            json.dumps(source, ensure_ascii=False, sort_keys=True)
            for source in existing.get("sources", [])
        }
        for source in document.get("sources", []):
            key = json.dumps(source, ensure_ascii=False, sort_keys=True)
            if key not in source_keys:
                existing.setdefault("sources", []).append(source)
                source_keys.add(key)

    return merged


def filter_excluded(workspace: Path, config: dict[str, Any]) -> None:
    raw_ids = config.get("excluded_document_ids", [])
    if not isinstance(raw_ids, list):
        raise ValueError("site-config.json: excluded_document_ids must be a list")
    excluded = {str(value) for value in raw_ids}
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
        documents = coalesce_legacy_fec_employment_collisions(documents, selected)
        kept = [document for document in documents if str(document.get("_id")) not in excluded]
        if kept:
            preferred.write_text(
                "".join(
                    json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
                    for document in kept
                ),
                encoding="utf-8",
            )
        elif preferred.exists():
            preferred.unlink()
        for candidate in path.parent.glob("starintel-documents.jsonl.gz.b64*"):
            candidate.unlink()


def materialize_input_native(
    db_root: Path,
    workspace: Path,
    config_path: Path,
) -> bool:
    materializer = os.environ.get("STARINTEL_SITE_MATERIALIZER")
    if not materializer or os.environ.get("STARINTEL_CORPUS_VALIDATED") != "1":
        return False

    executable = Path(materializer)
    if not executable.is_file():
        raise RuntimeError(f"Nim site materializer not found: {executable}")

    subprocess.run(
        [
            str(executable),
            "--db",
            str(db_root),
            "--workspace",
            str(workspace),
            "--config",
            str(config_path),
        ],
        cwd=ROOT,
        check=True,
    )
    return True


def materialize_input(
    digs_root: Path,
    db_root: Path,
    workspace: Path,
    config: dict[str, Any],
    config_path: Path = Path("site-config.json"),
) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    if digs_root.exists():
        shutil.copytree(digs_root, workspace, dirs_exist_ok=True)
    filter_excluded(workspace, config)

    if materialize_input_native(db_root, workspace, config_path):
        return

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
        materialize_input(args.input, args.db, args.workspace, config, args.config)
        build_site(args.workspace, args.output, args.org_output, args.config, args.assets)
        people = build_people_directory(args.workspace, args.output, args.assets)
        seal = publish_site_seal(
            args.output / "downloads" / "starintel-complete-corpus.jsonl",
            args.output,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        f"Built explorer at {args.output}, Org corpus at {args.org_output}, "
        f"and {people['people']} people profiles ({people['alumni']} alumni-linked); "
        f"evidence seal {seal['merkle_root_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
