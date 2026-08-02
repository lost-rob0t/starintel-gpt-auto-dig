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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
CYCLE = 2026
GENERATED_AT = "2026-07-31T22:14:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-fec-democratic-committees-2026")
BULK_URL = "https://www.fec.gov/files/bulk-downloads/{cycle}/cm{yy}.zip"
DESCRIPTION_URL = "https://www.fec.gov/campaign-finance-data/committee-master-file-description/"
PARTY_CODES_URL = "https://www.fec.gov/campaign-finance-data/party-code-descriptions/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_DOWNLOAD = 250_000_000
MAX_MATCHING_ROWS = 30_000
PARTITIONS = 32
PARTY_CODES = {"DEM", "DFL"}
DEMOCRATIC_PARTY_ID = "starintel:org:democratic-party-fec-affiliation"
RUN_ID = "dnc-fec-democratic-committees-2026-07-31"
FIELDS = [
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
    "official committee websites and archived pages",
    "state campaign-finance and corporate registries",
    "official candidate biographies and government records",
    "court records and established published reporting",
]
TARGET_AXES = (
    {
        "key": "leadership-registration",
        "label": "leadership and registration history",
        "target_type": "fec_committee_leadership_registration",
        "priority_penalty": 0.00,
        "question": "Who has formally governed, represented, or served as treasurer or officer of {name}, and how has the committee's registration changed over time?",
        "objectives": [
            "Acquire every current and historical Statement of Organization and amendment",
            "Enumerate treasurers, assistant treasurers, custodians, officers, and controlling persons",
            "Record role dates, filing image numbers, amendments, terminations, and reactivations",
            "Separate exact FEC records from unresolved identity matches",
        ],
        "next": "Collect the committee's complete FEC registration and amendment history and enumerate every named officer",
    },
    {
        "key": "candidate-linkage",
        "label": "candidate and authorized-committee linkage",
        "target_type": "fec_committee_candidate_linkage",
        "priority_penalty": 0.01,
        "question": "Which candidates, campaigns, joint fundraising committees, leadership PACs, and authorized committees are formally or operationally linked to {name}?",
        "objectives": [
            "Resolve every reported candidate ID through the FEC candidate master and linkage files",
            "Map principal, authorized, joint-fundraising, leadership-PAC, and affiliated committee relationships",
            "Preserve election cycle, office, district, designation, and linkage provenance",
        ],
        "next": "Join this committee to the FEC candidate master and candidate-committee linkage files",
    },
    {
        "key": "connected-organizations",
        "label": "connected organizations and party affiliations",
        "target_type": "fec_committee_connected_organizations",
        "priority_penalty": 0.015,
        "question": "Which organizations, sponsors, party bodies, employers, unions, corporations, associations, and committees are connected to {name}, and what public records establish each connection?",
        "objectives": [
            "Resolve the FEC-reported connected organization or sponsor without over-merging names",
            "Map formal affiliation, shared officers, shared addresses, vendors, transfers, and governance",
            "Distinguish FEC-reported affiliation from independently verified operational control",
        ],
        "next": "Verify every reported connected organization using FEC filings, official records, and archived websites",
    },
    {
        "key": "money-network",
        "label": "receipts, transfers, and disbursement network",
        "target_type": "fec_committee_money_network",
        "priority_penalty": 0.005,
        "question": "What money flows connect {name} to candidates, party committees, PACs, vendors, donors, conduits, and other organizations?",
        "objectives": [
            "Import itemized receipts, committee-to-committee transfers, operating expenditures, and independent expenditures",
            "Preserve amendments, memo entries, refunds, conduits, reattributions, and raw filing identifiers",
            "Rank counterparties by unreconciled row count and amount without flattening amended records",
            "Create evidence-qualified transaction and counterparty relations",
        ],
        "next": "Import the committee's official FEC transaction files and build amendment-aware counterparty indexes",
    },
    {
        "key": "staff-vendors",
        "label": "staff, consultants, and vendors",
        "target_type": "fec_committee_staff_vendors",
        "priority_penalty": 0.02,
        "question": "Which staff, consultants, legal firms, compliance vendors, fundraisers, media firms, technology providers, and subcontractors work for {name}?",
        "objectives": [
            "Enumerate public staff and consultant rosters from filings, websites, payroll records, and expenditure purposes",
            "Separate employees, direct vendors, subcontractors, pass-throughs, and payment processors",
            "Map principals and staff to other campaigns, committees, government roles, nonprofits, and companies",
        ],
        "next": "Resolve recurring payees and public staff into dated person–organization and vendor relations",
    },
)
TREASURER_AXES = (
    {
        "key": "identity-role",
        "label": "identity and committee-role verification",
        "target_type": "fec_treasurer_identity_role",
        "priority_penalty": 0.00,
        "question": "Which public records establish {person}'s exact identity, tenure, authority, and filings as treasurer of {committee}?",
        "objectives": [
            "Resolve the person without merging namesakes",
            "Collect every filing naming the person and establish start and end dates",
            "Identify assistant treasurer, compliance, legal, and financial-control roles",
        ],
        "next": "Trace the treasurer name through committee amendments, filing images, official biographies, and professional records",
    },
    {
        "key": "cross-ties",
        "label": "other committee and institutional cross-ties",
        "target_type": "fec_treasurer_cross_ties",
        "priority_penalty": 0.015,
        "question": "Which other committees, campaigns, firms, nonprofits, public offices, and vendors connect to {person}, the reported treasurer of {committee}?",
        "objectives": [
            "Enumerate all other FEC committees naming the same resolved person",
            "Map employment, ownership, board, legal, compliance, and campaign roles",
            "Separate exact matches, likely matches, ambiguous names, and contradictions",
        ],
        "next": "Search FEC committee records and primary-source professional records for the resolved treasurer identity",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FEC Democratic and DFL committee infrastructure")
    parser.add_argument("--cycle", type=int, default=CYCLE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--offline-zip", type=Path)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def sha_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return f"starintel:{prefix}:{hashlib.sha256(raw).hexdigest()}"


def bulk_url(cycle: int) -> str:
    return BULK_URL.format(cycle=cycle, yy=str(cycle)[-2:])


def source_id(cycle: int) -> str:
    return f"starintel:source:fec-committee-master-democratic-{cycle}"


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
                raise RuntimeError("FEC committee-master download exceeds safety limit")
            handle.write(chunk)


def read_rows(path: Path) -> tuple[str, list[dict[str, str]], int]:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            info
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))
        ]
        if not candidates:
            raise RuntimeError("FEC ZIP contains no committee-master text file")
        member = max(candidates, key=lambda info: info.file_size).filename
        rows: list[dict[str, str]] = []
        total_rows = 0
        seen_ids: set[str] = set()
        with archive.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                total_rows += 1
                if len(values) == len(FIELDS) + 1 and values[-1] == "":
                    values.pop()
                if len(values) != len(FIELDS):
                    raise RuntimeError(f"unexpected FEC committee row width at {line_number}: {len(values)}")
                row = dict(zip(FIELDS, values, strict=True))
                committee_id = row["CMTE_ID"].strip()
                if not committee_id:
                    raise RuntimeError(f"committee-master row {line_number} has no committee ID")
                if committee_id in seen_ids:
                    raise RuntimeError(f"duplicate committee ID in committee master: {committee_id}")
                seen_ids.add(committee_id)
                if row["CMTE_PTY_AFFILIATION"].strip().upper() not in PARTY_CODES:
                    continue
                if not row["CMTE_NM"].strip():
                    raise RuntimeError(f"Democratic committee {committee_id} has no name")
                rows.append(row)
                if len(rows) > MAX_MATCHING_ROWS:
                    raise RuntimeError("matching Democratic committee rows exceed safety limit")
    if not rows:
        raise RuntimeError("no DEM or DFL committees found in FEC committee master")
    return member, rows, total_rows


def source_document(cycle: int, member: str, rows: int, file_sha256: str, when: str) -> dict[str, Any]:
    document = {
        "_id": source_id(cycle),
        "data": {
            "accessed_at": when,
            "archive_member": member,
            "credibility": 1.0,
            "file_sha256": file_sha256,
            "kind": "official_fec_bulk_data",
            "party_codes": sorted(PARTY_CODES),
            "publisher": "Federal Election Commission",
            "record_count": rows,
            "uri": bulk_url(cycle),
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
        "summary": "Official FEC committee master rows whose reported party affiliation is DEM or DFL; residential and mailing address fields are not emitted.",
        "tags": ["dnc", "fec", "committee-master", "democratic-party", "official-source"],
        "title": f"FEC {cycle} committee master — DEM and DFL rows",
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def party_document(source: str, when: str) -> dict[str, Any]:
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
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Source-scoped grouping for FEC party affiliation codes DEM and DFL; it does not by itself establish DNC control over every committee carrying those codes.",
        "tags": ["dnc", "fec", "democratic-party", "party-affiliation"],
        "title": "Democratic Party / DFL FEC affiliation grouping",
        "verification": {"last_reviewed_at": when, "status": "official-code-mapping", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def committee_id(row: dict[str, str]) -> str:
    return f"starintel:org:fec-committee-{row['CMTE_ID'].strip().lower()}"


def committee_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    fec_id = row["CMTE_ID"].strip()
    name = row["CMTE_NM"].strip()
    data = {
        "candidate_id": row["CAND_ID"].strip() or None,
        "committee_designation": row["CMTE_DSGN"].strip() or None,
        "committee_type": row["CMTE_TP"].strip() or None,
        "fec_committee_id": fec_id,
        "filing_frequency": row["CMTE_FILING_FREQ"].strip() or None,
        "name": name,
        "organization_type_code": row["ORG_TP"].strip() or None,
        "org_type": "fec_registered_democratic_committee",
        "party_affiliation": row["CMTE_PTY_AFFILIATION"].strip().upper(),
        "reported_connected_organization": row["CONNECTED_ORG_NM"].strip() or None,
        "reported_treasurer": row["TRES_NM"].strip() or None,
    }
    data = {key: value for key, value in data.items() if value is not None}
    document = {
        "_id": committee_id(row),
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
        "summary": f"FEC committee-master record for {name}, reporting party affiliation {row['CMTE_PTY_AFFILIATION'].strip().upper()}.",
        "tags": ["dnc", "fec", "committee", "democratic-party", row["CMTE_PTY_AFFILIATION"].strip().lower()],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def treasurer_id(row: dict[str, str]) -> str:
    return sha_id("person", "fec-treasurer-source-scoped", row["CMTE_ID"].strip(), norm(row["TRES_NM"]))


def treasurer_document(row: dict[str, str], source: str, when: str) -> dict[str, Any]:
    name = re.sub(r"\s+", " ", row["TRES_NM"].strip())
    document = {
        "_id": treasurer_id(row),
        "data": {
            "full_name": name,
            "identity_resolution": "source_scoped_to_fec_committee_until_namesake_resolution",
            "reported_role": "treasurer",
            "source_committee_id": row["CMTE_ID"].strip(),
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {
                "canonical": True,
                "issuer": "Federal Election Commission committee master",
                "scheme": "source_scoped_treasurer_name",
                "value": f"{row['CMTE_ID'].strip()}:{norm(name)}",
            }
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"The FEC committee master reports {name} as treasurer of {row['CMTE_NM'].strip()}; identity remains source-scoped pending resolution.",
        "tags": ["dnc", "fec", "treasurer", "person", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-name", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def connected_org_id(name: str) -> str:
    return sha_id("org", "fec-connected-organization-name", norm(name))


def connected_org_document(name: str, source: str, when: str) -> dict[str, Any]:
    clean_name = re.sub(r"\s+", " ", name.strip())
    document = {
        "_id": connected_org_id(clean_name),
        "data": {
            "identity_resolution": "exact_reported_name_source_scoped_until_legal_entity_resolution",
            "name": clean_name,
            "org_type": "fec_reported_connected_organization",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Federal Election Commission committee master", "scheme": "normalized_reported_name", "value": norm(clean_name)}
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": "Organization name reported in the FEC committee-master connected-organization field; legal identity and control require independent verification.",
        "tags": ["dnc", "fec", "connected-organization", "source-scoped-identity"],
        "title": clean_name,
        "verification": {"last_reviewed_at": when, "status": "official-fec-reported-name", "verified": True},
        "version": 1,
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
    source: str,
    when: str,
    confidence: float = 0.99,
) -> dict[str, Any]:
    relation = {
        "_id": sha_id("relation", subject, predicate, obj, json.dumps(qualifiers, sort_keys=True)),
        "data": {
            "confidence": confidence,
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
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "committee", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-fec-record", "verified": True},
        "version": 1,
    }
    validate_document(relation)
    return relation


def priority(row: dict[str, str]) -> float:
    committee_type = row["CMTE_TP"].strip().upper()
    designation = row["CMTE_DSGN"].strip().upper()
    party_code = row["CMTE_PTY_AFFILIATION"].strip().upper()
    if row["CMTE_ID"].strip() == "C00010603":
        base = 1.0
    elif committee_type in {"X", "Y", "Z"}:
        base = 0.95
    elif designation in {"P", "A", "J"}:
        base = 0.91
    elif committee_type in {"H", "S", "P"}:
        base = 0.90
    else:
        base = 0.84
    if party_code == "DFL":
        base += 0.01
    if row["CONNECTED_ORG_NM"].strip():
        base += 0.015
    if row["TRES_NM"].strip():
        base += 0.01
    return round(min(1.0, base), 4)


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
    source: str,
    priority_value: float,
    when: str,
    tags: list[str],
    depth: int,
) -> dict[str, Any]:
    document = {
        "_id": target_id,
        "data": {
            "breadth": 80 if depth == 1 else 40,
            "depth": depth,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official committee registrations and amendments",
                "official campaign-finance transaction files",
                "official committee and candidate websites and archives",
                "public corporate, nonprofit, lobbying, and government records",
                "court records and published reporting",
            ],
            "max_depth": 7,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": priority_value,
            "required_dtypes": ["source", "org", "person", "relation", "claim", "financial-observation"],
            "research_question": research_question,
            "scope_type": "public_source",
            "seed_ids": seed_ids,
            "source_ids": [source],
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
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "fec", "investigation-target", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-fec-record", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority_value,
            "queue": "dnc-fec-democratic-committees",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def build(rows: list[dict[str, str]], source: str, when: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = [party_document(source, when)]
    inventory: list[dict[str, Any]] = []
    emitted: set[str] = {documents[0]["_id"]}
    connected_orgs: dict[str, dict[str, Any]] = {}

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    for row in sorted(rows, key=lambda item: (item["CMTE_NM"].strip().lower(), item["CMTE_ID"].strip())):
        committee = committee_document(row, source, when)
        emit(committee)
        committee_name = row["CMTE_NM"].strip()
        committee_node = committee["_id"]
        party_code = row["CMTE_PTY_AFFILIATION"].strip().upper()
        committee_priority = priority(row)
        seed_ids = [committee_node]
        target_ids: list[str] = []

        emit(
            relation_document(
                subject=committee_node,
                predicate="fec_reported_party_affiliation",
                obj=DEMOCRATIC_PARTY_ID,
                title=f"{committee_name}: FEC party affiliation {party_code}",
                summary=f"The FEC committee master reports party affiliation {party_code}; this does not by itself establish DNC governance or operational control.",
                qualifiers={"cycle": CYCLE, "fec_committee_id": row["CMTE_ID"].strip(), "party_code": party_code},
                source=source,
                when=when,
            )
        )

        treasurer_node: str | None = None
        if row["TRES_NM"].strip():
            treasurer = treasurer_document(row, source, when)
            treasurer_node = treasurer["_id"]
            emit(treasurer)
            emit(
                relation_document(
                    subject=treasurer_node,
                    predicate="fec_reported_treasurer_of",
                    obj=committee_node,
                    title=f"{treasurer['title']} reported as treasurer of {committee_name}",
                    summary="The FEC committee master reports this source-scoped person name as committee treasurer; exact identity and tenure require amendment-history review.",
                    qualifiers={"cycle": CYCLE, "fec_committee_id": row["CMTE_ID"].strip(), "role": "treasurer"},
                    source=source,
                    when=when,
                )
            )
            seed_ids.append(treasurer_node)

        connected_node: str | None = None
        connected_name = row["CONNECTED_ORG_NM"].strip()
        if connected_name:
            connected_node = connected_org_id(connected_name)
            if connected_node not in connected_orgs:
                connected_orgs[connected_node] = connected_org_document(connected_name, source, when)
                emit(connected_orgs[connected_node])
            emit(
                relation_document(
                    subject=committee_node,
                    predicate="fec_reported_connected_organization",
                    obj=connected_node,
                    title=f"{committee_name}: reported connected organization {connected_name}",
                    summary="The FEC committee master reports this connected-organization name; legal identity, affiliation, and control remain to be independently verified.",
                    qualifiers={"cycle": CYCLE, "fec_committee_id": row["CMTE_ID"].strip(), "reported_name": connected_name},
                    source=source,
                    when=when,
                )
            )
            seed_ids.append(connected_node)

        for axis in TARGET_AXES:
            target_id = sha_id("investigation-target", "dnc-fec-committee", row["CMTE_ID"].strip(), axis["key"])
            question = axis["question"].format(name=committee_name)
            axis_priority = round(max(0.5, committee_priority - float(axis["priority_penalty"])), 4)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{committee_name}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=list(seed_ids),
                    source=source,
                    priority_value=axis_priority,
                    when=when,
                    tags=["committee", str(axis["key"]), party_code.lower()],
                    depth=1,
                )
            )

        treasurer_target_ids: list[str] = []
        if treasurer_node:
            person_name = re.sub(r"\s+", " ", row["TRES_NM"].strip())
            for axis in TREASURER_AXES:
                target_id = sha_id("investigation-target", "dnc-fec-treasurer", treasurer_node, committee_node, axis["key"])
                question = axis["question"].format(person=person_name, committee=committee_name)
                axis_priority = round(max(0.5, committee_priority - float(axis["priority_penalty"])), 4)
                treasurer_target_ids.append(target_id)
                emit(
                    target_document(
                        target_id=target_id,
                        target_title=f"{person_name} / {committee_name}: {axis['label']}",
                        summary=question,
                        research_question=question,
                        objectives=list(axis["objectives"]),
                        next_action=str(axis["next"]),
                        target_type=str(axis["target_type"]),
                        seed_ids=[treasurer_node, committee_node],
                        source=source,
                        priority_value=axis_priority,
                        when=when,
                        tags=["treasurer", str(axis["key"]), party_code.lower()],
                        depth=2,
                    )
                )

        inventory.append(
            {
                "candidate_id": row["CAND_ID"].strip() or None,
                "committee": committee_name,
                "committee_designation": row["CMTE_DSGN"].strip() or None,
                "committee_id": row["CMTE_ID"].strip(),
                "committee_node": committee_node,
                "committee_type": row["CMTE_TP"].strip() or None,
                "connected_organization": connected_name or None,
                "party_affiliation": party_code,
                "priority": committee_priority,
                "reported_treasurer": row["TRES_NM"].strip() or None,
                "target_ids": target_ids,
                "treasurer_target_ids": treasurer_target_ids,
            }
        )

    return documents, inventory


def partition(document: dict[str, Any]) -> int:
    digest = hashlib.sha256(document["_id"].encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % PARTITIONS


def write(
    output: Path,
    source: dict[str, Any],
    documents: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
    source_zip: Path,
    member: str,
    total_rows: int,
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    root_jsonl = (json.dumps(source, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(root_jsonl)

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    for document in documents:
        buckets[partition(document)].append(document)
    partition_manifest: list[dict[str, Any]] = []
    document_hash = hashlib.sha256(root_jsonl)
    for index, bucket in enumerate(buckets):
        directory = output / f"part-{index:02d}"
        directory.mkdir()
        payload = "".join(
            json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
            for document in sorted(bucket, key=lambda item: item["_id"])
        ).encode("utf-8")
        (directory / "starintel-documents.jsonl").write_bytes(payload)
        document_hash.update(payload)
        partition_manifest.append(
            {
                "documents": len(bucket),
                "part": index,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }
        )

    inventory_bytes = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in inventory
    ).encode("utf-8")
    (output / "source/committee-inventory.jsonl").write_bytes(inventory_bytes)
    counts = Counter(document["dtype"] for document in [source, *documents])
    target_counts = Counter(
        document["data"]["target_type"]
        for document in documents
        if document["dtype"] == "investigation-target"
    )
    manifest = {
        "bulk_url": bulk_url(CYCLE),
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "description_url": DESCRIPTION_URL,
        "document_stream_sha256": document_hash.hexdigest(),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "matching_committees": len(inventory),
        "party_codes": sorted(PARTY_CODES),
        "party_codes_url": PARTY_CODES_URL,
        "partitions": partition_manifest,
        "raw_archive_member": member,
        "raw_archive_sha256": hashlib.sha256(source_zip.read_bytes()).hexdigest(),
        "raw_committee_master_rows": total_rows,
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": 1 + len(documents),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    top = sorted(inventory, key=lambda item: (-float(item["priority"]), item["committee"].lower(), item["committee_id"]))[:40]
    lines = [
        "# FEC Democratic and DFL committee infrastructure",
        "",
        "Official 2026 FEC committee-master rows whose reported party affiliation is `DEM` or `DFL`.",
        "",
        f"- matching committees: {len(inventory):,}",
        f"- StarIntel documents: {1 + len(documents):,}",
        f"- investigation targets: {sum(target_counts.values()):,}",
        f"- reported treasurer records: {counts.get('person', 0):,}",
        f"- organization records: {counts.get('org', 0):,}",
        f"- relation records: {counts.get('relation', 0):,}",
        f"- partitions: {PARTITIONS}",
        "",
        "Mailing and residential address fields from the FEC file are deliberately not emitted. Treasurer names are source-scoped to each committee until namesakes are resolved. A DEM or DFL code establishes an FEC-reported party affiliation, not automatic DNC governance or control.",
        "",
        "## Highest-priority committee leads",
        "",
        "| Committee | FEC ID | Party | Type | Designation | Priority |",
        "|---|---|---|---|---|---:|",
    ]
    for item in top:
        lines.append(
            f"| {str(item['committee']).replace('|', '/')} | {item['committee_id']} | {item['party_affiliation']} | {item['committee_type'] or ''} | {item['committee_designation'] or ''} | {float(item['priority']):.4f} |"
        )
    lines.extend(
        [
            "",
            "```bash",
            "python3 scripts/import_dnc_fec_democratic_committees.py",
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
        archive_path = Path(temporary) / f"cm{str(ns.cycle)[-2:]}.zip"
        if ns.offline_zip:
            shutil.copy2(ns.offline_zip, archive_path)
        else:
            download(bulk_url(ns.cycle), archive_path)
        member, rows, total_rows = read_rows(archive_path)
        archive_sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        source = source_document(ns.cycle, member, len(rows), archive_sha256, ns.generated_at)
        documents, inventory = build(rows, source["_id"], ns.generated_at)
        write(ns.output, source, documents, inventory, archive_path, member, total_rows, ns.generated_at)
    print(
        json.dumps(
            {
                "committees": len(inventory),
                "documents": 1 + len(documents),
                "output": str(ns.output),
                "targets": sum(1 for document in documents if document["dtype"] == "investigation-target"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
