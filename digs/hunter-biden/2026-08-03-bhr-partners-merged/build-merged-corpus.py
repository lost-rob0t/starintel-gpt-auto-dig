#!/usr/bin/env python3
"""Materialize the validated BHR depth packets as one exact JSONL corpus.

The source packets remain canonical and immutable. This utility verifies their
manifests and concatenates their existing records without rewriting documents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MergeError(RuntimeError):
    """Raised when a source packet violates a merge invariant."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MergeError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MergeError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MergeError(f"expected JSON object in {path}")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def parse_jsonl(
    path: Path,
    *,
    dataset: str,
    schema_version: str,
    seen_ids: dict[str, str],
) -> tuple[list[bytes], Counter[str]]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise MergeError(f"missing declared JSONL file: {path}") from exc

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MergeError(f"non-UTF-8 JSONL file: {path}") from exc

    records: list[bytes] = []
    counts: Counter[str] = Counter()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise MergeError(f"blank line in {path}:{line_number}")
        try:
            document = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MergeError(f"invalid JSON in {path}:{line_number}: {exc}") from exc
        if not isinstance(document, dict):
            raise MergeError(f"non-object record in {path}:{line_number}")

        document_id = document.get("_id")
        dtype = document.get("dtype")
        if not isinstance(document_id, str) or not document_id:
            raise MergeError(f"missing _id in {path}:{line_number}")
        if not isinstance(dtype, str) or not dtype:
            raise MergeError(f"missing dtype for {document_id} in {path}:{line_number}")
        if document.get("dataset") != dataset:
            raise MergeError(
                f"dataset mismatch for {document_id}: {document.get('dataset')!r} != {dataset!r}"
            )
        if document.get("schema_version") != schema_version:
            raise MergeError(
                f"schema mismatch for {document_id}: "
                f"{document.get('schema_version')!r} != {schema_version!r}"
            )
        if document_id in seen_ids:
            raise MergeError(
                f"duplicate _id {document_id!r} in {path}; first seen in {seen_ids[document_id]}"
            )

        seen_ids[document_id] = f"{path}:{line_number}"
        counts[dtype] += 1
        records.append(line.encode("utf-8"))

    return records, counts


def build(repo_root: Path, index_path: Path) -> tuple[bytes, dict[str, Any]]:
    index = load_json(index_path)
    dataset = index.get("dataset")
    schema_version = index.get("schema_version")
    packets = index.get("packets")
    if not isinstance(dataset, str) or not dataset:
        raise MergeError("packet index is missing dataset")
    if not isinstance(schema_version, str) or not schema_version:
        raise MergeError("packet index is missing schema_version")
    if not isinstance(packets, list) or not packets:
        raise MergeError("packet index contains no packets")

    all_records: list[bytes] = []
    global_counts: Counter[str] = Counter()
    seen_ids: dict[str, str] = {}
    packet_results: list[dict[str, Any]] = []

    for packet in packets:
        if not isinstance(packet, dict):
            raise MergeError("packet index entry is not an object")
        packet_path_value = packet.get("path")
        expected_total = packet.get("expected_total")
        if not isinstance(packet_path_value, str) or not packet_path_value:
            raise MergeError("packet index entry is missing path")
        packet_path = repo_root / packet_path_value
        manifest_path = packet_path / "manifest.json"
        manifest = load_json(manifest_path)

        if manifest.get("dataset") != dataset:
            raise MergeError(f"dataset mismatch in {manifest_path}")
        if manifest.get("schema_version") != schema_version:
            raise MergeError(f"schema mismatch in {manifest_path}")
        if manifest.get("total") != expected_total:
            raise MergeError(
                f"total mismatch in {manifest_path}: {manifest.get('total')} != {expected_total}"
            )

        declared_files = manifest.get("document_files")
        if not isinstance(declared_files, list) or not declared_files:
            raise MergeError(f"manifest has no document_files: {manifest_path}")

        packet_counts: Counter[str] = Counter()
        packet_records: list[bytes] = []
        file_results: list[dict[str, Any]] = []

        for file_entry in declared_files:
            if not isinstance(file_entry, dict):
                raise MergeError(f"invalid document_files entry in {manifest_path}")
            relative_path = file_entry.get("path")
            expected_count = file_entry.get("count")
            declared_sha256 = file_entry.get("sha256")
            if not isinstance(relative_path, str) or not relative_path:
                raise MergeError(f"document_files entry missing path in {manifest_path}")
            if not isinstance(expected_count, int) or expected_count < 0:
                raise MergeError(f"invalid count for {relative_path} in {manifest_path}")

            source_path = packet_path / relative_path
            source_bytes = source_path.read_bytes()
            actual_sha256 = sha256_bytes(source_bytes)
            if declared_sha256 is not None and actual_sha256 != declared_sha256:
                raise MergeError(
                    f"SHA-256 mismatch for {source_path}: {actual_sha256} != {declared_sha256}"
                )

            records, counts = parse_jsonl(
                source_path,
                dataset=dataset,
                schema_version=schema_version,
                seen_ids=seen_ids,
            )
            if len(records) != expected_count:
                raise MergeError(
                    f"record-count mismatch for {source_path}: {len(records)} != {expected_count}"
                )

            packet_records.extend(records)
            packet_counts.update(counts)
            file_results.append(
                {
                    "path": str(source_path.relative_to(repo_root)),
                    "count": len(records),
                    "sha256": actual_sha256,
                    "declared_sha256": declared_sha256,
                }
            )

        manifest_counts = manifest.get("counts")
        if not isinstance(manifest_counts, dict):
            raise MergeError(f"manifest counts missing in {manifest_path}")
        normalized_manifest_counts = {key: int(value) for key, value in manifest_counts.items()}
        if dict(packet_counts) != normalized_manifest_counts:
            raise MergeError(
                f"dtype counts mismatch in {manifest_path}: "
                f"parsed={dict(packet_counts)} declared={normalized_manifest_counts}"
            )
        if len(packet_records) != expected_total:
            raise MergeError(
                f"packet total mismatch for {packet_path}: {len(packet_records)} != {expected_total}"
            )

        all_records.extend(packet_records)
        global_counts.update(packet_counts)
        packet_results.append(
            {
                "depth": packet.get("depth"),
                "path": packet_path_value,
                "manifest": str(manifest_path.relative_to(repo_root)),
                "record_count": len(packet_records),
                "counts": dict(sorted(packet_counts.items())),
                "declared_combined_documents_sha256": packet.get(
                    "combined_documents_sha256"
                ),
                "files": file_results,
            }
        )

    expected_counts = index.get("expected_counts")
    expected_total = index.get("expected_total")
    if not isinstance(expected_counts, dict) or not isinstance(expected_total, int):
        raise MergeError("packet index is missing expected aggregate counts")
    normalized_expected_counts = {key: int(value) for key, value in expected_counts.items()}
    if dict(global_counts) != normalized_expected_counts:
        raise MergeError(
            f"aggregate dtype counts mismatch: "
            f"parsed={dict(global_counts)} expected={normalized_expected_counts}"
        )
    if len(all_records) != expected_total:
        raise MergeError(
            f"aggregate total mismatch: {len(all_records)} != {expected_total}"
        )

    merged_bytes = b"\n".join(all_records) + b"\n"
    generated_manifest = {
        "dataset": dataset,
        "schema_version": schema_version,
        "merge_mode": index.get("merge_mode"),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "packet_count": len(packet_results),
        "record_count": len(all_records),
        "counts": dict(sorted(global_counts.items())),
        "sha256": sha256_bytes(merged_bytes),
        "duplicate_ids": 0,
        "ordering": "packet depth, manifest document_files order, original line order",
        "source_packets": packet_results,
    }
    return merged_bytes, generated_manifest


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_repo_root = script_dir.parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_repo_root)
    parser.add_argument("--index", type=Path, default=script_dir / "packet-index.json")
    parser.add_argument(
        "--output", type=Path, default=script_dir / "starintel-documents.jsonl"
    )
    parser.add_argument(
        "--manifest-output", type=Path, default=script_dir / "merged-manifest.json"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and print the manifest without writing"
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    index_path = args.index.resolve()
    try:
        merged_bytes, manifest = build(repo_root, index_path)
        manifest_bytes = (
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
            + b"\n"
        )
        if args.dry_run:
            sys.stdout.buffer.write(manifest_bytes)
        else:
            atomic_write(args.output.resolve(), merged_bytes)
            atomic_write(args.manifest_output.resolve(), manifest_bytes)
            print(
                f"merged {manifest['record_count']} records from "
                f"{manifest['packet_count']} packets into {args.output}"
            )
            print(f"sha256: {manifest['sha256']}")
    except (MergeError, OSError, ValueError) as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
