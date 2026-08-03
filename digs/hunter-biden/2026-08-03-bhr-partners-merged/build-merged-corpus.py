#!/usr/bin/env python3
"""Materialize BHR depths 1-11 as one validated, revision-aware JSONL corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MergeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    document_id: str
    dtype: str
    line: bytes
    source_path: str
    line_number: int
    version: int
    date_updated: str

    @property
    def location(self) -> str:
        return f"{self.source_path}:{self.line_number}"


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
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def parse_jsonl(
    path: Path,
    *,
    repo_root: Path,
    dataset: str,
    schema_version: str,
) -> tuple[list[Candidate], Counter[str]]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise MergeError(f"missing declared JSONL file: {path}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MergeError(f"non-UTF-8 JSONL file: {path}") from exc

    relative_path = str(path.relative_to(repo_root))
    records: list[Candidate] = []
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
        version = document.get("version")
        date_updated = document.get("date_updated")
        if not isinstance(document_id, str) or not document_id:
            raise MergeError(f"missing _id in {path}:{line_number}")
        if not isinstance(dtype, str) or not dtype:
            raise MergeError(f"missing dtype for {document_id} in {path}:{line_number}")
        if not isinstance(version, int) or version < 1:
            raise MergeError(f"invalid version for {document_id} in {path}:{line_number}")
        if not isinstance(date_updated, str) or not date_updated:
            raise MergeError(f"missing date_updated for {document_id} in {path}:{line_number}")
        if document.get("dataset") != dataset:
            raise MergeError(f"dataset mismatch for {document_id}")
        if document.get("schema_version") != schema_version:
            raise MergeError(f"schema mismatch for {document_id}")

        records.append(
            Candidate(
                document_id=document_id,
                dtype=dtype,
                line=line.encode("utf-8"),
                source_path=relative_path,
                line_number=line_number,
                version=version,
                date_updated=date_updated,
            )
        )
        counts[dtype] += 1
    return records, counts


def normalize_counts(value: Any, *, label: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise MergeError(f"{label} is missing or not an object")
    try:
        return {str(key): int(count) for key, count in value.items()}
    except (TypeError, ValueError) as exc:
        raise MergeError(f"{label} contains an invalid count") from exc


def resolve_candidates(
    candidates: list[Candidate],
    duplicate_resolutions: Any,
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    if duplicate_resolutions is None:
        duplicate_resolutions = {}
    if not isinstance(duplicate_resolutions, dict):
        raise MergeError("duplicate_resolutions must be an object")

    grouped: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.document_id].append(candidate)

    chosen: dict[str, Candidate] = {}
    resolution_report: list[dict[str, Any]] = []
    unresolved: list[str] = []

    for document_id, group in grouped.items():
        if len(group) == 1:
            chosen[document_id] = group[0]
            continue

        dtypes = {candidate.dtype for candidate in group}
        if len(dtypes) != 1:
            unresolved.append(
                f"{document_id}: conflicting dtypes {sorted(dtypes)} at "
                + ", ".join(candidate.location for candidate in group)
            )
            continue

        unique_lines = {candidate.line for candidate in group}
        if len(unique_lines) == 1:
            chosen[document_id] = group[0]
            resolution_report.append(
                {
                    "_id": document_id,
                    "method": "identical-byte-coalesce",
                    "preferred_source": group[0].source_path,
                    "superseded_sources": [candidate.source_path for candidate in group[1:]],
                    "reason": "The repeated records are byte-identical.",
                }
            )
            continue

        resolution = duplicate_resolutions.get(document_id)
        if not isinstance(resolution, dict):
            unresolved.append(
                f"{document_id}: non-identical duplicate at "
                + ", ".join(candidate.location for candidate in group)
            )
            continue

        preferred_source = resolution.get("preferred_source")
        superseded_sources = resolution.get("superseded_sources")
        reason = resolution.get("reason")
        if not isinstance(preferred_source, str) or not preferred_source:
            unresolved.append(f"{document_id}: resolution missing preferred_source")
            continue
        if not isinstance(superseded_sources, list) or not all(
            isinstance(item, str) and item for item in superseded_sources
        ):
            unresolved.append(f"{document_id}: resolution has invalid superseded_sources")
            continue
        if not isinstance(reason, str) or not reason:
            unresolved.append(f"{document_id}: resolution missing reason")
            continue

        preferred = [candidate for candidate in group if candidate.source_path == preferred_source]
        if len(preferred) != 1:
            unresolved.append(
                f"{document_id}: preferred_source {preferred_source!r} matched {len(preferred)} records"
            )
            continue
        actual_superseded = sorted(
            candidate.source_path for candidate in group if candidate is not preferred[0]
        )
        if sorted(superseded_sources) != actual_superseded:
            unresolved.append(
                f"{document_id}: superseded source mismatch; "
                f"actual={actual_superseded} declared={sorted(superseded_sources)}"
            )
            continue

        chosen[document_id] = preferred[0]
        resolution_report.append(
            {
                "_id": document_id,
                "method": "explicit-documented-correction",
                "preferred_source": preferred[0].source_path,
                "preferred_version": preferred[0].version,
                "preferred_date_updated": preferred[0].date_updated,
                "superseded_sources": actual_superseded,
                "superseded_versions": [
                    candidate.version for candidate in group if candidate is not preferred[0]
                ],
                "superseded_dates_updated": [
                    candidate.date_updated for candidate in group if candidate is not preferred[0]
                ],
                "reason": reason,
            }
        )

    undeclared_resolutions = sorted(set(duplicate_resolutions) - set(grouped))
    if undeclared_resolutions:
        unresolved.append(
            "duplicate resolutions reference IDs not present in the corpus: "
            + ", ".join(undeclared_resolutions)
        )

    if unresolved:
        raise MergeError("unresolved duplicate records:\n- " + "\n- ".join(sorted(unresolved)))

    resolved_records = [candidate for candidate in candidates if chosen[candidate.document_id] is candidate]
    return resolved_records, sorted(resolution_report, key=lambda item: item["_id"])


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

    all_candidates: list[Candidate] = []
    raw_counts: Counter[str] = Counter()
    packet_results: list[dict[str, Any]] = []

    for packet in packets:
        if not isinstance(packet, dict):
            raise MergeError("packet index entry is not an object")
        packet_path_value = packet.get("path")
        expected_total = packet.get("expected_total")
        if not isinstance(packet_path_value, str) or not packet_path_value:
            raise MergeError("packet index entry is missing path")
        if not isinstance(expected_total, int):
            raise MergeError(f"packet {packet_path_value} is missing expected_total")

        packet_path = repo_root / packet_path_value
        manifest_path = packet_path / "manifest.json"
        manifest = load_json(manifest_path)
        if manifest.get("dataset") != dataset:
            raise MergeError(f"dataset mismatch in {manifest_path}")
        if manifest.get("schema_version") != schema_version:
            raise MergeError(f"schema mismatch in {manifest_path}")
        if manifest.get("total") != expected_total:
            raise MergeError(f"total mismatch in {manifest_path}")

        declared_files = manifest.get("document_files")
        if not isinstance(declared_files, list) or not declared_files:
            raise MergeError(f"manifest has no document_files: {manifest_path}")

        packet_counts: Counter[str] = Counter()
        packet_candidates: list[Candidate] = []
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
            try:
                source_bytes = source_path.read_bytes()
            except FileNotFoundError as exc:
                raise MergeError(f"missing declared JSONL file: {source_path}") from exc
            actual_sha256 = sha256_bytes(source_bytes)
            if declared_sha256 is not None and actual_sha256 != declared_sha256:
                raise MergeError(f"SHA-256 mismatch for {source_path}")

            records, counts = parse_jsonl(
                source_path,
                repo_root=repo_root,
                dataset=dataset,
                schema_version=schema_version,
            )
            if len(records) != expected_count:
                raise MergeError(f"record-count mismatch for {source_path}")
            packet_candidates.extend(records)
            packet_counts.update(counts)
            file_results.append(
                {
                    "path": str(source_path.relative_to(repo_root)),
                    "count": len(records),
                    "sha256": actual_sha256,
                    "declared_sha256": declared_sha256,
                }
            )

        manifest_counts = normalize_counts(manifest.get("counts"), label=f"counts in {manifest_path}")
        if dict(packet_counts) != manifest_counts:
            raise MergeError(
                f"dtype counts mismatch in {manifest_path}: parsed={dict(packet_counts)} "
                f"declared={manifest_counts}"
            )
        if len(packet_candidates) != expected_total:
            raise MergeError(f"packet total mismatch for {packet_path}")

        all_candidates.extend(packet_candidates)
        raw_counts.update(packet_counts)
        packet_results.append(
            {
                "depth": packet.get("depth"),
                "path": packet_path_value,
                "record_count": len(packet_candidates),
                "counts": dict(sorted(packet_counts.items())),
                "declared_combined_documents_sha256": packet.get("combined_documents_sha256"),
                "files": file_results,
            }
        )

    expected_raw_counts = normalize_counts(
        index.get("expected_raw_counts"), label="expected_raw_counts"
    )
    expected_raw_total = index.get("expected_raw_total")
    if not isinstance(expected_raw_total, int):
        raise MergeError("expected_raw_total is missing or invalid")
    if dict(raw_counts) != expected_raw_counts:
        raise MergeError(
            f"raw aggregate dtype counts mismatch: parsed={dict(raw_counts)} "
            f"expected={expected_raw_counts}"
        )
    if len(all_candidates) != expected_raw_total:
        raise MergeError(
            f"raw aggregate total mismatch: {len(all_candidates)} != {expected_raw_total}"
        )

    resolved_records, resolution_report = resolve_candidates(
        all_candidates, index.get("duplicate_resolutions")
    )
    unique_counts = Counter(candidate.dtype for candidate in resolved_records)
    expected_unique_counts = normalize_counts(
        index.get("expected_unique_counts"), label="expected_unique_counts"
    )
    expected_unique_total = index.get("expected_unique_total")
    if not isinstance(expected_unique_total, int):
        raise MergeError("expected_unique_total is missing or invalid")
    if dict(unique_counts) != expected_unique_counts:
        raise MergeError(
            f"unique aggregate dtype counts mismatch: parsed={dict(unique_counts)} "
            f"expected={expected_unique_counts}"
        )
    if len(resolved_records) != expected_unique_total:
        raise MergeError(
            f"unique aggregate total mismatch: {len(resolved_records)} != {expected_unique_total}"
        )

    merged_bytes = b"\n".join(candidate.line for candidate in resolved_records) + b"\n"
    manifest = {
        "dataset": dataset,
        "schema_version": schema_version,
        "merge_mode": index.get("merge_mode"),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "packet_count": len(packet_results),
        "raw_record_count": len(all_candidates),
        "record_count": len(resolved_records),
        "raw_counts": dict(sorted(raw_counts.items())),
        "counts": dict(sorted(unique_counts.items())),
        "sha256": sha256_bytes(merged_bytes),
        "resolved_duplicate_ids": len(resolution_report),
        "duplicate_resolutions": resolution_report,
        "ordering": "packet depth, manifest document_files order, original line order; superseded revisions omitted",
        "source_packets": packet_results,
    }
    return merged_bytes, manifest


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=script_dir.parents[2])
    parser.add_argument("--index", type=Path, default=script_dir / "packet-index.json")
    parser.add_argument("--output", type=Path, default=script_dir / "starintel-documents.jsonl")
    parser.add_argument("--manifest-output", type=Path, default=script_dir / "merged-manifest.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        merged_bytes, manifest = build(args.repo_root.resolve(), args.index.resolve())
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
                f"merged {manifest['record_count']} unique records from "
                f"{manifest['raw_record_count']} packet records"
            )
            print(f"sha256: {manifest['sha256']}")
    except (MergeError, OSError, ValueError) as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
