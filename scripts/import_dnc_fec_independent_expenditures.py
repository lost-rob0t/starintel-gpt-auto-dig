#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import urllib.request
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, TextIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
CYCLE = 2026
GENERATED_AT = "2026-07-31T23:58:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-independent-expenditures-democratic-candidates-2026")
IE_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/independent_expenditure_{cycle}.csv"
CN_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cn{yy}.zip"
IE_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/independent-expenditures-file-description/"
CN_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/candidate-master-file-description/"
PARTY_CODES_URL = "https://www.fec.gov/campaign-finance-data/party-code-descriptions/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
RUN_ID = "dnc-fec-independent-expenditures-democratic-candidates-2026-07-31"
PARTY_CODES = {"DEM", "DFL"}
MAX_DOWNLOAD = 1_500_000_000
MAX_ROWS = 2_000_000
MAX_PAIRS = 250_000
PARTITIONS = 128

CN_FIELDS = [
    "CAND_ID",
    "CAND_NAME",
    "CAND_PTY_AFFILIATION",
    "CAND_ELECTION_YR",
    "CAND_OFFICE_ST",
    "CAND_OFFICE",
    "CAND_OFFICE_DISTRICT",
    "CAND_ICI",
    "CAND_STATUS",
    "CAND_PCC",
    "CAND_ST1",
    "CAND_ST2",
    "CAND_CITY",
    "CAND_ST",
    "CAND_ZIP",
]
REQUIRED_IE_FIELDS = {
    "CAN_ID",
    "CAN_NAM",
    "SPE_ID",
    "SPE_NAM",
    "ELE_TYP",
    "CAN_OFF_STA",
    "CAN_OFF_DIS",
    "CAN_OFF",
    "CAN_PAR_AFF",
    "EXP_AMO",
    "EXP_DAT",
    "AGG_AMO",
    "SUP_OPP",
    "PUR",
    "PAY",
    "FILE_NUM",
    "AMN_IND",
    "TRA_ID",
    "IMA_NUM",
    "REC_DT",
    "FEC_ELECTION_YR",
    "PREV_FILE_NUM",
    "DISSEM_DT",
}

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
    "Federal Election Commission reports, images, amendments, and bulk data",
    "official spender, candidate, campaign, vendor, corporate, nonprofit, union, and government records",
    "FCC political files, platform ad libraries, broadcast records, court records, archives, and established reporting",
]

PAIR_AXES = (
    {
        "key": "amendment-reconciliation",
        "label": "amendment lineage, report images, duplication, and reconciliation",
        "target_type": "fec_ie_amendment_reconciliation",
        "penalty": 0.00,
        "question": "What complete original-report, amendment, previous-filing, transaction-ID, image, receipt-date, dissemination-date, aggregate, and reconciliation history governs independent expenditures by {spender} that support or oppose {candidate}?",
        "objectives": [
            "Acquire every original and amended 24-hour or 48-hour report, linked image, previous filing, and transaction row",
            "Group duplicate and superseding records by spender, candidate, report, transaction, date, amount, support/oppose code, and amendment lineage",
            "Publish raw-row and reconciled views separately with transparent calculations and unresolved discrepancies",
            "Preserve dissemination timing, election designation, aggregate amount, purpose, payee, and legal reporting context",
        ],
        "next": "Fetch every underlying filing and image and construct a transparent row-level amendment and duplicate reconciliation ledger",
    },
    {
        "key": "spender-control-funding",
        "label": "spender legal entities, leadership, funders, control, and affiliations",
        "target_type": "fec_ie_spender_control_funding",
        "penalty": 0.005,
        "question": "Which legal entities, officers, directors, founders, employees, donors, funders, connected organizations, committees, sponsors, clients, and governance rights comprise or influence {spender}, which reported spending concerning {candidate}?",
        "objectives": [
            "Resolve the spender ID, legal names, aliases, former names, committee registrations, corporate or nonprofit entities, and tax status",
            "Enumerate officers, treasurers, directors, founders, executives, staff, consultants, counsel, compliance firms, and controlling persons",
            "Trace receipts, donors, grants, transfers, sponsors, clients, ownership, governance, and affiliated organizations",
            "Separate disclosed funding and formal control from unsupported dark-money, pass-through, or coordination claims",
        ],
        "next": "Join FEC registrations and receipts with corporate, nonprofit, tax, lobbying, board, grant, and official organizational records",
    },
    {
        "key": "vendors-creative-distribution",
        "label": "payees, vendors, creative, placements, audiences, and distribution evidence",
        "target_type": "fec_ie_vendors_creative_distribution",
        "penalty": 0.01,
        "question": "Which payees, media buyers, creative firms, consultants, platforms, publishers, broadcasters, printers, production companies, subcontractors, advertisements, audiences, markets, and distribution records comprise {spender}'s reported independent expenditures concerning {candidate}?",
        "objectives": [
            "Resolve every payee and purpose into legal vendors, principals, staff, subcontractors, and services",
            "Acquire ad creatives, scripts, disclaimers, invoices, contracts, FCC political files, platform ad-library records, targeting data, placement schedules, and archives",
            "Map vendor principals and staff to other committees, campaigns, companies, nonprofits, unions, media outlets, and government roles",
            "Separate direct vendors, payment processors, pass-throughs, reimbursements, production firms, media buyers, platforms, and publishers",
        ],
        "next": "Resolve all payees and purposes, then acquire public ad, contract, invoice, placement, platform-library, and FCC political-file evidence",
    },
    {
        "key": "timing-message-counterevidence",
        "label": "message, targeting, timing, election context, and counter-evidence",
        "target_type": "fec_ie_message_timing_counterevidence",
        "penalty": 0.012,
        "question": "What messages, claims, quotations, visuals, targeted audiences, geographic markets, release sequences, election events, polling, public actions, and credible counter-evidence contextualize {spender}'s independent expenditures supporting or opposing {candidate}?",
        "objectives": [
            "Extract every material claim and cited source from the communication with exact context and attribution",
            "Map dissemination timing against elections, debates, endorsements, filings, news events, litigation, public votes, and campaign milestones",
            "Verify factual assertions against primary records and credible counter-sources",
            "Separate documented support or opposition, measured timing and distribution, rhetorical framing, inference, and unsupported coordination claims",
        ],
        "next": "Acquire the communication artifacts and build an attributed claim, distribution, timing, event, and counter-evidence ledger",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import independent expenditures concerning DEM or DFL candidates")
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-ie-csv", type=Path)
    parser.add_argument("--offline-candidate-zip", type=Path)
    return parser.parse_args()


def cycle_url(template: str, cycle: int) -> str:
    return template.format(cycle=cycle, yy=str(cycle)[-2:])


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def sha_id(prefix: str, *parts: str) -> str:
    return f"starintel:{prefix}:{hashlib.sha256(chr(31).join(parts).encode('utf-8')).hexdigest()}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=240) as response, destination.open("wb") as handle:
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


def read_candidates(zip_path: Path) -> tuple[str, dict[str, dict[str, str]], set[str], int]:
    import zipfile
    with zipfile.ZipFile(zip_path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))]
        if not members:
            raise RuntimeError("candidate ZIP contains no text member")
        member = max(members, key=lambda info: info.file_size).filename
        candidates: dict[str, dict[str, str]] = {}
        democratic_ids: set[str] = set()
        total = 0
        with archive.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                if len(values) == len(CN_FIELDS) + 1 and values[-1] == "":
                    values.pop()
                if len(values) != len(CN_FIELDS):
                    raise RuntimeError(f"unexpected candidate row width at {line_number}: {len(values)}")
                row = dict(zip(CN_FIELDS, values, strict=True))
                candidate_id = row["CAND_ID"].strip()
                if not candidate_id:
                    raise RuntimeError(f"candidate row {line_number} lacks ID")
                if candidate_id in candidates:
                    raise RuntimeError(f"duplicate candidate ID: {candidate_id}")
                candidates[candidate_id] = row
                total += 1
                if row["CAND_PTY_AFFILIATION"].strip().upper() in PARTY_CODES:
                    democratic_ids.add(candidate_id)
    return member, candidates, democratic_ids, total


def parse_date(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def amount(value: str) -> float:
    try:
        return float(Decimal(value.strip().replace(",", "") or "0"))
    except (InvalidOperation, ValueError):
        raise RuntimeError(f"invalid FEC independent-expenditure amount: {value!r}")


def source_document(document_id: str, title: str, summary: str, uri: str, description_uri: str, file_sha: str, rows: int, matching: int, when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {
            "accessed_at": when,
            "credibility": 1.0,
            "description_uri": description_uri,
            "file_sha256": file_sha,
            "kind": "official_fec_bulk_data",
            "matching_record_count": matching,
            "publisher": "Federal Election Commission",
            "record_count": rows,
            "uri": uri,
        },
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
        "tags": ["dnc", "fec", "independent-expenditure", "official-source"],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def candidate_id(fec_id: str) -> str:
    return f"starintel:person:fec-candidate-{fec_id.lower()}"


def candidate_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row["CAND_ID"].strip()
    name = row["CAND_NAME"].strip() or fec_id
    data = {
        "candidate_id": fec_id,
        "candidate_status": row["CAND_STATUS"].strip() or None,
        "district": row["CAND_OFFICE_DISTRICT"].strip() or None,
        "election_year": row["CAND_ELECTION_YR"].strip() or None,
        "full_name": name,
        "incumbent_challenger_open": row["CAND_ICI"].strip() or None,
        "office": row["CAND_OFFICE"].strip() or None,
        "office_state": row["CAND_OFFICE_ST"].strip() or None,
        "party_affiliation": row["CAND_PTY_AFFILIATION"].strip().upper(),
        "principal_campaign_committee_id": row["CAND_PCC"].strip() or None,
    }
    document = {
        "_id": candidate_id(fec_id),
        "data": {key: value for key, value in data.items() if value is not None},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_candidate_id", "value": fec_id}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official FEC candidate-master record for {name}; address fields are not emitted.",
        "tags": ["dnc", "fec", "candidate", "independent-expenditure-target"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 3,
    }
    validate_document(document)
    return document


def fallback_candidate(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row.get("CAN_ID", "").strip()
    name = row.get("CAN_NAM", "").strip() or fec_id or "Unspecified candidate"
    document_id = candidate_id(fec_id) if fec_id else sha_id("person", "fec-ie-candidate", norm(name), row.get("CAN_OFF_STA", ""), row.get("CAN_OFF_DIS", ""), row.get("CAN_OFF", ""))
    identifiers = []
    if fec_id:
        identifiers.append({"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_candidate_id", "value": fec_id})
    else:
        identifiers.append({"canonical": True, "issuer": "Federal Election Commission independent-expenditure file", "scheme": "source_scoped_candidate", "value": f"{norm(name)}:{row.get('CAN_OFF_STA','')}:{row.get('CAN_OFF_DIS','')}:{row.get('CAN_OFF','')}"})
    document = {
        "_id": document_id,
        "data": {
            "district": row.get("CAN_OFF_DIS", "").strip() or None,
            "full_name": name,
            "identity_resolution": "official_ie_row_pending_candidate_master_resolution",
            "office": row.get("CAN_OFF", "").strip() or None,
            "office_state": row.get("CAN_OFF_STA", "").strip() or None,
            "party_affiliation": row.get("CAN_PAR_AFF", "").strip().upper() or None,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": identifiers,
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Candidate reported in the official FEC independent-expenditure file; candidate-master identity remains unresolved or unavailable.",
        "tags": ["dnc", "fec", "candidate", "independent-expenditure", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-name", "verified": True},
        "version": 1,
    }
    document["data"] = {key: value for key, value in document["data"].items() if value is not None}
    validate_document(document)
    return document


def spender_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row["SPE_ID"].strip()
    name = row["SPE_NAM"].strip() or fec_id or "Unspecified spender"
    document_id = f"starintel:org:fec-independent-expenditure-spender-{fec_id.lower()}" if fec_id else sha_id("org", "fec-ie-spender", norm(name))
    identifiers = []
    if fec_id:
        identifiers.append({"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_spender_id", "value": fec_id})
    else:
        identifiers.append({"canonical": True, "issuer": "Federal Election Commission independent-expenditure file", "scheme": "normalized_reported_spender_name", "value": norm(name)})
    document = {
        "_id": document_id,
        "data": {
            "fec_spender_id": fec_id or None,
            "identity_resolution": "official_spender_id" if fec_id else "source_scoped_reported_name",
            "name": name,
            "org_type": "fec_independent_expenditure_spender",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": identifiers,
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Spender reported in the official FEC independent-expenditure file; legal form, governance, funding, and affiliations require separate resolution.",
        "tags": ["dnc", "fec", "independent-expenditure", "spender"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-entity", "verified": True},
        "version": 1,
    }
    document["data"] = {key: value for key, value in document["data"].items() if value is not None}
    validate_document(document)
    return document


def payee_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    name = row["PAY"].strip() or "Unspecified payee"
    document_id = sha_id("org", "fec-ie-payee", norm(name))
    document = {
        "_id": document_id,
        "data": {"identity_resolution": "source_scoped_reported_name", "name": name, "org_type": "fec_independent_expenditure_payee"},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission independent-expenditure file", "scheme": "normalized_reported_payee_name", "value": norm(name)}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Payee name reported in the official FEC independent-expenditure file; legal identity and role require separate resolution.",
        "tags": ["dnc", "fec", "independent-expenditure", "payee", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-name", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def row_key(row: dict[str, str], line_number: int) -> str:
    canonical = "\x1f".join(row.get(field, "") for field in sorted(REQUIRED_IE_FIELDS))
    return hashlib.sha256(f"{line_number}\x1f{canonical}".encode("utf-8")).hexdigest()


def row_metadata(row: dict[str, str]) -> dict[str, Any]:
    metadata = {
        "aggregate_amount": amount(row["AGG_AMO"]),
        "amendment_indicator": row["AMN_IND"].strip() or None,
        "candidate_party": row["CAN_PAR_AFF"].strip().upper() or None,
        "dissemination_date": parse_date(row["DISSEM_DT"]),
        "election_type": row["ELE_TYP"].strip() or None,
        "fec_election_year": row["FEC_ELECTION_YR"].strip() or None,
        "file_number": row["FILE_NUM"].strip() or None,
        "image_number": row["IMA_NUM"].strip() or None,
        "previous_file_number": row["PREV_FILE_NUM"].strip() or None,
        "purpose": row["PUR"].strip() or None,
        "receipt_date": parse_date(row["REC_DT"]),
        "support_oppose": row["SUP_OPP"].strip().upper() or None,
        "transaction_id": row["TRA_ID"].strip() or None,
    }
    return {key: value for key, value in metadata.items() if value is not None}


def financial_document(row: dict[str, str], key: str, spender_id: str, candidate_node: str, payee_id: str, source: str, when: str) -> dict[str, Any]:
    exp_amount = amount(row["EXP_AMO"])
    exp_date = parse_date(row["EXP_DAT"])
    qualifications = [
        "Raw official FEC independent-expenditure row; originals and amended reports may duplicate transactions and no reconciliation has been applied.",
        "The filer reports the support-or-oppose characterization and independent nature of the expenditure; this import does not independently establish legal compliance or non-coordination.",
    ]
    if row["AMN_IND"].strip().upper().startswith("A"):
        qualifications.append("This record is associated with an amended report.")
    document = {
        "_id": f"starintel:financial-observation:fec-ie-{key}",
        "data": {
            "amount": exp_amount,
            "counterparty_ids": [candidate_node, payee_id],
            "currency": "USD",
            "entity_id": spender_id,
            "methodology": "Direct row import from the official FEC independent-expenditure file.",
            "observation_type": "reported_independent_expenditure",
            "period_end": exp_date,
            "period_start": exp_date,
            "qualifications": qualifications,
            "reported_at": parse_date(row["REC_DT"]),
            "value_type": "reported_transaction_amount",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "financial-observation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission independent-expenditure file", "scheme": "row_sha256", "value": key}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"row sha256 {key}", "metadata": row_metadata(row)}],
        "status": "recorded",
        "summary": f"Official FEC row reports a ${exp_amount:,.2f} independent expenditure by {row['SPE_NAM'].strip() or 'the named spender'} concerning {row['CAN_NAM'].strip() or 'the named candidate'}, with support/oppose code {row['SUP_OPP'].strip() or 'unspecified'}.",
        "tags": ["dnc", "fec", "independent-expenditure", "financial-observation", "raw-row"],
        "title": f"FEC independent expenditure: {row['SPE_NAM'].strip() or 'spender'} / {row['CAN_NAM'].strip() or 'candidate'}",
        "verification": {"last_reviewed_at": when, "status": "official-fec-row", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def relation_document(subject: str, predicate: str, obj: str, title: str, summary: str, qualifiers: dict[str, Any], source: str, financial_id: str, when: str) -> dict[str, Any]:
    document = {
        "_id": sha_id("relation", subject, predicate, obj, qualifiers.get("row_sha256", "")),
        "data": {"confidence": 0.99, "directed": True, "object": obj, "predicate": predicate, "qualifiers": qualifiers, "subject": subject},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "related_ids": [financial_id],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "independent-expenditure", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-fec-row", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def target_document(target_id: str, title: str, question: str, objectives: list[str], next_action: str, target_type: str, seed_ids: list[str], sources: list[str], priority: float, when: str, tags: list[str]) -> dict[str, Any]:
    document = {
        "_id": target_id,
        "data": {
            "breadth": 250,
            "depth": 2,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official FEC reports, images, amendments, registrations, receipts, and bulk data",
                "official spender, candidate, campaign, vendor, corporate, nonprofit, union, government, FCC, and platform records",
                "public contracts, archives, court records, and established reporting",
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
            "target": title,
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
        "tags": ["dnc", "fec", "independent-expenditure", "investigation-target", *tags],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-fec-rows", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-fec-independent-expenditures",
            "recursion_depth": 2,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


class PartitionWriter:
    def __init__(self, root: Path) -> None:
        self.handles: list[TextIO] = []
        self.counts = [0] * PARTITIONS
        self.sizes = [0] * PARTITIONS
        self.hashes = [hashlib.sha256() for _ in range(PARTITIONS)]
        for index in range(PARTITIONS):
            directory = root / f"part-{index:03d}"
            directory.mkdir(parents=True)
            self.handles.append((directory / "starintel-documents.jsonl").open("w", encoding="utf-8", newline=""))

    def write(self, document: dict[str, Any]) -> None:
        validate_document(document)
        index = int.from_bytes(hashlib.sha256(document["_id"].encode("utf-8")).digest()[:2], "big") % PARTITIONS
        line = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        self.handles[index].write(line)
        self.hashes[index].update(encoded)
        self.counts[index] += 1
        self.sizes[index] += len(encoded)

    def close(self) -> list[dict[str, Any]]:
        for handle in self.handles:
            handle.close()
        return [{"documents": self.counts[index], "part": index, "sha256": self.hashes[index].hexdigest(), "size": self.sizes[index]} for index in range(PARTITIONS)]


def scan(ie_path: Path, candidate_zip: Path, output: Path, cycle: int, when: str) -> dict[str, Any]:
    candidate_member, candidates, democratic_candidate_ids, candidate_total = read_candidates(candidate_zip)
    ie_source = f"starintel:source:fec-independent-expenditures-democratic-candidates-{cycle}"
    candidate_source = f"starintel:source:fec-candidate-master-independent-expenditure-targets-{cycle}"
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    writer = PartitionWriter(output)
    emitted_entities: set[str] = set()
    emitted_rows: set[str] = set()
    pair_stats: dict[tuple[str, str], dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    total_rows = 0
    matching_rows = 0
    raw_amount_sum = Decimal("0")
    filtered_hash = hashlib.sha256()
    filtered_path = output / "source/fec-independent-expenditures-democratic-candidates.csv.gz"

    with ie_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED_IE_FIELDS - fields
        if missing:
            raise RuntimeError(f"independent-expenditure CSV lacks fields: {sorted(missing)}")
        fieldnames = list(reader.fieldnames or [])
        with filtered_path.open("wb") as raw_out, gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, compresslevel=9, mtime=0) as compressed:
            buffer = io.StringIO()
            csv_writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
            csv_writer.writeheader()
            header = buffer.getvalue().encode("utf-8")
            compressed.write(header)
            filtered_hash.update(header)
            buffer.seek(0)
            buffer.truncate(0)
            for line_number, raw_row in enumerate(reader, 2):
                total_rows += 1
                row = {key: (value or "") for key, value in raw_row.items() if key is not None}
                fec_candidate_id = row["CAN_ID"].strip()
                reported_party = row["CAN_PAR_AFF"].strip().upper()
                if fec_candidate_id not in democratic_candidate_ids and reported_party not in PARTY_CODES:
                    continue
                matching_rows += 1
                if matching_rows > MAX_ROWS:
                    raise RuntimeError(f"matching independent-expenditure rows exceed cap {MAX_ROWS}")
                key = row_key(row, line_number)
                if key in emitted_rows:
                    raise RuntimeError(f"duplicate generated row key: {key}")
                emitted_rows.add(key)
                csv_writer.writerow({field: row.get(field, "") for field in fieldnames})
                raw_bytes = buffer.getvalue().encode("utf-8")
                compressed.write(raw_bytes)
                filtered_hash.update(raw_bytes)
                buffer.seek(0)
                buffer.truncate(0)

                candidate_row = candidates.get(fec_candidate_id)
                candidate = candidate_document(candidate_row, candidate_source, when) if candidate_row else fallback_candidate(row, ie_source, when)
                spender = spender_document(row, ie_source, when)
                payee = payee_document(row, ie_source, when)
                for entity in (candidate, spender, payee):
                    if entity["_id"] not in emitted_entities:
                        writer.write(entity)
                        emitted_entities.add(entity["_id"])
                        counts[entity["dtype"]] += 1

                financial = financial_document(row, key, spender["_id"], candidate["_id"], payee["_id"], ie_source, when)
                qualifiers = {"row_sha256": key, **row_metadata(row)}
                relation = relation_document(
                    spender["_id"],
                    "fec_reported_independent_expenditure_concerning",
                    candidate["_id"],
                    f"{spender['title']}: independent expenditure concerning {candidate['title']}",
                    "The official FEC independent-expenditure row reports spending by this spender concerning this candidate with the filer-supplied support or oppose code; original and amended rows remain unreconciled.",
                    qualifiers,
                    ie_source,
                    financial["_id"],
                    when,
                )
                payee_relation = relation_document(
                    spender["_id"],
                    "fec_reported_independent_expenditure_payment_to",
                    payee["_id"],
                    f"{spender['title']}: reported independent-expenditure payment to {payee['title']}",
                    "The official FEC row reports this named payee in connection with the independent expenditure; vendor identity, service, direction, and amendment treatment require resolution.",
                    qualifiers,
                    ie_source,
                    financial["_id"],
                    when,
                )
                for document in (financial, relation, payee_relation):
                    writer.write(document)
                    counts[document["dtype"]] += 1
                exp_amount = Decimal(row["EXP_AMO"].strip().replace(",", "") or "0")
                raw_amount_sum += exp_amount
                pair_key = (spender["_id"], candidate["_id"])
                stats = pair_stats.setdefault(
                    pair_key,
                    {
                        "amendment_indicators": set(),
                        "candidate_id": candidate["_id"],
                        "candidate_name": candidate["title"],
                        "date_end": None,
                        "date_start": None,
                        "election_types": set(),
                        "payee_ids": set(),
                        "raw_amount_sum": Decimal("0"),
                        "rows": 0,
                        "spender_id": spender["_id"],
                        "spender_name": spender["title"],
                        "support_oppose": set(),
                    },
                )
                exp_date = parse_date(row["EXP_DAT"])
                stats["rows"] += 1
                stats["raw_amount_sum"] += exp_amount
                stats["amendment_indicators"].add(row["AMN_IND"].strip())
                stats["election_types"].add(row["ELE_TYP"].strip())
                stats["payee_ids"].add(payee["_id"])
                stats["support_oppose"].add(row["SUP_OPP"].strip().upper())
                if exp_date:
                    stats["date_start"] = min(stats["date_start"], exp_date) if stats["date_start"] else exp_date
                    stats["date_end"] = max(stats["date_end"], exp_date) if stats["date_end"] else exp_date

    if not matching_rows:
        raise RuntimeError("independent-expenditure file yielded no Democratic candidate rows")
    if len(pair_stats) > MAX_PAIRS:
        raise RuntimeError(f"spender-candidate pairs exceed cap {MAX_PAIRS}")

    pair_inventory: list[dict[str, Any]] = []
    for pair_index, ((spender_id, candidate_node), stats) in enumerate(sorted(pair_stats.items()), 1):
        target_ids: list[str] = []
        candidate_name = str(stats["candidate_name"])
        spender_name = str(stats["spender_name"])
        base_priority = 0.98 if "S" in stats["support_oppose"] and "O" in stats["support_oppose"] else 0.96
        for axis in PAIR_AXES:
            target_id = sha_id("investigation-target", "dnc-fec-ie-pair", spender_id, candidate_node, str(axis["key"]))
            question = axis["question"].format(spender=spender_name, candidate=candidate_name)
            target = target_document(
                target_id,
                f"{spender_name} / {candidate_name}: {axis['label']}",
                question,
                list(axis["objectives"]),
                str(axis["next"]),
                str(axis["target_type"]),
                [spender_id, candidate_node, *sorted(stats["payee_ids"])[:50]],
                [ie_source, candidate_source],
                round(base_priority - float(axis["penalty"]), 4),
                when,
                ["spender-candidate-pair", str(axis["key"])],
            )
            writer.write(target)
            counts["investigation-target"] += 1
            target_ids.append(target_id)
        pair_inventory.append(
            {
                "amendment_indicators": sorted(value for value in stats["amendment_indicators"] if value),
                "candidate_id": candidate_node,
                "candidate_name": candidate_name,
                "date_end": stats["date_end"],
                "date_start": stats["date_start"],
                "election_types": sorted(value for value in stats["election_types"] if value),
                "pair_index": pair_index,
                "payee_ids": sorted(stats["payee_ids"]),
                "raw_amount_sum_unreconciled": str(stats["raw_amount_sum"]),
                "rows": stats["rows"],
                "spender_id": spender_id,
                "spender_name": spender_name,
                "support_oppose": sorted(value for value in stats["support_oppose"] if value),
                "target_ids": target_ids,
            }
        )

    partitions = writer.close()
    pair_bytes = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in pair_inventory).encode("utf-8")
    (output / "source/spender-candidate-pairs.jsonl").write_bytes(pair_bytes)
    source_documents = [
        source_document(
            ie_source,
            f"FEC {cycle} independent expenditures concerning DEM or DFL candidates",
            "Official FEC current-cycle independent-expenditure rows whose candidate ID resolves to a DEM or DFL candidate or whose reported candidate party is DEM or DFL. Original and amended reports are preserved without reconciliation.",
            cycle_url(IE_URL, cycle),
            IE_DESCRIPTION,
            file_sha256(ie_path),
            total_rows,
            matching_rows,
            when,
        ),
        source_document(
            candidate_source,
            f"FEC {cycle} candidate master for independent-expenditure targets",
            "Official FEC candidate-master file used to identify DEM and DFL candidates and resolve candidate IDs; mailing address fields are not emitted.",
            cycle_url(CN_URL, cycle),
            CN_DESCRIPTION,
            file_sha256(candidate_zip),
            candidate_total,
            len(democratic_candidate_ids),
            when,
        ),
    ]
    root_payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in source_documents).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(root_payload)
    counts["source"] = len(source_documents)
    target_counts = {axis["target_type"]: len(pair_inventory) for axis in PAIR_AXES}
    manifest = {
        "candidate_master_url": cycle_url(CN_URL, cycle),
        "counts": dict(sorted(counts.items())),
        "cycle": cycle,
        "dataset": DATASET,
        "democratic_candidate_ids": len(democratic_candidate_ids),
        "filtered_csv_gzip_sha256": file_sha256(filtered_path),
        "filtered_uncompressed_sha256": filtered_hash.hexdigest(),
        "generated_at": when,
        "independent_expenditure_description_url": IE_DESCRIPTION,
        "independent_expenditure_url": cycle_url(IE_URL, cycle),
        "matching_rows": matching_rows,
        "pair_inventory_sha256": hashlib.sha256(pair_bytes).hexdigest(),
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "party_codes": sorted(PARTY_CODES),
        "party_codes_url": PARTY_CODES_URL,
        "raw_amount_sum_unreconciled": str(raw_amount_sum),
        "raw_candidate_master_sha256": file_sha256(candidate_zip),
        "raw_independent_expenditure_sha256": file_sha256(ie_path),
        "raw_total_rows": total_rows,
        "reconciliation": "none; original and amended report rows preserved",
        "schema_version": "0.9.0",
        "spender_candidate_pairs": len(pair_inventory),
        "target_counts": target_counts,
        "total_documents": sum(counts.values()),
        "total_targets": counts["investigation-target"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    top_pairs = sorted(pair_inventory, key=lambda item: (-int(item["rows"]), item["spender_name"], item["candidate_name"]))[:50]
    lines = [
        "# FEC independent expenditures concerning Democratic candidates",
        "",
        "Official current-cycle FEC independent-expenditure rows whose candidate resolves to `DEM` or `DFL` through the candidate master or the row's reported party field.",
        "",
        f"- raw rows scanned: {total_rows:,}",
        f"- matching raw rows: {matching_rows:,}",
        f"- unique spender-candidate pairs: {len(pair_inventory):,}",
        f"- StarIntel documents: {manifest['total_documents']:,}",
        f"- pair-level investigation targets: {manifest['total_targets']:,}",
        f"- GitHub-safe partitions: {PARTITIONS}",
        "",
        "The raw amount sum is retained only as an unreconciled source statistic. The FEC warns that this file contains original and amended reports, so rows may duplicate transactions. The filer-supplied support/oppose code and independent-expenditure classification are preserved as reported facts, not treated as independent proof of message truth or legal non-coordination.",
        "",
        "## Largest spender-candidate pairs by raw row count",
        "",
        "| Spender | Candidate | Rows | Support/Oppose | Date start | Date end | Unreconciled raw amount |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for item in top_pairs:
        lines.append(f"| {str(item['spender_name']).replace('|', '/')} | {str(item['candidate_name']).replace('|', '/')} | {int(item['rows']):,} | {', '.join(item['support_oppose'])} | {item['date_start'] or ''} | {item['date_end'] or ''} | ${Decimal(item['raw_amount_sum_unreconciled']):,.2f} |")
    lines.extend(["", "## Target families", ""])
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(["", "```bash", "python3 scripts/import_dnc_fec_independent_expenditures.py", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main() -> int:
    ns = parse_args()
    if ns.cycle < 2000 or ns.cycle % 2:
        raise RuntimeError("cycle must be an even election year")
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        ie_path = temp / f"independent_expenditure_{ns.cycle}.csv"
        candidate_zip = temp / f"cn{str(ns.cycle)[-2:]}.zip"
        copy_or_download(ns.offline_ie_csv, cycle_url(IE_URL, ns.cycle), ie_path)
        copy_or_download(ns.offline_candidate_zip, cycle_url(CN_URL, ns.cycle), candidate_zip)
        manifest = scan(ie_path, candidate_zip, ns.output, ns.cycle, ns.generated_at)
    print(json.dumps({"documents": manifest["total_documents"], "matching_rows": manifest["matching_rows"], "output": str(ns.output), "pairs": manifest["spender_candidate_pairs"], "targets": manifest["total_targets"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
