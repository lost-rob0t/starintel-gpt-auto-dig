#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "digs" / "global-shapers" / "global-shapers-current-members-api"
REPORT = ROOT / "reports" / "global-shapers-current-api-id-collisions.json"


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_packet(packet_dir: Path) -> list[dict[str, Any]]:
    manifest = packet_dir / "starintel-documents.jsonl.gz.b64.parts"
    if not manifest.is_file():
        raise RuntimeError(f"missing packet manifest: {manifest}")
    names = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    encoded = "".join("".join((packet_dir / name).read_text(encoding="utf-8").split()) for name in names)
    payload = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    documents: list[dict[str, Any]] = []
    for number, line in enumerate(payload.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"packet line {number}: expected object")
        documents.append(value)
    return documents


def unique_strings(*values: Any) -> list[str]:
    result: set[str] = set()
    for value in values:
        if isinstance(value, str) and value.strip():
            result.add(value.strip())
        elif isinstance(value, list):
            result.update(item.strip() for item in value if isinstance(item, str) and item.strip())
    return sorted(result)


def unique_objects(*values: Any) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict):
                result.setdefault(compact(item), item)
    return [result[key] for key in sorted(result)]


def merge_org(documents: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(documents[0])
    data = dict(merged.get("data") or {})
    labels: list[str] = []
    for document in documents:
        current = document.get("data")
        if isinstance(current, dict):
            labels.extend(
                value.strip()
                for key in ("name", "display_name", "short_name", "legal_name")
                if isinstance((value := current.get(key)), str) and value.strip()
            )
        labels.extend(unique_strings(document.get("aliases")))
    canonical_name = str(data.get("name") or data.get("display_name") or documents[0].get("title") or "Global Shapers Hub")
    aliases = sorted(set(labels) - {canonical_name})
    data["name"] = canonical_name
    data["display_name"] = str(data.get("display_name") or canonical_name)
    if aliases:
        data["former_names"] = unique_strings(data.get("former_names"), aliases)
        merged["aliases"] = unique_strings(merged.get("aliases"), aliases)
    merged["data"] = data
    merged["tags"] = unique_strings(*(document.get("tags") for document in documents))
    merged["related_ids"] = unique_strings(*(document.get("related_ids") for document in documents))
    merged["sources"] = unique_objects(*(document.get("sources") for document in documents))
    merged["evidence"] = unique_objects(*(document.get("evidence") for document in documents))
    return merged


def merge_relation(documents: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(documents[0])
    base_data = dict(merged.get("data") or {})
    for document in documents[1:]:
        data = document.get("data")
        if not isinstance(data, dict):
            continue
        for key in ("subject", "predicate", "object", "source", "target"):
            if data.get(key) != base_data.get(key):
                raise RuntimeError(
                    f"relation ID collision changes {key}: {merged.get('_id')} "
                    f"{base_data.get(key)!r} != {data.get(key)!r}"
                )
    notes = unique_strings(*(document.get("data", {}).get("note") for document in documents if isinstance(document.get("data"), dict)))
    if notes:
        base_data["note"] = " | ".join(notes)
    merged["data"] = base_data
    merged["tags"] = unique_strings(*(document.get("tags") for document in documents))
    merged["related_ids"] = unique_strings(*(document.get("related_ids") for document in documents))
    merged["sources"] = unique_objects(*(document.get("sources") for document in documents))
    merged["evidence"] = unique_objects(*(document.get("evidence") for document in documents))
    return merged


def reconcile(documents: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        doc_id = str(document.get("_id") or "")
        if not doc_id:
            raise RuntimeError("generated document has no _id")
        grouped[doc_id].append(document)

    output: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    for doc_id, values in sorted(grouped.items()):
        if len(values) == 1:
            output.append(values[0])
            continue
        dtypes = sorted({str(value.get("dtype") or "") for value in values})
        if len(dtypes) != 1:
            raise RuntimeError(f"ID collision spans document types: {doc_id}: {dtypes}")
        dtype = dtypes[0]
        if dtype == "org":
            merged = merge_org(values)
        elif dtype == "relation":
            merged = merge_relation(values)
        else:
            raise RuntimeError(f"unsafe {dtype} ID collision: {doc_id} ({len(values)} documents)")
        output.append(merged)
        collisions.append(
            {
                "_id": doc_id,
                "dtype": dtype,
                "input_documents": len(values),
                "titles": unique_strings(*(value.get("title") for value in values)),
                "names": unique_strings(
                    *(value.get("data", {}).get("name") for value in values if isinstance(value.get("data"), dict))
                ),
            }
        )

    return output, {
        "input_documents": len(documents),
        "output_documents": len(output),
        "duplicate_documents_removed": len(documents) - len(output),
        "collision_groups": len(collisions),
        "counts_by_dtype_before": dict(sorted(Counter(str(value.get("dtype") or "") for value in documents).items())),
        "counts_by_dtype_after": dict(sorted(Counter(str(value.get("dtype") or "") for value in output).items())),
        "collisions": collisions,
    }


def write_packet(documents: Iterable[dict[str, Any]], packet_dir: Path, chunk_size: int) -> dict[str, Any]:
    values = list(documents)
    payload = "".join(compact(document) + "\n" for document in values).encode()
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    for old in packet_dir.glob("starintel-documents.jsonl*"):
        old.unlink()
    names: list[str] = []
    for offset in range(0, len(encoded), chunk_size):
        name = f"starintel-documents.jsonl.gz.b64.part-{offset // chunk_size:03d}"
        (packet_dir / name).write_text(encoded[offset : offset + chunk_size] + "\n", encoding="utf-8")
        names.append(name)
    (packet_dir / "starintel-documents.jsonl.gz.b64.parts").write_text("\n".join(names) + "\n", encoding="utf-8")
    return {
        "documents": len(values),
        "jsonl_sha256": hashlib.sha256(payload).hexdigest(),
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "base64_parts": names,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile deterministic org/relation ID collisions in the Global Shapers API packet.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--chunk-size", type=int, default=850_000)
    args = parser.parse_args()
    if args.root.resolve() != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    documents = read_packet(args.packet_dir)
    reconciled, report = reconcile(documents)
    report["packet"] = write_packet(reconciled, args.packet_dir, args.chunk_size)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
