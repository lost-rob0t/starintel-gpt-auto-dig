#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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
from collections import Counter
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
GENERATED_AT = "2026-07-31T06:45:00Z"
CYCLE = 2026
OUTPUT = Path("digs/dnc/2026-07-31-fec-operating-expenditures-2026")
DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/"
BULK_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/oppexp{yy}.zip"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_DOWNLOAD = 1_500_000_000
MAX_MATCHING_ROWS = 50_000
FIELDS = [
    "CMTE_ID", "AMNDT_IND", "RPT_YR", "RPT_TP", "IMAGE_NUM", "LINE_NUM",
    "FORM_TP_CD", "SCHED_TP_CD", "NAME", "CITY", "STATE", "ZIP_CODE",
    "TRANSACTION_DT", "TRANSACTION_AMT", "TRANSACTION_PGI", "PURPOSE",
    "CATEGORY", "CATEGORY_DESC", "MEMO_CD", "MEMO_TEXT", "ENTITY_TP",
    "SUB_ID", "FILE_NUM", "TRAN_ID", "BACK_REF_TRAN_ID",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import DNC FEC operating expenditures")
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


def sha_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return f"starintel:{prefix}:{hashlib.sha256(raw).hexdigest()}"


def source_id(cycle: int, committee_id: str) -> str:
    return f"starintel:source:fec-oppexp-{cycle}-dnc-{committee_id.lower()}"


def bulk_url(cycle: int) -> str:
    return BULK_URL.format(cycle=cycle, yy=str(cycle)[-2:])


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise RuntimeError("FEC bulk download exceeds safety limit")
            handle.write(chunk)


def zip_member(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            info for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
        if not candidates:
            raise RuntimeError("FEC ZIP contains no text data file")
        return max(candidates, key=lambda info: info.file_size).filename


def rows(path: Path, committee_id: str) -> tuple[str, list[dict[str, str]]]:
    member = zip_member(path)
    matched: list[dict[str, str]] = []
    seen_sub_ids: set[str] = set()
    with zipfile.ZipFile(path) as archive, archive.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
        for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
            if len(values) == len(FIELDS) + 1 and values[-1] == "":
                values.pop()
            if len(values) != len(FIELDS):
                raise RuntimeError(f"unexpected FEC row width at {line_no}: {len(values)}")
            row = dict(zip(FIELDS, values, strict=True))
            if row["CMTE_ID"] != committee_id:
                continue
            sub_id = row["SUB_ID"].strip()
            if not sub_id:
                raise RuntimeError(f"matching row {line_no} has no SUB_ID")
            if sub_id in seen_sub_ids:
                raise RuntimeError(f"duplicate FEC SUB_ID in bulk file: {sub_id}")
            seen_sub_ids.add(sub_id)
            matched.append(row)
            if len(matched) > MAX_MATCHING_ROWS:
                raise RuntimeError("matching FEC rows exceed safety limit")
    if not matched:
        raise RuntimeError(f"no operating expenditures found for {committee_id}")
    return member, matched


def iso_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    for date_format in ("%m%d%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format).strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            continue
    raise RuntimeError(f"invalid FEC date {value!r}")


def amount(value: str) -> float:
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
    verified: bool = True,
    status: str = "official-filing-record",
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
            "pii": dtype == "person",
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "operating-expenditure", dtype],
        "title": title,
        "verification": {
            "last_reviewed_at": when,
            "status": status,
            "verified": verified,
        },
        "version": 1,
    }


def payee_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row["ENTITY_TP"].strip().upper() or "UNK",
        norm(row["NAME"]),
        norm(row["CITY"]),
        row["STATE"].strip().upper(),
        row["ZIP_CODE"].strip(),
    )


def payee_doc(row: dict[str, str], when: str, source: str, committee_id: str) -> dict[str, Any]:
    entity_type, name_key, city_key, state, postal = payee_key(row)
    name = re.sub(r"\s+", " ", row["NAME"]).strip() or "Unspecified FEC payee"
    digest = hashlib.sha256(
        "\x1f".join((entity_type, name_key, city_key, state, postal)).encode()
    ).hexdigest()
    dtype = "person" if entity_type == "IND" else "org"
    doc_id = f"starintel:{dtype}:fec-payee-{digest}"
    if dtype == "person":
        data: dict[str, Any] = {
            "full_name": name,
            "name": name,
            "public_roles": ["FEC-reported DNC operating-expenditure payee"],
        }
    else:
        data = {"name": name, "org_type": "fec_reported_payee"}
    return base(
        doc_id,
        dtype,
        name,
        f"Source-scoped unresolved payee identity reported in the FEC operating-expenditure file for {committee_id}.",
        data,
        when,
        source,
        verified=False,
        status="source-scoped-unresolved-identity",
    )


def identifiers(row: dict[str, str]) -> list[dict[str, Any]]:
    out = [
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
            out.append(
                {
                    "scheme": scheme,
                    "value": value,
                    "issuer": "Federal Election Commission",
                    "canonical": False,
                }
            )
    return out


def row_metadata(row: dict[str, str]) -> dict[str, Any]:
    return {key.lower(): value for key, value in row.items() if value != ""}


def build(
    fec_rows: list[dict[str, str]],
    cycle: int,
    when: str,
    source: str,
    committee_id: str,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    emitted: set[str] = set()
    payees: dict[tuple[str, str, str, str, str], str] = {}

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
        f"FEC {cycle} operating expenditures bulk file — {committee_id}",
        "Official FEC bulk operating-expenditure rows filtered to the DNC committee. Every amendment and memo row is preserved without reconciliation.",
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

    for row in fec_rows:
        key = payee_key(row)
        if key not in payees:
            doc = payee_doc(row, when, source, committee_id)
            payees[key] = doc["_id"]
            emit(doc)
        payee_id = payees[key]
        sub_id = row["SUB_ID"]
        transaction_date = iso_date(row["TRANSACTION_DT"])
        transaction_amount = amount(row["TRANSACTION_AMT"])
        raw_meta = row_metadata(row)
        qualifications = [
            "Raw FEC bulk row; amendment chains, memo entries, refunds, and subitemizations are not netted or deduplicated."
        ]
        if row["AMNDT_IND"] == "A":
            qualifications.append("This row was reported in an amended filing.")
        if row["MEMO_CD"] == "X":
            qualifications.append(
                "FEC memo code X indicates the amount is not included in the itemization total."
            )

        financial_id = f"starintel:financial-observation:fec-oppexp-{sub_id}"
        financial = base(
            financial_id,
            "financial-observation",
            f"FEC operating expenditure {sub_id}: {row['NAME'].strip() or 'unspecified payee'}",
            f"Official FEC row reports a ${transaction_amount:,.2f} operating expenditure by the DNC to the named payee; amendment and memo semantics remain attached to the row.",
            {
                "amount": transaction_amount,
                "counterparty_ids": [payee_id],
                "currency": "USD",
                "entity_id": DNC_ID,
                "methodology": "Direct row import from the official FEC operating-expenditures bulk file.",
                "observation_type": "reported_operating_expenditure",
                "period_end": transaction_date,
                "period_start": transaction_date,
                "qualifications": qualifications,
                "reported_at": None,
                "value_type": "reported_transaction_amount",
            },
            when,
            source,
        )
        financial["identifiers"] = identifiers(row)
        financial["sources"] = [
            {
                "source_id": source,
                "locator": f"SUB_ID {sub_id}",
                "metadata": raw_meta,
            }
        ]
        emit(financial)

        relation = base(
            sha_id(
                "relation",
                DNC_ID,
                "reported_operating_expenditure_to",
                payee_id,
                sub_id,
            ),
            "relation",
            f"DNC reported operating expenditure to {row['NAME'].strip() or 'unspecified payee'}",
            f"FEC row {sub_id} reports a ${transaction_amount:,.2f} operating expenditure to the named payee.",
            {
                "confidence": 0.99,
                "directed": True,
                "object": payee_id,
                "predicate": "reported_operating_expenditure_to",
                "qualifiers": {
                    "amount": transaction_amount,
                    "currency": "USD",
                    "transaction_date": transaction_date,
                    **raw_meta,
                    "raw_row_preserved": True,
                    "reconciled": False,
                },
                "subject": DNC_ID,
            },
            when,
            source,
        )
        relation["related_ids"] = [financial_id]
        emit(relation)

    return sorted(docs, key=lambda doc: doc["_id"])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(
    output: Path,
    zip_path: Path,
    member: str,
    fec_rows: list[dict[str, str]],
    docs: list[dict[str, Any]],
    cycle: int,
    committee_id: str,
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    psv = io.StringIO()
    writer = csv.DictWriter(psv, fieldnames=FIELDS, delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerows(fec_rows)
    psv_bytes = psv.getvalue().encode("utf-8")
    (output / f"source/dnc-oppexp-{cycle}.psv").write_bytes(psv_bytes)
    jsonl = "".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"
        for doc in docs
    ).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(jsonl)
    counts = Counter(doc["dtype"] for doc in docs)
    manifest = {
        "committee_id": committee_id,
        "counts": dict(sorted(counts.items())),
        "cycle": cycle,
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "generated_at": when,
        "raw_matching_rows": len(fec_rows),
        "raw_source_member": member,
        "raw_source_psv_sha256": hashlib.sha256(psv_bytes).hexdigest(),
        "raw_source_zip_sha256": file_sha256(zip_path),
        "reconciliation": "none; all raw amendment and memo rows preserved",
        "schema_version": "0.9.0",
        "total_documents": len(docs),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        f"""# DNC FEC operating expenditures — {cycle} cycle

Official FEC `oppexp{str(cycle)[-2:]}.zip` rows filtered to `{committee_id}`.

- raw matching rows: {len(fec_rows):,}
- StarIntel documents: {len(docs):,}
- payee people: {counts.get('person', 0):,}
- payee organizations: {counts.get('org', 0):,}
- financial observations: {counts.get('financial-observation', 0):,}
- graph relations: {counts.get('relation', 0):,}

This corpus preserves every raw amendment and memo row. It is not a netted or audited total. Payee identities are source-scoped and unresolved unless separately corroborated.

```bash
python3 scripts/import_dnc_fec_oppexp.py
python3 scripts/validate-for-merge.py --site
```
""",
        encoding="utf-8",
    )


def main() -> int:
    ns = parse_args()
    if ns.cycle % 2:
        raise RuntimeError("FEC cycle must be an even-numbered election cycle")
    with tempfile.TemporaryDirectory(prefix="dnc-fec-") as tmp:
        zip_path = Path(tmp) / f"oppexp{str(ns.cycle)[-2:]}.zip"
        if ns.offline_zip:
            shutil.copy2(ns.offline_zip, zip_path)
        else:
            download(bulk_url(ns.cycle), zip_path)
        member, fec_rows = rows(zip_path, ns.committee_id)
        source = source_id(ns.cycle, ns.committee_id)
        docs = build(fec_rows, ns.cycle, ns.generated_at, source, ns.committee_id)
        write(
            ns.output,
            zip_path,
            member,
            fec_rows,
            docs,
            ns.cycle,
            ns.committee_id,
            ns.generated_at,
        )
    print(
        json.dumps(
            {
                "documents": len(docs),
                "raw_rows": len(fec_rows),
                "output": str(ns.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
