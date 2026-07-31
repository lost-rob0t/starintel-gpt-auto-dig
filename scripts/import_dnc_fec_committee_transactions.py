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
CYCLE = 2026
GENERATED_AT = "2026-07-31T08:15:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-committee-transactions-2026")
OTH_DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/"
CM_DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/committee-master-file-description/"
OTH_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/oth{yy}.zip"
CM_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cm{yy}.zip"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_DOWNLOAD = 3_000_000_000
MAX_MATCHING_ROWS = 250_000
PART_SIZE = 30_000_000
OTH_FIELDS = [
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
CM_FIELDS = [
    "CMTE_ID",
    "CMTE_NM",
    "TRES_NM",
    "CMTE_ST1",
    "CMTE_ST2",
    "CMTE_CITY",
    "CMTE_ST",
    "CMTE_ZIP",
    "CMTE_DSGN",
    "CMTE_TP",
    "CMTE_PTY_AFFILIATION",
    "CMTE_FILING_FREQ",
    "ORG_TP",
    "CONNECTED_ORG_NM",
    "CAND_ID",
]
PUBLIC_OTH_FIELDS = [field for field in OTH_FIELDS if field != "ZIP_CODE"]
PUBLIC_CM_FIELDS = [
    field for field in CM_FIELDS if field not in {"CMTE_ST1", "CMTE_ST2", "CMTE_ZIP"}
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import DNC-linked committee transactions, committees, treasurers, and connected organizations"
    )
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--committee-id", default=COMMITTEE_ID)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--offline-oth-zip", type=Path)
    parser.add_argument("--offline-cm-zip", type=Path)
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


def oth_url(cycle: int) -> str:
    return OTH_URL.format(cycle=cycle, yy=str(cycle)[-2:])


def cm_url(cycle: int) -> str:
    return CM_URL.format(cycle=cycle, yy=str(cycle)[-2:])


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
                raise RuntimeError(f"download exceeds safety limit: {url}")
            handle.write(chunk)


def members(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        values = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
    if not values:
        raise RuntimeError(f"ZIP contains no text data files: {path}")
    return sorted(values)


def parse_zip_rows(path: Path, fields: list[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        for member in members(path):
            with archive.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
                    if len(values) == len(fields) + 1 and values[-1] == "":
                        values.pop()
                    if len(values) != len(fields):
                        raise RuntimeError(
                            f"unexpected row width in {member}:{line_no}: {len(values)}"
                        )
                    result.append(dict(zip(fields, values, strict=True)))
    return result


def matching_oth_rows(path: Path, committee_id: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for member in members(path):
            with archive.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
                    if len(values) == len(OTH_FIELDS) + 1 and values[-1] == "":
                        values.pop()
                    if len(values) != len(OTH_FIELDS):
                        raise RuntimeError(
                            f"unexpected OTH row width in {member}:{line_no}: {len(values)}"
                        )
                    row = dict(zip(OTH_FIELDS, values, strict=True))
                    if row["CMTE_ID"] != committee_id and row["OTHER_ID"] != committee_id:
                        continue
                    sub_id = row["SUB_ID"].strip()
                    if not sub_id:
                        raise RuntimeError(f"matching OTH row {member}:{line_no} has no SUB_ID")
                    if sub_id in seen:
                        raise RuntimeError(f"duplicate FEC OTH SUB_ID: {sub_id}")
                    seen.add(sub_id)
                    result.append(row)
                    if len(result) > MAX_MATCHING_ROWS:
                        raise RuntimeError("matching OTH rows exceed safety limit")
    if not result:
        raise RuntimeError(f"no OTH transactions found for {committee_id}")
    return result


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
    sources: list[str],
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
        "sources": [{"source_id": source_id} for source_id in sources],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "committee-transaction", dtype],
        "title": title,
        "verification": {
            "last_reviewed_at": when,
            "status": status,
            "verified": verified,
        },
        "version": 1,
    }


def committee_doc_id(committee_id: str) -> str:
    return DNC_ID if committee_id == COMMITTEE_ID else f"starintel:org:fec-committee-{committee_id.lower()}"


def public_oth(row: dict[str, str]) -> dict[str, str]:
    return {field.lower(): row[field] for field in PUBLIC_OTH_FIELDS if row[field] != ""}


def public_cm(row: dict[str, str]) -> dict[str, str]:
    return {field.lower(): row[field] for field in PUBLIC_CM_FIELDS if row[field] != ""}


def counterparty_id(row: dict[str, str]) -> str:
    other_id = row["OTHER_ID"].strip()
    if other_id:
        return committee_doc_id(other_id)
    entity = row["ENTITY_TP"].strip().upper() or "UNK"
    dtype = "person" if entity in {"IND", "CAN"} else "org"
    return sha_id(
        f"{dtype}:fec-oth-counterparty",
        entity,
        norm(row["NAME"]),
        norm(row["CITY"]),
        row["STATE"].strip().upper(),
        row["ZIP_CODE"].strip(),
    )


def build(
    oth_rows: list[dict[str, str]],
    committee_master: dict[str, dict[str, str]],
    cycle: int,
    committee_id: str,
    when: str,
    oth_source: str,
    cm_source: str,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    emitted: set[str] = set()

    def emit(doc: dict[str, Any]) -> None:
        if doc["_id"] in emitted:
            raise RuntimeError(f"duplicate generated ID: {doc['_id']}")
        validate_document(doc)
        emitted.add(doc["_id"])
        docs.append(doc)

    for source_id, title, uri, kind in (
        (
            oth_source,
            f"FEC {cycle} transactions among committees — DNC filtered",
            oth_url(cycle),
            "official_fec_oth_bulk_file",
        ),
        (
            cm_source,
            f"FEC {cycle} committee master — DNC-linked committees",
            cm_url(cycle),
            "official_fec_committee_master",
        ),
    ):
        doc = base(
            source_id,
            "source",
            title,
            "Official FEC bulk source used to resolve DNC-linked federal committee transactions and committee metadata.",
            {
                "accessed_at": when,
                "credibility": 0.99,
                "kind": kind,
                "publisher": "Federal Election Commission",
                "uri": uri,
            },
            when,
            [],
        )
        emit(doc)

    linked_committee_ids = {committee_id}
    for row in oth_rows:
        linked_committee_ids.add(row["CMTE_ID"])
        if row["OTHER_ID"].strip():
            linked_committee_ids.add(row["OTHER_ID"].strip())

    for cid in sorted(linked_committee_ids):
        record = committee_master.get(cid)
        if cid == committee_id:
            continue
        name = clean(record["CMTE_NM"]) if record else cid
        data: dict[str, Any] = {
            "name": name,
            "org_type": f"fec_registered_committee_{clean(record['CMTE_TP']).lower()}" if record else "fec_registered_committee",
            "registration_number": cid,
        }
        if record:
            if clean(record["CMTE_PTY_AFFILIATION"]):
                data["professional_affiliations"] = [clean(record["CMTE_PTY_AFFILIATION"])]
        doc = base(
            committee_doc_id(cid),
            "org",
            name,
            "Federal committee connected to the DNC through an official FEC committee-to-committee transaction record.",
            data,
            when,
            [cm_source] if record else [oth_source],
            verified=record is not None,
            status="official-fec-committee-master" if record else "source-scoped-unresolved-committee",
        )
        doc["identifiers"] = [
            {
                "scheme": "fec_committee_id",
                "value": cid,
                "issuer": "Federal Election Commission",
                "canonical": True,
            }
        ]
        if record:
            doc["sources"] = [
                {
                    "source_id": cm_source,
                    "locator": cid,
                    "metadata": public_cm(record),
                }
            ]
        emit(doc)

        if not record:
            continue
        treasurer = clean(record["TRES_NM"])
        if treasurer:
            person_id = sha_id("person:fec-committee-treasurer", cid, norm(treasurer))
            emit(
                base(
                    person_id,
                    "person",
                    treasurer,
                    f"Treasurer name reported for {name} in the FEC committee master file.",
                    {
                        "full_name": treasurer,
                        "name": treasurer,
                        "public_roles": [f"Treasurer of {name}"],
                    },
                    when,
                    [cm_source],
                    verified=False,
                    status="source-scoped-officer-name",
                    pii=True,
                )
            )
            employment_id = sha_id("employment:fec-committee-role", person_id, committee_doc_id(cid), "treasurer")
            emit(
                base(
                    employment_id,
                    "employment",
                    f"Treasurer role: {treasurer} / {name}",
                    "Committee officer role reported in the FEC committee master file; compensation and current employment status are not inferred.",
                    {
                        "employment_type": "fec_reported_committee_officer",
                        "organization_id": committee_doc_id(cid),
                        "person_id": person_id,
                        "title": "Treasurer",
                    },
                    when,
                    [cm_source],
                    verified=False,
                    status="official-record-role-unresolved-identity",
                    pii=True,
                )
            )
            relation = base(
                sha_id("relation", person_id, "treasurer_of", committee_doc_id(cid)),
                "relation",
                f"{treasurer} — treasurer of {name}",
                "Treasurer relation reported by the FEC committee master file.",
                {
                    "confidence": 0.98,
                    "directed": True,
                    "object": committee_doc_id(cid),
                    "predicate": "treasurer_of",
                    "qualifiers": {"employment_document_id": employment_id},
                    "subject": person_id,
                },
                when,
                [cm_source],
                pii=True,
            )
            relation["related_ids"] = [employment_id]
            emit(relation)

        connected_name = clean(record["CONNECTED_ORG_NM"])
        if connected_name:
            connected_id = sha_id("org:fec-connected-organization", norm(connected_name))
            if connected_id not in emitted:
                emit(
                    base(
                        connected_id,
                        "org",
                        connected_name,
                        "Connected organization name reported in the FEC committee master file; legal-entity resolution remains pending.",
                        {"name": connected_name, "org_type": "fec_reported_connected_organization"},
                        when,
                        [cm_source],
                        verified=False,
                        status="source-scoped-unresolved-identity",
                    )
                )
            emit(
                base(
                    sha_id("relation", committee_doc_id(cid), "reported_connected_organization", connected_id),
                    "relation",
                    f"{name} — reported connected organization: {connected_name}",
                    "Connected-organization relation reported in the FEC committee master file.",
                    {
                        "confidence": 0.98,
                        "directed": True,
                        "object": connected_id,
                        "predicate": "reported_connected_organization",
                        "subject": committee_doc_id(cid),
                    },
                    when,
                    [cm_source],
                )
            )

    for row in oth_rows:
        filer_id = committee_doc_id(row["CMTE_ID"])
        other_id = counterparty_id(row)
        if other_id not in emitted and other_id != DNC_ID:
            dtype = "person" if row["ENTITY_TP"].strip().upper() in {"IND", "CAN"} else "org"
            name = clean(row["NAME"]) or "Unspecified FEC transaction counterparty"
            data = (
                {"full_name": name, "name": name, "public_roles": ["FEC-reported committee transaction counterparty"]}
                if dtype == "person"
                else {"name": name, "org_type": "fec_oth_transaction_counterparty"}
            )
            emit(
                base(
                    other_id,
                    dtype,
                    name,
                    "Source-scoped counterparty identity in an official FEC transaction-among-committees record.",
                    data,
                    when,
                    [oth_source],
                    verified=False,
                    status="source-scoped-unresolved-identity",
                    pii=dtype == "person",
                )
            )

        sub_id = row["SUB_ID"]
        tx_date = iso_date(row["TRANSACTION_DT"])
        tx_amount = numeric_amount(row["TRANSACTION_AMT"])
        metadata = public_oth(row)
        qualifications = [
            "Raw FEC OTH row; transaction direction is not inferred solely from the transaction code.",
            "Amendments and memo entries are preserved and not netted.",
        ]
        if row["AMNDT_IND"] == "A":
            qualifications.append("This row was reported in an amended filing.")
        if row["MEMO_CD"] == "X":
            qualifications.append("This row carries FEC memo code X.")

        finance_id = f"starintel:campaign-finance:fec-oth-{sub_id}"
        finance = base(
            finance_id,
            "campaign-finance",
            f"FEC committee transaction {sub_id}",
            f"Official FEC OTH row reports a ${tx_amount:,.2f} transaction involving {row['CMTE_ID']} and the named counterparty.",
            {
                "amount": tx_amount,
                "committee_id": row["CMTE_ID"],
                "contribution_type": row["TRANSACTION_TP"].strip() or "reported_committee_transaction",
                "counterparty_ids": [other_id],
                "currency": "USD",
                "election_cycle": str(cycle),
                "entity_id": filer_id,
                "filing_id": row["FILE_NUM"].strip(),
                "methodology": "Direct row import from the official FEC OTH bulk file.",
                "observation_type": "reported_committee_transaction",
                "period_end": tx_date,
                "period_start": tx_date,
                "qualifications": qualifications,
                "reported_at": None,
                "value_type": "reported_transaction_amount",
            },
            when,
            [oth_source],
        )
        finance["identifiers"] = [
            {
                "scheme": "fec_sub_id",
                "value": sub_id,
                "issuer": "Federal Election Commission",
                "canonical": True,
            }
        ]
        finance["sources"] = [
            {
                "source_id": oth_source,
                "locator": f"SUB_ID {sub_id}",
                "metadata": metadata,
            }
        ]
        emit(finance)

        relation = base(
            sha_id("relation", filer_id, "reported_committee_transaction_between", other_id, sub_id),
            "relation",
            f"Reported committee transaction: {row['CMTE_ID']} / {clean(row['NAME']) or row['OTHER_ID']}",
            "Official FEC OTH record connecting the filer committee and counterparty; direction remains encoded only in the raw transaction fields.",
            {
                "confidence": 0.99,
                "directed": False,
                "object": other_id,
                "predicate": "reported_committee_transaction_between",
                "qualifiers": {
                    "amount": tx_amount,
                    "currency": "USD",
                    "transaction_date": tx_date,
                    **metadata,
                    "postal_code_emitted": False,
                    "raw_row_preserved": True,
                    "reconciled": False,
                },
                "subject": filer_id,
            },
            when,
            [oth_source],
        )
        relation["related_ids"] = [finance_id]
        emit(relation)

    return sorted(docs, key=lambda doc: doc["_id"])


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(
    output: Path,
    oth_zip: Path,
    cm_zip: Path,
    oth_rows: list[dict[str, str]],
    linked_cm_rows: list[dict[str, str]],
    docs: list[dict[str, Any]],
    cycle: int,
    committee_id: str,
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)

    oth_buffer = io.StringIO()
    oth_writer = csv.DictWriter(
        oth_buffer, fieldnames=PUBLIC_OTH_FIELDS, delimiter="|", lineterminator="\n"
    )
    oth_writer.writeheader()
    for row in oth_rows:
        oth_writer.writerow({field: row[field] for field in PUBLIC_OTH_FIELDS})
    oth_bytes = oth_buffer.getvalue().encode("utf-8")
    oth_parts = write_gzip_b64_parts(
        output / "source" / f"dnc-committee-transactions-{cycle}.psv.gz.b64",
        oth_bytes,
    )

    cm_buffer = io.StringIO()
    cm_writer = csv.DictWriter(
        cm_buffer, fieldnames=PUBLIC_CM_FIELDS, delimiter="|", lineterminator="\n"
    )
    cm_writer.writeheader()
    for row in linked_cm_rows:
        cm_writer.writerow({field: row[field] for field in PUBLIC_CM_FIELDS})
    cm_bytes = cm_buffer.getvalue().encode("utf-8")
    cm_parts = write_gzip_b64_parts(
        output / "source" / f"dnc-linked-committee-master-{cycle}.psv.gz.b64",
        cm_bytes,
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
        "linked_committee_master_rows": len(linked_cm_rows),
        "postal_codes_emitted": False,
        "raw_matching_rows": len(oth_rows),
        "raw_oth_part_count": len(oth_parts),
        "raw_oth_sha256": hashlib.sha256(oth_bytes).hexdigest(),
        "raw_oth_zip_sha256": file_sha256(oth_zip),
        "raw_committee_master_part_count": len(cm_parts),
        "raw_committee_master_sha256": hashlib.sha256(cm_bytes).hexdigest(),
        "raw_committee_master_zip_sha256": file_sha256(cm_zip),
        "reconciliation": "none; all raw amendment and memo rows preserved",
        "schema_version": "0.9.0",
        "total_documents": len(docs),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "README.md").write_text(
        f"""# DNC FEC committee transactions and officers — {cycle} cycle

Official FEC `oth{str(cycle)[-2:]}.zip` records where `{committee_id}` is the filer or identified counterparty, joined to `cm{str(cycle)[-2:]}.zip` committee-master records.

- raw matching committee transactions: {len(oth_rows):,}
- linked committee-master rows: {len(linked_cm_rows):,}
- StarIntel documents: {len(docs):,}
- people and committee officers: {counts.get('person', 0):,}
- organizations: {counts.get('org', 0):,}
- committee-role records: {counts.get('employment', 0):,}
- campaign-finance records: {counts.get('campaign-finance', 0):,}
- graph relations: {counts.get('relation', 0):,}

Transaction direction is not guessed from ambiguous transaction codes. Every amendment and memo row remains distinct. Postal codes and committee street addresses are not emitted.

```bash
python3 scripts/import_dnc_fec_committee_transactions.py
python3 scripts/validate-for-merge.py --site
```
""",
        encoding="utf-8",
    )


def main() -> int:
    ns = parse_args()
    if ns.cycle % 2:
        raise RuntimeError("FEC cycle must be an even-numbered election cycle")
    with tempfile.TemporaryDirectory(prefix="dnc-fec-committee-") as tmp:
        oth_zip = Path(tmp) / f"oth{str(ns.cycle)[-2:]}.zip"
        cm_zip = Path(tmp) / f"cm{str(ns.cycle)[-2:]}.zip"
        if ns.offline_oth_zip:
            shutil.copy2(ns.offline_oth_zip, oth_zip)
        else:
            download(oth_url(ns.cycle), oth_zip)
        if ns.offline_cm_zip:
            shutil.copy2(ns.offline_cm_zip, cm_zip)
        else:
            download(cm_url(ns.cycle), cm_zip)

        oth_rows = matching_oth_rows(oth_zip, ns.committee_id)
        all_cm_rows = parse_zip_rows(cm_zip, CM_FIELDS)
        committee_master = {row["CMTE_ID"]: row for row in all_cm_rows}
        linked_ids = {ns.committee_id}
        for row in oth_rows:
            linked_ids.add(row["CMTE_ID"])
            if row["OTHER_ID"].strip():
                linked_ids.add(row["OTHER_ID"].strip())
        linked_cm_rows = [committee_master[cid] for cid in sorted(linked_ids) if cid in committee_master]

        oth_source = f"starintel:source:fec-oth-{ns.cycle}-{ns.committee_id.lower()}"
        cm_source = f"starintel:source:fec-committee-master-{ns.cycle}-dnc-linked"
        docs = build(
            oth_rows,
            committee_master,
            ns.cycle,
            ns.committee_id,
            ns.generated_at,
            oth_source,
            cm_source,
        )
        write(
            ns.output,
            oth_zip,
            cm_zip,
            oth_rows,
            linked_cm_rows,
            docs,
            ns.cycle,
            ns.committee_id,
            ns.generated_at,
        )
    print(
        json.dumps(
            {
                "documents": len(docs),
                "linked_committees": len(linked_cm_rows),
                "output": str(ns.output),
                "raw_rows": len(oth_rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
