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
CYCLE = 2026
GENERATED_AT = "2026-08-01T00:34:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-administrative-fines")
ADMIN_FINE_URL = "https://cg-519a459a-0ea3-42c2-b7bc-fa1143481f74.s3-us-gov-west-1.amazonaws.com/bulk-downloads/data.fec.gov/admin_fine.csv"
ADMIN_FINE_METADATA_URL = "https://www.fec.gov/legal-resources/enforcement/administrative-fines/administrative-fines-file-metadata/"
ADMIN_FINE_PROGRAM_URL = "https://www.fec.gov/legal-resources/enforcement/administrative-fines/"
COMMITTEE_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cm{yy}.zip"
COMMITTEE_DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/committee-master-file-description/"
PARTY_CODES_URL = "https://www.fec.gov/campaign-finance-data/party-code-descriptions/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
RUN_ID = "dnc-fec-administrative-fines-2026-07-31"
PARTY_CODES = {"DEM", "DFL"}
MAX_DOWNLOAD = 500_000_000
MAX_ROWS = 50_000
PARTITIONS = 32
NAME_LEAD_RE = re.compile(r"\b(?:DEMOCRAT(?:IC|S)?|DFL|DNC)\b", re.IGNORECASE)

COMMITTEE_FIELDS = [
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
REQUIRED_FIELDS = {
    "CAS_NUM",
    "COM_ID",
    "COM_NAM",
    "REP_TYP",
    "REP_YEA",
    "FIN_AMO",
    "OFF",
    "STA",
    "DIS",
    "CAN_NAM",
    "LAT_FIL_NOT_FIL",
    "PAI_YES_NO",
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
    "official FEC administrative-fine files, case pages, findings, challenges, reviewing-officer recommendations, Commission determinations, payment records, and Treasury referrals",
    "official FEC committee filings and report images",
    "court records, committee records, archives, and established reporting",
]

TARGET_AXES = (
    {
        "key": "complete-case-record",
        "label": "complete findings, challenge, determination, payment, and document record",
        "target_type": "fec_administrative_fine_complete_case_record",
        "penalty": 0.00,
        "question": "What complete official reason-to-believe finding, notification, proposed penalty, challenge, evidence, reviewing-officer recommendation, Commission vote, final determination, recalculation, payment, delinquency, Treasury referral, court review, and document record exists for Administrative Fine {case_number} involving {committee}?",
        "objectives": [
            "Acquire every official case document and preserve title, date, document type, page count, URI, and hash",
            "Create a chronological event ledger for the initial finding, challenge, recommendation, vote, final determination, payment, collection, referral, and closure",
            "Record proposed, recalculated, final, paid, unpaid, pending, partially paid, or transferred amounts separately",
            "Represent allegations, defenses, findings, and dispositions as distinct attributed claims rather than collapsing the case into a generic violation label",
        ],
        "next": "Fetch the official case page and every linked document, then build a disposition- and payment-aware chronological record",
    },
    {
        "key": "report-filing-history",
        "label": "underlying report, filing deadline, amendments, activity, and timeliness audit",
        "target_type": "fec_administrative_fine_report_audit",
        "penalty": 0.005,
        "question": "What filing deadline, coverage period, report type, level of activity, original filing, amendment history, receipt timestamp, technical issue, best-efforts defense, and official calculation supports Administrative Fine {case_number} involving {committee}?",
        "objectives": [
            "Acquire the underlying report, amendments, filing timestamps, FEC notices, and relevant filing calendar",
            "Reconstruct whether the report was late or not filed and calculate lateness using official dates",
            "Identify the activity amount and prior-violation factors used by the FEC's formula",
            "Audit claimed technical failures, disasters, staff issues, or other defenses against official records without substituting independent legal conclusions",
        ],
        "next": "Join the case to the committee's filing history, deadlines, report images, amendments, and official fine calculation",
    },
    {
        "key": "leadership-compliance-cross-ties",
        "label": "treasurer, officers, compliance vendors, counsel, and organizational cross-ties",
        "target_type": "fec_administrative_fine_leadership_compliance",
        "penalty": 0.01,
        "question": "Which treasurers, assistant treasurers, officers, compliance vendors, filing software, counsel, consultants, connected organizations, candidates, party bodies, and other committees relate to Administrative Fine {case_number} involving {committee}?",
        "objectives": [
            "Acquire the committee's complete registration and treasurer history covering the report and case dates",
            "Enumerate publicly named compliance vendors, filing software, counsel, consultants, and representatives",
            "Map the committee, officers, vendors, and counsel to candidates, party committees, public offices, companies, nonprofits, unions, and other enforcement matters",
            "Separate formal responsibility, representation, shared infrastructure, and mere common-vendor correlation",
        ],
        "next": "Join the case to committee registrations, statements of organization, filings, counsel appearances, vendor payments, and outside-role records",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FEC administrative-fine cases tied to Democratic committee leads")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-admin-fine-csv", type=Path)
    parser.add_argument("--offline-committee-zip", type=Path)
    return parser.parse_args()


def cycle_url(cycle: int) -> str:
    return COMMITTEE_URL.format(cycle=cycle, yy=str(cycle)[-2:])


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
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as handle:
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


def read_committees(path: Path) -> tuple[str, dict[str, dict[str, str]], int]:
    with zipfile.ZipFile(path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))]
        if not members:
            raise RuntimeError("committee-master ZIP contains no text member")
        member = max(members, key=lambda info: info.file_size).filename
        rows: dict[str, dict[str, str]] = {}
        with archive.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                if len(values) == len(COMMITTEE_FIELDS) + 1 and values[-1] == "":
                    values.pop()
                if len(values) != len(COMMITTEE_FIELDS):
                    raise RuntimeError(f"unexpected committee row width at line {line_number}: {len(values)}")
                row = dict(zip(COMMITTEE_FIELDS, values, strict=True))
                committee_id = row["CMTE_ID"].strip()
                if not committee_id:
                    raise RuntimeError(f"committee-master row {line_number} lacks ID")
                if committee_id in rows:
                    raise RuntimeError(f"duplicate committee ID: {committee_id}")
                rows[committee_id] = row
    return member, rows, len(rows)


def money(value: str) -> float:
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        return float(Decimal(cleaned or "0"))
    except (InvalidOperation, ValueError):
        raise RuntimeError(f"invalid administrative-fine amount: {value!r}")


def read_cases(path: Path, committees: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    cases: list[dict[str, str]] = []
    seen: set[str] = set()
    total = 0
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"administrative-fine CSV lacks fields: {sorted(missing)}")
        for row in reader:
            total += 1
            case_number = (row.get("CAS_NUM") or "").strip()
            if not case_number:
                raise RuntimeError(f"administrative-fine row {total + 1} lacks case number")
            if case_number in seen:
                raise RuntimeError(f"duplicate administrative-fine case number: {case_number}")
            seen.add(case_number)
            committee_id = (row.get("COM_ID") or "").strip()
            committee_name = (row.get("COM_NAM") or "").strip()
            committee = committees.get(committee_id)
            official_party = (committee or {}).get("CMTE_PTY_AFFILIATION", "").strip().upper()
            if official_party in PARTY_CODES:
                row["DNC_CLASSIFICATION_BASIS"] = "official_current_committee_master_party_code"
                row["DNC_CLASSIFICATION_PARTY_CODE"] = official_party
                cases.append(row)
            elif NAME_LEAD_RE.search(committee_name):
                row["DNC_CLASSIFICATION_BASIS"] = "explicit_democratic_name_lead_pending_party_resolution"
                row["DNC_CLASSIFICATION_PARTY_CODE"] = official_party
                cases.append(row)
        if total > MAX_ROWS:
            raise RuntimeError(f"administrative-fine CSV exceeds row cap {MAX_ROWS}")
    if not cases:
        raise RuntimeError("administrative-fine CSV yielded no Democratic cases or name leads")
    return sorted(cases, key=lambda row: int(row["CAS_NUM"])), total


def source_document(document_id: str, title: str, summary: str, uri: str, kind: str, file_sha: str | None, record_count: int | None, matching_count: int | None, when: str) -> dict[str, Any]:
    data: dict[str, Any] = {"accessed_at": when, "credibility": 1.0, "kind": kind, "publisher": "Federal Election Commission", "uri": uri}
    if file_sha:
        data["file_sha256"] = file_sha
    if record_count is not None:
        data["record_count"] = record_count
    if matching_count is not None:
        data["matching_record_count"] = matching_count
    document = {
        "_id": document_id,
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "administrative-fine", "official-source"],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    if file_sha:
        document["identifiers"] = [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "file_sha256", "value": file_sha}]
    validate_document(document)
    return document


def committee_document(row: dict[str, str], committee_master: dict[str, str] | None, source_ids: list[str], when: str) -> dict[str, Any]:
    committee_id = row["COM_ID"].strip()
    name = row["COM_NAM"].strip() or committee_id or "Unspecified committee"
    document_id = f"starintel:org:fec-committee-{committee_id.lower()}" if committee_id else sha_id("org", "fec-admin-fine-committee", name.lower())
    data = {
        "fec_committee_id": committee_id or None,
        "name": name,
        "org_type": "fec_administrative_fine_respondent_committee",
        "party_affiliation": (committee_master or {}).get("CMTE_PTY_AFFILIATION", "").strip().upper() or None,
        "classification_basis": row["DNC_CLASSIFICATION_BASIS"],
    }
    document = {
        "_id": document_id,
        "data": {key: value for key, value in data.items() if value is not None},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": "Official FEC administrative-fine respondent committee. DEM/DFL affiliation is represented only when found in the current committee master; explicit Democratic names without a current party code remain classification leads.",
        "tags": ["dnc", "fec", "committee", "administrative-fine", row["DNC_CLASSIFICATION_BASIS"].replace("_", "-")],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 5,
    }
    if committee_id:
        document["identifiers"] = [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_committee_id", "value": committee_id}]
    validate_document(document)
    return document


def case_event(row: dict[str, str], committee_id: str, source: str, when: str) -> dict[str, Any]:
    case_number = row["CAS_NUM"].strip()
    report_year = row["REP_YEA"].strip()
    report_type = row["REP_TYP"].strip()
    status = row["LAT_FIL_NOT_FIL"].strip().upper()
    paid = row["PAI_YES_NO"].strip().upper()
    fine = money(row["FIN_AMO"])
    document = {
        "_id": f"starintel:event:fec-administrative-fine-{case_number}",
        "data": {
            "case_number": case_number,
            "committee_id": committee_id,
            "event_kind": "fec_administrative_fine_case",
            "final_approved_fine": fine,
            "late_or_not_filed_code": status or None,
            "name": f"FEC Administrative Fine {case_number}",
            "payment_status_code": paid or None,
            "report_type": report_type or None,
            "report_year": int(report_year) if report_year.isdigit() else None,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "event",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "administrative_fine_case_number", "value": case_number}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"CAS_NUM {case_number}"}],
        "status": "recorded",
        "summary": f"Official FEC administrative-fine data reports final approved fine ${fine:,.2f} for case {case_number}, concerning report {report_type or 'unspecified'} for {report_year or 'an unspecified year'}, with late/not-filed code {status or 'unspecified'} and payment code {paid or 'unspecified'}.",
        "tags": ["dnc", "fec", "administrative-fine", "event", "official-disposition"],
        "temporal": {"observed_at": when},
        "title": f"FEC Administrative Fine {case_number}: {row['COM_NAM'].strip()}",
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    document["data"] = {key: value for key, value in document["data"].items() if value is not None}
    validate_document(document)
    return document


def financial_document(row: dict[str, str], committee_id: str, case_id: str, source: str, when: str) -> dict[str, Any]:
    case_number = row["CAS_NUM"].strip()
    fine = money(row["FIN_AMO"])
    paid = row["PAI_YES_NO"].strip().upper()
    qualifications = [
        "The FEC metadata defines FIN_AMO as the fine amount ultimately approved by the Commission.",
        "The payment field is preserved as an FEC code and should be reconciled to case-level payment and collection records.",
    ]
    document = {
        "_id": f"starintel:financial-observation:fec-administrative-fine-{case_number}",
        "data": {
            "amount": fine,
            "counterparty_ids": [case_id],
            "currency": "USD",
            "entity_id": committee_id,
            "methodology": "Direct import of FIN_AMO from the official FEC administrative-fine bulk file.",
            "observation_type": "fec_final_approved_administrative_fine",
            "period_end": None,
            "period_start": None,
            "qualifications": qualifications,
            "reported_at": None,
            "value_type": "final_approved_fine_amount",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "financial-observation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Federal Election Commission", "scheme": "administrative_fine_case_number", "value": case_number}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"CAS_NUM {case_number}", "metadata": {"payment_status_code": paid or None}}],
        "status": "recorded",
        "summary": f"The official FEC administrative-fine bulk file reports a final approved fine of ${fine:,.2f} in case {case_number}; payment status code is {paid or 'unspecified'}.",
        "tags": ["dnc", "fec", "administrative-fine", "financial-observation", "official-disposition"],
        "title": f"FEC Administrative Fine {case_number}: final approved fine",
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def relation_document(committee_id: str, case_id: str, row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    case_number = row["CAS_NUM"].strip()
    qualifiers = {
        "case_number": case_number,
        "classification_basis": row["DNC_CLASSIFICATION_BASIS"],
        "final_approved_fine": money(row["FIN_AMO"]),
        "late_or_not_filed_code": row["LAT_FIL_NOT_FIL"].strip().upper() or None,
        "payment_status_code": row["PAI_YES_NO"].strip().upper() or None,
        "report_type": row["REP_TYP"].strip() or None,
        "report_year": row["REP_YEA"].strip() or None,
    }
    qualifiers = {key: value for key, value in qualifiers.items() if value is not None}
    document = {
        "_id": sha_id("relation", committee_id, "respondent_in_fec_administrative_fine", case_id),
        "data": {"confidence": 1.0, "directed": True, "object": case_id, "predicate": "respondent_in_fec_administrative_fine", "qualifiers": qualifiers, "subject": committee_id},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source, "locator": f"CAS_NUM {case_number}"}],
        "status": "recorded",
        "summary": "The official FEC administrative-fine file identifies this committee as the respondent in the named case and reports the final approved fine and status codes.",
        "tags": ["dnc", "fec", "administrative-fine", "relation", "official-disposition"],
        "title": f"{row['COM_NAM'].strip()}: respondent in Administrative Fine {case_number}",
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def target_document(axis: dict[str, Any], row: dict[str, str], committee_id: str, case_id: str, source_ids: list[str], when: str) -> dict[str, Any]:
    case_number = row["CAS_NUM"].strip()
    committee = row["COM_NAM"].strip()
    question = axis["question"].format(case_number=case_number, committee=committee)
    priority = 0.98 if row["DNC_CLASSIFICATION_BASIS"].startswith("official") else 0.88
    target_id = sha_id("investigation-target", "dnc-fec-administrative-fine", case_number, str(axis["key"]))
    document = {
        "_id": target_id,
        "data": {
            "breadth": 100,
            "depth": 2,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official FEC administrative-fine case pages, documents, findings, challenges, recommendations, votes, determinations, payments, and collection records",
                "official committee registrations, filings, report images, deadlines, vendors, counsel, and public records",
                "court records, archives, and established reporting",
            ],
            "max_depth": 7,
            "objectives": axis["objectives"],
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": round(priority - float(axis["penalty"]), 4),
            "required_dtypes": ["source", "org", "person", "relation", "claim", "event", "financial-observation"],
            "research_question": question,
            "scope_type": "public_source",
            "seed_ids": [committee_id, case_id],
            "source_ids": source_ids,
            "status": "queued",
            "target": f"Administrative Fine {case_number}: {axis['label']}",
            "target_type": axis["target_type"],
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "investigation-target",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": question,
        "tags": ["dnc", "fec", "administrative-fine", "investigation-target", str(axis["key"]), row["DNC_CLASSIFICATION_BASIS"].replace("_", "-")],
        "title": f"Administrative Fine {case_number} / {committee}: {axis['label']}",
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-fec-record", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": axis["next"],
            "priority": round(priority - float(axis["penalty"]), 4),
            "queue": "dnc-fec-administrative-fines",
            "recursion_depth": 2,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def partition(document: dict[str, Any]) -> int:
    return int.from_bytes(hashlib.sha256(document["_id"].encode("utf-8")).digest()[:2], "big") % PARTITIONS


def build(cases: list[dict[str, str]], committees: dict[str, dict[str, str]], admin_source: str, committee_source: str, when: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    emitted: set[str] = set()
    inventory: list[dict[str, Any]] = []

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    for row in cases:
        committee_master = committees.get(row["COM_ID"].strip())
        committee = committee_document(row, committee_master, [admin_source, committee_source], when)
        case = case_event(row, committee["_id"], admin_source, when)
        financial = financial_document(row, committee["_id"], case["_id"], admin_source, when)
        relation = relation_document(committee["_id"], case["_id"], row, admin_source, when)
        for document in (committee, case, financial, relation):
            emit(document)
        target_ids: list[str] = []
        for axis in TARGET_AXES:
            target = target_document(axis, row, committee["_id"], case["_id"], [admin_source, committee_source], when)
            emit(target)
            target_ids.append(target["_id"])
        inventory.append(
            {
                "case_number": row["CAS_NUM"].strip(),
                "classification_basis": row["DNC_CLASSIFICATION_BASIS"],
                "committee_id": row["COM_ID"].strip() or None,
                "committee_name": row["COM_NAM"].strip(),
                "event_id": case["_id"],
                "final_approved_fine": money(row["FIN_AMO"]),
                "late_or_not_filed_code": row["LAT_FIL_NOT_FIL"].strip().upper() or None,
                "party_code": row["DNC_CLASSIFICATION_PARTY_CODE"] or None,
                "payment_status_code": row["PAI_YES_NO"].strip().upper() or None,
                "report_type": row["REP_TYP"].strip() or None,
                "report_year": row["REP_YEA"].strip() or None,
                "target_ids": target_ids,
            }
        )
    return documents, inventory


def write(output: Path, sources: list[dict[str, Any]], documents: list[dict[str, Any]], inventory: list[dict[str, Any]], metadata: dict[str, Any], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    root_payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in sources).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(root_payload)
    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    for document in documents:
        buckets[partition(document)].append(document)
    partitions: list[dict[str, Any]] = []
    stream_hash = hashlib.sha256(root_payload)
    for index, bucket in enumerate(buckets):
        directory = output / f"part-{index:02d}"
        directory.mkdir()
        payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in sorted(bucket, key=lambda item: item["_id"])).encode("utf-8")
        (directory / "starintel-documents.jsonl").write_bytes(payload)
        stream_hash.update(payload)
        partitions.append({"documents": len(bucket), "part": index, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)})
    source_dir = output / "source"
    source_dir.mkdir()
    inventory_bytes = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in inventory).encode("utf-8")
    (source_dir / "administrative-fine-inventory.jsonl").write_bytes(inventory_bytes)
    all_documents = [*sources, *documents]
    counts = Counter(document["dtype"] for document in all_documents)
    classifications = Counter(item["classification_basis"] for item in inventory)
    payments = Counter(item["payment_status_code"] or "unspecified" for item in inventory)
    target_counts = Counter(document["data"]["target_type"] for document in documents if document["dtype"] == "investigation-target")
    manifest = {
        **metadata,
        "classification_counts": dict(sorted(classifications.items())),
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_stream_sha256": stream_hash.hexdigest(),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "matching_cases": len(inventory),
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "party_codes": sorted(PARTY_CODES),
        "party_codes_url": PARTY_CODES_URL,
        "payment_status_counts": dict(sorted(payments.items())),
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(all_documents),
        "total_final_approved_fines": sum(Decimal(str(item["final_approved_fine"])) for item in inventory),
        "total_targets": sum(target_counts.values()),
    }
    manifest["total_final_approved_fines"] = str(manifest["total_final_approved_fines"])
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# FEC administrative fines involving Democratic committee records and explicit name leads",
        "",
        "Official FEC administrative-fine bulk records classified by current FEC committee-master party code where available. Explicit Democratic/DFL/DNC committee names without a current DEM/DFL code remain name-derived leads and are not represented as verified party affiliation.",
        "",
        f"- matching cases: {len(inventory):,}",
        f"- official DEM/DFL committee-master classifications: {classifications.get('official_current_committee_master_party_code', 0):,}",
        f"- explicit-name leads pending party resolution: {classifications.get('explicit_democratic_name_lead_pending_party_resolution', 0):,}",
        f"- StarIntel documents: {len(all_documents):,}",
        f"- recursive investigation targets: {sum(target_counts.values()):,}",
        f"- final approved fine amounts in selected bulk rows: ${Decimal(manifest['total_final_approved_fines']):,.2f}",
        "",
        "The FEC metadata defines `FIN_AMO` as the fine ultimately approved by the Commission. Payment codes are preserved but require reconciliation to case-level payment, collection, and Treasury records. A fine case is represented by its procedural record and disposition—not as a generic corruption or criminal label.",
        "",
        "## Classification",
        "",
    ]
    for key, count in sorted(classifications.items()):
        lines.append(f"- `{key}`: {count:,}")
    lines.extend(["", "## Target families", ""])
    for key, count in sorted(target_counts.items()):
        lines.append(f"- `{key}`: {count:,}")
    lines.extend(["", "```bash", "python3 scripts/import_dnc_fec_administrative_fines.py", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        admin_csv = temp / "admin_fine.csv"
        committee_zip = temp / f"cm{str(ns.cycle)[-2:]}.zip"
        copy_or_download(ns.offline_admin_fine_csv, ADMIN_FINE_URL, admin_csv)
        copy_or_download(ns.offline_committee_zip, cycle_url(ns.cycle), committee_zip)
        committee_member, committees, committee_count = read_committees(committee_zip)
        cases, total_rows = read_cases(admin_csv, committees)
        admin_source_id = "starintel:source:fec-administrative-fine-bulk-2026-07-31"
        committee_source_id = f"starintel:source:fec-committee-master-admin-fine-resolution-{ns.cycle}"
        sources = [
            source_document(admin_source_id, "FEC administrative-fine bulk data", "Official FEC bulk administrative-fine cases from the program beginning with the 2000 July Quarterly reports.", ADMIN_FINE_URL, "official_fec_administrative_fine_bulk", file_sha256(admin_csv), total_rows, len(cases), ns.generated_at),
            source_document(committee_source_id, f"FEC {ns.cycle} committee master for administrative-fine classification", "Official current-cycle committee master used to verify DEM and DFL party codes where available; mailing address fields are not emitted.", cycle_url(ns.cycle), "official_fec_committee_master", file_sha256(committee_zip), committee_count, None, ns.generated_at),
            source_document("starintel:source:fec-administrative-fine-metadata", "FEC administrative-fine file metadata", "Official FEC data dictionary defining case, committee, report, final fine, late/not-filed, and payment fields.", ADMIN_FINE_METADATA_URL, "official_fec_data_dictionary", None, None, None, ns.generated_at),
        ]
        documents, inventory = build(cases, committees, admin_source_id, committee_source_id, ns.generated_at)
        metadata = {
            "administrative_fine_metadata_url": ADMIN_FINE_METADATA_URL,
            "administrative_fine_program_url": ADMIN_FINE_PROGRAM_URL,
            "administrative_fine_url": ADMIN_FINE_URL,
            "committee_master_archive_member": committee_member,
            "committee_master_description_url": COMMITTEE_DESCRIPTION_URL,
            "committee_master_url": cycle_url(ns.cycle),
            "raw_administrative_fine_rows": total_rows,
            "raw_administrative_fine_sha256": file_sha256(admin_csv),
            "raw_committee_master_rows": committee_count,
            "raw_committee_master_sha256": file_sha256(committee_zip),
        }
        write(ns.output, sources, documents, inventory, metadata, ns.generated_at)
    print(json.dumps({"cases": len(inventory), "documents": len(sources) + len(documents), "output": str(ns.output), "targets": sum(1 for document in documents if document["dtype"] == "investigation-target")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
