#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import import_dnc_fec_individual_contributions as source
from starintel_doc.validation import validate_document

BUCKETS = 32
GENERATED_AT = "2026-07-31T08:55:00Z"
INDEX_DIR = Path("digs/dnc/2026-07-31-fec-people-employment-2026-index")
PART_PREFIX = "2026-07-31-fec-people-employment-2026-part-"
SOURCE_ID = "starintel:source:fec-individual-contributions-2026-c00010603-canonical"
PUBLIC_FIELDS = [field for field in source.FIELDS if field != "ZIP_CODE"]
PART_SIZE = 30_000_000
TARGET_AXES = (
    ("identity", "Resolve identities", "Resolve source-scoped identities against primary public records without merging namesakes."),
    ("employment", "Verify employment", "Verify reported employer, occupation, role type, and date range against primary public records."),
    ("fec", "Reconcile FEC rows", "Reconcile amendments, memo entries, refunds, conduits, and repeated reporting for this partition."),
    ("ties", "Map institutional ties", "Map campaign, committee, government, nonprofit, corporate, lobbying, and vendor ties."),
    ("employers", "Resolve employer networks", "Resolve employer legal entities, owners, officers, subsidiaries, contracts, and political links."),
)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


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


def amount(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError) as exc:
        raise RuntimeError(f"invalid FEC amount {value!r}") from exc


def identity_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["ENTITY_TP"].strip().upper() or "UNKNOWN",
        norm(row["NAME"]),
        norm(row["CITY"]),
        row["STATE"].strip().upper(),
        row["ZIP_CODE"].strip(),
    )


def identity_id(key: tuple[str, str, str, str, str]) -> str:
    dtype = "person" if key[0] in source.PERSON_ENTITY_TYPES else "org"
    digest = hashlib.sha256("\x1f".join(key).encode()).hexdigest()
    return f"starintel:{dtype}:fec-contributor-{digest}"


def employer_id(value: str) -> str:
    return "starintel:org:fec-reported-employer-" + hashlib.sha256(norm(value).encode()).hexdigest()


def employment_id(person_id: str, organization_id: str, occupation: str, status: str) -> str:
    raw = "\x1f".join((person_id, organization_id, norm(occupation), status))
    return "starintel:employment:fec-reported-" + hashlib.sha256(raw.encode()).hexdigest()


def bucket_for(doc_id: str) -> int:
    return int(hashlib.sha256(doc_id.encode()).hexdigest()[:8], 16) % BUCKETS


def base(
    doc_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, Any],
    *,
    verified: bool,
    status: str,
    pii: bool = False,
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "data": data,
        "dataset": "dnc",
        "date_added": GENERATED_AT,
        "date_updated": GENERATED_AT,
        "dtype": dtype,
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": pii,
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [{"source_id": SOURCE_ID}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "people-employment", dtype],
        "title": title,
        "verification": {
            "last_reviewed_at": GENERATED_AT,
            "status": status,
            "verified": verified,
        },
        "version": 1,
    }


def encode_parts(source_path: Path, base_path: Path) -> list[str]:
    gzip_path = source_path.with_suffix(source_path.suffix + ".gz")
    with source_path.open("rb") as input_handle, gzip.GzipFile(
        filename="", mode="wb", fileobj=gzip_path.open("wb"), compresslevel=9, mtime=0
    ) as compressed:
        shutil.copyfileobj(input_handle, compressed, length=1024 * 1024)
    names: list[str] = []
    buffer = ""
    index = 0
    with gzip_path.open("rb") as handle:
        while True:
            chunk = handle.read(3 * 1024 * 1024)
            if not chunk:
                break
            buffer += base64.b64encode(chunk).decode("ascii")
            while len(buffer) >= PART_SIZE:
                name = f"{base_path.name}.part-{index:04d}"
                (base_path.parent / name).write_text(buffer[:PART_SIZE] + "\n", encoding="utf-8")
                names.append(name)
                buffer = buffer[PART_SIZE:]
                index += 1
    if buffer or not names:
        name = f"{base_path.name}.part-{index:04d}"
        (base_path.parent / name).write_text(buffer + "\n", encoding="utf-8")
        names.append(name)
    (base_path.parent / f"{base_path.name}.parts").write_text(
        "".join(f"{name}\n" for name in names), encoding="utf-8"
    )
    gzip_path.unlink()
    return names


def emit(handle, counts: Counter[str], document: dict[str, Any]) -> None:
    validate_document(document)
    handle.write(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n")
    counts[document["dtype"]] += 1


def target_document(bucket: int, axis: str, label: str, question: str) -> dict[str, Any]:
    target_id = f"starintel:investigation-target:dnc-fec-people-part-{bucket:02d}-{axis}"
    return base(
        target_id,
        "investigation-target",
        f"DNC FEC people partition {bucket:02d}: {label}",
        question,
        {
            "breadth": 250,
            "depth": 1,
            "excluded_sources": ["people-search sites", "data brokers", "unsourced reposts"],
            "in_scope": [
                "official FEC records", "official biographies and staff directories",
                "corporate and nonprofit filings", "lobbying and ethics disclosures",
                "public procurement and court records", "archived official websites",
            ],
            "max_depth": 7,
            "objectives": [question, f"Process canonical partition {bucket:02d} without false identity merges"],
            "out_of_scope": [
                "private residential addresses", "private contact information",
                "credentials", "non-public personal data", "unsupported criminal conclusions",
            ],
            "preferred_sources": [
                "Federal Election Commission", "official organization records",
                "state corporate and charity registries", "IRS nonprofit filings",
                "public lobbying, ethics, procurement, and court records",
            ],
            "priority": 0.82,
            "required_dtypes": ["source", "person", "org", "employment", "relation", "campaign-finance"],
            "research_question": question,
            "scope_type": "public_source",
            "seed_ids": [SOURCE_ID],
            "source_ids": [SOURCE_ID],
            "status": "queued",
            "target": f"DNC FEC people partition {bucket:02d}: {label}",
            "target_type": f"dnc_fec_people_{axis}",
        },
        verified=True,
        status="deterministically-derived-from-corpus",
    ) | {
        "workflow": {
            "max_depth": 7,
            "next_action": question,
            "priority": 0.82,
            "queue": "dnc-fec-people",
            "recursion_depth": 1,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": "dnc-fec-people-2026-partitions",
        }
    }


def main() -> int:
    people: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    organizations: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    employers: dict[str, str] = {}
    employments: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    raw_rows = 0
    raw_amount = Decimal("0")

    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    for bucket in range(BUCKETS):
        path = Path("digs/dnc") / f"{PART_PREFIX}{bucket:02d}"
        if path.exists():
            shutil.rmtree(path)
    INDEX_DIR.mkdir(parents=True)
    (INDEX_DIR / "source").mkdir()

    with tempfile.TemporaryDirectory(prefix="dnc-fec-index-") as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / "indiv26.zip"
        source.download(source.bulk_url(source.CYCLE), archive_path)
        raw_path = tmp_path / "dnc-individual-contributions-2026.psv"
        with zipfile.ZipFile(archive_path) as archive, archive.open("itcont.txt") as raw, raw_path.open(
            "w", encoding="utf-8", newline=""
        ) as raw_output:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            writer = csv.DictWriter(raw_output, fieldnames=PUBLIC_FIELDS, delimiter="|", lineterminator="\n")
            writer.writeheader()
            for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
                if len(values) == len(source.FIELDS) + 1 and values[-1] == "":
                    values.pop()
                if len(values) != len(source.FIELDS):
                    raise RuntimeError(f"unexpected row width at itcont.txt:{line_no}")
                row = dict(zip(source.FIELDS, values, strict=True))
                if row["CMTE_ID"] != source.COMMITTEE_ID:
                    continue
                raw_rows += 1
                raw_amount += amount(row["TRANSACTION_AMT"])
                writer.writerow({field: row[field] for field in PUBLIC_FIELDS})
                key = identity_key(row)
                person_like = key[0] in source.PERSON_ENTITY_TYPES
                target = people if person_like else organizations
                profile = target.setdefault(
                    key,
                    {
                        "id": identity_id(key),
                        "name": clean(row["NAME"]) or "Unspecified FEC contributor",
                        "city": clean(row["CITY"]),
                        "state": row["STATE"].strip().upper(),
                        "row_count": 0,
                        "amount": Decimal("0"),
                        "first_date": None,
                        "last_date": None,
                        "employers": set(),
                        "occupations": set(),
                    },
                )
                profile["row_count"] += 1
                profile["amount"] += amount(row["TRANSACTION_AMT"])
                transaction_date = iso_date(row["TRANSACTION_DT"])
                if transaction_date:
                    profile["first_date"] = min(
                        date for date in (profile["first_date"], transaction_date) if date
                    )
                    profile["last_date"] = max(
                        date for date in (profile["last_date"], transaction_date) if date
                    )
                if not person_like:
                    continue
                employer = clean(row["EMPLOYER"])
                occupation = clean(row["OCCUPATION"])
                if occupation:
                    profile["occupations"].add(occupation)
                organization_id = ""
                if source.meaningful_employer(employer):
                    organization_id = employer_id(employer)
                    employers.setdefault(organization_id, employer)
                    profile["employers"].add(organization_id)
                status = source.status_label(row)
                employment_key = (profile["id"], organization_id, norm(occupation), status)
                record = employments.setdefault(
                    employment_key,
                    {
                        "person_id": profile["id"],
                        "organization_id": organization_id,
                        "title": occupation or employer or "Unspecified reported status",
                        "status": status,
                        "row_count": 0,
                        "first_date": transaction_date,
                        "last_date": transaction_date,
                        "first_sub_id": row["SUB_ID"],
                    },
                )
                record["row_count"] += 1
                dates = [date for date in (record["first_date"], record["last_date"], transaction_date) if date]
                if dates:
                    record["first_date"] = min(dates)
                    record["last_date"] = max(dates)

        raw_base = INDEX_DIR / "source" / "dnc-individual-contributions-2026.psv.gz.b64"
        raw_parts = encode_parts(raw_path, raw_base)
        bucket_paths = [tmp_path / f"bucket-{bucket:02d}.jsonl" for bucket in range(BUCKETS)]
        handles = [path.open("w", encoding="utf-8") for path in bucket_paths]
        counts = [Counter() for _ in range(BUCKETS)]
        try:
            source_doc = base(
                SOURCE_ID,
                "source",
                "FEC 2026 individual contributions — DNC canonical combined file",
                "Official FEC individual-contribution rows from the canonical combined itcont.txt member, filtered to C00010603. The equivalent by-date copies are not duplicated.",
                {
                    "accessed_at": GENERATED_AT,
                    "credibility": 0.99,
                    "kind": "official_fec_bulk_file",
                    "publisher": "Federal Election Commission",
                    "uri": source.bulk_url(source.CYCLE),
                },
                verified=True,
                status="official-fec-bulk-source",
            )
            source_doc["sources"] = []
            emit(handles[0], counts[0], source_doc)

            for profile in people.values():
                data: dict[str, Any] = {
                    "full_name": profile["name"],
                    "name": profile["name"],
                    "employers": sorted(profile["employers"]),
                    "occupations": sorted(profile["occupations"]),
                    "public_roles": ["FEC-reported contributor to the DNC"],
                }
                if profile["state"]:
                    data["jurisdiction"] = profile["state"]
                doc = base(
                    profile["id"],
                    "person",
                    profile["name"],
                    "Source-scoped identity from official FEC records; exact real-world identity and current employment remain unresolved.",
                    data,
                    verified=False,
                    status="source-scoped-unresolved-identity",
                    pii=True,
                )
                doc["extensions"] = {
                    "fec_summary": {
                        "city": profile["city"],
                        "state": profile["state"],
                        "row_count": profile["row_count"],
                        "raw_reported_amount_sum": float(profile["amount"]),
                        "first_transaction_date": profile["first_date"],
                        "last_transaction_date": profile["last_date"],
                        "postal_code_emitted": False,
                        "amount_reconciled": False,
                    }
                }
                bucket = bucket_for(doc["_id"])
                emit(handles[bucket], counts[bucket], doc)

            for profile in organizations.values():
                doc = base(
                    profile["id"],
                    "org",
                    profile["name"],
                    "Source-scoped non-individual contributor identity reported in official FEC records.",
                    {"name": profile["name"], "org_type": "fec_reported_contributor"},
                    verified=False,
                    status="source-scoped-unresolved-identity",
                )
                doc["extensions"] = {
                    "fec_summary": {
                        "row_count": profile["row_count"],
                        "raw_reported_amount_sum": float(profile["amount"]),
                        "first_transaction_date": profile["first_date"],
                        "last_transaction_date": profile["last_date"],
                        "amount_reconciled": False,
                    }
                }
                bucket = bucket_for(doc["_id"])
                emit(handles[bucket], counts[bucket], doc)

            for organization_id, employer in employers.items():
                doc = base(
                    organization_id,
                    "org",
                    employer,
                    "Employer value reported in official FEC contribution records; legal-entity resolution remains pending.",
                    {"name": employer, "org_type": "fec_reported_employer"},
                    verified=False,
                    status="source-scoped-unresolved-identity",
                )
                bucket = bucket_for(doc["_id"])
                emit(handles[bucket], counts[bucket], doc)

            for record in employments.values():
                doc_id = employment_id(
                    record["person_id"], record["organization_id"], record["title"], record["status"]
                )
                data: dict[str, Any] = {
                    "person_id": record["person_id"],
                    "title": record["title"],
                    "employment_type": record["status"],
                }
                if record["organization_id"]:
                    data["organization_id"] = record["organization_id"]
                doc = base(
                    doc_id,
                    "employment",
                    f"FEC-reported role/status: {record['title']}",
                    "Employer or occupational status as reported in FEC records; this is not independent verification or proof of current employment.",
                    data,
                    verified=False,
                    status="reported-by-filer-unverified",
                    pii=True,
                )
                doc["extensions"] = {
                    "fec_reporting": {
                        "row_count": record["row_count"],
                        "first_transaction_date": record["first_date"],
                        "last_transaction_date": record["last_date"],
                        "first_fec_sub_id": record["first_sub_id"],
                    }
                }
                bucket = bucket_for(doc["_id"])
                emit(handles[bucket], counts[bucket], doc)

            for bucket in range(BUCKETS):
                for axis, label, question in TARGET_AXES:
                    emit(handles[bucket], counts[bucket], target_document(bucket, axis, label, question))
        finally:
            for handle in handles:
                handle.close()

        part_manifests = []
        for bucket, bucket_path in enumerate(bucket_paths):
            output = Path("digs/dnc") / f"{PART_PREFIX}{bucket:02d}"
            output.mkdir(parents=True)
            part_names = encode_parts(bucket_path, output / "starintel-documents.jsonl.gz.b64")
            payload_sha = hashlib.sha256(bucket_path.read_bytes()).hexdigest()
            manifest = {
                "bucket": bucket,
                "bucket_count": BUCKETS,
                "counts": dict(sorted(counts[bucket].items())),
                "dataset": "dnc",
                "document_part_count": len(part_names),
                "document_sha256": payload_sha,
                "generated_at": GENERATED_AT,
                "schema_version": "0.9.0",
                "source_id": SOURCE_ID,
                "total_documents": sum(counts[bucket].values()),
            }
            (output / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            (output / "README.md").write_text(
                f"# DNC FEC people/employment partition {bucket:02d}\n\n"
                f"- documents: {manifest['total_documents']:,}\n"
                f"- partition: {bucket:02d} of {BUCKETS}\n",
                encoding="utf-8",
            )
            part_manifests.append(manifest)

        total_counts = Counter()
        for count in counts:
            total_counts.update(count)
        index_manifest = {
            "bucket_count": BUCKETS,
            "committee_id": source.COMMITTEE_ID,
            "counts": dict(sorted(total_counts.items())),
            "cycle": source.CYCLE,
            "dataset": "dnc",
            "employer_organizations": len(employers),
            "employment_records": len(employments),
            "generated_at": GENERATED_AT,
            "non_individual_contributors": len(organizations),
            "postal_codes_emitted": False,
            "raw_matching_rows": raw_rows,
            "raw_reported_amount_sum": float(raw_amount),
            "raw_source_part_count": len(raw_parts),
            "raw_source_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "schema_version": "0.9.0",
            "source_id": SOURCE_ID,
            "source_scoped_people": len(people),
            "total_documents": sum(total_counts.values()),
            "unique_fec_records": raw_rows,
            "zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        }
        (INDEX_DIR / "manifest.json").write_text(
            json.dumps(index_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (INDEX_DIR / "README.md").write_text(
            "# DNC FEC people and employment index\n\n"
            f"- unique FEC records preserved: {raw_rows:,}\n"
            f"- source-scoped people: {len(people):,}\n"
            f"- employer organizations: {len(employers):,}\n"
            f"- employment/status records: {len(employments):,}\n"
            f"- canonical documents: {sum(total_counts.values()):,}\n"
            f"- partitions: {BUCKETS}\n\n"
            "The raw amount is not a reconciled receipt total. Amendments, memo entries, refunds, conduits, and reattributions remain in the preserved source rows. Postal codes are used only inside source-scoped identity hashes and are not emitted.\n",
            encoding="utf-8",
        )

    print(json.dumps(index_manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
