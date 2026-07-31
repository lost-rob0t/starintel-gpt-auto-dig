#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO, TextIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
CYCLE = 2026
GENERATED_AT = "2026-07-31T23:42:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-democratic-committee-transactions-2026")
OTH_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/oth{yy}.zip"
CM_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cm{yy}.zip"
OTH_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/"
CM_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/committee-master-file-description/"
PARTY_CODES_URL = "https://www.fec.gov/campaign-finance-data/party-code-descriptions/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
RUN_ID = "dnc-fec-democratic-committee-transactions-2026-07-31"
PARTY_CODES = {"DEM", "DFL"}
MAX_DOWNLOAD = 1_500_000_000
MAX_MATCHING_ROWS = 1_000_000
MAX_PAIR_TARGETS = 150_000
PARTITIONS = 128

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

OUT_OF_SCOPE = [
    "private residential addresses",
    "private contact information",
    "credentials or access tokens",
    "non-public personal data",
    "unsupported criminal conclusions",
]
EXCLUDED_SOURCES = [
    "unsourced reposts",
    "anonymous claims without underlying artifacts",
    "people-search or data-broker profiles",
]
PREFERRED_SOURCES = [
    "Federal Election Commission filings, report images, and bulk data",
    "official committee, candidate, party, campaign, corporate, nonprofit, union, and government records",
    "state campaign-finance records, court records, archives, and established reporting",
]

PAIR_AXES = (
    {
        "key": "amendment-reconciliation",
        "label": "amendment chain, report images, memo treatment, and reconciliation",
        "target_type": "fec_committee_pair_amendment_reconciliation",
        "penalty": 0.00,
        "question": "What complete filing, amendment, memo, refund, attribution, subitemization, report-image, and reconciliation history governs the reported FEC transactions between {filer} and {counterparty}?",
        "objectives": [
            "Acquire every underlying report, amendment, schedule, image, memo, refund, attribution, and related filing row",
            "Group records by committee, report, transaction ID, image, and amendment chain without silently discarding superseded or memo rows",
            "Determine transaction direction, legal category, election designation, paid versus accrued status, and final reconciled treatment",
            "Publish raw-row and reconciled views separately with transparent calculations and unresolved discrepancies",
        ],
        "next": "Fetch all linked filing images and amendment chains and build a transparent row-level reconciliation ledger",
    },
    {
        "key": "officers-affiliations-shared-infrastructure",
        "label": "officers, affiliations, joint fundraising, and shared infrastructure",
        "target_type": "fec_committee_pair_officers_affiliations",
        "penalty": 0.005,
        "question": "Which candidates, officers, treasurers, staff, consultants, connected organizations, joint-fundraising agreements, vendors, data systems, counsel, and other shared infrastructure connect {filer} and {counterparty}?",
        "objectives": [
            "Acquire each committee's complete registration, amendment, officer, treasurer, connected-organization, and candidate-linkage history",
            "Map joint fundraising, affiliated committees, transfers, shared addresses, shared staff, shared vendors, counsel, compliance, fundraising, data, media, technology, and payment infrastructure",
            "Trace every principal to campaigns, party committees, public offices, agencies, nonprofits, unions, companies, and lobbying clients",
            "Distinguish formal affiliation, authorization, and joint fundraising from common-vendor correlation",
        ],
        "next": "Join committee registrations, candidate linkages, joint-fundraising notices, officers, vendors, and transfer records across cycles",
    },
    {
        "key": "network-context",
        "label": "wider money-flow, candidate, party, and institutional network",
        "target_type": "fec_committee_pair_network_context",
        "penalty": 0.01,
        "question": "How do the reported transactions between {filer} and {counterparty} fit into the wider network of Democratic candidates, party committees, PACs, donors, vendors, nonprofits, unions, companies, public officials, and coordinated campaigns?",
        "objectives": [
            "Map all inbound and outbound committee transactions for both endpoints across election cycles",
            "Identify recurring counterparties, transaction sequences, joint fundraising distributions, coordinated-party flows, candidate support, refunds, and pass-through patterns",
            "Connect transaction dates to elections, endorsements, conventions, leadership changes, litigation, public events, and program launches",
            "Separate measured transaction facts and network structure from hypotheses about coordination, intent, or control",
        ],
        "next": "Build amendment-aware multi-hop money-flow and timing views for both committees and resolve every high-value counterparty",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FEC committee transactions involving DEM or DFL committees")
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-oth-zip", type=Path)
    parser.add_argument("--offline-cm-zip", type=Path)
    return parser.parse_args()


def cycle_url(template: str, cycle: int) -> str:
    return template.format(cycle=cycle, yy=str(cycle)[-2:])


def sha_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:{prefix}:{digest}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=240) as response, path.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise RuntimeError(f"download exceeds safety cap: {url}")
            handle.write(chunk)


def copy_or_download(offline: Path | None, url: str, destination: Path) -> None:
    if offline:
        shutil.copy2(offline, destination)
    else:
        download(url, destination)


def largest_text_member(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))]
        if not members:
            raise RuntimeError(f"ZIP contains no text member: {path}")
        return max(members, key=lambda info: info.file_size).filename


def normalized_values(values: list[str], expected: int, member: str, line_number: int) -> list[str]:
    if len(values) == expected + 1 and values[-1] == "":
        values.pop()
    if len(values) != expected:
        raise RuntimeError(f"unexpected row width in {member} at line {line_number}: {len(values)}")
    return values


def read_committee_master(path: Path) -> tuple[str, dict[str, dict[str, str]], set[str], int]:
    member = largest_text_member(path)
    committees: dict[str, dict[str, str]] = {}
    democratic_ids: set[str] = set()
    total = 0
    with zipfile.ZipFile(path) as archive, archive.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
        for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
            values = normalized_values(values, len(CM_FIELDS), member, line_number)
            row = dict(zip(CM_FIELDS, values, strict=True))
            committee_id = row["CMTE_ID"].strip()
            if not committee_id:
                raise RuntimeError(f"committee-master row {line_number} lacks committee ID")
            if committee_id in committees:
                raise RuntimeError(f"duplicate committee ID in committee master: {committee_id}")
            committees[committee_id] = row
            total += 1
            if row["CMTE_PTY_AFFILIATION"].strip().upper() in PARTY_CODES:
                democratic_ids.add(committee_id)
    if not democratic_ids:
        raise RuntimeError("committee master yielded no DEM or DFL committee IDs")
    return member, committees, democratic_ids, total


def source_document(
    *,
    document_id: str,
    title: str,
    summary: str,
    uri: str,
    description_uri: str,
    member: str,
    file_sha: str,
    total_rows: int | None,
    matching_rows: int | None,
    when: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "accessed_at": when,
        "archive_member": member,
        "credibility": 1.0,
        "description_uri": description_uri,
        "file_sha256": file_sha,
        "kind": "official_fec_bulk_data",
        "publisher": "Federal Election Commission",
        "uri": uri,
    }
    if total_rows is not None:
        data["record_count"] = total_rows
    if matching_rows is not None:
        data["matching_record_count"] = matching_rows
    document = {
        "_id": document_id,
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "bulk_file_sha256", "value": file_sha}],
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "official-source", "committee-transactions"],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def committee_node_id(fec_id: str) -> str:
    return f"starintel:org:fec-committee-{fec_id.strip().lower()}"


def committee_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row["CMTE_ID"].strip()
    name = row["CMTE_NM"].strip() or fec_id
    data = {
        "candidate_id": row["CAND_ID"].strip() or None,
        "committee_designation": row["CMTE_DSGN"].strip() or None,
        "committee_type": row["CMTE_TP"].strip() or None,
        "fec_committee_id": fec_id,
        "filing_frequency": row["CMTE_FILING_FREQ"].strip() or None,
        "name": name,
        "organization_type_code": row["ORG_TP"].strip() or None,
        "org_type": "fec_registered_committee",
        "party_affiliation": row["CMTE_PTY_AFFILIATION"].strip().upper() or None,
        "reported_connected_organization": row["CONNECTED_ORG_NM"].strip() or None,
        "reported_treasurer": row["TRES_NM"].strip() or None,
    }
    data = {key: value for key, value in data.items() if value is not None}
    document = {
        "_id": committee_node_id(fec_id),
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_committee_id", "value": fec_id}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official FEC committee-master record for {name}; mailing address fields are not emitted.",
        "tags": ["dnc", "fec", "committee", "committee-transaction-counterparty"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 4,
    }
    validate_document(document)
    return document


def fallback_counterparty(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    entity_type = row["ENTITY_TP"].strip().upper()
    name = row["NAME"].strip() or "Unspecified FEC counterparty"
    if entity_type == "IND":
        dtype = "person"
        prefix = "person"
        data = {
            "full_name": name,
            "identity_resolution": "source_scoped_to_fec_committee_transaction_row_until_namesake_resolution",
        }
        org_type = None
    else:
        dtype = "org"
        prefix = "org"
        org_type = "fec_reported_transaction_counterparty"
        data = {
            "name": name,
            "org_type": org_type,
            "identity_resolution": "source_scoped_to_fec_reported_name_until_legal_entity_resolution",
        }
    document_id = sha_id(prefix, "fec-oth-counterparty", row["CMTE_ID"].strip(), row["OTHER_ID"].strip(), name.lower(), entity_type)
    document = {
        "_id": document_id,
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": dtype,
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {
                "canonical": True,
                "issuer": "Federal Election Commission OTH bulk file",
                "scheme": "source_scoped_counterparty",
                "value": f"{row['CMTE_ID'].strip()}:{row['OTHER_ID'].strip()}:{entity_type}:{hashlib.sha256(name.encode('utf-8')).hexdigest()}",
            }
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Counterparty name reported in an official FEC committee-transaction row; the identity remains source-scoped pending primary-source resolution.",
        "tags": ["dnc", "fec", "transaction-counterparty", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-name", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def parse_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%m%d%Y").date().isoformat()
    except ValueError:
        return None


def parse_amount(value: str) -> float:
    try:
        return float(Decimal(value.strip() or "0"))
    except (InvalidOperation, ValueError):
        raise RuntimeError(f"invalid FEC transaction amount: {value!r}")


def public_row_metadata(row: dict[str, str]) -> dict[str, Any]:
    metadata = {
        "amendment_indicator": row["AMNDT_IND"].strip() or None,
        "entity_type": row["ENTITY_TP"].strip() or None,
        "file_number": row["FILE_NUM"].strip() or None,
        "image_number": row["IMAGE_NUM"].strip() or None,
        "memo_code": row["MEMO_CD"].strip() or None,
        "memo_text": row["MEMO_TEXT"].strip() or None,
        "other_id": row["OTHER_ID"].strip() or None,
        "primary_general_indicator": row["TRANSACTION_PGI"].strip() or None,
        "report_type": row["RPT_TP"].strip() or None,
        "sub_id": row["SUB_ID"].strip(),
        "transaction_id": row["TRAN_ID"].strip() or None,
        "transaction_type": row["TRANSACTION_TP"].strip() or None,
    }
    return {key: value for key, value in metadata.items() if value is not None}


def financial_document(
    row: dict[str, str],
    filer_node: str,
    counterparty_node: str,
    source: str,
    when: str,
) -> dict[str, Any]:
    amount = parse_amount(row["TRANSACTION_AMT"])
    transaction_date = parse_date(row["TRANSACTION_DT"])
    qualifications = [
        "Raw official FEC OTH row; amendment chains, memo entries, refunds, attributions, subitemizations, and transaction direction are not reconciled.",
        "Address, ZIP, employer, and occupation columns are not emitted.",
    ]
    if row["AMNDT_IND"].strip().upper() == "A":
        qualifications.append("This row was reported in an amended filing.")
    if row["MEMO_CD"].strip().upper() == "X":
        qualifications.append("FEC memo code X has special inclusion or attribution semantics and must not be treated as an ordinary additive amount.")
    sub_id = row["SUB_ID"].strip()
    title_name = row["NAME"].strip() or row["OTHER_ID"].strip() or "unspecified counterparty"
    document = {
        "_id": f"starintel:financial-observation:fec-oth-{sub_id}",
        "data": {
            "amount": amount,
            "counterparty_ids": [counterparty_node],
            "currency": "USD",
            "entity_id": filer_node,
            "methodology": "Direct row import from the official FEC any-transaction-from-one-committee-to-another bulk file.",
            "observation_type": "reported_committee_transaction",
            "period_end": transaction_date,
            "period_start": transaction_date,
            "qualifications": qualifications,
            "reported_at": None,
            "value_type": "reported_transaction_amount",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "financial-observation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_sub_id", "value": sub_id}
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"SUB_ID {sub_id}", "metadata": public_row_metadata(row)}],
        "status": "recorded",
        "summary": f"Official FEC OTH row reports a ${amount:,.2f} transaction involving the filer committee and {title_name}; amendment, memo, and direction semantics remain unreconciled.",
        "tags": ["dnc", "fec", "committee-transaction", "financial-observation", "raw-row"],
        "title": f"FEC committee transaction {sub_id}: {title_name}",
        "verification": {"last_reviewed_at": when, "status": "official-fec-row", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def transaction_relation(
    row: dict[str, str],
    filer_node: str,
    counterparty_node: str,
    financial_id: str,
    source: str,
    when: str,
) -> dict[str, Any]:
    amount = parse_amount(row["TRANSACTION_AMT"])
    sub_id = row["SUB_ID"].strip()
    qualifiers = {
        "amount": amount,
        "currency": "USD",
        "direction_reconciled": False,
        "raw_row_preserved": True,
        "transaction_date": parse_date(row["TRANSACTION_DT"]),
        **public_row_metadata(row),
    }
    qualifiers = {key: value for key, value in qualifiers.items() if value is not None}
    document = {
        "_id": sha_id("relation", filer_node, "reported_fec_committee_transaction_with", counterparty_node, sub_id),
        "data": {
            "confidence": 0.99,
            "directed": True,
            "object": counterparty_node,
            "predicate": "reported_fec_committee_transaction_with",
            "qualifiers": qualifiers,
            "subject": filer_node,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "related_ids": [financial_id],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"SUB_ID {sub_id}", "metadata": public_row_metadata(row)}],
        "status": "recorded",
        "summary": f"Official FEC OTH row {sub_id} reports a ${amount:,.2f} transaction involving these endpoints; the relation preserves the filer-to-counterparty row orientation without asserting final reconciled money-flow direction.",
        "tags": ["dnc", "fec", "committee-transaction", "relation", "raw-row"],
        "title": f"FEC reported committee transaction {sub_id}",
        "verification": {"last_reviewed_at": when, "status": "official-fec-row", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def target_document(
    *,
    target_id: str,
    target_title: str,
    question: str,
    objectives: list[str],
    next_action: str,
    target_type: str,
    seed_ids: list[str],
    sources: list[str],
    priority: float,
    when: str,
    tags: list[str],
) -> dict[str, Any]:
    document = {
        "_id": target_id,
        "data": {
            "breadth": 220,
            "depth": 2,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official FEC filings, report images, amendments, committee registrations, candidate linkages, and bulk data",
                "official campaign, party, committee, corporate, nonprofit, union, government, contract, lobbying, and court records",
                "public archives and established reporting",
            ],
            "max_depth": 7,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": priority,
            "required_dtypes": ["source", "org", "person", "relation", "claim", "event", "financial-observation"],
            "research_question": question,
            "scope_type": "public_source",
            "seed_ids": seed_ids,
            "source_ids": sources,
            "status": "queued",
            "target": target_title,
            "target_type": target_type,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "investigation-target",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source} for source in sources],
        "status": "recorded",
        "summary": question,
        "tags": ["dnc", "fec", "committee-transaction", "investigation-target", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-fec-rows", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-fec-democratic-committee-transactions",
            "recursion_depth": 2,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


class PartitionWriter:
    def __init__(self, root: Path, partitions: int) -> None:
        self.root = root
        self.partitions = partitions
        self.handles: list[TextIO] = []
        self.hashes = [hashlib.sha256() for _ in range(partitions)]
        self.counts = [0 for _ in range(partitions)]
        self.sizes = [0 for _ in range(partitions)]
        for index in range(partitions):
            directory = root / f"part-{index:03d}"
            directory.mkdir(parents=True)
            self.handles.append((directory / "starintel-documents.jsonl").open("w", encoding="utf-8", newline=""))

    def write(self, document: dict[str, Any]) -> None:
        validate_document(document)
        digest = hashlib.sha256(document["_id"].encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % self.partitions
        line = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        self.handles[index].write(line)
        self.hashes[index].update(encoded)
        self.counts[index] += 1
        self.sizes[index] += len(encoded)

    def close(self) -> list[dict[str, Any]]:
        for handle in self.handles:
            handle.close()
        return [
            {"documents": self.counts[index], "part": index, "sha256": self.hashes[index].hexdigest(), "size": self.sizes[index]}
            for index in range(self.partitions)
        ]


def counterparty_node(
    row: dict[str, str],
    committees: dict[str, dict[str, str]],
    cm_source: str,
    oth_source: str,
    when: str,
) -> tuple[str, dict[str, Any] | None]:
    other_id = row["OTHER_ID"].strip()
    if other_id in committees:
        document = committee_document(committees[other_id], cm_source, when)
        return document["_id"], document
    if other_id.startswith("C") and len(other_id) == 9:
        placeholder = {
            "CMTE_ID": other_id,
            "CMTE_NM": row["NAME"].strip() or other_id,
            "TRES_NM": "",
            "CMTE_ST1": "",
            "CMTE_ST2": "",
            "CMTE_CITY": "",
            "CMTE_ST": "",
            "CMTE_ZIP": "",
            "CMTE_DSGN": "",
            "CMTE_TP": "",
            "CMTE_PTY_AFFILIATION": "",
            "CMTE_FILING_FREQ": "",
            "ORG_TP": "",
            "CONNECTED_ORG_NM": "",
            "CAND_ID": "",
        }
        document = committee_document(placeholder, oth_source, when)
        return document["_id"], document
    if other_id and other_id[0] in {"H", "S", "P"} and len(other_id) == 9:
        node_id = f"starintel:person:fec-candidate-{other_id.lower()}"
        document = fallback_counterparty(row, oth_source, when)
        document["_id"] = node_id
        document["identifiers"] = [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_candidate_id", "value": other_id}]
        document["data"]["candidate_id"] = other_id
        validate_document(document)
        return node_id, document
    document = fallback_counterparty(row, oth_source, when)
    return document["_id"], document


def scan_and_write(
    *,
    oth_zip: Path,
    cm_zip: Path,
    output: Path,
    cycle: int,
    when: str,
) -> dict[str, Any]:
    cm_member, committees, democratic_ids, committee_total = read_committee_master(cm_zip)
    oth_member = largest_text_member(oth_zip)
    oth_source = f"starintel:source:fec-oth-democratic-involved-{cycle}"
    cm_source = f"starintel:source:fec-committee-master-transaction-endpoints-{cycle}"

    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    writer = PartitionWriter(output, PARTITIONS)
    emitted_entities: set[str] = set()
    emitted_rows: set[str] = set()
    counts: Counter[str] = Counter()
    pair_stats: dict[tuple[str, str], dict[str, Any]] = {}
    matching_rows = 0
    total_rows = 0
    raw_amount_sum = Decimal("0")
    filtered_hash = hashlib.sha256()
    filtered_path = output / "source/fec-oth-democratic-involved.psv.gz"

    with filtered_path.open("wb") as compressed_raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=compressed_raw, compresslevel=9, mtime=0) as compressed:
            header = ("|".join(OTH_FIELDS) + "\n").encode("utf-8")
            compressed.write(header)
            filtered_hash.update(header)
            with zipfile.ZipFile(oth_zip) as archive, archive.open(oth_member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                    values = normalized_values(values, len(OTH_FIELDS), oth_member, line_number)
                    row = dict(zip(OTH_FIELDS, values, strict=True))
                    total_rows += 1
                    filer_id = row["CMTE_ID"].strip()
                    other_id = row["OTHER_ID"].strip()
                    if filer_id not in democratic_ids and other_id not in democratic_ids:
                        continue
                    matching_rows += 1
                    if matching_rows > MAX_MATCHING_ROWS:
                        raise RuntimeError(f"matching OTH rows exceed safety cap {MAX_MATCHING_ROWS}")
                    sub_id = row["SUB_ID"].strip()
                    if not sub_id:
                        raise RuntimeError(f"matching OTH row {line_number} lacks SUB_ID")
                    if sub_id in emitted_rows:
                        raise RuntimeError(f"duplicate matching FEC SUB_ID: {sub_id}")
                    emitted_rows.add(sub_id)
                    raw_line = ("|".join(values) + "\n").encode("utf-8")
                    compressed.write(raw_line)
                    filtered_hash.update(raw_line)

                    if filer_id not in committees:
                        raise RuntimeError(f"filer committee missing from committee master: {filer_id}")
                    filer_document = committee_document(committees[filer_id], cm_source, when)
                    filer_node = filer_document["_id"]
                    if filer_node not in emitted_entities:
                        writer.write(filer_document)
                        emitted_entities.add(filer_node)
                        counts[filer_document["dtype"]] += 1

                    counterparty_id, counterparty_document = counterparty_node(row, committees, cm_source, oth_source, when)
                    if counterparty_document is not None and counterparty_id not in emitted_entities:
                        writer.write(counterparty_document)
                        emitted_entities.add(counterparty_id)
                        counts[counterparty_document["dtype"]] += 1

                    financial = financial_document(row, filer_node, counterparty_id, oth_source, when)
                    relation = transaction_relation(row, filer_node, counterparty_id, financial["_id"], oth_source, when)
                    writer.write(financial)
                    writer.write(relation)
                    counts["financial-observation"] += 1
                    counts["relation"] += 1

                    amount = Decimal(row["TRANSACTION_AMT"].strip() or "0")
                    raw_amount_sum += amount
                    pair_key = (filer_node, counterparty_id)
                    stats = pair_stats.setdefault(
                        pair_key,
                        {
                            "amendment_indicators": set(),
                            "counterparty_id": counterparty_id,
                            "counterparty_name": counterparty_document["title"] if counterparty_document else counterparty_id,
                            "date_end": None,
                            "date_start": None,
                            "filer_id": filer_node,
                            "filer_name": filer_document["title"],
                            "memo_codes": set(),
                            "raw_amount_sum": Decimal("0"),
                            "rows": 0,
                            "transaction_types": set(),
                        },
                    )
                    transaction_date = parse_date(row["TRANSACTION_DT"])
                    stats["rows"] += 1
                    stats["raw_amount_sum"] += amount
                    stats["amendment_indicators"].add(row["AMNDT_IND"].strip())
                    stats["memo_codes"].add(row["MEMO_CD"].strip())
                    stats["transaction_types"].add(row["TRANSACTION_TP"].strip())
                    if transaction_date:
                        stats["date_start"] = min(filter(None, (stats["date_start"], transaction_date))) if stats["date_start"] else transaction_date
                        stats["date_end"] = max(filter(None, (stats["date_end"], transaction_date))) if stats["date_end"] else transaction_date

    if not matching_rows:
        raise RuntimeError("no OTH rows involved a DEM or DFL committee")
    if len(pair_stats) > MAX_PAIR_TARGETS:
        raise RuntimeError(f"unique endpoint pairs exceed target safety cap: {len(pair_stats)}")

    pair_inventory: list[dict[str, Any]] = []
    for pair_index, ((filer_node, counterparty_id), stats) in enumerate(sorted(pair_stats.items()), 1):
        filer_name = str(stats["filer_name"])
        counterparty_name = str(stats["counterparty_name"])
        target_ids: list[str] = []
        base_priority = 1.0 if "fec-committee-c00010603" in filer_node or "fec-committee-c00010603" in counterparty_id else 0.92
        for axis in PAIR_AXES:
            target_id = sha_id("investigation-target", "dnc-fec-committee-pair", filer_node, counterparty_id, str(axis["key"]))
            question = axis["question"].format(filer=filer_name, counterparty=counterparty_name)
            document = target_document(
                target_id=target_id,
                target_title=f"{filer_name} / {counterparty_name}: {axis['label']}",
                question=question,
                objectives=list(axis["objectives"]),
                next_action=str(axis["next"]),
                target_type=str(axis["target_type"]),
                seed_ids=[filer_node, counterparty_id],
                sources=[oth_source, cm_source],
                priority=round(base_priority - float(axis["penalty"]), 4),
                when=when,
                tags=["committee-pair", str(axis["key"])],
            )
            writer.write(document)
            counts["investigation-target"] += 1
            target_ids.append(target_id)
        pair_inventory.append(
            {
                "amendment_indicators": sorted(value for value in stats["amendment_indicators"] if value),
                "counterparty_id": counterparty_id,
                "counterparty_name": counterparty_name,
                "date_end": stats["date_end"],
                "date_start": stats["date_start"],
                "filer_id": filer_node,
                "filer_name": filer_name,
                "memo_codes": sorted(value for value in stats["memo_codes"] if value),
                "pair_index": pair_index,
                "raw_amount_sum_unreconciled": str(stats["raw_amount_sum"]),
                "rows": stats["rows"],
                "target_ids": target_ids,
                "transaction_types": sorted(value for value in stats["transaction_types"] if value),
            }
        )

    partitions = writer.close()
    pair_bytes = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pair_inventory).encode("utf-8")
    (output / "source/committee-pairs.jsonl").write_bytes(pair_bytes)
    source_documents = [
        source_document(
            document_id=oth_source,
            title=f"FEC {cycle} committee-to-committee transactions involving DEM or DFL committees",
            summary="Official FEC OTH rows where the filer or reported counterparty is a committee whose committee-master party affiliation is DEM or DFL. Every matching amendment and memo row is preserved without reconciliation; address, ZIP, employer, and occupation fields are not emitted.",
            uri=cycle_url(OTH_URL, cycle),
            description_uri=OTH_DESCRIPTION,
            member=oth_member,
            file_sha=file_sha256(oth_zip),
            total_rows=total_rows,
            matching_rows=matching_rows,
            when=when,
        ),
        source_document(
            document_id=cm_source,
            title=f"FEC {cycle} committee master for transaction endpoints",
            summary="Official FEC committee-master file used to identify DEM and DFL committees and resolve committee transaction endpoints; mailing address fields are not emitted.",
            uri=cycle_url(CM_URL, cycle),
            description_uri=CM_DESCRIPTION,
            member=cm_member,
            file_sha=file_sha256(cm_zip),
            total_rows=committee_total,
            matching_rows=len(emitted_entities),
            when=when,
        ),
    ]
    source_payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in source_documents).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(source_payload)
    counts["source"] = len(source_documents)

    total_documents = sum(counts.values())
    target_counts = {axis["target_type"]: len(pair_inventory) for axis in PAIR_AXES}
    manifest = {
        "committee_master_description_url": CM_DESCRIPTION,
        "committee_master_url": cycle_url(CM_URL, cycle),
        "counts": dict(sorted(counts.items())),
        "cycle": cycle,
        "dataset": DATASET,
        "democratic_committee_ids": len(democratic_ids),
        "filtered_psv_gzip_sha256": file_sha256(filtered_path),
        "filtered_uncompressed_sha256": filtered_hash.hexdigest(),
        "generated_at": when,
        "matching_rows": matching_rows,
        "oth_description_url": OTH_DESCRIPTION,
        "oth_url": cycle_url(OTH_URL, cycle),
        "pair_inventory_sha256": hashlib.sha256(pair_bytes).hexdigest(),
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "party_codes": sorted(PARTY_CODES),
        "party_codes_url": PARTY_CODES_URL,
        "raw_amount_sum_unreconciled": str(raw_amount_sum),
        "raw_committee_master_sha256": file_sha256(cm_zip),
        "raw_oth_sha256": file_sha256(oth_zip),
        "raw_total_rows": total_rows,
        "reconciliation": "none; all matching amendment and memo rows preserved",
        "schema_version": "0.9.0",
        "target_counts": target_counts,
        "total_documents": total_documents,
        "total_targets": counts["investigation-target"],
        "unique_endpoint_pairs": len(pair_inventory),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    top_pairs = sorted(pair_inventory, key=lambda item: (-int(item["rows"]), item["filer_name"], item["counterparty_name"]))[:50]
    lines = [
        "# FEC committee transactions involving Democratic committees",
        "",
        "Official FEC `OTH` rows where either the filer or the reported counterparty is a committee whose committee-master party affiliation is `DEM` or `DFL`.",
        "",
        f"- raw OTH rows scanned: {total_rows:,}",
        f"- matching raw rows: {matching_rows:,}",
        f"- unique endpoint pairs: {len(pair_inventory):,}",
        f"- Democratic committee IDs: {len(democratic_ids):,}",
        f"- StarIntel documents: {total_documents:,}",
        f"- pair-level investigation targets: {counts['investigation-target']:,}",
        f"- GitHub-safe partitions: {PARTITIONS}",
        "",
        "The raw amount sum is retained only as an unreconciled source statistic. Amendments, memo items, refunds, attributions, subitemizations, transaction type, and direction must be reconciled from filings before any final flow total is stated. Mailing addresses, ZIP codes, employer fields, and occupation fields are not emitted.",
        "",
        "## Largest endpoint pairs by raw row count",
        "",
        "| Filer | Counterparty | Rows | Date start | Date end | Unreconciled raw amount |",
        "|---|---|---:|---|---|---:|",
    ]
    for item in top_pairs:
        lines.append(f"| {str(item['filer_name']).replace('|', '/')} | {str(item['counterparty_name']).replace('|', '/')} | {int(item['rows']):,} | {item['date_start'] or ''} | {item['date_end'] or ''} | ${Decimal(item['raw_amount_sum_unreconciled']):,.2f} |")
    lines.extend(["", "## Target families", ""])
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(["", "```bash", "python3 scripts/import_dnc_fec_committee_transactions.py", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main() -> int:
    ns = parse_args()
    if ns.cycle < 2000 or ns.cycle % 2:
        raise RuntimeError("cycle must be an even election year")
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        oth_zip = temp / f"oth{str(ns.cycle)[-2:]}.zip"
        cm_zip = temp / f"cm{str(ns.cycle)[-2:]}.zip"
        copy_or_download(ns.offline_oth_zip, cycle_url(OTH_URL, ns.cycle), oth_zip)
        copy_or_download(ns.offline_cm_zip, cycle_url(CM_URL, ns.cycle), cm_zip)
        manifest = scan_and_write(oth_zip=oth_zip, cm_zip=cm_zip, output=ns.output, cycle=ns.cycle, when=ns.generated_at)
    print(json.dumps({"documents": manifest["total_documents"], "matching_rows": manifest["matching_rows"], "output": str(ns.output), "pairs": manifest["unique_endpoint_pairs"], "targets": manifest["total_targets"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
