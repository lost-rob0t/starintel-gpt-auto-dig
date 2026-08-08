#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "gop"
RNC_ID = "starintel:org:republican-national-committee"
COMMITTEE_ID = "C00003418"
CYCLE = 2026
GENERATED_AT = "2026-08-08T21:50:00Z"
OUTPUT = Path("digs/gop/2026-07-31-fec-individual-contributions-2026")
DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/"
BULK_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/indiv{yy}.zip"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_DOWNLOAD = 6_000_000_000
MAX_UNIQUE_ROWS = 1_500_000
PART_SIZE = 30_000_000
READ_CHUNK = 3 * 1024 * 1024
FIELDS = [
    "CMTE_ID",
    "AMNDT_IND",
    "RPT_TP",
    "TRANSACTION_PGI",
    "IMAGE_NUM",
    "TRANSACTION_TP",
    "ENTITY_TP",
    "NAME",
    "CITY",
    "STATE",
    "ZIP_CODE",
    "EMPLOYER",
    "OCCUPATION",
    "TRANSACTION_DT",
    "TRANSACTION_AMT",
    "OTHER_ID",
    "TRAN_ID",
    "FILE_NUM",
    "MEMO_CD",
    "MEMO_TEXT",
    "SUB_ID",
]
SAFE_METADATA_FIELDS = (
    "CMTE_ID",
    "AMNDT_IND",
    "RPT_TP",
    "TRANSACTION_PGI",
    "IMAGE_NUM",
    "TRANSACTION_TP",
    "ENTITY_TP",
    "TRANSACTION_DT",
    "TRANSACTION_AMT",
    "OTHER_ID",
    "TRAN_ID",
    "FILE_NUM",
    "MEMO_CD",
    "SUB_ID",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import de-identified RNC individual-receipt rows from official FEC bulk data"
    )
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--committee-id", default=COMMITTEE_ID)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--offline-zip", type=Path)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def bulk_url(cycle: int) -> str:
    return BULK_URL.format(cycle=cycle, yy=str(cycle)[-2:])


def source_id(cycle: int, committee_id: str) -> str:
    return f"starintel:source:fec-individual-contributions-{cycle}-gop-{committee_id.lower()}"


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=300) as response, path.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise RuntimeError("FEC individual-contribution download exceeds safety limit")
            handle.write(chunk)


def copy_or_download(offline: Path | None, url: str, destination: Path) -> None:
    if offline is not None:
        shutil.copy2(offline, destination)
    else:
        download(url, destination)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_members(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        members = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
    if not members:
        raise RuntimeError("FEC ZIP contains no text data files")
    return sorted(members)


def iso_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%m%d%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            pass
    raise RuntimeError(f"invalid FEC date {value!r}")


def numeric_amount(value: str) -> float:
    try:
        return float(Decimal(value.strip()))
    except (InvalidOperation, ValueError) as exc:
        raise RuntimeError(f"invalid FEC amount {value!r}") from exc


def identifiers(row: dict[str, str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = [
        {
            "scheme": "fec_sub_id",
            "value": row["SUB_ID"],
            "issuer": "Federal Election Commission",
            "canonical": True,
        }
    ]
    for scheme, field in (
        ("fec_file_num", "FILE_NUM"),
        ("fec_transaction_id", "TRAN_ID"),
        ("fec_image_num", "IMAGE_NUM"),
    ):
        value = row[field].strip()
        if value:
            result.append(
                {
                    "scheme": scheme,
                    "value": value,
                    "issuer": "Federal Election Commission",
                    "canonical": False,
                }
            )
    return result


def safe_metadata(row: dict[str, str]) -> dict[str, str]:
    return {
        field.lower(): row[field]
        for field in SAFE_METADATA_FIELDS
        if row[field] != ""
    }


def source_document(cycle: int, committee_id: str, when: str) -> dict[str, Any]:
    doc = {
        "_id": source_id(cycle, committee_id),
        "data": {
            "accessed_at": when,
            "credibility": 0.99,
            "kind": "official_fec_bulk_file",
            "publisher": "Federal Election Commission",
            "uri": bulk_url(cycle),
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "extensions": {
            "privacy_transform": {
                "description_uri": DESCRIPTION_URL,
                "contributor_identity_emitted": False,
                "contributor_location_emitted": False,
                "contributor_employment_emitted": False,
                "raw_source_rows_embedded": False,
            }
        },
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": (
            "Official FEC individual-contribution bulk source filtered to the Republican National Committee; "
            "published StarIntel records intentionally omit contributor identity and employment/location fields."
        ),
        "tags": ["gop", "fec", "official-source", "individual-contribution", "deidentified"],
        "title": f"FEC {cycle} de-identified RNC individual-receipt source",
        "verification": {
            "last_reviewed_at": when,
            "status": "official-fec-record",
            "verified": True,
        },
        "version": 1,
    }
    validate_document(doc)
    return doc


def finance_document(
    row: dict[str, str], cycle: int, committee_id: str, when: str, source: str
) -> dict[str, Any]:
    sub_id = row["SUB_ID"].strip()
    tx_date = iso_date(row["TRANSACTION_DT"])
    tx_amount = numeric_amount(row["TRANSACTION_AMT"])
    qualifications = [
        "Raw FEC bulk row; amendments, memo entries, reattributions, refunds, and conduit records are preserved and not netted."
    ]
    if row["AMNDT_IND"] == "A":
        qualifications.append("This row was reported in an amended filing.")
    if row["MEMO_CD"] == "X":
        qualifications.append("FEC memo code X is preserved; this record is not treated as a net-new contribution.")

    doc = {
        "_id": f"starintel:campaign-finance:fec-individual-{sub_id}",
        "data": {
            "amount": tx_amount,
            "committee_id": committee_id,
            "contribution_type": row["TRANSACTION_TP"].strip() or "reported_receipt",
            "counterparty_ids": [RNC_ID],
            "currency": "USD",
            "election_cycle": str(cycle),
            "filing_id": row["FILE_NUM"].strip(),
            "methodology": (
                "Direct row import from the official FEC individual-contributions bulk file with contributor identity fields omitted."
            ),
            "observation_type": "reported_itemized_contribution",
            "period_end": tx_date,
            "period_start": tx_date,
            "qualifications": qualifications,
            "recipient_id": RNC_ID,
            "reported_at": None,
            "value_type": "reported_transaction_amount",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "campaign-finance",
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "identifiers": identifiers(row),
        "schema_version": "0.9.0",
        "sources": [
            {
                "source_id": source,
                "locator": f"SUB_ID {sub_id}",
                "metadata": safe_metadata(row),
            }
        ],
        "status": "recorded",
        "summary": (
            f"Official FEC row reports ${tx_amount:,.2f} as an itemized contribution or related receipt record "
            "to the Republican National Committee; contributor identity is intentionally omitted."
        ),
        "tags": ["gop", "fec", "individual-contribution", "campaign-finance", "deidentified"],
        "title": f"FEC contribution {sub_id}",
        "verification": {
            "last_reviewed_at": when,
            "status": "official-filing-record",
            "verified": True,
        },
        "version": 1,
    }
    validate_document(doc)
    return doc


def normalized_values(values: list[str], member: str, line_number: int) -> list[str]:
    if len(values) == len(FIELDS) + 1 and values[-1] == "":
        values.pop()
    if len(values) != len(FIELDS):
        raise RuntimeError(f"unexpected FEC row width in {member}:{line_number}: {len(values)}")
    return values


def write_json_line(handle: BinaryIO, hasher: Any, doc: dict[str, Any]) -> int:
    payload = (json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    handle.write(payload)
    hasher.update(payload)
    return len(payload)


def encode_gzip_parts(gzip_path: Path, base_path: Path) -> list[str]:
    for path in base_path.parent.glob(f"{base_path.name}.part-*"):
        path.unlink()
    parts_manifest = base_path.parent / f"{base_path.name}.parts"
    parts_manifest.unlink(missing_ok=True)

    names: list[str] = []
    buffer = ""
    part_index = 0

    def flush(force: bool = False) -> None:
        nonlocal buffer, part_index
        while len(buffer) >= PART_SIZE or (force and buffer):
            take = len(buffer) if force and len(buffer) < PART_SIZE else PART_SIZE
            name = f"{base_path.name}.part-{part_index:04d}"
            (base_path.parent / name).write_text(buffer[:take] + "\n", encoding="utf-8")
            names.append(name)
            buffer = buffer[take:]
            part_index += 1

    with gzip_path.open("rb") as handle:
        while True:
            chunk = handle.read(READ_CHUNK)
            if not chunk:
                break
            buffer += base64.b64encode(chunk).decode("ascii")
            flush()
    flush(force=True)
    if not names:
        raise RuntimeError("no encoded document parts were produced")
    parts_manifest.write_text("".join(f"{name}\n" for name in names), encoding="utf-8")
    return names


def generate(
    zip_path: Path,
    output: Path,
    cycle: int,
    committee_id: str,
    when: str,
) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    members = data_members(zip_path)
    seen_sub_ids: set[str] = set()
    raw_matching_rows = 0
    duplicate_sub_id_rows = 0
    counts: Counter[str] = Counter()
    source = source_id(cycle, committee_id)
    jsonl_hash = hashlib.sha256()

    with tempfile.NamedTemporaryFile(prefix="gop-rnc-receipts-", suffix=".jsonl.gz", delete=False) as temp:
        gzip_path = Path(temp.name)

    try:
        with gzip_path.open("wb") as raw_out:
            with gzip.GzipFile(fileobj=raw_out, mode="wb", compresslevel=9, mtime=0) as gz_out:
                src = source_document(cycle, committee_id, when)
                write_json_line(gz_out, jsonl_hash, src)
                counts[src["dtype"]] += 1

                with zipfile.ZipFile(zip_path) as archive:
                    for member in members:
                        with archive.open(member) as raw:
                            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                            for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                                values = normalized_values(values, member, line_number)
                                row = dict(zip(FIELDS, values, strict=True))
                                if row["CMTE_ID"].strip() != committee_id:
                                    continue
                                raw_matching_rows += 1
                                sub_id = row["SUB_ID"].strip()
                                if not sub_id:
                                    raise RuntimeError(f"matching FEC row {member}:{line_number} lacks SUB_ID")
                                if sub_id in seen_sub_ids:
                                    duplicate_sub_id_rows += 1
                                    continue
                                seen_sub_ids.add(sub_id)
                                if len(seen_sub_ids) > MAX_UNIQUE_ROWS:
                                    raise RuntimeError(
                                        f"unique RNC FEC receipt rows exceed safety cap {MAX_UNIQUE_ROWS:,}"
                                    )
                                doc = finance_document(row, cycle, committee_id, when, source)
                                write_json_line(gz_out, jsonl_hash, doc)
                                counts[doc["dtype"]] += 1

        if not seen_sub_ids:
            raise RuntimeError(f"no individual-contribution rows found for {committee_id}")

        document_base = output / "starintel-documents.jsonl.gz.b64"
        document_parts = encode_gzip_parts(gzip_path, document_base)
        manifest = {
            "committee_id": committee_id,
            "contributor_employment_emitted": False,
            "contributor_identity_emitted": False,
            "contributor_location_emitted": False,
            "counts": dict(sorted(counts.items())),
            "cycle": cycle,
            "dataset": DATASET,
            "document_part_count": len(document_parts),
            "document_sha256": jsonl_hash.hexdigest(),
            "duplicate_sub_id_rows": duplicate_sub_id_rows,
            "generated_at": when,
            "privacy_transform": "deidentified-fec-receipt-ledger-v2-streaming",
            "raw_matching_rows": raw_matching_rows,
            "raw_source_members": members,
            "raw_source_rows_embedded": False,
            "raw_source_zip_sha256": file_sha256(zip_path),
            "reconciliation": "duplicate SUB_ID rows skipped; amendment and memo rows with distinct SUB_IDs preserved",
            "schema_version": "0.9.0",
            "total_documents": sum(counts.values()),
            "unique_fec_sub_ids": len(seen_sub_ids),
        }
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (output / "README.md").write_text(
            f"""# GOP FEC de-identified individual-receipt ledger — {cycle} cycle

Official FEC `indiv{str(cycle)[-2:]}.zip` rows filtered to `{committee_id}`.

- raw matching FEC rows: {raw_matching_rows:,}
- duplicate `SUB_ID` rows skipped: {duplicate_sub_id_rows:,}
- unique FEC receipt rows: {len(seen_sub_ids):,}
- published StarIntel documents: {sum(counts.values()):,}
- contributor names emitted: no
- contributor locations emitted: no
- contributor employers/occupations emitted: no
- raw contributor rows embedded: no

Each campaign-finance record retains the FEC `SUB_ID`, filing/transaction/image identifiers, transaction amount/date/type, amendment/memo flags, and the RNC recipient linkage. Duplicate physical rows caused by overlapping FEC archive members are not counted twice. Contributor identity fields are never materialized.

```bash
python3 scripts/import_gop_fec_deidentified_receipts.py
python3 scripts/validate-for-merge.py --site
```
""",
            encoding="utf-8",
        )
        return manifest
    finally:
        gzip_path.unlink(missing_ok=True)


def main() -> int:
    ns = parse_args()
    if ns.cycle % 2:
        raise RuntimeError("FEC cycle must be an even-numbered election cycle")
    if ns.committee_id.upper() != COMMITTEE_ID:
        raise RuntimeError(
            f"this privacy-preserving importer is intentionally scoped to the RNC committee {COMMITTEE_ID}"
        )

    with tempfile.TemporaryDirectory(prefix="gop-fec-rnc-receipts-") as tmp:
        zip_path = Path(tmp) / f"indiv{str(ns.cycle)[-2:]}.zip"
        copy_or_download(ns.offline_zip, bulk_url(ns.cycle), zip_path)
        manifest = generate(zip_path, ns.output, ns.cycle, ns.committee_id.upper(), ns.generated_at)

    print(
        json.dumps(
            {
                "documents": manifest["total_documents"],
                "duplicate_rows": manifest["duplicate_sub_id_rows"],
                "output": str(ns.output),
                "raw_rows": manifest["raw_matching_rows"],
                "unique_rows": manifest["unique_fec_sub_ids"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
