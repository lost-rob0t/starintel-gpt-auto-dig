#!/usr/bin/env python3
"""Reproduce this bounded packet through the pinned canonical draft CLI.

This is an explicit adaptation of archived input, not a general schema migrator.
It performs no research, normalized DB writes, or publication.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = ROOT / "reports/archives/2026-10-10-columbus-election-institutions/original-unpublished-packet.jsonl.txt"
PACKET = HERE / "starintel-documents.jsonl"
RECEIPT = HERE / "adaptation-receipt.json"
ARCHIVE_SHA256 = "6811aa5d3f0f171f9a7d8493571a7363cccad21e0761eb7115c74249823b9b48"
PYTHON_COMMIT = "ac015a5d92a1d9587e5dc7764dd9e0a150a6d0a8"
STARLANG_COMMIT = "765f1673851192bcaf1cdd2f35c47608f979b079"
DTYPE_MAP = {"source": "url", "org": "org", "relation": "relation", "research-pass": "finding"}
SOURCE_ONLY = {"accessMethod", "kind", "retrievedAt", "title"}
REVIEW_ONLY = {
    "agentIdentity", "counterevidenceIds", "findings", "iteration", "method",
    "researchQuestion", "supportingRecordIds", "terminationReason", "unresolvedTargetIds",
}


def cli(*args: str) -> str:
    return subprocess.check_output(
        [sys.executable, str(ROOT / "scripts/starintel.py"), *args],
        cwd=ROOT, text=True,
    )


def original_records() -> list[dict]:
    raw = ARCHIVE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("archived input bytes changed; this bounded adaptation must be reviewed")
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if Counter(row["dtype"] for row in records) != {"source": 5, "org": 6, "relation": 1, "research-pass": 1}:
        raise ValueError("unexpected original packet composition")
    if len({row["id"] for row in records}) != len(records):
        raise ValueError("duplicate original IDs")
    return records


def assert_authority() -> None:
    control = json.loads((ROOT / "config/auto-dig-control.json").read_text())
    if control.get("enabled") is not True or control.get("state") != "running":
        raise ValueError("Auto-Dig control is not running; generation is paused")
    runtime = json.loads((ROOT / "schema/starintel-runtime.lock.json").read_text())
    release = json.loads((ROOT / "schema/starintel-schema.lock.json").read_text())
    if runtime["python_commit"] != PYTHON_COMMIT or release["canonical_commit"] != STARLANG_COMMIT:
        raise ValueError("pinned authority changed; review the bounded adaptation first")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/schema-release.py"), "check"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    types = set(cli("types").splitlines())
    if len(types) != 60 or not set(DTYPE_MAP.values()) <= types or {"source", "research-pass"} & types:
        raise ValueError("unexpected published dtype inventory")


def unix_seconds(value: str) -> int:
    # The published schema has integer UnixTime. Full fractional precision stays
    # in the byte-exact archive and is explicitly accounted for in the receipt.
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def prepare_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    by_id = {row["id"]: row for row in records}
    urls = {row["url"]: row for row in records if row["dtype"] == "source"}
    result, mappings = [], []
    for line, original in enumerate(records, 1):
        old_dtype = original["dtype"]
        new_dtype = DTYPE_MAP[old_dtype]
        fields = {key: value for key, value in original.items() if key not in {"id", "dataset", "dtype", "schemaVersion"}}
        omitted = SOURCE_ONLY if old_dtype == "source" else REVIEW_ONLY if old_dtype == "research-pass" else set()
        fields = {key: value for key, value in fields.items() if key not in omitted}
        mapped_fields = {}
        if old_dtype == "source":
            fields["contentTitle"] = original["title"]
            fields["fetchedAt"] = unix_seconds(original["retrievedAt"])
            fields["sourceRetrievedAt"] = fields["fetchedAt"]
            # A URL observation does not cite itself as independent evidence.
            fields["sources"] = []
            mapped_fields = {
                "title": ["contentTitle"],
                "retrievedAt": ["fetchedAt", "sourceRetrievedAt"],
            }
        else:
            fields["sources"] = [
                {"schema": "url", "id": urls[url]["id"]}
                for url in original["sourceUrls"]
            ]
        if old_dtype == "research-pass":
            if len(original["findings"]) != 1 or set(original["findings"][0]) != {"description"}:
                raise ValueError("unexpected review findings; do not silently collapse them")
            fields["title"] = original["researchQuestion"]
            fields["description"] = original["findings"][0]["description"]
            fields["evidence"] = [
                {"schema": DTYPE_MAP[by_id[doc_id]["dtype"]], "id": doc_id}
                for doc_id in original["supportingRecordIds"]
            ]
            mapped_fields = {
                "researchQuestion": ["title"],
                "findings[0].description": ["description"],
                "supportingRecordIds": ["evidence"],
            }
        fields.update({
            "createdAt": original["collectedAt"],
            "updatedAt": original["collectedAt"],
            "sourceKinds": ["web"],
            "visibility": "public",
            "sensitivity": "public",
        })
        # All wire records come from the authoritative create --fields path.
        document = json.loads(cli(
            "create", new_dtype, "--dataset", original["dataset"],
            "--id", original["id"], "--fields", json.dumps(fields),
        ))
        result.append(document)
        preserved = sorted(key for key, value in original.items() if key in document and document[key] == value)
        archive_only = sorted(omitted - {"title", "retrievedAt", "researchQuestion", "findings", "supportingRecordIds"})
        mappings.append({
            "originalLine": line,
            "id": original["id"],
            "originalDtype": old_dtype,
            "canonicalDtype": new_dtype,
            "preservedFields": preserved,
            "mappedFields": mapped_fields,
            "archiveOnlyFields": archive_only,
            "addedFields": sorted(set(document) - set(original)),
            "precisionLossInCanonicalOnly": (
                {"retrievedAt": "Fractional seconds are retained only in the exact archive; canonical timestamps are integer seconds."}
                if old_dtype == "source" else {}
            ),
        })
    validate_references(result)
    return result, mappings


def validate_references(records: list[dict]) -> None:
    by_id = {row["id"]: row for row in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate adapted IDs")
    for row in records:
        references = row.get("sources", []) + row.get("evidence", [])
        if row["dtype"] == "relation":
            references += [row["source"], row["destination"]]
        for ref in references:
            if ref["id"] not in by_id or by_id[ref["id"]]["dtype"] != ref["schema"]:
                raise ValueError(f"unresolved or mismatched reference in {row['id']}: {ref}")


def generate() -> tuple[bytes, bytes]:
    assert_authority()
    original = original_records()
    records, mappings = prepare_records(original)
    packet = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in records).encode()
    receipt = {
        "format": "columbus-election-packet-adaptation.v1",
        "scope": "Schema adaptation of the existing 13-record institutional packet only; no new collection.",
        "originalArtifact": str(ARCHIVE.relative_to(ROOT)),
        "originalSha256": ARCHIVE_SHA256,
        "canonicalArtifact": str(PACKET.relative_to(ROOT)),
        "canonicalSha256": hashlib.sha256(packet).hexdigest(),
        "pythonRuntimeCommit": PYTHON_COMMIT,
        "starLangCommit": STARLANG_COMMIT,
        "schemaVersion": "0.10.1",
        "recordCount": len(records),
        "dtypeCounts": dict(sorted(Counter(row["dtype"] for row in records).items())),
        "identityPolicy": "All 13 original IDs are retained, including source/research-pass prefixes after dtype adaptation. Identity is the preserved observation, not the dtype prefix. This is a documented correction, not a new observation or an identity merge.",
        "archivePolicy": "Original bytes, unsupported fields, exact retrieval precision, and the complete research-pass receipt remain in the non-canonical archival artifact. No unsupported field is hidden in extensions, raw, metadata, or provenance.",
        "metadataPolicy": {
            "createdAt": "original collectedAt",
            "updatedAt": "original collectedAt; adaptation does not claim a new collection time",
            "sourceKinds": ["web"],
            "visibility": "public",
            "sensitivity": "public",
            "sources": "org/relation/finding reference the url records that match their original sourceUrls exactly; url observations have no self-citations",
        },
        "records": mappings,
    }
    return packet, (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify exact reproducibility without writing")
    args = parser.parse_args()
    packet, receipt = generate()
    for path, payload in ((PACKET, packet), (RECEIPT, receipt)):
        if args.check:
            if not path.exists() or path.read_bytes() != payload:
                raise ValueError(f"generated artifact differs: {path.relative_to(ROOT)}")
        else:
            path.write_bytes(payload)
    print("Verified" if args.check else "Generated", "13 canonical records (6 org, 5 url, 1 relation, 1 finding); original IDs retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
