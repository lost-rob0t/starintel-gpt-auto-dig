#!/usr/bin/env python3
"""Resolve canonical Auto-Dig documents and stream them as JSONL.

The merge path is intentionally diff-first: only logical documents introduced or
version-bumped since the supplied base are emitted. Existing identical logical
IDs are skipped so merge ingest is idempotent and does not resend duplicates.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_IMPORTER = ROOT / "scripts" / "import-starintel-documents.py"
GREP_BATCH_SIZE = 100


def load_importer():
    spec = importlib.util.spec_from_file_location("starintel_import_documents", LEGACY_IMPORTER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LEGACY_IMPORTER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve canonical Auto-Dig documents and emit JSONL for the Nim ingest core."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--diff",
        metavar="BASE",
        help="Emit only new logical IDs and valid version bumps since BASE.",
    )
    mode.add_argument("--all", action="store_true", help="Emit the full canonical corpus.")
    return parser.parse_args(argv)


def ere_escape(value: str) -> str:
    return re.sub(r"([.\^$*+?{}\[\]\\|()])", r"\\\1", value)


def records_at_ref_for_ids(importer, root: Path, ref: str, document_ids: set[str]):
    """Read only documents with candidate `_id`s from a historical tree.

    `git grep` searches exact `_id` fields, so references to the same ID in relation
    bodies do not make an existing logical document look present.
    """
    if not document_ids:
        return []

    wanted = set(document_ids)
    ordered = sorted(wanted)
    records = []

    for start in range(0, len(ordered), GREP_BATCH_SIZE):
        batch = ordered[start : start + GREP_BATCH_SIZE]
        alternatives = "|".join(ere_escape(document_id) for document_id in batch)
        pattern = rf'"_id"[[:space:]]*:[[:space:]]*"({alternatives})"'
        result = subprocess.run(
            ["git", "grep", "-n", "-E", pattern, ref, "--", "db", "digs"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode not in {0, 1}:
            raise RuntimeError(
                f"git grep failed for {ref}: {result.stderr.strip() or result.returncode}"
            )

        for raw_line in result.stdout.splitlines():
            try:
                _tree, path, line_number, text = raw_line.split(":", 3)
            except ValueError as exc:
                raise ValueError(f"unexpected git grep line: {raw_line!r}") from exc
            parsed = importer.parse_jsonl(text, f"{path}@{ref}:{line_number}")
            for record in parsed:
                if record.document_id in wanted:
                    records.append(record)

    return records


def resolve_diff_records(importer, root: Path, base: str):
    importer.run_git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    _base_paths, current_paths = importer.changed_document_paths(root, base)

    current_records = []
    for relative in sorted(current_paths):
        path = root / relative
        if path.is_file():
            current_records.extend(
                importer.parse_jsonl(path.read_text(encoding="utf-8"), relative)
            )

    current_by_id = importer.merge_records(current_records)
    if not current_by_id:
        return []

    base_records = records_at_ref_for_ids(importer, root, base, set(current_by_id))
    base_by_id = importer.merge_records(base_records, prefer_db=True)

    selected = []
    for document_id, current in current_by_id.items():
        previous = base_by_id.get(document_id)
        if previous is None:
            selected.append(current)
            continue

        if importer.canonical_document(previous.document) == importer.canonical_document(
            current.document
        ):
            continue

        old_version = importer.integer_version(previous.document)
        new_version = importer.integer_version(current.document)
        if old_version is None or new_version is None:
            raise ValueError(
                f"changed existing _id {document_id!r} without comparable integer versions: "
                f"{previous.source} vs {current.source}"
            )
        if new_version == old_version:
            raise ValueError(
                f"changed existing _id {document_id!r} without a version bump: "
                f"version {new_version}; {previous.source} vs {current.source}"
            )
        if new_version < old_version:
            raise ValueError(
                f"version regression for _id {document_id!r}: "
                f"{old_version} -> {new_version}; {previous.source} vs {current.source}"
            )

        selected.append(current)

    return selected


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    importer = load_importer()
    root = importer.repo_root(ROOT)

    if args.diff:
        records = resolve_diff_records(importer, root, args.diff)
        mode = f"diff:{args.diff}"
    else:
        records = importer.collect_all_documents(root)
        mode = "all"

    records.sort(key=lambda record: record.document_id)
    print(
        json.dumps({"mode": mode, "documents": len(records)}, sort_keys=True),
        file=sys.stderr,
    )
    for record in records:
        print(json.dumps(record.document, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
