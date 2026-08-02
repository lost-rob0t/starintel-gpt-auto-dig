#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
GENERATED_AT = "2026-08-01T00:45:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-governance-primary-documents")
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
PARTITIONS = 16
MAX_DOWNLOAD = 75_000_000

DOCUMENTS = (
    {
        "key": "charter-bylaws-2025-10",
        "title": "DNC Charter and Bylaws — October 2025",
        "source_id": "starintel:source:dnc-charter-bylaws-2025-10",
        "uri": "https://democrats.org/wp-content/uploads/2025/10/DNC-Charter-Bylaws-10.2025.pdf",
        "document_type": "official_dnc_charter_and_bylaws_page",
    },
    {
        "key": "2024-call-for-convention",
        "title": "2024 Call for the Democratic National Convention",
        "source_id": "starintel:source:dnc-2024-call-for-convention",
        "uri": "https://democrats.org/wp-content/uploads/2023/03/2024-Call-for-Convention.pdf",
        "document_type": "official_dnc_call_for_convention_page",
    },
    {
        "key": "2024-delegate-selection-rules",
        "title": "2024 Delegate Selection Rules — Final Revised",
        "source_id": "starintel:source:dnc-2024-delegate-selection-rules",
        "uri": "https://democrats.org/wp-content/uploads/2023/05/2024-Delegate-Selection-Rules-Final-Revised-9.8.22.pdf",
        "document_type": "official_dnc_delegate_selection_rules_page",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize page-level DNC governance documents")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-dir", type=Path)
    return parser.parse_args()


def download(uri: str, destination: Path) -> None:
    request = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise RuntimeError(f"PDF exceeds safety cap: {uri}")
            handle.write(chunk)


def acquire(item: dict[str, str], temporary: Path, offline_dir: Path | None) -> Path:
    destination = temporary / f"{item['key']}.pdf"
    if offline_dir:
        source = offline_dir / destination.name
        if not source.exists():
            raise RuntimeError(f"offline PDF is missing: {source}")
        shutil.copy2(source, destination)
    else:
        download(item["uri"], destination)
    if not destination.read_bytes().startswith(b"%PDF"):
        raise RuntimeError(f"download is not a PDF: {item['uri']}")
    return destination


def page_document(item: dict[str, str], page_number: int, page_count: int, text: str, file_sha256: str, when: str) -> dict[str, Any]:
    title = f"{item['title']} — page {page_number} of {page_count}"
    document = {
        "_id": f"starintel:document:dnc-{item['key']}-page-{page_number:04d}",
        "data": {
            "document_type": item["document_type"],
            "length": len(text),
            "text": text,
            "title": title,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "document",
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "identifiers": [
            {
                "canonical": True,
                "issuer": "StarIntel DNC governance materializer",
                "scheme": "pdf_sha256_page",
                "value": f"{file_sha256}:page:{page_number}",
            }
        ],
        "schema_version": "0.9.0",
        "sources": [
            {
                "source_id": item["source_id"],
                "locator": f"PDF page {page_number} of {page_count}",
                "metadata": {
                    "file_sha256": file_sha256,
                    "page_count": page_count,
                    "page_number": page_number,
                    "uri": item["uri"],
                },
            }
        ],
        "status": "recorded",
        "summary": f"Page {page_number} of the official document {item['title']}; extracted text is preserved with the PDF hash and exact page locator.",
        "tags": [
            "dnc",
            "official-governing-document",
            "pdf-page",
            item["key"],
        ],
        "title": title,
        "verification": {
            "last_reviewed_at": when,
            "status": "deterministic-pdf-page-extraction",
            "verified": True,
        },
        "version": 1,
    }
    validate_document(document)
    return document


def partition(document: dict[str, Any]) -> int:
    digest = hashlib.sha256(document["_id"].encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % PARTITIONS


def main() -> int:
    ns = parse_args()
    output = ns.output
    pages_root = output / "pages"
    if pages_root.exists():
        shutil.rmtree(pages_root)
    pages_root.mkdir(parents=True)

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    source_inventory: list[dict[str, Any]] = []
    page_counts: Counter[str] = Counter()

    with tempfile.TemporaryDirectory() as temporary_name:
        temporary = Path(temporary_name)
        for item in DOCUMENTS:
            pdf_path = acquire(item, temporary, ns.offline_dir)
            raw = pdf_path.read_bytes()
            file_sha256 = hashlib.sha256(raw).hexdigest()
            reader = PdfReader(str(pdf_path))
            page_count = len(reader.pages)
            if page_count < 1:
                raise RuntimeError(f"PDF has no pages: {item['uri']}")
            extracted_chars = 0
            blank_pages: list[int] = []
            for page_number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").replace("\x00", "").strip()
                if not text:
                    blank_pages.append(page_number)
                    text = "[No extractable text on this PDF page; inspect the official page image.]"
                extracted_chars += len(text)
                document = page_document(item, page_number, page_count, text, file_sha256, ns.generated_at)
                buckets[partition(document)].append(document)
                page_counts[item["key"]] += 1
            source_inventory.append(
                {
                    "blank_or_image_only_pages": blank_pages,
                    "document_key": item["key"],
                    "extracted_characters": extracted_chars,
                    "file_sha256": file_sha256,
                    "page_count": page_count,
                    "source_id": item["source_id"],
                    "title": item["title"],
                    "uri": item["uri"],
                }
            )

    partitions: list[dict[str, Any]] = []
    stream_hash = hashlib.sha256()
    total_pages = 0
    for index, bucket in enumerate(buckets):
        directory = pages_root / f"part-{index:02d}"
        directory.mkdir()
        payload = "".join(
            json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
            for document in sorted(bucket, key=lambda value: value["_id"])
        ).encode("utf-8")
        path = directory / "starintel-documents.jsonl"
        path.write_bytes(payload)
        stream_hash.update(payload)
        total_pages += len(bucket)
        partitions.append(
            {
                "documents": len(bucket),
                "part": index,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )

    inventory_payload = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in source_inventory
    ).encode("utf-8")
    (output / "source-inventory.jsonl").write_bytes(inventory_payload)

    manifest_path = output / "manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    existing.update(
        {
            "generated_at": ns.generated_at,
            "page_document_count": total_pages,
            "page_document_stream_sha256": stream_hash.hexdigest(),
            "page_partitions": partitions,
            "page_source_inventory_sha256": hashlib.sha256(inventory_payload).hexdigest(),
            "pages_by_document": dict(sorted(page_counts.items())),
            "packet_status": "primary_sources_targets_and_page_documents_materialized",
            "total_documents": int(existing.get("total_documents", 21)) + total_pages,
            "validation": {
                "current_status": "page_documents_validated_during_generation",
                "page_level_materialization": "complete",
            },
        }
    )
    manifest_path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "page_documents": total_pages, "partitions": PARTITIONS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
