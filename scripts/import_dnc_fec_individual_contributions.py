#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
COMMITTEE_ID = "C00010603"
CYCLE = 2026
GENERATED_AT = "2026-07-31T08:05:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-individual-contributions-2026")
DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/"
BULK_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/indiv{yy}.zip"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_DOWNLOAD = 6_000_000_000
MAX_MATCHING_ROWS = 750_000
PART_SIZE = 30_000_000
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
PUBLIC_FIELDS = [field for field in FIELDS if field != "ZIP_CODE"]
NON_EMPLOYERS = {
    "",
    "n a",
    "na",
    "none",
    "not applicable",
    "not employed",
    "unemployed",
    "retired",
    "homemaker",
    "student",
    "self",
    "self employed",
    "self-employed",
    "information requested",
    "requested",
    "refused",
}
PERSON_ENTITY_TYPES = {"", "IND", "CAN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import DNC individual contributions, people, employers, and reported employment"
    )
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--committee-id", default=COMMITTEE_ID)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--offline-zip", type=Path)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return f"starintel:{prefix}:{hashlib.sha256(raw).hexdigest()}"


def source_id(cycle: int, committee_id: str) -> str:
    return f"starintel:source:fec-individual-contributions-{cycle}-{committee_id.lower()}"


def bulk_url(cycle: int) -> str:
    return BULK_URL.format(cycle=cycle, yy=str(cycle)[-2:])


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


def data_members(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        members = [
            info
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
    if not members:
        raise RuntimeError("FEC ZIP contains no text data files")
    return [info.filename for info in sorted(members, key=lambda item: item.filename)]


def matching_rows(path: Path, committee_id: str) -> tuple[list[str], list[dict[str, str]]]:
    members = data_members(path)
    matched: list[dict[str, str]] = []
    seen_sub_ids: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for member in members:
            with archive.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
                    if len(values) == len(FIELDS) + 1 and values[-1] == "":
                        values.pop()
                    if len(values) != len(FIELDS):
                        raise RuntimeError(
                            f"unexpected FEC row width in {member}:{line_no}: {len(values)}"
                        )
                    row = dict(zip(FIELDS, values, strict=True))
                    if row["CMTE_ID"] != committee_id:
                        continue
                    sub_id = row["SUB_ID"].strip()
                    if not sub_id:
                        raise RuntimeError(f"matching row {member}:{line_no} has no SUB_ID")
                    if sub_id in seen_sub_ids:
                        raise RuntimeError(f"duplicate FEC SUB_ID in bulk file: {sub_id}")
                    seen_sub_ids.add(sub_id)
                    matched.append(row)
                    if len(matched) > MAX_MATCHING_ROWS:
                        raise RuntimeError("matching FEC contribution rows exceed safety limit")
    if not matched:
        raise RuntimeError(f"no individual-contribution rows found for {committee_id}")
    return members, matched


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


def base(
    doc_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, Any],
    when: str,
    source: str,
    *,
    verified: bool = True,
    status: str = "official-filing-record",
    pii: bool = False,
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": dtype,
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": pii,
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "individual-contribution", dtype],
        "title": title,
        "verification": {
            "last_reviewed_at": when,
            "status": status,
            "verified": verified,
        },
        "version": 1,
    }


def public_row(row: dict[str, str]) -> dict[str, str]:
    return {field.lower(): row[field] for field in PUBLIC_FIELDS if row[field] != ""}


def contributor_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    entity_type = row["ENTITY_TP"].strip().upper()
    return (
        entity_type,
        norm(row["NAME"]),
        norm(row["CITY"]),
        row["STATE"].strip().upper(),
        row["ZIP_CODE"].strip(),
    )


def contributor_dtype(row: dict[str, str]) -> str:
    return "person" if row["ENTITY_TP"].strip().upper() in PERSON_ENTITY_TYPES else "org"


def contributor_id(row: dict[str, str]) -> str:
    dtype = contributor_dtype(row)
    return sha_id(f"{dtype}:fec-contributor", *contributor_key(row))


def employer_key(value: str) -> str:
    return norm(value)


def meaningful_employer(value: str) -> bool:
    return employer_key(value) not in NON_EMPLOYERS


def employer_id(value: str) -> str:
    return sha_id("org:fec-reported-employer", employer_key(value))


def status_label(row: dict[str, str]) -> str:
    employer = clean(row["EMPLOYER"])
    occupation = clean(row["OCCUPATION"])
    if meaningful_employer(employer):
        return "fec_reported_employment"
    if norm(employer) in {"self", "self employed", "self-employed"}:
        return "fec_reported_self_employment"
    if norm(employer) == "retired" or norm(occupation) == "retired":
        return "fec_reported_retired"
    if norm(employer) in {"not employed", "unemployed", "none"}:
        return "fec_reported_not_employed"
    return "fec_reported_occupation_only"


def identifiers(row: dict[str, str]) -> list[dict[str, Any]]:
    result = [
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


def build(
    rows: list[dict[str, str]],
    cycle: int,
    committee_id: str,
    when: str,
    source: str,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    emitted: set[str] = set()
    people_profiles: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    org_contributors: dict[str, dict[str, Any]] = {}
    employers: dict[str, str] = {}
    employment_stats: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def emit(doc: dict[str, Any]) -> None:
        doc_id = doc["_id"]
        if doc_id in emitted:
            raise RuntimeError(f"duplicate generated ID: {doc_id}")
        validate_document(doc)
        emitted.add(doc_id)
        docs.append(doc)

    source_doc = base(
        source,
        "source",
        f"FEC {cycle} individual contributions bulk file — {committee_id}",
        "Official FEC individual-contribution bulk rows filtered to the DNC committee. Postal codes are used only for source-scoped identity separation and are not emitted.",
        {
            "accessed_at": when,
            "credibility": 0.99,
            "kind": "official_fec_bulk_file",
            "publisher": "Federal Election Commission",
            "uri": bulk_url(cycle),
        },
        when,
        source,
    )
    source_doc["sources"] = []
    emit(source_doc)

    for row in rows:
        cid = contributor_id(row)
        dtype = contributor_dtype(row)
        name = clean(row["NAME"]) or "Unspecified FEC contributor"
        employer = clean(row["EMPLOYER"])
        occupation = clean(row["OCCUPATION"])
        tx_date = iso_date(row["TRANSACTION_DT"])
        if dtype == "person":
            key = contributor_key(row)
            profile = people_profiles.setdefault(
                key,
                {
                    "id": cid,
                    "name": name,
                    "city": clean(row["CITY"]),
                    "state": row["STATE"].strip().upper(),
                    "employers": set(),
                    "occupations": set(),
                    "rows": 0,
                },
            )
            profile["rows"] += 1
            if occupation:
                profile["occupations"].add(occupation)
            eid = ""
            if meaningful_employer(employer):
                eid = employer_id(employer)
                employers.setdefault(eid, employer)
                profile["employers"].add(eid)
            employment_key = (cid, eid, norm(occupation), status_label(row))
            stats = employment_stats.setdefault(
                employment_key,
                {
                    "person_id": cid,
                    "organization_id": eid,
                    "title": occupation or employer or "Unspecified reported status",
                    "employment_type": status_label(row),
                    "row_count": 0,
                    "first_date": tx_date,
                    "last_date": tx_date,
                    "first_sub_id": row["SUB_ID"],
                },
            )
            stats["row_count"] += 1
            dates = [date for date in (stats["first_date"], stats["last_date"], tx_date) if date]
            if dates:
                stats["first_date"] = min(dates)
                stats["last_date"] = max(dates)
        else:
            org_contributors.setdefault(
                cid,
                {
                    "name": name,
                    "entity_type": row["ENTITY_TP"].strip().upper() or "UNK",
                },
            )

    for eid, name in sorted(employers.items()):
        emit(
            base(
                eid,
                "org",
                name,
                "Source-scoped employer name reported by one or more contributors in official FEC records; legal-entity resolution remains pending.",
                {"name": name, "org_type": "fec_reported_employer"},
                when,
                source,
                verified=False,
                status="source-scoped-unresolved-identity",
            )
        )

    for profile in sorted(people_profiles.values(), key=lambda item: item["id"]):
        data: dict[str, Any] = {
            "full_name": profile["name"],
            "name": profile["name"],
            "occupations": sorted(profile["occupations"]),
            "employers": sorted(profile["employers"]),
            "public_roles": ["FEC-reported contributor to the DNC"],
        }
        if profile["state"]:
            data["jurisdiction"] = profile["state"]
        doc = base(
            profile["id"],
            "person",
            profile["name"],
            "Source-scoped contributor identity derived from official FEC filings. Exact real-world identity and current employment are not independently resolved.",
            data,
            when,
            source,
            verified=False,
            status="source-scoped-unresolved-identity",
            pii=True,
        )
        doc["extensions"] = {
            "fec_identity_scope": {
                "city": profile["city"],
                "state": profile["state"],
                "filing_rows": profile["rows"],
                "postal_code_emitted": False,
            }
        }
        emit(doc)

    for cid, profile in sorted(org_contributors.items()):
        emit(
            base(
                cid,
                "org",
                profile["name"],
                "Source-scoped non-individual contributor identity reported in the FEC individual-contribution file.",
                {
                    "name": profile["name"],
                    "org_type": f"fec_reported_contributor_{profile['entity_type'].lower()}",
                },
                when,
                source,
                verified=False,
                status="source-scoped-unresolved-identity",
            )
        )

    for key, stats in sorted(employment_stats.items()):
        person_id, organization_id, _, employment_type = key
        employment_doc_id = sha_id(
            "employment:fec-reported",
            person_id,
            organization_id,
            norm(stats["title"]),
            employment_type,
        )
        data = {
            "person_id": person_id,
            "title": stats["title"],
            "employment_type": employment_type,
        }
        if organization_id:
            data["organization_id"] = organization_id
        employment_doc = base(
            employment_doc_id,
            "employment",
            f"FEC-reported employment/status: {stats['title']}",
            "Employment or occupational status exactly as reported in FEC contribution records; this is not independent verification of employment or current status.",
            data,
            when,
            source,
            verified=False,
            status="reported-by-filer-unverified",
            pii=True,
        )
        employment_doc["sources"] = [
            {"source_id": source, "locator": f"SUB_ID {stats['first_sub_id']}"}
        ]
        employment_doc["extensions"] = {
            "fec_reporting": {
                "first_transaction_date": stats["first_date"],
                "last_transaction_date": stats["last_date"],
                "row_count": stats["row_count"],
            }
        }
        emit(employment_doc)
        if organization_id:
            relation = base(
                sha_id("relation", person_id, "reported_employment_with", organization_id, employment_doc_id),
                "relation",
                "FEC-reported employment relation",
                "The contributor reported this employer in one or more FEC contribution records; independent verification remains pending.",
                {
                    "confidence": 0.75,
                    "directed": True,
                    "object": organization_id,
                    "predicate": "reported_employment_with",
                    "qualifiers": {
                        "employment_document_id": employment_doc_id,
                        "occupation": stats["title"],
                        "first_transaction_date": stats["first_date"],
                        "last_transaction_date": stats["last_date"],
                        "row_count": stats["row_count"],
                    },
                    "subject": person_id,
                },
                when,
                source,
                verified=False,
                status="reported-by-filer-unverified",
                pii=True,
            )
            relation["related_ids"] = [employment_doc_id]
            emit(relation)

    for row in rows:
        cid = contributor_id(row)
        sub_id = row["SUB_ID"]
        tx_date = iso_date(row["TRANSACTION_DT"])
        tx_amount = numeric_amount(row["TRANSACTION_AMT"])
        metadata = public_row(row)
        qualifications = [
            "Raw FEC bulk row; amendments, memo entries, reattributions, refunds, and conduit records are preserved and not netted."
        ]
        if row["AMNDT_IND"] == "A":
            qualifications.append("This row was reported in an amended filing.")
        if row["MEMO_CD"] == "X":
            qualifications.append(
                "FEC memo code X may indicate a memo, conduit, reattribution, or previously reported transaction."
            )

        finance_id = f"starintel:campaign-finance:fec-individual-{sub_id}"
        finance = base(
            finance_id,
            "campaign-finance",
            f"FEC contribution {sub_id}: {clean(row['NAME']) or 'unspecified contributor'}",
            f"Official FEC row reports a ${tx_amount:,.2f} itemized contribution or related receipt record involving the named contributor and the DNC.",
            {
                "amount": tx_amount,
                "committee_id": committee_id,
                "contribution_type": row["TRANSACTION_TP"].strip() or "reported_receipt",
                "counterparty_ids": [DNC_ID],
                "currency": "USD",
                "donor_id": cid,
                "election_cycle": str(cycle),
                "entity_id": cid,
                "filing_id": row["FILE_NUM"].strip(),
                "methodology": "Direct row import from the official FEC individual-contributions bulk file.",
                "observation_type": "reported_itemized_contribution",
                "period_end": tx_date,
                "period_start": tx_date,
                "qualifications": qualifications,
                "recipient_id": DNC_ID,
                "reported_at": None,
                "value_type": "reported_transaction_amount",
            },
            when,
            source,
        )
        finance["identifiers"] = identifiers(row)
        finance["sources"] = [
            {
                "source_id": source,
                "locator": f"SUB_ID {sub_id}",
                "metadata": metadata,
            }
        ]
        emit(finance)

        relation = base(
            sha_id("relation", cid, "reported_contribution_to", DNC_ID, sub_id),
            "relation",
            f"Reported contribution to DNC: {clean(row['NAME']) or 'unspecified contributor'}",
            f"FEC row {sub_id} reports a ${tx_amount:,.2f} contribution or related receipt record involving this contributor and the DNC.",
            {
                "confidence": 0.99,
                "directed": True,
                "object": DNC_ID,
                "predicate": "reported_contribution_to",
                "qualifiers": {
                    "amount": tx_amount,
                    "currency": "USD",
                    "transaction_date": tx_date,
                    **metadata,
                    "postal_code_emitted": False,
                    "raw_row_preserved": True,
                    "reconciled": False,
                },
                "subject": cid,
            },
            when,
            source,
            pii=contributor_dtype(row) == "person",
        )
        relation["related_ids"] = [finance_id]
        emit(relation)

    return sorted(docs, key=lambda doc: doc["_id"])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_gzip_b64_parts(base_path: Path, payload: bytes) -> list[str]:
    encoded = base64.b64encode(gzip.compress(payload, compresslevel=9, mtime=0)).decode("ascii")
    names: list[str] = []
    for index, start in enumerate(range(0, len(encoded), PART_SIZE)):
        name = f"{base_path.name}.part-{index:04d}"
        (base_path.parent / name).write_text(
            encoded[start : start + PART_SIZE] + "\n", encoding="utf-8"
        )
        names.append(name)
    (base_path.parent / f"{base_path.name}.parts").write_text(
        "".join(f"{name}\n" for name in names), encoding="utf-8"
    )
    return names


def write(
    output: Path,
    zip_path: Path,
    members: list[str],
    rows: list[dict[str, str]],
    docs: list[dict[str, Any]],
    cycle: int,
    committee_id: str,
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)

    source_buffer = io.StringIO()
    writer = csv.DictWriter(
        source_buffer, fieldnames=PUBLIC_FIELDS, delimiter="|", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in PUBLIC_FIELDS})
    source_bytes = source_buffer.getvalue().encode("utf-8")
    source_parts = write_gzip_b64_parts(
        output / "source" / f"dnc-individual-contributions-{cycle}.psv.gz.b64",
        source_bytes,
    )

    jsonl = "".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in docs
    ).encode("utf-8")
    document_parts = write_gzip_b64_parts(
        output / "starintel-documents.jsonl.gz.b64", jsonl
    )
    counts = Counter(doc["dtype"] for doc in docs)
    manifest = {
        "committee_id": committee_id,
        "counts": dict(sorted(counts.items())),
        "cycle": cycle,
        "dataset": DATASET,
        "document_part_count": len(document_parts),
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "generated_at": when,
        "identity_resolution": "source-scoped name+city+state+postal key; postal value not emitted",
        "postal_codes_emitted": False,
        "raw_matching_rows": len(rows),
        "raw_source_members": members,
        "raw_source_psv_part_count": len(source_parts),
        "raw_source_psv_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "raw_source_zip_sha256": file_sha256(zip_path),
        "reconciliation": "none; all raw amendment and memo rows preserved",
        "schema_version": "0.9.0",
        "total_documents": len(docs),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "README.md").write_text(
        f"""# DNC FEC people, employers, and individual contributions — {cycle} cycle

Official FEC `indiv{str(cycle)[-2:]}.zip` rows filtered to `{committee_id}`.

- raw matching rows: {len(rows):,}
- StarIntel documents: {len(docs):,}
- source-scoped people: {counts.get('person', 0):,}
- organizations: {counts.get('org', 0):,}
- reported employment/status records: {counts.get('employment', 0):,}
- campaign-finance records: {counts.get('campaign-finance', 0):,}
- graph relations: {counts.get('relation', 0):,}

Every amendment and memo row is retained. Contributions are not netted or treated as unique donors. Employer and occupation values are filer-reported and remain unverified. Postal codes are used only to separate source-scoped identities and are not emitted in the corpus.

```bash
python3 scripts/import_dnc_fec_individual_contributions.py
python3 scripts/validate-for-merge.py --site
```
""",
        encoding="utf-8",
    )


def main() -> int:
    ns = parse_args()
    if ns.cycle % 2:
        raise RuntimeError("FEC cycle must be an even-numbered election cycle")
    with tempfile.TemporaryDirectory(prefix="dnc-fec-individual-") as tmp:
        zip_path = Path(tmp) / f"indiv{str(ns.cycle)[-2:]}.zip"
        if ns.offline_zip:
            shutil.copy2(ns.offline_zip, zip_path)
        else:
            download(bulk_url(ns.cycle), zip_path)
        members, rows = matching_rows(zip_path, ns.committee_id)
        source = source_id(ns.cycle, ns.committee_id)
        docs = build(rows, ns.cycle, ns.committee_id, ns.generated_at, source)
        write(
            ns.output,
            zip_path,
            members,
            rows,
            docs,
            ns.cycle,
            ns.committee_id,
            ns.generated_at,
        )
    print(
        json.dumps(
            {
                "documents": len(docs),
                "output": str(ns.output),
                "raw_rows": len(rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
