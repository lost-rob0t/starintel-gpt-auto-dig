#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
GENERATED_AT = "2026-07-31T23:22:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-institutional-structure")
INTERNSHIPS_URL = "https://democrats.org/internships/"
RBC_MAY_URL = "https://democrats.org/dnc-rules-and-bylaws-committee-continues-consideration-of-early-window-of-the-2028-presidential-calendar/"
RBC_JULY_URL = "https://democrats.org/dnc-rules-and-bylaws-committee-proposes-early-states-for-2028-democratic-presidential-nominating-calendar/"
RBC_RULES_URL = "https://democrats.org/dnc-rules-and-bylaws-committee-votes-to-strengthen-penalties-for-violations-of-early-window-of-presidential-nominating-calendar/"
STAFF_UNION_URL = "https://democrats.org/news/dnc-leadership-and-staff-union-reach-collective-bargaining-agreement/"
PLAYBOOK_URL = "https://democrats.org/the-dnc-playbook/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
RUN_ID = "dnc-institutional-structure-2026-07-31"
MAX_PAGE_BYTES = 15_000_000

DNC_MEMBERSHIP_ID = "starintel:org:dnc-national-membership"
DNC_EXECUTIVE_ID = "starintel:org:dnc-executive-committee"
DNC_STANDING_ID = "starintel:org:dnc-standing-committees"
RBC_ID = "starintel:org:dnc-rules-and-bylaws-committee"
STAFF_UNION_ID = "starintel:org:dnc-staff-union"
SEIU_LOCAL_500_ID = "starintel:org:seiu-local-500"

APPLICANT_STATES = (
    "Delaware",
    "Georgia",
    "Illinois",
    "Iowa",
    "Michigan",
    "Nevada",
    "New Hampshire",
    "New Mexico",
    "North Carolina",
    "South Carolina",
    "Tennessee",
    "Virginia",
)
SELECTED_STATES = (
    ("South Carolina", "2028-01-22"),
    ("Nevada", "2028-02-01"),
    ("New Hampshire", "2028-02-08"),
    ("New Mexico", "2028-02-15"),
    ("Michigan", "2028-02-22"),
    ("Virginia", "2028-02-29"),
)
STATE_CODES = {
    "Delaware": "de",
    "Georgia": "ga",
    "Illinois": "il",
    "Iowa": "ia",
    "Michigan": "mi",
    "Nevada": "nv",
    "New Hampshire": "nh",
    "New Mexico": "nm",
    "North Carolina": "nc",
    "South Carolina": "sc",
    "Tennessee": "tn",
    "Virginia": "va",
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
    "official DNC rules, rosters, minutes, proceedings, department pages, and archives",
    "Federal Election Commission and state campaign-finance records",
    "public contracts, corporate, nonprofit, union, lobbying, legislative, agency, and court records",
    "established reporting and direct counter-sources",
]

DEPARTMENT_AXES = (
    {
        "key": "leadership-staff-roster",
        "label": "complete leadership, staff, and role-history roster",
        "target_type": "dnc_department_leadership_staff_roster",
        "penalty": 0.00,
        "question": "Who currently and historically leads or works in the DNC {name}, in what public roles, under which reporting lines, and during what dates?",
        "objectives": [
            "Acquire current and archived staff directories, leadership announcements, biographies, and public job postings",
            "Create one source-backed person and dated role relation per named leader, employee, advisor, fellow, intern coordinator, or contractor",
            "Map reporting lines, reorganizations, vacancies, promotions, departures, and cross-department roles",
            "Resolve each person against campaigns, committees, public offices, companies, nonprofits, unions, and vendors",
        ],
        "next": "Crawl official staff, careers, press, archive, and professional records and enumerate every publicly named department member",
    },
    {
        "key": "budgets-contracts-vendors",
        "label": "budgets, contracts, consultants, and vendors",
        "target_type": "dnc_department_budgets_contracts_vendors",
        "penalty": 0.005,
        "question": "Which budgets, expenditures, contracts, consultants, vendors, subcontractors, grants, and shared-service providers support the DNC {name}?",
        "objectives": [
            "Map FEC expenditure rows and purposes to department programs, staff, and procurement functions",
            "Resolve legal, compliance, technology, data, research, communications, fundraising, events, facilities, travel, and staffing vendors",
            "Separate direct vendors, payment processors, reimbursements, pass-throughs, subcontractors, and shared national-party services",
            "Trace vendor principals and staff to campaigns, committees, government, nonprofits, companies, and lobbying clients",
        ],
        "next": "Join FEC expenditures, public contracts, program pages, job descriptions, archived announcements, and vendor records",
    },
    {
        "key": "programs-systems-data",
        "label": "programs, systems, tools, data, and operational dependencies",
        "target_type": "dnc_department_programs_systems_data",
        "penalty": 0.01,
        "question": "Which programs, tools, platforms, datasets, applications, archives, training pipelines, procedures, and operational dependencies are owned, administered, or used by the DNC {name}?",
        "objectives": [
            "Enumerate every named program, platform, data resource, application, vendor tool, training, fellowship, pilot, archive, and internal procedure",
            "Map program leadership, participants, vendors, contracts, launch dates, geographic scope, and partner organizations",
            "Identify public statements about data sharing, cybersecurity, disinformation, vetting, research, messaging, organizing, fundraising, and compliance workflows",
            "Distinguish documented system relationships from hypotheses based only on common vendors or terminology",
        ],
        "next": "Crawl official department, program, playbook, careers, press, and archive pages and resolve each named system and partner",
    },
    {
        "key": "authority-governance-policy",
        "label": "authority, governance, policies, and decision records",
        "target_type": "dnc_department_authority_governance",
        "penalty": 0.015,
        "question": "What charter, bylaws, policies, delegations, approvals, committees, meeting records, decision rights, and compliance obligations govern the DNC {name}?",
        "objectives": [
            "Acquire current and historical charters, bylaws, manuals, policies, resolutions, minutes, procedures, and organizational charts",
            "Map authority to approve people, vendors, donors, locations, contracts, budgets, data access, messaging, programs, and coordinated campaigns",
            "Record named decision-makers, review bodies, appeal paths, reporting lines, and dated policy changes",
        ],
        "next": "Collect official rules, policies, minutes, resolutions, procedures, job descriptions, and organizational records defining department authority",
    },
    {
        "key": "outside-cross-ties",
        "label": "campaign, party, government, union, nonprofit, and corporate cross-ties",
        "target_type": "dnc_department_outside_cross_ties",
        "penalty": 0.012,
        "question": "Which campaigns, party committees, state parties, public offices, agencies, unions, nonprofits, companies, funders, media outlets, coalitions, and vendors connect to the DNC {name} through shared people, money, contracts, programs, or data?",
        "objectives": [
            "Map every known leader, staff principal, program owner, consultant, and vendor principal to outside roles",
            "Trace coordinated-campaign, state-party, sister-committee, government, nonprofit, union, corporate, lobbying, media, and academic relationships",
            "Create evidence-qualified relations and contradiction records while preserving unresolved identities",
        ],
        "next": "Run all known people, vendors, programs, and partners through official role, filing, contract, lobbying, corporate, nonprofit, government, and archive records",
    },
)

BODY_AXES = (
    {
        "key": "complete-roster",
        "label": "complete current and historical public membership roster",
        "target_type": "dnc_governance_body_complete_roster",
        "penalty": 0.00,
        "question": "What is the complete current and historical public membership roster of {name}, including roles, constituencies, appointment or election basis, voting status, start and end dates, and vacancies?",
        "objectives": [
            "Acquire every official current and archived membership list",
            "Create one person record and dated membership relation per named member",
            "Resolve duplicate names without merging namesakes",
            "Record chairs, vice chairs, officers, ex officio members, proxies, voting status, constituencies, terms, and vacancies",
        ],
        "next": "Acquire official rosters, minutes, proceedings, appointment records, and archives and enumerate every named member",
    },
    {
        "key": "rules-authority",
        "label": "rules, authority, procedures, and decision powers",
        "target_type": "dnc_governance_body_rules_authority",
        "penalty": 0.005,
        "question": "Which charter provisions, bylaws, rules, procedures, delegations, precedents, and votes define the authority and decision powers of {name}?",
        "objectives": [
            "Acquire current and historical rules, bylaws, resolutions, procedures, manuals, and precedents",
            "Map powers over membership, officers, budgets, committees, delegate selection, conventions, disputes, waivers, penalties, and appeals",
            "Record every dated amendment, vote, quorum rule, proxy rule, and procedural change",
        ],
        "next": "Collect official rules, amendments, resolutions, proceedings, and meeting records and model each authority and procedural change",
    },
    {
        "key": "meetings-minutes-votes",
        "label": "meetings, minutes, agendas, votes, and proceedings",
        "target_type": "dnc_governance_body_meetings_votes",
        "penalty": 0.01,
        "question": "What complete public meeting, agenda, minutes, attendance, motion, vote, resolution, livestream, transcript, and proceeding record exists for {name}?",
        "objectives": [
            "Enumerate every public meeting and associated notice, agenda, packet, minutes, attendance record, video, transcript, motion, and vote",
            "Extract named participants, presenters, counsel, applicants, witnesses, state parties, vendors, and staff",
            "Create event, claim, decision, and voting relations with exact dates and source provenance",
        ],
        "next": "Build a chronological meeting index and acquire all linked agendas, packets, minutes, recordings, transcripts, resolutions, and vote records",
    },
    {
        "key": "money-staff-vendors",
        "label": "budgets, staff, counsel, consultants, and vendors",
        "target_type": "dnc_governance_body_money_staff_vendors",
        "penalty": 0.015,
        "question": "Which budgets, staff, counsel, consultants, vendors, contractors, technology, travel, events, and operational resources support {name}?",
        "objectives": [
            "Enumerate publicly named staff liaisons, counsel, consultants, contractors, presenters, and service providers",
            "Map expenditures, contracts, venues, travel, livestream, voting, data, archive, compliance, and meeting-support vendors",
            "Trace principals and staff to campaigns, committees, public offices, nonprofits, unions, companies, and lobbying clients",
        ],
        "next": "Join meeting records, FEC expenditures, contracts, job descriptions, archives, and vendor records",
    },
    {
        "key": "outside-cross-ties",
        "label": "member and institutional cross-ties",
        "target_type": "dnc_governance_body_cross_ties",
        "penalty": 0.012,
        "question": "Which campaigns, party committees, state parties, public offices, agencies, unions, nonprofits, companies, funders, clients, and vendors connect to {name} through its members and operations?",
        "objectives": [
            "Map every member, officer, counsel, staff liaison, presenter, and principal to outside organizations and roles",
            "Trace campaign, government, nonprofit, union, corporate, lobbying, academic, legal, and vendor relationships",
            "Separate verified facts, attributed claims, contradictions, and unresolved names",
        ],
        "next": "Run all known members and operational principals through official biographies, filings, lobbying, corporate, nonprofit, government, court, and archive records",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import official DNC institutional departments and governance targets")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-internships-html", type=Path)
    return parser.parse_args()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def slug(value: str) -> str:
    return norm(value).replace(" ", "-") or "unknown"


def sha_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:{prefix}:{digest}"


def fetch_text(url: str, offline: Path | None = None) -> str:
    if offline:
        return offline.read_text(encoding="utf-8")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(MAX_PAGE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"
    if len(payload) > MAX_PAGE_BYTES:
        raise RuntimeError(f"page exceeds safety cap: {url}")
    return payload.decode(charset, errors="replace")


def parse_departments(html_text: str) -> list[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    headings = [heading for heading in soup.find_all(["h2", "h3"])]
    start = None
    end = None
    for index, heading in enumerate(headings):
        text = norm(clean(heading.get_text(" ", strip=True)))
        if text == "departments":
            start = index
        elif start is not None and text == "equal employment opportunity policy":
            end = index
            break
    if start is None:
        raise RuntimeError("internships page lacks Departments heading")
    if end is None:
        end = len(headings)
    departments: list[str] = []
    for heading in headings[start + 1 : end]:
        if heading.name != "h3":
            continue
        name = clean(heading.get_text(" ", strip=True)).rstrip("+").strip()
        if not name or name.lower().endswith("internship") or name.lower() in {"general internship"}:
            continue
        if name not in departments:
            departments.append(name)
    if len(departments) < 8:
        raise RuntimeError(f"unexpected official DNC department count: {len(departments)}")
    return departments


def source_document(document_id: str, title: str, summary: str, uri: str, kind: str, when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {"accessed_at": when, "credibility": 0.99, "kind": kind, "publisher": "Democratic National Committee", "uri": uri},
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
        "tags": ["dnc", "official-source", kind.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def org_document(document_id: str, name: str, org_type: str, summary: str, sources: list[str], when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {"name": name, "org_type": org_type},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Democratic National Committee", "scheme": "official_unit_name", "value": norm(name)}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in sources],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "organization", org_type.replace("_", "-")],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def person_document(document_id: str, name: str, source: str, when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {"full_name": name, "identity_resolution": "source_scoped_to_current_rbc_cochair_listing_until_namesake_resolution"},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Democratic National Committee", "scheme": "source_scoped_rbc_cochair_name", "value": norm(name)}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official DNC 2026 Rules and Bylaws Committee releases identify {name} as an RBC co-chair; identity remains source-scoped until resolved.",
        "tags": ["dnc", "person", "rules-bylaws-committee", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-listed-name", "verified": True},
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
    sources: list[str],
    when: str,
) -> dict[str, Any]:
    document = {
        "_id": sha_id("relation", subject, predicate, obj, json.dumps(qualifiers, sort_keys=True)),
        "data": {"confidence": 0.99, "directed": True, "object": obj, "predicate": predicate, "qualifiers": qualifiers, "subject": subject},
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
        "tags": ["dnc", "institutional-structure", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
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
                "official DNC rules, rosters, minutes, proceedings, departments, programs, press, careers, and archives",
                "public campaign-finance, contracts, corporate, nonprofit, union, lobbying, legislative, agency, and court records",
                "established reporting and direct counter-sources",
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
        "summary": question,
        "tags": ["dnc", "investigation-target", "institutional-structure", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-source", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-institutional-structure",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def build(departments: list[str], when: str) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    internships_source = "starintel:source:dnc-official-departments-2026-07-31"
    rbc_may_source = "starintel:source:dnc-rbc-2028-calendar-may-2026"
    rbc_july_source = "starintel:source:dnc-rbc-2028-calendar-july-2026"
    rbc_rules_source = "starintel:source:dnc-rbc-2028-rules-june-2026"
    union_source = "starintel:source:dnc-staff-union-cba-2025"
    playbook_source = "starintel:source:dnc-playbook-2026"
    documents: list[dict[str, Any]] = [
        source_document(internships_source, "Official DNC department descriptions", "Official DNC internships page enumerating departments and describing institutional responsibilities, including the office that maintains national-member lists and coordinates membership and committee meetings.", INTERNSHIPS_URL, "official_department_directory", when),
        source_document(rbc_may_source, "DNC RBC 2028 early-window presentations", "Official DNC release describing the Rules and Bylaws Committee's May 2026 consideration of 12 state applications for the 2028 early presidential calendar.", RBC_MAY_URL, "official_committee_release", when),
        source_document(rbc_july_source, "DNC RBC proposed 2028 early states", "Official DNC release reporting the July 2026 Rules and Bylaws Committee vote proposing six early-window states and dates.", RBC_JULY_URL, "official_committee_release", when),
        source_document(rbc_rules_source, "DNC RBC 2028 delegate-rule penalties", "Official DNC release reporting June 2026 Rules and Bylaws Committee amendments to 2028 Delegate Selection Rule 21.", RBC_RULES_URL, "official_committee_release", when),
        source_document(union_source, "DNC staff union collective bargaining agreement announcement", "Official DNC release announcing a four-year collective bargaining agreement between DNC leadership and the DNC Staff Union represented by SEIU Local 500.", STAFF_UNION_URL, "official_labor_announcement", when),
        source_document(playbook_source, "Official DNC Playbook", "Official DNC guide for state parties and coordinated campaigns describing organizing models, technology pilots, fellowships, and campaign case studies.", PLAYBOOK_URL, "official_program_directory", when),
    ]
    emitted: set[str] = {document["_id"] for document in documents}
    department_inventory: list[dict[str, Any]] = []
    body_inventory: list[dict[str, Any]] = []
    process_inventory: list[dict[str, Any]] = []

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    for name in departments:
        department_id = f"starintel:org:dnc-department-{slug(name)}"
        emit(org_document(department_id, f"DNC {name}", "dnc_internal_department", f"Department named on the official DNC internships page; its complete public leadership, staff, programs, authority, vendors, and cross-ties remain queued for enumeration.", [internships_source], when))
        emit(
            relation_document(
                subject=department_id,
                predicate="part_of",
                obj=DNC_ID,
                title=f"DNC {name} is part of the DNC",
                summary="The official DNC department directory lists this unit as a DNC department.",
                qualifiers={"current_as_of": "2026-07-31", "official_listing_name": name},
                sources=[internships_source],
                when=when,
            )
        )
        target_ids: list[str] = []
        for axis in DEPARTMENT_AXES:
            target_id = sha_id("investigation-target", "dnc-department", department_id, str(axis["key"]))
            question = axis["question"].format(name=name)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"DNC {name}: {axis['label']}",
                    question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[department_id, DNC_ID],
                    source_ids=[internships_source, playbook_source],
                    priority=round(0.94 - float(axis["penalty"]), 4),
                    when=when,
                    tags=["department", slug(name), str(axis["key"])],
                    depth=1,
                    breadth=180,
                )
            )
        department_inventory.append({"department": name, "department_id": department_id, "target_ids": target_ids})

    bodies = (
        (DNC_MEMBERSHIP_ID, "Democratic National Committee national membership", "dnc_membership_body", "The official DNC department page states that the party maintains membership lists for more than 450 national members.", [internships_source], 1.0),
        (DNC_EXECUTIVE_ID, "DNC Executive Committee", "dnc_governance_body", "The official DNC department page identifies the Executive Committee as a body whose meetings are coordinated by the Office of the Secretary and Party Affairs.", [internships_source], 0.99),
        (DNC_STANDING_ID, "DNC Standing Committees", "dnc_governance_body_group", "The official DNC department page identifies Standing Committees and their meetings as institutional responsibilities of the Office of the Secretary and Party Affairs.", [internships_source], 0.98),
        (RBC_ID, "DNC Rules and Bylaws Committee", "dnc_standing_committee", "Official DNC releases document the Rules and Bylaws Committee's 2026 work on the 2028 nominating calendar and delegate-selection rules.", [rbc_may_source, rbc_july_source, rbc_rules_source], 1.0),
    )
    for body_id, name, org_type, summary, sources, priority in bodies:
        emit(org_document(body_id, name, org_type, summary, sources, when))
        emit(
            relation_document(
                subject=body_id,
                predicate="part_of",
                obj=DNC_ID,
                title=f"{name} is part of the DNC",
                summary="Official DNC sources identify this membership or governance body within the Democratic National Committee.",
                qualifiers={"current_as_of": "2026-07-31"},
                sources=sources,
                when=when,
            )
        )
        target_ids: list[str] = []
        for axis in BODY_AXES:
            target_id = sha_id("investigation-target", "dnc-governance-body", body_id, str(axis["key"]))
            question = axis["question"].format(name=name)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{name}: {axis['label']}",
                    question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[body_id, DNC_ID],
                    source_ids=sources,
                    priority=round(priority - float(axis["penalty"]), 4),
                    when=when,
                    tags=["governance-body", slug(name), str(axis["key"])],
                    depth=1,
                    breadth=250,
                )
            )
        body_inventory.append({"body": name, "body_id": body_id, "target_ids": target_ids})

    for person_name in ("Minyon Moore", "James Roosevelt, Jr."):
        person_id = sha_id("person", "dnc-rbc-cochair-2026", norm(person_name))
        emit(person_document(person_id, person_name, rbc_july_source, when))
        emit(
            relation_document(
                subject=person_id,
                predicate="officially_listed_cochair_of",
                obj=RBC_ID,
                title=f"{person_name}: Rules and Bylaws Committee co-chair",
                summary="Official DNC 2026 releases identify this person as a co-chair of the Rules and Bylaws Committee.",
                qualifiers={"current_as_of": "2026-07-24", "role": "co-chair"},
                sources=[rbc_may_source, rbc_july_source, rbc_rules_source],
                when=when,
            )
        )

    for state in APPLICANT_STATES:
        state_org = f"starintel:org:dnc-state-party-{STATE_CODES[state]}"
        relation = relation_document(
            subject=state_org,
            predicate="submitted_2028_early_window_application",
            obj=RBC_ID,
            title=f"{state} Democratic Party: 2028 early-window application",
            summary="Official DNC releases identify this state among the 12 applicants considered by the Rules and Bylaws Committee for the 2028 early presidential nominating window.",
            qualifiers={"application_process": "2028 Democratic presidential nominating calendar", "presented_by": "2026-05-29", "state": state},
            sources=[rbc_may_source],
            when=when,
        )
        emit(relation)
        target_id = sha_id("investigation-target", "dnc-rbc-early-window-application", state)
        question = f"What complete application, presentation, scoring, supporting evidence, presenters, consultants, vendors, endorsements, communications, meeting discussion, and decision record exists for {state}'s 2028 Democratic presidential early-window bid?"
        emit(
            target_document(
                target_id=target_id,
                target_title=f"{state}: complete 2028 DNC early-window application record",
                question=question,
                objectives=[
                    "Acquire the full RFP response, appendices, presentation, video, transcript, supporting letters, datasets, and cited evidence",
                    "Enumerate every presenter, author, state-party officer, elected official, consultant, vendor, coalition, and supporting organization",
                    "Map scoring criteria, committee questions, deliberations, waivers, votes, decisions, contradictions, and later revisions",
                    "Trace campaign-finance, travel, event, consulting, research, polling, and presentation-related expenditures",
                ],
                next_action="Locate the official state submission, DNC meeting materials, livestream, transcript, press records, and state-party disclosures",
                target_type="dnc_2028_early_window_state_application",
                seed_ids=[state_org, RBC_ID, relation["_id"]],
                source_ids=[rbc_may_source, rbc_july_source],
                priority=0.97,
                when=when,
                tags=["rules-bylaws-committee", "2028-calendar", "state-application", STATE_CODES[state]],
                depth=2,
                breadth=200,
            )
        )
        process_inventory.append({"state": state, "state_party_id": state_org, "application_relation_id": relation["_id"], "application_target_id": target_id})

    selected_map = {state: date_value for state, date_value in SELECTED_STATES}
    for item in process_inventory:
        state = item["state"]
        if state not in selected_map:
            continue
        relation = relation_document(
            subject=RBC_ID,
            predicate="proposed_2028_early_window_state",
            obj=item["state_party_id"],
            title=f"RBC proposed {state} for the 2028 early window",
            summary="The official DNC July 2026 release reports that the Rules and Bylaws Committee voted to propose this state and date for the 2028 presidential nominating calendar early window.",
            qualifiers={"contest_date": selected_map[state], "decision_date": "2026-07-24", "state": state},
            sources=[rbc_july_source],
            when=when,
        )
        emit(relation)
        item["selection_relation_id"] = relation["_id"]
        item["proposed_contest_date"] = selected_map[state]

    emit(org_document(STAFF_UNION_ID, "DNC Staff Union", "labor_union_bargaining_unit", "Official DNC reporting identifies the DNC Staff Union as the bargaining representative for covered DNC staff in a 2025–2029 collective bargaining agreement.", [union_source], when))
    emit(org_document(SEIU_LOCAL_500_ID, "SEIU Local 500", "labor_union", "Official DNC reporting identifies SEIU Local 500 as representing DNC Staff Union members in the 2025 collective bargaining agreement.", [union_source], when))
    emit(
        relation_document(
            subject=STAFF_UNION_ID,
            predicate="represented_by",
            obj=SEIU_LOCAL_500_ID,
            title="DNC Staff Union represented by SEIU Local 500",
            summary="The official DNC collective-bargaining announcement states that DNC staff are members of SEIU Local 500.",
            qualifiers={"agreement_effective": "2025-07-01", "agreement_expires": "2029-05-31"},
            sources=[union_source],
            when=when,
        )
    )
    union_target = sha_id("investigation-target", "dnc-staff-union", "public-cba-bargaining-structure")
    union_question = "What complete public collective-bargaining agreement, bargaining-unit structure, publicly named bargaining representatives, negotiations, implementation records, grievances or disputes, wage schedules, benefits, severance rules, vendors, and institutional cross-ties define the DNC Staff Union relationship with DNC leadership and SEIU Local 500?"
    emit(
        target_document(
            target_id=union_target,
            target_title="DNC Staff Union: public CBA, representatives, implementation, and cross-ties",
            question=union_question,
            objectives=[
                "Acquire the complete public collective bargaining agreement and all official summaries, amendments, memoranda, and implementation guidance",
                "Enumerate publicly named bargaining committee members, union officers, DNC negotiators, counsel, consultants, and mediators without seeking private membership lists",
                "Map wage schedules, benefits, severance, classifications, deployment provisions, grievance procedures, term, and enforcement",
                "Trace public expenditures, legal counsel, labor consultants, vendors, and organizational cross-ties",
            ],
            next_action="Locate the full CBA and official union and DNC records, then enumerate every publicly named representative and implementation document",
            target_type="dnc_staff_union_public_cba_structure",
            seed_ids=[STAFF_UNION_ID, SEIU_LOCAL_500_ID, DNC_ID],
            source_ids=[union_source],
            priority=0.94,
            when=when,
            tags=["staff-union", "collective-bargaining", "public-records"],
            depth=1,
            breadth=150,
        )
    )

    playbook_target = sha_id("investigation-target", "dnc-playbook", "programs-technology-vendors-participants")
    playbook_question = "Which organizing models, technology pilots, tools, vendors, fellowships, participants, state parties, coordinated campaigns, case studies, authors, evaluators, datasets, and performance findings comprise every current and archived version of the DNC Playbook?"
    emit(
        target_document(
            target_id=playbook_target,
            target_title="DNC Playbook: programs, technology pilots, vendors, participants, and findings",
            question=playbook_question,
            objectives=[
                "Acquire every current and archived Playbook version, appendix, template, guide, submission form, case study, and linked artifact",
                "Enumerate every named tool, vendor, pilot, campaign, state party, fellowship, participant, author, evaluator, and partner",
                "Map contracts, expenditures, data flows, technology dependencies, program dates, evaluation methods, findings, and later adoption",
                "Separate official performance claims, measured results, participant accounts, marketing language, and independent evidence",
            ],
            next_action="Capture the current Playbook and archives, then resolve every named program, tool, vendor, participant, state party, and cited result",
            target_type="dnc_playbook_programs_technology_network",
            seed_ids=[DNC_ID],
            source_ids=[playbook_source, internships_source],
            priority=0.96,
            when=when,
            tags=["playbook", "technology-pilots", "organizing", "vendors"],
            depth=1,
            breadth=300,
        )
    )

    return sorted(documents, key=lambda document: document["_id"]), {
        "bodies": body_inventory,
        "departments": department_inventory,
        "early_window_process": process_inventory,
    }


def write(output: Path, documents: list[dict[str, Any]], inventories: dict[str, list[dict[str, Any]]], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in documents).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(payload)
    inventory_hashes: dict[str, str] = {}
    for name, values in inventories.items():
        inventory = "".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values).encode("utf-8")
        path = output / "source" / f"{name.replace('_', '-')}.jsonl"
        path.write_bytes(inventory)
        inventory_hashes[name] = hashlib.sha256(inventory).hexdigest()
    counts = Counter(document["dtype"] for document in documents)
    target_counts = Counter(document["data"]["target_type"] for document in documents if document["dtype"] == "investigation-target")
    manifest = {
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "departments": len(inventories["departments"]),
        "document_sha256": hashlib.sha256(payload).hexdigest(),
        "early_window_applications": len(inventories["early_window_process"]),
        "generated_at": when,
        "governance_bodies": len(inventories["bodies"]),
        "inventory_sha256": inventory_hashes,
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(documents),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# DNC institutional structure",
        "",
        "Official-source organizational map and recursive target queue for DNC departments, national membership, Executive Committee, Standing Committees, Rules and Bylaws Committee, staff-union relationship, Playbook, and the 2028 early-state process.",
        "",
        f"- official departments: {len(inventories['departments']):,}",
        f"- governance bodies: {len(inventories['bodies']):,}",
        f"- 2028 early-window state applications: {len(inventories['early_window_process']):,}",
        f"- StarIntel documents: {len(documents):,}",
        f"- recursive investigation targets: {sum(target_counts.values()):,}",
        "",
        "The staff-union target is limited to public agreements and publicly named representatives; it does not seek a private membership list. Committee and department targets require primary-source rosters, rules, meeting records, budgets, programs, contracts, systems, vendors, and cross-ties.",
        "",
        "## Target families",
        "",
    ]
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(["", "```bash", "python3 -m pip install 'beautifulsoup4>=4.12,<5'", "python3 scripts/import_dnc_institutional_structure.py", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    departments = parse_departments(fetch_text(INTERNSHIPS_URL, ns.offline_internships_html))
    documents, inventories = build(departments, ns.generated_at)
    write(ns.output, documents, inventories, ns.generated_at)
    print(json.dumps({"departments": len(departments), "documents": len(documents), "output": str(ns.output), "targets": sum(1 for document in documents if document["dtype"] == "investigation-target")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
