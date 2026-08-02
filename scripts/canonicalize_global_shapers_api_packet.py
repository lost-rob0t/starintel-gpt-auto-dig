#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import ValidationError, validate_document

SCHEMA_VERSION = "0.9.0"
DATASET = "global-shapers"
RUN = "global-shapers-current-members-api"
PACKET_DIR = ROOT / "digs" / DATASET / RUN
REPORT_JSON = ROOT / "reports" / "global-shapers-current-api.json"
REPORT_MD = ROOT / "reports" / "global-shapers-current-api.md"
GLOBAL_SHAPERS_ID = "starintel:org:global-shapers-community"
WEF_ID = "starintel:org:world-economic-forum"
ROOT_RELATION_ID = "starintel:relation:global-shapers-community:part-of:world-economic-forum"


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_packet(packet_dir: Path) -> list[dict[str, Any]]:
    parts_manifest = packet_dir / "starintel-documents.jsonl.gz.b64.parts"
    direct = packet_dir / "starintel-documents.jsonl.gz.b64"
    plain = packet_dir / "starintel-documents.jsonl"
    if parts_manifest.is_file():
        names = [line.strip() for line in parts_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        encoded = "".join("".join((packet_dir / name).read_text(encoding="utf-8").split()) for name in names)
        payload = gzip.decompress(base64.b64decode(encoded))
    elif direct.is_file():
        encoded = "".join(direct.read_text(encoding="utf-8").split())
        payload = gzip.decompress(base64.b64decode(encoded))
    elif plain.is_file():
        payload = plain.read_bytes()
    else:
        raise RuntimeError(f"no StarIntel packet found under {packet_dir}")

    documents: list[dict[str, Any]] = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"packet line {number}: expected object")
        documents.append(value)
    return documents


def clean_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item.strip() for item in value if isinstance(item, str) and item.strip()})


def move_source_endpoint(document: dict[str, Any]) -> bool:
    provenance = document.get("provenance")
    if not isinstance(provenance, dict) or "source_endpoint" not in provenance:
        return False
    endpoint = provenance.pop("source_endpoint")
    metadata = provenance.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        provenance["metadata"] = metadata
    metadata["source_endpoint"] = endpoint
    return True


def canonicalize_person(document: dict[str, Any]) -> dict[str, Any]:
    raw = document.get("data")
    if not isinstance(raw, dict):
        raw = {}

    name = str(raw.get("full_name") or raw.get("name") or document.get("title") or "Unknown Global Shaper").strip()
    positions = clean_strings(raw.get("positions"))
    organizations = clean_strings(raw.get("organizations"))
    hubs = clean_strings(raw.get("hub_names"))
    statuses = clean_strings(raw.get("statuses"))
    roles = clean_strings(raw.get("roles"))
    alternate_names = clean_strings(raw.get("alternate_names"))
    linkedin_urls = clean_strings(raw.get("linkedin_urls"))
    photo_urls = clean_strings(raw.get("photo_urls"))
    thumbnail_urls = clean_strings(raw.get("thumbnail_urls"))
    wef_profile_id = str(raw.get("wef_profile_id") or "").strip()

    affiliations = sorted({*organizations, *hubs, "Global Shapers Community"})
    misc_urls = sorted({*linkedin_urls, *photo_urls, *thumbnail_urls})
    status = statuses[0] if len(statuses) == 1 else ("mixed" if statuses else "current")

    data: dict[str, Any] = {
        "name": name,
        "display_name": name,
        "full_name": name,
        "status": status,
        "positions": positions,
        "employers": organizations,
        "professional_affiliations": affiliations,
        "public_roles": roles,
        "former_names": alternate_names,
        "misc": misc_urls,
    }
    if linkedin_urls:
        data["website"] = linkedin_urls[0]
    image_urls = photo_urls or thumbnail_urls
    if image_urls:
        data["image_url"] = image_urls[0]
    if wef_profile_id:
        data["external_ids"] = [
            {
                "scheme": "wef-profile-id",
                "value": wef_profile_id,
                "issuer": "World Economic Forum / Global Shapers Community",
                "canonical": True,
                "confidence": 1.0,
                "url": image_urls[0] if image_urls else "https://www.globalshapers.org/shapers",
            }
        ]

    document["data"] = data
    if alternate_names:
        document["aliases"] = alternate_names

    extensions = document.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}
        document["extensions"] = extensions
    api_extension = extensions.get("global_shapers_api")
    if not isinstance(api_extension, dict):
        api_extension = {}
        extensions["global_shapers_api"] = api_extension
    api_extension.update(
        {
            "identity_kind": raw.get("identity_kind", ""),
            "identity_key": raw.get("identity_key", ""),
            "wef_profile_id": wef_profile_id,
            "alternate_names": alternate_names,
            "hub_names": hubs,
            "statuses": statuses,
            "roles": roles,
            "organizations": organizations,
            "linkedin_urls": linkedin_urls,
            "photo_urls": photo_urls,
            "thumbnail_urls": thumbnail_urls,
        }
    )
    document["tags"] = sorted({*clean_strings(document.get("tags")), *statuses, "global-shapers", "official-api"})
    return document


def source_for_roots(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for document in documents:
        sources = document.get("sources")
        if isinstance(sources, list) and sources:
            return sources
    return []


def base_root_document(
    doc_id: str,
    dtype: str,
    data: dict[str, Any],
    retrieved_at: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": retrieved_at,
        "date_updated": retrieved_at,
        "sources": sources,
        "evidence": [],
        "data": data,
        "provenance": {
            "collector": "scripts/canonicalize_global_shapers_api_packet.py",
            "collector_type": "deterministic-transform",
            "method": "canonicalize public API packet to StarIntel v0.9.0",
            "run_id": RUN,
        },
        "handling": {"visibility": "public", "pii": False, "sensitive": False},
        "quality": {
            "validation_status": "schema_validated_by_canonicalizer",
            "validator": "starintel_doc.validation.validate_document",
            "warnings": [],
        },
    }


def root_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retrieved_at = next(
        (
            str(document.get("date_updated"))
            for document in documents
            if isinstance(document.get("date_updated"), str) and document.get("date_updated")
        ),
        "1970-01-01T00:00:00Z",
    )
    sources = source_for_roots(documents)

    wef = base_root_document(
        WEF_ID,
        "org",
        {
            "name": "World Economic Forum",
            "display_name": "World Economic Forum",
            "org_type": "international organization",
            "website": "https://www.weforum.org",
        },
        retrieved_at,
        sources,
    )
    wef.update(
        {
            "title": "World Economic Forum",
            "summary": "Parent organization of the Global Shapers Community.",
            "tags": ["world-economic-forum", "global-shapers", "official-api"],
            "related_ids": [GLOBAL_SHAPERS_ID],
        }
    )

    community = base_root_document(
        GLOBAL_SHAPERS_ID,
        "org",
        {
            "name": "Global Shapers Community",
            "display_name": "Global Shapers Community",
            "org_type": "World Economic Forum initiative",
            "website": "https://www.globalshapers.org",
            "parent_id": WEF_ID,
        },
        retrieved_at,
        sources,
    )
    community.update(
        {
            "title": "Global Shapers Community",
            "summary": "Global Shapers Community, an initiative of the World Economic Forum.",
            "tags": ["global-shapers", "world-economic-forum", "official-api"],
            "related_ids": [WEF_ID],
        }
    )

    relation = base_root_document(
        ROOT_RELATION_ID,
        "relation",
        {
            "subject": GLOBAL_SHAPERS_ID,
            "predicate": "part_of",
            "object": WEF_ID,
            "source": GLOBAL_SHAPERS_ID,
            "target": WEF_ID,
            "directed": True,
            "note": "The Global Shapers Community is a World Economic Forum initiative.",
        },
        retrieved_at,
        sources,
    )
    relation.update(
        {
            "tags": ["global-shapers", "world-economic-forum", "part_of", "official-api"],
            "related_ids": [GLOBAL_SHAPERS_ID, WEF_ID],
        }
    )
    return [wef, community, relation]


def canonicalize_documents(documents: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    transformed_people = 0
    moved_source_endpoints = 0
    by_id: dict[str, dict[str, Any]] = {}

    for document in documents:
        if move_source_endpoint(document):
            moved_source_endpoints += 1
        if document.get("dtype") == "person":
            canonicalize_person(document)
            transformed_people += 1
        doc_id = str(document.get("_id") or "")
        if not doc_id:
            raise RuntimeError("generated document is missing _id")
        if doc_id in by_id:
            raise RuntimeError(f"duplicate generated document ID: {doc_id}")
        by_id[doc_id] = document

    added_roots: list[str] = []
    for document in root_documents(documents):
        doc_id = document["_id"]
        if doc_id not in by_id:
            by_id[doc_id] = document
            added_roots.append(doc_id)

    canonical = [by_id[key] for key in sorted(by_id)]
    errors: list[str] = []
    for document in canonical:
        try:
            validate_document(document)
        except ValidationError as exc:
            errors.append(f"{document.get('_id')}: {exc}")
            if len(errors) >= 25:
                break
    if errors:
        raise RuntimeError("canonical packet validation failed:\n" + "\n".join(errors))

    return canonical, {
        "input_documents": len(documents),
        "output_documents": len(canonical),
        "transformed_people": transformed_people,
        "moved_source_endpoints": moved_source_endpoints,
        "added_root_documents": added_roots,
        "schema_validated_documents": len(canonical),
    }


def write_packet(documents: Iterable[dict[str, Any]], packet_dir: Path, chunk_size: int) -> dict[str, Any]:
    values = list(documents)
    payload = "".join(compact(document) + "\n" for document in values).encode()
    counts = Counter(str(document.get("dtype") or "") for document in values)
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")

    packet_dir.mkdir(parents=True, exist_ok=True)
    for old in packet_dir.glob("starintel-documents.jsonl*"):
        old.unlink()
    parts: list[str] = []
    for offset in range(0, len(encoded), chunk_size):
        name = f"starintel-documents.jsonl.gz.b64.part-{offset // chunk_size:03d}"
        (packet_dir / name).write_text(encoded[offset : offset + chunk_size] + "\n", encoding="utf-8")
        parts.append(name)
    (packet_dir / "starintel-documents.jsonl.gz.b64.parts").write_text(
        "\n".join(parts) + "\n", encoding="utf-8"
    )
    return {
        "documents": len(values),
        "counts_by_dtype": dict(sorted(counts.items())),
        "jsonl_sha256": hashlib.sha256(payload).hexdigest(),
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "base64_parts": parts,
        "schema_validated_documents": len(values),
    }


def update_report(report_path: Path, packet: dict[str, Any], canonicalization: dict[str, Any]) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise RuntimeError(f"{report_path}: expected report object")
    report["packet"] = packet
    report["canonicalization"] = canonicalization
    report["status"] = "complete" if int(report.get("people") or 0) >= int(report.get("minimum_people") or 0) else "incomplete"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if REPORT_MD.is_file():
        text = REPORT_MD.read_text(encoding="utf-8")
        marker = "## Canonicalization"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + "\n\n"
        text += (
            f"{marker}\n\n"
            f"- Schema-validated documents: **{packet['schema_validated_documents']:,}**\n"
            f"- Person documents transformed: **{canonicalization['transformed_people']:,}**\n"
            f"- Invalid provenance fields moved into metadata: **{canonicalization['moved_source_endpoints']:,}**\n"
            f"- Root organization/relation documents added: **{len(canonicalization['added_root_documents']):,}**\n"
        )
        REPORT_MD.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonicalize and validate the generated Global Shapers API packet against StarIntel v0.9.0."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_JSON)
    parser.add_argument("--chunk-size", type=int, default=850_000)
    args = parser.parse_args()
    if args.root.resolve() != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    documents = read_packet(args.packet_dir)
    canonical, canonicalization = canonicalize_documents(documents)
    packet = write_packet(canonical, args.packet_dir, args.chunk_size)
    update_report(args.report, packet, canonicalization)
    print(
        json.dumps(
            {
                "status": "complete",
                "documents": packet["documents"],
                "counts_by_dtype": packet["counts_by_dtype"],
                "jsonl_sha256": packet["jsonl_sha256"],
                "gzip_sha256": packet["gzip_sha256"],
                "canonicalization": canonicalization,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
