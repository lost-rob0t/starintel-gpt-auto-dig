#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
ASDC_ID = "starintel:org:association-of-state-democratic-committees"
GENERATED_AT = "2026-07-31T22:32:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-official-party-structure")
STATE_DIRECTORY_URL = "https://democrats.org/find-a-state-party/"
LEADERSHIP_URL = "https://democrats.org/leadership/"
ACT_URL = "https://democrats.org/act/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
RUN_ID = "dnc-official-party-structure-2026-07-31"
MAX_PAGE_BYTES = 15_000_000

GEO = dict(
    line.split("=", 1)
    for line in """AK=Alaska
AL=Alabama
AR=Arkansas
AS=American Samoa
AZ=Arizona
CA=California
CO=Colorado
CT=Connecticut
DA=Democrats Abroad
DC=District of Columbia
DE=Delaware
FL=Florida
GA=Georgia
GU=Guam
HI=Hawaii
IA=Iowa
ID=Idaho
IL=Illinois
IN=Indiana
KS=Kansas
KY=Kentucky
LA=Louisiana
MA=Massachusetts
MD=Maryland
ME=Maine
MI=Michigan
MN=Minnesota
MO=Missouri
MP=Northern Mariana Islands
MS=Mississippi
MT=Montana
NC=North Carolina
ND=North Dakota
NE=Nebraska
NH=New Hampshire
NJ=New Jersey
NM=New Mexico
NV=Nevada
NY=New York
OH=Ohio
OK=Oklahoma
OR=Oregon
PA=Pennsylvania
PR=Puerto Rico
RI=Rhode Island
SC=South Carolina
SD=South Dakota
TN=Tennessee
TX=Texas
UT=Utah
VA=Virginia
VI=U.S. Virgin Islands
VT=Vermont
WA=Washington
WI=Wisconsin
WV=West Virginia
WY=Wyoming""".splitlines()
)

COMMITTEE_NAMES = (
    "Democratic Association of Secretaries of State",
    "Democratic Mayors Association",
    "Democratic Attorneys General Association",
    "Democratic Municipal Officials",
    "Democratic Congressional Campaign Committee",
    "Democratic Senatorial Campaign Committee",
    "Democratic Governors Association",
    "Democratic Treasurers Association",
    "Democratic Lieutenant Governors Association",
    "National Democratic County Officials",
    "Democratic Legislative Campaign Committee",
    "The ASDC",
)

STATE_AXES = (
    {
        "key": "current-leadership",
        "label": "current chairs, vice chairs, officers, and executive committee",
        "target_type": "state_party_current_leadership",
        "penalty": 0.00,
        "question": "Who currently governs {name}, including every chair, vice chair, officer, executive-committee member, DNC member, and ex officio seat?",
        "objectives": [
            "Acquire the newest official leadership and executive-committee roster",
            "Create one source-backed person and dated role relation per named official",
            "Record appointment or election basis, voting status, start and end dates, and vacancies",
            "Compare the current roster with archived rosters and the January 2025 DNC membership snapshot",
        ],
        "next": "Crawl the official party site and archives for the newest complete officer and executive-committee roster",
    },
    {
        "key": "bylaws-governance",
        "label": "bylaws, committees, delegates, and governance",
        "target_type": "state_party_bylaws_governance",
        "penalty": 0.01,
        "question": "What bylaws, rules, committees, delegate structures, appointment powers, and internal election procedures govern {name}?",
        "objectives": [
            "Acquire current and archived bylaws, charters, rules, meeting minutes, and convention materials",
            "Enumerate standing committees, caucuses, councils, delegates, and their complete public memberships",
            "Map authority to elect DNC members, fill vacancies, approve budgets, and endorse candidates",
        ],
        "next": "Collect current bylaws and enumerate every named committee, delegate body, and governance seat",
    },
    {
        "key": "local-affiliates",
        "label": "county, district, municipal, and local affiliates",
        "target_type": "state_party_local_affiliates",
        "penalty": 0.015,
        "question": "What is the complete public hierarchy beneath {name}, including county, district, municipal, ward, club, caucus, and constituency affiliates and their leaders?",
        "objectives": [
            "Enumerate every officially recognized local affiliate",
            "Capture each affiliate's website, officers, committees, jurisdiction, status, and parent relation",
            "Resolve cross-membership between local bodies, the state party, campaigns, public offices, unions, and advocacy groups",
        ],
        "next": "Acquire the official local-party directory and recursively enumerate each listed affiliate and leadership roster",
    },
    {
        "key": "staff-vendors-jobs",
        "label": "staff, consultants, vendors, and open positions",
        "target_type": "state_party_staff_vendors",
        "penalty": 0.02,
        "question": "Who works for, contracts with, or is being recruited by {name}, including executives, staff, consultants, legal firms, technology providers, fundraisers, and coordinated-campaign personnel?",
        "objectives": [
            "Enumerate current and archived staff directories and public job postings",
            "Map payroll, consulting, legal, technology, communications, fundraising, and field vendors",
            "Separate direct employment, coordinated-campaign roles, contractors, subcontractors, and shared national vendors",
        ],
        "next": "Collect staff pages, job postings, filings, expenditure purposes, archived bios, and vendor disclosures",
    },
    {
        "key": "finance-transfers",
        "label": "campaign-finance, transfers, grants, and counterparties",
        "target_type": "state_party_finance_network",
        "penalty": 0.005,
        "question": "What receipts, transfers, expenditures, grants, shared accounts, coordinated spending, and counterparties connect {name} to the DNC and the wider Democratic ecosystem?",
        "objectives": [
            "Resolve all federal and state committee registrations and linked accounts",
            "Import amendment-aware receipts, transfers, disbursements, independent expenditures, and coordinated spending",
            "Rank counterparties without flattening amended, memo, refunded, conduit, or reattributed records",
            "Map national-party, candidate, PAC, nonprofit, union, vendor, and local-affiliate money flows",
        ],
        "next": "Join federal and state campaign-finance records and build amendment-aware counterparty indexes",
    },
    {
        "key": "national-cross-ties",
        "label": "DNC, ASDC, campaign, government, and institutional cross-ties",
        "target_type": "state_party_national_cross_ties",
        "penalty": 0.012,
        "question": "Which people, committees, campaigns, public offices, agencies, PACs, unions, nonprofits, companies, and vendors connect to {name} through shared leadership, money, contracts, or governance?",
        "objectives": [
            "Map every officer, DNC member, committee chair, executive, and principal to outside roles",
            "Trace ASDC regional and committee roles, DNC committee service, campaigns, government employment, lobbying, boards, and vendors",
            "Create evidence-qualified relations while preserving unresolved names and contradictory records",
        ],
        "next": "Run every known leader through official role, filing, lobbying, corporate, nonprofit, and government records",
    },
)

ORG_AXES = (
    {
        "key": "leadership-membership",
        "label": "complete leadership, board, and membership roster",
        "target_type": "democratic_ecosystem_org_roster",
        "penalty": 0.00,
        "question": "What is the complete current and historical public leadership, board, officer, committee, staff, and membership roster of {name}?",
        "objectives": [
            "Acquire every official current and archived roster",
            "Create dated person-role relations without collapsing ambiguous names",
            "Capture bylaws, appointment powers, voting rights, vacancies, and term changes",
        ],
        "next": "Acquire official governance records and enumerate every named leader, officer, board member, committee member, and staff principal",
    },
    {
        "key": "legal-entities-control",
        "label": "legal entities, ownership, governance, and control",
        "target_type": "democratic_ecosystem_org_control",
        "penalty": 0.015,
        "question": "Which legal entities, affiliates, founders, officers, boards, sponsors, funders, and governance rights control or materially influence {name}?",
        "objectives": [
            "Resolve legal names, former names, parents, subsidiaries, PACs, nonprofits, and related committees",
            "Acquire corporate, nonprofit, campaign-finance, lobbying, and tax records",
            "Map shared officers, addresses, counsel, compliance vendors, funding sources, and governance rights",
        ],
        "next": "Resolve every legal entity and acquire registration, governance, funding, and tax records",
    },
    {
        "key": "money-vendors",
        "label": "money flows, contracts, consultants, and vendors",
        "target_type": "democratic_ecosystem_org_money_vendors",
        "penalty": 0.005,
        "question": "What receipts, transfers, grants, expenditures, contracts, consultants, and vendors connect {name} to party committees, campaigns, public officials, unions, nonprofits, and companies?",
        "objectives": [
            "Import amendment-aware federal and state transaction records",
            "Enumerate funders, grantees, donors, recipients, vendors, subcontractors, and payment processors",
            "Distinguish direct payments, pass-throughs, shared vendors, coordinated spending, and reported affiliation",
        ],
        "next": "Build a filing-backed money and vendor network with raw identifiers and amendment semantics preserved",
    },
    {
        "key": "people-cross-ties",
        "label": "people, campaign, government, and institutional cross-ties",
        "target_type": "democratic_ecosystem_org_cross_ties",
        "penalty": 0.01,
        "question": "Which campaigns, committees, public offices, agencies, lobbying clients, advocacy groups, unions, companies, and vendors connect to {name} through shared people?",
        "objectives": [
            "Map every leader, board member, officer, executive, founder, and principal to outside roles",
            "Trace prior and subsequent campaign, government, nonprofit, union, corporate, and lobbying positions",
            "Separate verified facts, attributed claims, contradictions, and unresolved identity matches",
        ],
        "next": "Run every known principal through official biographies, filings, lobbying records, corporate records, archives, and published reporting",
    },
    {
        "key": "programs-affiliates",
        "label": "programs, affiliates, chapters, partners, and operational footprint",
        "target_type": "democratic_ecosystem_org_programs_affiliates",
        "penalty": 0.02,
        "question": "Which programs, chapters, affiliates, coalitions, partners, events, training pipelines, and data or technology systems comprise the operational footprint of {name}?",
        "objectives": [
            "Enumerate current and archived programs, chapters, committees, coalitions, and partners",
            "Map program leadership, participants, grants, vendors, technology platforms, and data-sharing relationships",
            "Capture geographic scope, launch and sunset dates, and links to campaigns and party committees",
        ],
        "next": "Crawl official program and archive pages and enumerate every named affiliate, partner, program leader, and technology provider",
    },
)

PERSON_AXES = (
    {
        "key": "identity-role",
        "label": "identity, authority, and role-history verification",
        "target_type": "official_party_leader_identity_role",
        "penalty": 0.00,
        "question": "Which primary records establish {person}'s exact identity, authority, tenure, selection basis, and role history as {role} in {org}?",
        "objectives": [
            "Resolve the person without merging namesakes",
            "Verify exact title, start and end dates, election or appointment basis, and voting authority",
            "Collect current and archived official rosters, biographies, minutes, filings, and announcements",
        ],
        "next": "Resolve the person against official rosters, biographies, minutes, filings, and archived pages",
    },
    {
        "key": "cross-ties",
        "label": "campaign, government, organization, and vendor cross-ties",
        "target_type": "official_party_leader_cross_ties",
        "penalty": 0.015,
        "question": "Which campaigns, party committees, public offices, employers, boards, unions, nonprofits, companies, funders, clients, and vendors connect to {person}, currently listed as {role} in {org}?",
        "objectives": [
            "Enumerate current and historical public employment, campaign, committee, PAC, government, board, nonprofit, union, and corporate roles",
            "Trace donations, contracts, lobbying, consulting, vendor, and governance relationships",
            "Separate exact matches, likely matches, ambiguous names, and contradictory records",
        ],
        "next": "Search official biographies, filings, corporate and nonprofit records, lobbying disclosures, archives, and published reporting",
    },
)

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
    "official party and organization records",
    "Federal Election Commission and state campaign-finance agencies",
    "state corporate and charity registries",
    "IRS filings, lobbying disclosures, and government records",
    "court records, archives, and established published reporting",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import official DNC party structure and recursive targets")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--offline-state-html", type=Path)
    parser.add_argument("--offline-leadership-html", type=Path)
    parser.add_argument("--offline-act-html", type=Path)
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
    raw = "\x1f".join(parts).encode("utf-8")
    return f"starintel:{prefix}:{hashlib.sha256(raw).hexdigest()}"


def fetch_text(url: str, offline: Path | None) -> str:
    if offline:
        return offline.read_text(encoding="utf-8")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(MAX_PAGE_BYTES + 1)
        charset = response.headers.get_content_charset() or "utf-8"
    if len(payload) > MAX_PAGE_BYTES:
        raise RuntimeError(f"page exceeds safety cap: {url}")
    return payload.decode(charset, errors="replace")


def iter_corpus_records(output: Path) -> Iterable[dict[str, Any]]:
    skip = output.resolve()
    for pattern in ("db/**/*.ndjson", "digs/dnc/**/*.jsonl"):
        for path in sorted(Path.cwd().glob(pattern)):
            try:
                path.resolve().relative_to(skip)
                continue
            except ValueError:
                pass
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line in lines:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("dataset") == DATASET:
                    yield record


def corpus_index(output: Path) -> tuple[set[str], dict[str, list[str]], dict[str, list[str]]]:
    ids: set[str] = set()
    people: dict[str, list[str]] = defaultdict(list)
    orgs: dict[str, list[str]] = defaultdict(list)
    latest: dict[str, dict[str, Any]] = {}
    for record in iter_corpus_records(output):
        document_id = str(record.get("_id") or "")
        if not document_id:
            continue
        current = latest.get(document_id)
        candidate_key = (int(record.get("version", 0)), str(record.get("date_updated", "")))
        current_key = (int(current.get("version", 0)), str(current.get("date_updated", ""))) if current else (-1, "")
        if candidate_key >= current_key:
            latest[document_id] = record
    for document_id, record in latest.items():
        ids.add(document_id)
        data = record.get("data") if isinstance(record.get("data"), dict) else {}
        names = (record.get("title"), data.get("name"), data.get("full_name"))
        target = people if record.get("dtype") == "person" else orgs if record.get("dtype") == "org" else None
        if target is None:
            continue
        for value in names:
            key = norm(str(value or ""))
            if key and document_id not in target[key]:
                target[key].append(document_id)
    return ids, people, orgs


def source_document(document_id: str, title: str, summary: str, uri: str, kind: str, when: str, publisher: str = "Democratic National Committee") -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {
            "accessed_at": when,
            "credibility": 0.99,
            "kind": kind,
            "publisher": publisher,
            "uri": uri,
        },
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


def org_document(document_id: str, name: str, org_type: str, summary: str, source: str, when: str, identifiers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {"name": name, "org_type": org_type},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "organization", org_type.replace("_", "-")],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    if identifiers:
        document["identifiers"] = identifiers
    validate_document(document)
    return document


def person_document(document_id: str, name: str, source: str, context: str, when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {
            "full_name": name,
            "identity_resolution": "source_scoped_to_official_dnc_leadership_page_until_namesake_resolution",
            "source_context": context,
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
                "issuer": "Democratic National Committee leadership page",
                "scheme": "source_scoped_name",
                "value": f"{norm(context)}:{norm(name)}",
            }
        ],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source}],
        "status": "recorded",
        "summary": f"Official DNC leadership page lists {name} in {context}; identity remains source-scoped unless uniquely resolved in the existing corpus.",
        "tags": ["dnc", "person", "official-leadership", "source-scoped-identity"],
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
        "tags": ["dnc", "official-structure", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
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
                "official party and organization records and archives",
                "public campaign-finance, corporate, nonprofit, lobbying, tax, and government records",
                "court records and established published reporting",
                "archived public event programs, biographies, rosters, minutes, and job postings",
            ],
            "max_depth": 7,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": priority,
            "required_dtypes": ["source", "org", "person", "relation", "claim", "financial-observation"],
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
        "tags": ["dnc", "investigation-target", "official-party-structure", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-source", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-official-party-structure",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def heading_matches(text: str, expected: str) -> bool:
    left = norm(text)
    right = norm(expected)
    return left == right or left.startswith(right + " democratic party website") or left.startswith(right + " site")


def parse_state_websites(html_text: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html_text, "html.parser")
    results: list[dict[str, str]] = []
    used_urls: set[str] = set()
    for code, jurisdiction in GEO.items():
        heading: Tag | None = None
        for candidate in soup.find_all(["h2", "h3", "h4"]):
            if heading_matches(clean(candidate.get_text(" ", strip=True)), jurisdiction):
                heading = candidate
                break
        if heading is None:
            raise RuntimeError(f"state directory lacks heading for {jurisdiction}")
        link: str | None = None
        for node in heading.find_all_next():
            if node is not heading and getattr(node, "name", None) in {"h2", "h3", "h4"}:
                break
            if getattr(node, "name", None) != "a" or not node.get("href"):
                continue
            text = norm(clean(node.get_text(" ", strip=True)))
            if "visit party website" not in text and "party website" not in text:
                continue
            link = urllib.parse.urljoin(STATE_DIRECTORY_URL, str(node["href"]))
            break
        if not link:
            raise RuntimeError(f"state directory lacks official website link for {jurisdiction}")
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"invalid official party website for {jurisdiction}: {link}")
        canonical = urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))
        if canonical in used_urls:
            raise RuntimeError(f"duplicate official party URL: {canonical}")
        used_urls.add(canonical)
        results.append({"code": code, "jurisdiction": jurisdiction, "url": canonical})
    if len(results) != 57:
        raise RuntimeError(f"expected 57 official state and territorial party websites, found {len(results)}")
    return results


def parse_committee_links(html_text: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html_text, "html.parser")
    anchors: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        text = clean(anchor.get_text(" ", strip=True))
        if not text:
            continue
        href = urllib.parse.urljoin(ACT_URL, str(anchor["href"]))
        anchors.setdefault(norm(text), href)
    results: list[dict[str, str]] = []
    for name in COMMITTEE_NAMES:
        key = norm(name)
        href = anchors.get(key)
        if not href and name == "The ASDC":
            href = anchors.get(norm("ASDC"))
        if not href:
            raise RuntimeError(f"official DNC act page lacks link for {name}")
        results.append({"name": name, "url": href})
    return results


def role_from_card(heading: Tag) -> str | None:
    name = clean(heading.get_text(" ", strip=True))
    candidates: list[str] = []
    parent = heading.parent
    if isinstance(parent, Tag):
        values = [clean(value) for value in parent.stripped_strings]
        candidates.extend(value for value in values if value and value != name and value.lower() != "image")
    for node in heading.find_all_next(limit=8):
        if node is heading:
            continue
        if getattr(node, "name", None) in {"h1", "h2", "h3"}:
            break
        text = clean(node.get_text(" ", strip=True)) if isinstance(node, Tag) else ""
        if text and text != name and text.lower() != "image":
            candidates.append(text)
    unique = []
    for value in candidates:
        if value not in unique and len(value) <= 180:
            unique.append(value)
    return min(unique, key=len) if unique else None


def heading_index(headings: list[Tag], text: str) -> int:
    key = norm(text)
    for index, heading in enumerate(headings):
        if norm(clean(heading.get_text(" ", strip=True))) == key:
            return index
    raise RuntimeError(f"leadership page lacks section heading: {text}")


def parse_dash_roles(strings: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for raw in strings:
        text = clean(raw)
        parts = re.split(r"\s+[–—-]\s+", text, maxsplit=1)
        if len(parts) != 2:
            continue
        name, role = map(clean, parts)
        if len(name.split()) < 2 or len(role) < 3:
            continue
        results.append({"name": name, "role": role})
    return results


def parse_leadership(html_text: str) -> dict[str, list[dict[str, str]]]:
    soup = BeautifulSoup(html_text, "html.parser")
    headings = [heading for heading in soup.find_all(["h1", "h2", "h3"])]
    asdc_start = heading_index(headings, "ASDC Leadership")
    association_start = heading_index(headings, "Association-wide Leadership")
    regional_start = heading_index(headings, "Regional Leadership")
    cochair_start = heading_index(headings, "Committee Co-Chairs")

    dnc_roles: list[dict[str, str]] = []
    for heading in headings[:asdc_start]:
        if heading.name != "h3":
            continue
        name = clean(heading.get_text(" ", strip=True))
        role = role_from_card(heading)
        if name and role:
            dnc_roles.append({"name": name, "role": role})

    association_roles: list[dict[str, str]] = []
    for heading in headings[association_start + 1 : regional_start]:
        if heading.name != "h3":
            continue
        name = clean(heading.get_text(" ", strip=True))
        role = role_from_card(heading)
        if name and role:
            association_roles.append({"name": name, "role": role})

    regional_heading = headings[regional_start]
    cochair_heading = headings[cochair_start]
    regional_strings: list[str] = []
    for node in regional_heading.find_all_next():
        if node is cochair_heading:
            break
        if getattr(node, "name", None) == "li":
            regional_strings.append(clean(node.get_text(" ", strip=True)))
    regional_roles = parse_dash_roles(regional_strings)

    cochair_strings = [clean(node.get_text(" ", strip=True)) for node in cochair_heading.find_all_next("li")]
    committee_roles = parse_dash_roles(cochair_strings)

    def dedupe(values: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        output: list[dict[str, str]] = []
        for value in values:
            key = (norm(value["name"]), norm(value["role"]))
            if key in seen:
                continue
            seen.add(key)
            output.append(value)
        return output

    result = {
        "dnc": dedupe(dnc_roles),
        "asdc_association": dedupe(association_roles),
        "asdc_regional": dedupe(regional_roles),
        "asdc_committees": dedupe(committee_roles),
    }
    if len(result["dnc"]) < 8:
        raise RuntimeError(f"unexpected DNC leadership count: {len(result['dnc'])}")
    if len(result["asdc_association"]) < 5:
        raise RuntimeError(f"unexpected ASDC association-wide leadership count: {len(result['asdc_association'])}")
    if len(result["asdc_regional"]) < 15:
        raise RuntimeError(f"unexpected ASDC regional leadership count: {len(result['asdc_regional'])}")
    if len(result["asdc_committees"]) < 8:
        raise RuntimeError(f"unexpected ASDC committee co-chair count: {len(result['asdc_committees'])}")
    return result


def resolve_named_entity(name: str, index: dict[str, list[str]], prefix: str, context: str) -> tuple[str, bool]:
    matches = index.get(norm(name), [])
    if len(matches) == 1:
        return matches[0], False
    return sha_id(prefix, "official-dnc-source-scoped", context, norm(name)), True


def state_party_name(code: str, jurisdiction: str) -> str:
    if code == "DA":
        return "Democrats Abroad"
    if code == "DC":
        return "District of Columbia Democratic Party"
    return f"{jurisdiction} Democratic Party"


def build(
    state_sites: list[dict[str, str]],
    committees: list[dict[str, str]],
    leadership: dict[str, list[dict[str, str]]],
    existing_ids: set[str],
    people_index: dict[str, list[str]],
    org_index: dict[str, list[str]],
    when: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    directory_source = "starintel:source:dnc-official-state-party-directory-2026-07-31"
    leadership_source = "starintel:source:dnc-official-leadership-2026-07-31"
    act_source = "starintel:source:dnc-official-committee-directory-2026-07-31"
    documents: list[dict[str, Any]] = [
        source_document(directory_source, "Official DNC state-party directory", "Official DNC directory linking the 57 state, territorial, District of Columbia, and Democrats Abroad party organizations to their public websites.", STATE_DIRECTORY_URL, "official_party_directory", when),
        source_document(leadership_source, "Official DNC and ASDC leadership", "Official DNC leadership page listing current DNC officers and ASDC association-wide, regional, and committee leadership.", LEADERSHIP_URL, "official_leadership_roster", when),
        source_document(act_source, "Official DNC committee directory", "Official DNC action page listing national Democratic campaign, officeholder, local-government, and state-party associations under Explore committees.", ACT_URL, "official_committee_directory", when),
    ]
    emitted: set[str] = {document["_id"] for document in documents}

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    state_inventory: list[dict[str, Any]] = []
    for rank, item in enumerate(sorted(state_sites, key=lambda value: value["jurisdiction"]), 1):
        code = item["code"]
        jurisdiction = item["jurisdiction"]
        name = state_party_name(code, jurisdiction)
        org_id = f"starintel:org:dnc-state-party-{code.lower()}"
        website_source = sha_id("source", "official-state-party-website", code, item["url"])
        emit(
            source_document(
                website_source,
                f"Official website: {name}",
                f"Official party website linked from the DNC state-party directory for {jurisdiction}.",
                item["url"],
                "official_state_party_website",
                when,
                publisher=name,
            )
        )
        emit(
            relation_document(
                subject=org_id,
                predicate="official_website",
                obj=website_source,
                title=f"{name}: official website",
                summary="The official DNC state-party directory links this website for the named party organization.",
                qualifiers={"directory": STATE_DIRECTORY_URL, "jurisdiction": jurisdiction, "retrieved_at": when},
                source=directory_source,
                when=when,
            )
        )
        target_ids: list[str] = []
        priority_base = 0.96 if code in {"DA", "DC", "PR"} else 0.95
        for axis in STATE_AXES:
            target_id = sha_id("investigation-target", "dnc-official-state-party", org_id, axis["key"])
            question = axis["question"].format(name=name)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{name}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[org_id, website_source, DNC_ID, ASDC_ID],
                    source_ids=[directory_source, website_source],
                    priority=round(priority_base - float(axis["penalty"]), 4),
                    when=when,
                    tags=["state-party", code.lower(), str(axis["key"])],
                    depth=1,
                    breadth=150,
                )
            )
        state_inventory.append({**item, "organization": name, "organization_id": org_id, "rank": rank, "target_ids": target_ids})

    asdc_new = ASDC_ID not in existing_ids
    if asdc_new:
        emit(
            org_document(
                ASDC_ID,
                "Association of State Democratic Committees",
                "national_party_association",
                "The official DNC leadership page describes the ASDC as the national party organization focused on all 57 state parties and located within the DNC.",
                leadership_source,
                when,
            )
        )
    emit(
        relation_document(
            subject=ASDC_ID,
            predicate="located_within",
            obj=DNC_ID,
            title="ASDC located within the DNC",
            summary="The official DNC leadership page states that the ASDC is located within the Democratic National Committee.",
            qualifiers={"membership_scope": "chairs and vice chairs of all 57 state parties", "retrieved_at": when},
            source=leadership_source,
            when=when,
        )
    )

    committee_inventory: list[dict[str, Any]] = []
    for item in committees:
        display_name = "Association of State Democratic Committees" if item["name"] == "The ASDC" else item["name"]
        if item["name"] == "The ASDC":
            org_id = ASDC_ID
        else:
            org_id, create_org = resolve_named_entity(display_name, org_index, "org", "dnc-act-committee-directory")
            if create_org:
                emit(
                    org_document(
                        org_id,
                        display_name,
                        "democratic_ecosystem_organization",
                        "Organization listed by the DNC under Explore committees; the listing establishes directory inclusion, not automatic DNC control.",
                        act_source,
                        when,
                        identifiers=[
                            {"canonical": True, "issuer": "Democratic National Committee committee directory", "scheme": "normalized_name", "value": norm(display_name)}
                        ],
                    )
                )
        website_source = sha_id("source", "dnc-listed-committee-website", org_id, item["url"])
        emit(source_document(website_source, f"Official website: {display_name}", "Website linked by the DNC Explore committees directory.", item["url"], "official_organization_website", when, publisher=display_name))
        emit(
            relation_document(
                subject=DNC_ID,
                predicate="official_directory_lists_committee",
                obj=org_id,
                title=f"DNC committee directory lists {display_name}",
                summary="The official DNC action page lists this organization under Explore committees; the directory listing is not represented as ownership or control.",
                qualifiers={"listing_name": item["name"], "retrieved_at": when},
                source=act_source,
                when=when,
            )
        )
        emit(
            relation_document(
                subject=org_id,
                predicate="official_website",
                obj=website_source,
                title=f"{display_name}: official website",
                summary="The official DNC committee directory links this website for the organization.",
                qualifiers={"directory": ACT_URL, "retrieved_at": when},
                source=act_source,
                when=when,
            )
        )
        target_ids: list[str] = []
        for axis in ORG_AXES:
            target_id = sha_id("investigation-target", "dnc-official-committee-ecosystem", org_id, axis["key"])
            question = axis["question"].format(name=display_name)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{display_name}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[org_id, website_source, DNC_ID],
                    source_ids=[act_source, website_source],
                    priority=round(0.94 - float(axis["penalty"]), 4),
                    when=when,
                    tags=["democratic-ecosystem", "committee-directory", str(axis["key"])],
                    depth=1,
                    breadth=180,
                )
            )
        committee_inventory.append({**item, "display_name": display_name, "organization_id": org_id, "target_ids": target_ids})

    role_inventory: list[dict[str, Any]] = []
    role_groups = (
        ("dnc", DNC_ID, "Democratic National Committee", leadership["dnc"]),
        ("asdc-association", ASDC_ID, "Association of State Democratic Committees", leadership["asdc_association"]),
        ("asdc-regional", ASDC_ID, "Association of State Democratic Committees", leadership["asdc_regional"]),
        ("asdc-committee", ASDC_ID, "Association of State Democratic Committees", leadership["asdc_committees"]),
    )
    for group, org_id, org_name, roles in role_groups:
        for item in roles:
            person_id, create_person = resolve_named_entity(item["name"], people_index, "person", group)
            if create_person:
                emit(person_document(person_id, item["name"], leadership_source, group, when))
            relation = relation_document(
                subject=person_id,
                predicate="officially_listed_role_in",
                obj=org_id,
                title=f"{item['name']}: {item['role']} in {org_name}",
                summary=f"The official DNC leadership page lists {item['name']} as {item['role']} in {org_name} as accessed on 2026-07-31.",
                qualifiers={"current_as_of": "2026-07-31", "listing_group": group, "role": item["role"]},
                source=leadership_source,
                when=when,
            )
            emit(relation)
            target_ids: list[str] = []
            base = 0.98 if group == "dnc" else 0.96
            for axis in PERSON_AXES:
                target_id = sha_id("investigation-target", "dnc-official-party-leader", person_id, org_id, item["role"], axis["key"])
                question = axis["question"].format(person=item["name"], role=item["role"], org=org_name)
                target_ids.append(target_id)
                emit(
                    target_document(
                        target_id=target_id,
                        target_title=f"{item['name']} / {org_name}: {axis['label']}",
                        summary=question,
                        research_question=question,
                        objectives=list(axis["objectives"]),
                        next_action=str(axis["next"]),
                        target_type=str(axis["target_type"]),
                        seed_ids=[person_id, org_id, relation["_id"]],
                        source_ids=[leadership_source],
                        priority=round(base - float(axis["penalty"]), 4),
                        when=when,
                        tags=["person", "official-leadership", group, str(axis["key"])],
                        depth=2,
                        breadth=70,
                    )
                )
            role_inventory.append({**item, "group": group, "organization_id": org_id, "person_id": person_id, "target_ids": target_ids})

    for axis in ORG_AXES:
        target_id = sha_id("investigation-target", "dnc-official-asdc", ASDC_ID, axis["key"])
        question = axis["question"].format(name="Association of State Democratic Committees")
        emit(
            target_document(
                target_id=target_id,
                target_title=f"ASDC: {axis['label']}",
                summary=question,
                research_question=question,
                objectives=list(axis["objectives"]),
                next_action=str(axis["next"]),
                target_type=str(axis["target_type"]),
                seed_ids=[ASDC_ID, DNC_ID],
                source_ids=[leadership_source],
                priority=round(0.98 - float(axis["penalty"]), 4),
                when=when,
                tags=["asdc", str(axis["key"])],
                depth=1,
                breadth=250,
            )
        )

    metadata = {
        "committee_inventory": committee_inventory,
        "role_inventory": role_inventory,
        "state_inventory": state_inventory,
    }
    return sorted(documents, key=lambda document: document["_id"]), metadata


def write(output: Path, documents: list[dict[str, Any]], metadata: dict[str, Any], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    payload = "".join(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        for document in documents
    ).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(payload)
    for name, values in metadata.items():
        inventory = "".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
            for value in values
        ).encode("utf-8")
        (output / "source" / f"{name.replace('_', '-')}.jsonl").write_bytes(inventory)
    counts = Counter(document["dtype"] for document in documents)
    target_counts = Counter(
        document["data"]["target_type"]
        for document in documents
        if document["dtype"] == "investigation-target"
    )
    manifest = {
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(payload).hexdigest(),
        "generated_at": when,
        "official_committee_directory_entries": len(metadata["committee_inventory"]),
        "official_leadership_roles": len(metadata["role_inventory"]),
        "official_state_party_websites": len(metadata["state_inventory"]),
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(documents),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Official DNC party structure",
        "",
        "Live official-source import of the DNC state-party directory, DNC/ASDC leadership page, and DNC Explore committees directory.",
        "",
        f"- official state and territorial party websites: {len(metadata['state_inventory']):,}",
        f"- national committee-directory entries: {len(metadata['committee_inventory']):,}",
        f"- current official leadership-role listings: {len(metadata['role_inventory']):,}",
        f"- StarIntel documents: {len(documents):,}",
        f"- recursive investigation targets: {sum(target_counts.values()):,}",
        "",
        "Directory inclusion is not represented as ownership or operational control. Current roles are dated to the access date. Existing people and organizations are reused only when exact normalized names resolve to one unique corpus identity; otherwise identities remain source-scoped.",
        "",
        "## Target families",
        "",
    ]
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(
        [
            "",
            "```bash",
            "python3 -m pip install 'beautifulsoup4>=4.12,<5'",
            "python3 scripts/import_dnc_official_party_structure.py",
            "python3 scripts/validate-for-merge.py --site",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    state_html = fetch_text(STATE_DIRECTORY_URL, ns.offline_state_html)
    leadership_html = fetch_text(LEADERSHIP_URL, ns.offline_leadership_html)
    act_html = fetch_text(ACT_URL, ns.offline_act_html)
    state_sites = parse_state_websites(state_html)
    committees = parse_committee_links(act_html)
    leadership = parse_leadership(leadership_html)
    existing_ids, people_index, org_index = corpus_index(ns.output)
    documents, metadata = build(state_sites, committees, leadership, existing_ids, people_index, org_index, ns.generated_at)
    write(ns.output, documents, metadata, ns.generated_at)
    print(
        json.dumps(
            {
                "committees": len(committees),
                "documents": len(documents),
                "leadership_roles": sum(len(values) for values in leadership.values()),
                "output": str(ns.output),
                "state_party_websites": len(state_sites),
                "targets": sum(1 for document in documents if document["dtype"] == "investigation-target"),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
