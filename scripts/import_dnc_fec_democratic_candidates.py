#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
CYCLE = 2026
GENERATED_AT = "2026-07-31T23:04:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-democratic-candidates-2026")
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
CANDIDATE_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cn{yy}.zip"
LINKAGE_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/ccl{yy}.zip"
COMMITTEE_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cm{yy}.zip"
CANDIDATE_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/candidate-master-file-description/"
LINKAGE_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/"
COMMITTEE_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/committee-master-file-description/"
PARTY_CODES_URL = "https://www.fec.gov/campaign-finance-data/party-code-descriptions/"
PARTY_CODES = {"DEM", "DFL"}
DEMOCRATIC_PARTY_ID = "starintel:org:democratic-party-fec-affiliation"
RUN_ID = "dnc-fec-democratic-candidates-2026-07-31"
MAX_DOWNLOAD = 300_000_000
MAX_CANDIDATES = 30_000
MAX_LINKAGES = 100_000
PARTITIONS = 64

CANDIDATE_FIELDS = [
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
LINKAGE_FIELDS = [
    "CAND_ID",
    "CAND_ELECTION_YR",
    "FEC_ELECTION_YR",
    "CMTE_ID",
    "CMTE_TP",
    "CMTE_DSGN",
    "LINKAGE_ID",
]
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
    "Federal Election Commission filings and bulk data",
    "official candidate, campaign, party, government, and committee records",
    "state campaign-finance, election, corporate, nonprofit, and lobbying records",
    "court records, archives, and established published reporting",
]

CANDIDATE_AXES = (
    {
        "key": "identity-filing-biography",
        "label": "identity, candidacy filings, biography, and election history",
        "target_type": "fec_candidate_identity_filing_history",
        "penalty": 0.00,
        "question": "Which primary records establish {name}'s exact identity, candidacy, office sought, election history, status, biography, and filing chronology?",
        "objectives": [
            "Acquire every Statement of Candidacy, amendment, termination, ballot record, and official candidate biography",
            "Resolve namesakes and former names without merging distinct candidates",
            "Record office, state, district, election year, incumbent/challenger/open-seat status, candidate status, and filing dates",
            "Map prior and subsequent elections, public offices, appointments, and campaign entities",
        ],
        "next": "Collect the complete FEC candidacy filing history, official ballot records, campaign biographies, and archived candidate pages",
    },
    {
        "key": "committee-network",
        "label": "principal, authorized, joint-fundraising, leadership-PAC, and affiliate network",
        "target_type": "fec_candidate_committee_network",
        "penalty": 0.005,
        "question": "Which principal, authorized, joint-fundraising, leadership-PAC, party, and affiliated committees connect to {name}, and through which formal or operational relationships?",
        "objectives": [
            "Resolve every FEC candidate-committee linkage and principal campaign committee",
            "Acquire each committee's registration history, officers, treasurers, custodians, connected organizations, and amendments",
            "Map joint fundraising, transfers, shared staff, shared vendors, shared addresses, and affiliated committees",
            "Distinguish FEC authorization or linkage from inferred operational control",
        ],
        "next": "Join all FEC linkage cycles and committee registrations, then enumerate every linked committee and officer",
    },
    {
        "key": "staff-consultants-vendors",
        "label": "campaign staff, consultants, contractors, and vendors",
        "target_type": "fec_candidate_staff_consultants_vendors",
        "penalty": 0.015,
        "question": "Who works for or contracts with {name}'s campaign network, including managers, finance staff, field staff, pollsters, media firms, legal counsel, compliance vendors, fundraisers, technology providers, and subcontractors?",
        "objectives": [
            "Enumerate current and archived campaign staff, consultants, advisors, surrogates, and public job postings",
            "Resolve expenditure payees into legal organizations, principals, staff, subcontractors, and payment processors",
            "Separate direct employment, consulting, independent contracting, in-kind support, coordinated-party staffing, and volunteer roles",
            "Map every principal to other campaigns, committees, government roles, companies, nonprofits, and lobbying clients",
        ],
        "next": "Combine official campaign pages, filings, expenditure purposes, contracts, staff announcements, archives, and professional records",
    },
    {
        "key": "finance-donors-transfers",
        "label": "receipts, donors, transfers, loans, debts, and disbursement network",
        "target_type": "fec_candidate_finance_network",
        "penalty": 0.005,
        "question": "What amendment-aware money network connects {name}'s campaigns to donors, committees, party organizations, conduits, lenders, vendors, recipients, and other counterparties?",
        "objectives": [
            "Import itemized receipts, committee contributions, transfers, operating expenditures, independent expenditures, loans, debts, refunds, and offsets",
            "Preserve amendment, memo, conduit, earmark, reattribution, refund, and raw filing identifiers",
            "Rank counterparties by unreconciled row count and amount without presenting raw amended records as final totals",
            "Create source-scoped donor, employer, occupation, organization, committee, and financial-observation records",
        ],
        "next": "Import official FEC and state transaction files and build amendment-aware receipts, transfers, debt, and payee indexes",
    },
    {
        "key": "public-role-organizational-cross-ties",
        "label": "public office, employment, boards, lobbying, and organizational cross-ties",
        "target_type": "fec_candidate_public_role_cross_ties",
        "penalty": 0.01,
        "question": "Which public offices, agencies, employers, companies, boards, nonprofits, unions, advocacy groups, lobbying clients, funders, and vendors connect to {name} before, during, and after the candidacy?",
        "objectives": [
            "Enumerate current and historical public employment, elected and appointed office, board, nonprofit, union, corporate, academic, and advocacy roles",
            "Trace financial disclosures, lobbying, contracts, grants, donations, ownership, investments, and governance relationships",
            "Map endorsements, coalitions, major surrogates, institutional support, and opposition using attributable sources",
            "Separate verified facts, attributed claims, contradictions, and unresolved identity matches",
        ],
        "next": "Search official biographies, ethics disclosures, government records, corporate and nonprofit filings, lobbying records, archives, and established reporting",
    },
)

LINKAGE_AXES = (
    {
        "key": "registration-officers",
        "label": "committee registration, treasurers, officers, and governance",
        "target_type": "fec_candidate_linked_committee_registration",
        "penalty": 0.00,
        "question": "What complete registration, amendment, officer, treasurer, custodian, connected-organization, and termination history governs {committee}, linked to {candidate}?",
        "objectives": [
            "Acquire every Statement of Organization, amendment, termination, and FEC correspondence item",
            "Enumerate treasurers, assistant treasurers, custodians, officers, controlling persons, and connected organizations",
            "Record exact role dates, filing images, designations, committee types, linkage IDs, and candidate authorization",
        ],
        "next": "Collect the committee's full FEC registration and amendment history and enumerate every named officer and connected organization",
    },
    {
        "key": "money-vendors",
        "label": "receipts, transfers, spending, staff, consultants, and vendors",
        "target_type": "fec_candidate_linked_committee_money_vendors",
        "penalty": 0.005,
        "question": "What amendment-aware receipts, transfers, expenditures, debts, staff, consultants, and vendors comprise {committee}, linked to {candidate}?",
        "objectives": [
            "Import official receipts, transfers, disbursements, debts, loans, refunds, and offsets",
            "Resolve recurring donors, payees, staff, consultants, counsel, compliance firms, fundraisers, technology providers, and subcontractors",
            "Preserve raw filing semantics and distinguish direct payments, pass-throughs, reimbursements, in-kind support, and shared vendors",
        ],
        "next": "Build amendment-aware transaction and counterparty indexes and resolve every recurring public staff and vendor entity",
    },
    {
        "key": "joint-fundraising-affiliates",
        "label": "joint fundraising, affiliates, shared infrastructure, and cross-candidate ties",
        "target_type": "fec_candidate_linked_committee_affiliates",
        "penalty": 0.01,
        "question": "Which joint-fundraising committees, leadership PACs, party committees, candidate committees, nonprofits, companies, and shared service providers connect to {committee} and {candidate}?",
        "objectives": [
            "Map formal candidate-committee linkages, affiliated committees, joint fundraising participants, transfer networks, and shared officers",
            "Trace shared staff, vendors, counsel, compliance, fundraising, data, media, technology, and payment infrastructure",
            "Create evidence-qualified cross-candidate and cross-organization relations without inferring control from common vendors alone",
        ],
        "next": "Join committee registrations, transfers, joint fundraising notices, shared officers, and vendor records across election cycles",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FEC Democratic and DFL candidates and committee linkages")
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-candidate-zip", type=Path)
    parser.add_argument("--offline-linkage-zip", type=Path)
    parser.add_argument("--offline-committee-zip", type=Path)
    return parser.parse_args()


def cycle_url(template: str, cycle: int) -> str:
    return template.format(cycle=cycle, yy=str(cycle)[-2:])


def sha_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:{prefix}:{digest}"


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    total = 0
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as handle:
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
        candidates = [
            info
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
        if not candidates:
            raise RuntimeError(f"ZIP contains no text member: {path}")
        return max(candidates, key=lambda info: info.file_size).filename


def read_delimited(path: Path, fields: list[str]) -> tuple[str, list[dict[str, str]]]:
    member = largest_text_member(path)
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(path) as archive, archive.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
        for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
            if len(values) == len(fields) + 1 and values[-1] == "":
                values.pop()
            if len(values) != len(fields):
                raise RuntimeError(f"unexpected row width in {member} at {line_number}: {len(values)}")
            rows.append(dict(zip(fields, values, strict=True)))
    if not rows:
        raise RuntimeError(f"bulk member is empty: {member}")
    return member, rows


def source_document(
    *,
    document_id: str,
    title: str,
    summary: str,
    uri: str,
    description_uri: str,
    member: str,
    file_sha256: str,
    rows: int,
    matching_rows: int,
    when: str,
) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {
            "accessed_at": when,
            "archive_member": member,
            "credibility": 1.0,
            "description_uri": description_uri,
            "file_sha256": file_sha256,
            "kind": "official_fec_bulk_data",
            "matching_record_count": matching_rows,
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
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission", "scheme": "bulk_file_sha256", "value": file_sha256}
        ],
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "official-source", "democratic-candidates"],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def party_document(source_ids: list[str], when: str) -> dict[str, Any]:
    document = {
        "_id": DEMOCRATIC_PARTY_ID,
        "data": {
            "name": "Democratic Party and Democratic-Farmer-Labor FEC affiliation grouping",
            "org_type": "political_party_affiliation_group",
            "party_codes": sorted(PARTY_CODES),
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission", "scheme": "party_code_set", "value": "DEM|DFL"}
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": "Source-scoped grouping for FEC party affiliation codes DEM and DFL; it does not itself establish DNC governance or control over every candidate or committee carrying those codes.",
        "tags": ["dnc", "fec", "democratic-party", "party-affiliation"],
        "title": "Democratic Party / DFL FEC affiliation grouping",
        "verification": {"last_reviewed_at": when, "status": "official-code-mapping", "verified": True},
        "version": 2,
    }
    validate_document(document)
    return document


def candidate_id(row: dict[str, str]) -> str:
    return f"starintel:person:fec-candidate-{row['CAND_ID'].strip().lower()}"


def committee_id(fec_id: str) -> str:
    return f"starintel:org:fec-committee-{fec_id.strip().lower()}"


def candidate_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row["CAND_ID"].strip()
    name = row["CAND_NAME"].strip()
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
    data = {key: value for key, value in data.items() if value is not None}
    document = {
        "_id": candidate_id(row),
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_candidate_id", "value": fec_id}
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official FEC candidate-master record for {name}, reporting party affiliation {row['CAND_PTY_AFFILIATION'].strip().upper()}; mailing address fields are not emitted.",
        "tags": ["dnc", "fec", "candidate", row["CAND_PTY_AFFILIATION"].strip().lower()],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


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
        "org_type": "fec_candidate_linked_committee",
        "party_affiliation": row["CMTE_PTY_AFFILIATION"].strip().upper() or None,
        "reported_connected_organization": row["CONNECTED_ORG_NM"].strip() or None,
        "reported_treasurer": row["TRES_NM"].strip() or None,
    }
    data = {key: value for key, value in data.items() if value is not None}
    document = {
        "_id": committee_id(fec_id),
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission", "scheme": "fec_committee_id", "value": fec_id}
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official FEC committee-master record for {name}, selected because it is linked to a DEM or DFL candidate; mailing address fields are not emitted.",
        "tags": ["dnc", "fec", "committee", "candidate-linked"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 2,
    }
    validate_document(document)
    return document


def relation_document(
    *,
    subject: str,
    predicate: str,
    obj: str,
    title: str,
    summary: str,
    qualifiers: dict[str, Any],
    sources: list[str],
    when: str,
) -> dict[str, Any]:
    relation = {
        "_id": sha_id("relation", subject, predicate, obj, json.dumps(qualifiers, sort_keys=True)),
        "data": {
            "confidence": 0.99,
            "directed": True,
            "object": obj,
            "predicate": predicate,
            "qualifiers": qualifiers,
            "subject": subject,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in sources],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "candidate", "committee", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(relation)
    return relation


def target_document(
    *,
    target_id: str,
    target_title: str,
    summary: str,
    research_question: str,
    objectives: list[str],
    next_action: str,
    target_type: str,
    seed_ids: list[str],
    source_ids: list[str],
    priority: float,
    when: str,
    tags: list[str],
    depth: int,
    breadth: int,
) -> dict[str, Any]:
    document = {
        "_id": target_id,
        "data": {
            "breadth": breadth,
            "depth": depth,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official FEC and state campaign-finance records",
                "official candidate, campaign, party, committee, government, corporate, nonprofit, and union records",
                "court records, ethics disclosures, lobbying records, public archives, and established reporting",
            ],
            "max_depth": 7,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": priority,
            "required_dtypes": ["source", "org", "person", "relation", "claim", "event", "financial-observation"],
            "research_question": research_question,
            "scope_type": "public_source",
            "seed_ids": seed_ids,
            "source_ids": source_ids,
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
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "investigation-target", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-fec-record", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-fec-democratic-candidates",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def candidate_priority(row: dict[str, str]) -> float:
    status = row["CAND_STATUS"].strip().upper()
    election_year = row["CAND_ELECTION_YR"].strip()
    office = row["CAND_OFFICE"].strip().upper()
    base = 0.96 if status in {"C", "F"} and election_year == str(CYCLE) else 0.91
    if office == "P":
        base += 0.03
    elif office == "S":
        base += 0.02
    elif office == "H":
        base += 0.01
    if row["CAND_PCC"].strip():
        base += 0.005
    return round(min(1.0, base), 4)


def build(
    candidates: list[dict[str, str]],
    linkages: list[dict[str, str]],
    committees: dict[str, dict[str, str]],
    source_ids: dict[str, str],
    when: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = [party_document(list(source_ids.values()), when)]
    emitted: set[str] = {documents[0]["_id"]}
    candidate_inventory: list[dict[str, Any]] = []
    linkage_inventory: list[dict[str, Any]] = []
    candidate_rows = {row["CAND_ID"].strip(): row for row in candidates}
    linkages_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for linkage in linkages:
        linkages_by_candidate[linkage["CAND_ID"].strip()].append(linkage)

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    for fec_candidate_id, row in sorted(candidate_rows.items(), key=lambda item: (item[1]["CAND_NAME"].strip().lower(), item[0])):
        candidate = candidate_document(row, source_ids["candidate"], when)
        emit(candidate)
        candidate_node = candidate["_id"]
        name = candidate["title"]
        party_code = row["CAND_PTY_AFFILIATION"].strip().upper()
        priority = candidate_priority(row)
        candidate_target_ids: list[str] = []
        linked_committee_nodes: list[str] = []

        emit(
            relation_document(
                subject=candidate_node,
                predicate="fec_reported_party_affiliation",
                obj=DEMOCRATIC_PARTY_ID,
                title=f"{name}: FEC party affiliation {party_code}",
                summary=f"The FEC candidate master reports party affiliation {party_code}; this does not by itself establish DNC governance or endorsement.",
                qualifiers={"cycle": CYCLE, "fec_candidate_id": fec_candidate_id, "party_code": party_code},
                sources=[source_ids["candidate"]],
                when=when,
            )
        )

        for axis in CANDIDATE_AXES:
            target_id = sha_id("investigation-target", "dnc-fec-candidate", fec_candidate_id, str(axis["key"]))
            question = axis["question"].format(name=name)
            candidate_target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{name}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[candidate_node, DEMOCRATIC_PARTY_ID],
                    source_ids=[source_ids["candidate"], source_ids["linkage"], source_ids["committee"]],
                    priority=round(priority - float(axis["penalty"]), 4),
                    when=when,
                    tags=["candidate", party_code.lower(), str(axis["key"])],
                    depth=1,
                    breadth=180,
                )
            )

        pcc = row["CAND_PCC"].strip()
        if pcc and pcc in committees:
            committee = committee_document(committees[pcc], source_ids["committee"], when)
            emit(committee)
            linked_committee_nodes.append(committee["_id"])
            emit(
                relation_document(
                    subject=candidate_node,
                    predicate="fec_reported_principal_campaign_committee",
                    obj=committee["_id"],
                    title=f"{name}: principal campaign committee {committee['title']}",
                    summary="The FEC candidate master reports this committee as the candidate's principal campaign committee for the cycle.",
                    qualifiers={"cycle": CYCLE, "fec_candidate_id": fec_candidate_id, "fec_committee_id": pcc},
                    sources=[source_ids["candidate"], source_ids["committee"]],
                    when=when,
                )
            )

        for linkage in sorted(linkages_by_candidate.get(fec_candidate_id, []), key=lambda value: (value["CMTE_ID"], value["LINKAGE_ID"])):
            committee_fec_id = linkage["CMTE_ID"].strip()
            committee_row = committees.get(committee_fec_id)
            if not committee_row:
                raise RuntimeError(f"linked committee {committee_fec_id} is missing from committee master")
            committee = committee_document(committee_row, source_ids["committee"], when)
            emit(committee)
            committee_node = committee["_id"]
            if committee_node not in linked_committee_nodes:
                linked_committee_nodes.append(committee_node)
            qualifiers = {
                "candidate_election_year": linkage["CAND_ELECTION_YR"].strip() or None,
                "committee_designation": linkage["CMTE_DSGN"].strip() or None,
                "committee_type": linkage["CMTE_TP"].strip() or None,
                "fec_election_year": linkage["FEC_ELECTION_YR"].strip() or None,
                "linkage_id": linkage["LINKAGE_ID"].strip(),
            }
            qualifiers = {key: value for key, value in qualifiers.items() if value is not None}
            relation = relation_document(
                subject=candidate_node,
                predicate="fec_candidate_committee_linkage",
                obj=committee_node,
                title=f"{name}: FEC linkage to {committee['title']}",
                summary="The official FEC candidate-committee linkage file connects this candidate and committee with the reported type, designation, election year, and linkage ID.",
                qualifiers=qualifiers,
                sources=[source_ids["linkage"], source_ids["candidate"], source_ids["committee"]],
                when=when,
            )
            emit(relation)
            linkage_target_ids: list[str] = []
            for axis in LINKAGE_AXES:
                target_id = sha_id("investigation-target", "dnc-fec-candidate-linkage", fec_candidate_id, committee_fec_id, linkage["LINKAGE_ID"].strip(), str(axis["key"]))
                question = axis["question"].format(candidate=name, committee=committee["title"])
                linkage_target_ids.append(target_id)
                emit(
                    target_document(
                        target_id=target_id,
                        target_title=f"{name} / {committee['title']}: {axis['label']}",
                        summary=question,
                        research_question=question,
                        objectives=list(axis["objectives"]),
                        next_action=str(axis["next"]),
                        target_type=str(axis["target_type"]),
                        seed_ids=[candidate_node, committee_node, relation["_id"]],
                        source_ids=[source_ids["linkage"], source_ids["candidate"], source_ids["committee"]],
                        priority=round(max(0.5, priority - float(axis["penalty"])), 4),
                        when=when,
                        tags=["candidate", "committee-linkage", party_code.lower(), str(axis["key"])],
                        depth=2,
                        breadth=120,
                    )
                )
            linkage_inventory.append(
                {
                    "candidate": name,
                    "candidate_id": fec_candidate_id,
                    "committee": committee["title"],
                    "committee_id": committee_fec_id,
                    "committee_node": committee_node,
                    "linkage_id": linkage["LINKAGE_ID"].strip(),
                    "qualifiers": qualifiers,
                    "target_ids": linkage_target_ids,
                }
            )

        candidate_inventory.append(
            {
                "candidate": name,
                "candidate_id": fec_candidate_id,
                "candidate_node": candidate_node,
                "election_year": row["CAND_ELECTION_YR"].strip() or None,
                "linked_committee_nodes": linked_committee_nodes,
                "office": row["CAND_OFFICE"].strip() or None,
                "office_state": row["CAND_OFFICE_ST"].strip() or None,
                "party_affiliation": party_code,
                "principal_campaign_committee_id": pcc or None,
                "priority": priority,
                "status": row["CAND_STATUS"].strip() or None,
                "target_ids": candidate_target_ids,
            }
        )

    return documents, candidate_inventory, linkage_inventory


def partition(document: dict[str, Any]) -> int:
    digest = hashlib.sha256(document["_id"].encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % PARTITIONS


def write(
    output: Path,
    source_documents: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    candidate_inventory: list[dict[str, Any]],
    linkage_inventory: list[dict[str, Any]],
    metadata: dict[str, Any],
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    root_payload = "".join(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        for document in source_documents
    ).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(root_payload)

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    for document in documents:
        buckets[partition(document)].append(document)
    stream_hash = hashlib.sha256(root_payload)
    partitions: list[dict[str, Any]] = []
    for index, bucket in enumerate(buckets):
        directory = output / f"part-{index:02d}"
        directory.mkdir()
        payload = "".join(
            json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
            for document in sorted(bucket, key=lambda item: item["_id"])
        ).encode("utf-8")
        (directory / "starintel-documents.jsonl").write_bytes(payload)
        stream_hash.update(payload)
        partitions.append({"documents": len(bucket), "part": index, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)})

    candidate_bytes = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in candidate_inventory
    ).encode("utf-8")
    linkage_bytes = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in linkage_inventory
    ).encode("utf-8")
    (output / "source/candidate-inventory.jsonl").write_bytes(candidate_bytes)
    (output / "source/linkage-inventory.jsonl").write_bytes(linkage_bytes)

    all_documents = [*source_documents, *documents]
    counts = Counter(document["dtype"] for document in all_documents)
    target_counts = Counter(
        document["data"]["target_type"]
        for document in documents
        if document["dtype"] == "investigation-target"
    )
    manifest = {
        **metadata,
        "candidate_inventory_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_stream_sha256": stream_hash.hexdigest(),
        "generated_at": when,
        "linkage_inventory_sha256": hashlib.sha256(linkage_bytes).hexdigest(),
        "matching_candidates": len(candidate_inventory),
        "matching_linkages": len(linkage_inventory),
        "party_codes": sorted(PARTY_CODES),
        "party_codes_url": PARTY_CODES_URL,
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(all_documents),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    top = sorted(candidate_inventory, key=lambda item: (-float(item["priority"]), str(item["candidate"]).lower(), str(item["candidate_id"])))[:50]
    lines = [
        "# FEC Democratic and DFL candidates and committee linkages",
        "",
        "Official 2026 FEC candidate-master and candidate-committee-linkage records filtered to candidates whose reported party affiliation is `DEM` or `DFL`.",
        "",
        f"- matching candidates: {len(candidate_inventory):,}",
        f"- candidate-committee linkages: {len(linkage_inventory):,}",
        f"- StarIntel documents: {len(all_documents):,}",
        f"- investigation targets: {sum(target_counts.values()):,}",
        f"- candidate records: {counts.get('person', 0):,}",
        f"- linked committee records: {counts.get('org', 0):,}",
        f"- relation records: {counts.get('relation', 0):,}",
        f"- GitHub-safe partitions: {PARTITIONS}",
        "",
        "Candidate and committee mailing-address fields are deliberately not emitted. A DEM or DFL affiliation is an FEC-reported party code, not automatic evidence of DNC governance, endorsement, or operational control. Candidate and committee finance targets require amendment-aware treatment rather than flattening raw filings into final totals.",
        "",
        "## Highest-priority candidate leads",
        "",
        "| Candidate | FEC ID | Party | Office | State | Election | Status | Priority |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for item in top:
        lines.append(
            f"| {str(item['candidate']).replace('|', '/')} | {item['candidate_id']} | {item['party_affiliation']} | {item['office'] or ''} | {item['office_state'] or ''} | {item['election_year'] or ''} | {item['status'] or ''} | {float(item['priority']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Target families",
            "",
        ]
    )
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(
        [
            "",
            "```bash",
            "python3 scripts/import_dnc_fec_democratic_candidates.py",
            "python3 scripts/validate-for-merge.py --site",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    if ns.cycle < 2000 or ns.cycle % 2:
        raise RuntimeError("cycle must be an even election year")
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        candidate_zip = temp / f"cn{str(ns.cycle)[-2:]}.zip"
        linkage_zip = temp / f"ccl{str(ns.cycle)[-2:]}.zip"
        committee_zip = temp / f"cm{str(ns.cycle)[-2:]}.zip"
        candidate_uri = cycle_url(CANDIDATE_URL, ns.cycle)
        linkage_uri = cycle_url(LINKAGE_URL, ns.cycle)
        committee_uri = cycle_url(COMMITTEE_URL, ns.cycle)
        copy_or_download(ns.offline_candidate_zip, candidate_uri, candidate_zip)
        copy_or_download(ns.offline_linkage_zip, linkage_uri, linkage_zip)
        copy_or_download(ns.offline_committee_zip, committee_uri, committee_zip)

        candidate_member, all_candidates = read_delimited(candidate_zip, CANDIDATE_FIELDS)
        linkage_member, all_linkages = read_delimited(linkage_zip, LINKAGE_FIELDS)
        committee_member, all_committees = read_delimited(committee_zip, COMMITTEE_FIELDS)

        candidates = [
            row
            for row in all_candidates
            if row["CAND_PTY_AFFILIATION"].strip().upper() in PARTY_CODES
        ]
        if not candidates or len(candidates) > MAX_CANDIDATES:
            raise RuntimeError(f"unexpected DEM/DFL candidate count: {len(candidates)}")
        candidate_ids = {row["CAND_ID"].strip() for row in candidates}
        if len(candidate_ids) != len(candidates):
            raise RuntimeError("candidate master contains duplicate DEM/DFL candidate IDs")
        linkages = [row for row in all_linkages if row["CAND_ID"].strip() in candidate_ids]
        if len(linkages) > MAX_LINKAGES:
            raise RuntimeError(f"matching candidate-committee linkages exceed cap: {len(linkages)}")
        linkage_ids = [row["LINKAGE_ID"].strip() for row in linkages]
        if len(linkage_ids) != len(set(linkage_ids)):
            raise RuntimeError("matching candidate-committee linkage IDs are not unique")
        linked_committee_ids = {row["CMTE_ID"].strip() for row in linkages if row["CMTE_ID"].strip()}
        linked_committee_ids.update(row["CAND_PCC"].strip() for row in candidates if row["CAND_PCC"].strip())
        committee_rows = {row["CMTE_ID"].strip(): row for row in all_committees if row["CMTE_ID"].strip() in linked_committee_ids}
        missing = sorted(linked_committee_ids - committee_rows.keys())
        if missing:
            raise RuntimeError(f"candidate-linked committees missing from committee master: {missing[:20]}")

        source_ids = {
            "candidate": f"starintel:source:fec-candidate-master-democratic-{ns.cycle}",
            "linkage": f"starintel:source:fec-candidate-committee-linkage-democratic-{ns.cycle}",
            "committee": f"starintel:source:fec-committee-master-candidate-linked-{ns.cycle}",
        }
        source_documents = [
            source_document(
                document_id=source_ids["candidate"],
                title=f"FEC {ns.cycle} candidate master — DEM and DFL candidates",
                summary="Official FEC candidate-master rows whose reported party affiliation is DEM or DFL; all mailing-address fields are excluded from emitted records.",
                uri=candidate_uri,
                description_uri=CANDIDATE_DESCRIPTION,
                member=candidate_member,
                file_sha256=hashlib.sha256(candidate_zip.read_bytes()).hexdigest(),
                rows=len(all_candidates),
                matching_rows=len(candidates),
                when=ns.generated_at,
            ),
            source_document(
                document_id=source_ids["linkage"],
                title=f"FEC {ns.cycle} candidate-committee linkage — DEM and DFL candidates",
                summary="Official FEC linkage rows connecting DEM or DFL candidates to principal, authorized, joint-fundraising, leadership-PAC, or other linked committees.",
                uri=linkage_uri,
                description_uri=LINKAGE_DESCRIPTION,
                member=linkage_member,
                file_sha256=hashlib.sha256(linkage_zip.read_bytes()).hexdigest(),
                rows=len(all_linkages),
                matching_rows=len(linkages),
                when=ns.generated_at,
            ),
            source_document(
                document_id=source_ids["committee"],
                title=f"FEC {ns.cycle} committee master — candidate-linked committees",
                summary="Official FEC committee-master rows for committees linked to DEM or DFL candidates; mailing-address fields are excluded from emitted records.",
                uri=committee_uri,
                description_uri=COMMITTEE_DESCRIPTION,
                member=committee_member,
                file_sha256=hashlib.sha256(committee_zip.read_bytes()).hexdigest(),
                rows=len(all_committees),
                matching_rows=len(committee_rows),
                when=ns.generated_at,
            ),
        ]
        documents, candidate_inventory, linkage_inventory = build(candidates, linkages, committee_rows, source_ids, ns.generated_at)
        metadata = {
            "bulk_urls": {"candidate": candidate_uri, "committee": committee_uri, "linkage": linkage_uri},
            "candidate_description_url": CANDIDATE_DESCRIPTION,
            "committee_description_url": COMMITTEE_DESCRIPTION,
            "linkage_description_url": LINKAGE_DESCRIPTION,
            "raw_counts": {"candidate_rows": len(all_candidates), "committee_rows": len(all_committees), "linkage_rows": len(all_linkages)},
            "raw_sha256": {
                "candidate": hashlib.sha256(candidate_zip.read_bytes()).hexdigest(),
                "committee": hashlib.sha256(committee_zip.read_bytes()).hexdigest(),
                "linkage": hashlib.sha256(linkage_zip.read_bytes()).hexdigest(),
            },
        }
        write(ns.output, source_documents, documents, candidate_inventory, linkage_inventory, metadata, ns.generated_at)
    print(
        json.dumps(
            {
                "candidates": len(candidate_inventory),
                "documents": len(source_documents) + len(documents),
                "linkages": len(linkage_inventory),
                "output": str(ns.output),
                "targets": sum(1 for document in documents if document["dtype"] == "investigation-target"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
