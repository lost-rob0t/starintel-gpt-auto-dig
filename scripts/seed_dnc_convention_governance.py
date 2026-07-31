#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
GENERATED_AT = "2026-08-01T00:18:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-convention-governance")
RUN_ID = "dnc-convention-governance-2026-07-31"
DNC_ID = "starintel:org:dnc"
DNCC_ID = "starintel:org:democratic-national-convention-committee-2024"
RULES_ID = "starintel:org:dncc-convention-rules-committee-2024"
PLATFORM_ID = "starintel:org:dncc-platform-committee-2024"
CREDENTIALS_ID = "starintel:org:dncc-credentials-committee-2024"
DELEGATES_ID = "starintel:org:democratic-national-convention-delegates-2024"
OFFICER_ELECTION_ID = "starintel:event:dnc-2025-national-officer-election"
CONVENTION_ID = "starintel:event:democratic-national-convention-2024"
VIRTUAL_ROLL_CALL_ID = "starintel:event:dncc-2024-virtual-roll-call"
PLATFORM_PROCESS_ID = "starintel:event:dncc-2024-platform-process"
DEMPALOOZA_ID = "starintel:event:dncc-2024-dempalooza"

SOURCES = (
    {
        "id": "starintel:source:dnc-2024-permanent-convention-rules-release",
        "title": "DNCC Rules Committee passes permanent 2024 convention rules",
        "uri": "https://democrats.org/dncc-rules-committee-passes-permanent-rules-for-2024-presidential-nomination/",
        "published_at": "2024-07-24T00:00:00Z",
        "summary": "Official DNC release reporting that the 2024 Convention Rules Committee adopted permanent rules by a 157–3 vote and describing the virtual nomination process.",
        "kind": "official_convention_rules_release",
    },
    {
        "id": "starintel:source:dnc-2024-platform-final-release",
        "title": "DNC releases final 2024 party platform",
        "uri": "https://democrats.org/news/dnc-releases-2024-party-platform-to-be-voted-on-at-convention/",
        "published_at": "2024-08-18T00:00:00Z",
        "summary": "Official DNC release stating that the Platform Committee passed the final platform on July 16 after hearings, testimony submissions, and community engagement.",
        "kind": "official_platform_release",
    },
    {
        "id": "starintel:source:dnc-2024-nominating-petition-results",
        "title": "DNC and DNCC announce 2024 presidential nominating petition results",
        "uri": "https://democrats.org/news/dnc-and-dncc-chairs-announce-results-of-presidential-nominating-petition-process-and-opening-of-virtual-roll-call-on-august-1/",
        "published_at": "2024-07-30T00:00:00Z",
        "summary": "Official DNC release reporting the presidential nominating petition process, delegate signature totals, qualification threshold, and virtual voting window.",
        "kind": "official_nomination_results_release",
    },
    {
        "id": "starintel:source:dnc-2024-virtual-roll-call-results",
        "title": "DNC and DNCC announce closure and results of the 2024 virtual roll call",
        "uri": "https://democrats.org/dnc-chair-harrison-and-dncc-chair-moore-announce-roll-call-voting-window-has-closed-lay-out-next-steps-for-vp-harris-to-officially-clinch-nomination/",
        "published_at": "2024-08-05T00:00:00Z",
        "summary": "Official DNC release reporting the close of virtual voting, delegate participation, candidate vote share, state-by-state breakdown graphic, and certification steps.",
        "kind": "official_roll_call_results_release",
    },
    {
        "id": "starintel:source:dnc-2024-convention-leadership-announcement",
        "title": "DNC announces Chicago convention leadership team",
        "uri": "https://democrats.org/news/dnc-announces-chicago-conventionleadership-team/",
        "published_at": "2023-08-08T00:00:00Z",
        "summary": "Official DNC announcement naming the 2024 convention chair, executive director, senior advisers, and related campaign responsibilities.",
        "kind": "official_convention_leadership_announcement",
    },
    {
        "id": "starintel:source:dnc-2024-dempalooza-announcement",
        "title": "DNC announces DemPalooza convention events and trainings",
        "uri": "https://democrats.org/news/dnc-announces-full-daytime-convention-programming-in-chicago-debuts-dempalooza-events-and-trainings-open-to-all/",
        "published_at": "2024-08-14T00:00:00Z",
        "summary": "Official DNC announcement describing convention daytime training and event programming led by the DNC, campaign, and partner organizations, including named organizing tools.",
        "kind": "official_convention_program_announcement",
    },
    {
        "id": "starintel:source:dnc-2025-officer-election-rules-release",
        "title": "DNC RBC recommends 2025 national officer election rules",
        "uri": "https://democrats.org/news/dnc-rules-and-bylaws-committee-votes-to-recommend-2025-rules-of-procedure-for-election-of-dnc-officers/",
        "published_at": "2024-12-12T00:00:00Z",
        "summary": "Official DNC release reporting recommended procedures for the 2025 election of the DNC chair and national committee officers.",
        "kind": "official_officer_election_rules_release",
    },
    {
        "id": "starintel:source:dnc-official-proceedings-responsibility",
        "title": "DNC institutional responsibilities for convention proceedings",
        "uri": "https://democrats.org/internships/",
        "published_at": None,
        "summary": "Official DNC department description stating that the Office of the Secretary and Party Affairs certifies delegates, plans convention standing-committee meetings, oversees voting, and compiles official proceedings.",
        "kind": "official_department_responsibility",
    },
)

ORGS = (
    (DNCC_ID, "2024 Democratic National Convention Committee", "convention_committee", "Official DNC records identify the DNCC as the organizing committee for the 2024 Democratic National Convention."),
    (RULES_ID, "2024 Democratic National Convention Rules Committee", "convention_standing_committee", "Official DNC records report that the Rules Committee adopted the permanent convention rules by a 157–3 vote."),
    (PLATFORM_ID, "2024 Democratic National Convention Platform Committee", "convention_standing_committee", "Official DNC records state that the Platform Committee passed the final 2024 platform after public engagement and testimony."),
    (CREDENTIALS_ID, "2024 Democratic National Convention Credentials Committee", "convention_standing_committee", "Convention governance requires credentials review; the complete official committee roster and record are queued for acquisition."),
    (DELEGATES_ID, "2024 Democratic National Convention delegates", "convention_delegate_body", "Official DNC releases describe delegate petitions, voting eligibility, virtual roll-call ballots, and state-by-state results."),
)

PEOPLE = (
    ("starintel:person:dncc-minyon-moore-source-scoped", "Minyon Moore", DNCC_ID, "Chair", "starintel:source:dnc-2024-convention-leadership-announcement"),
    ("starintel:person:dncc-alex-hornbrook-source-scoped", "Alex Hornbrook", DNCC_ID, "Executive Director", "starintel:source:dnc-2024-convention-leadership-announcement"),
    ("starintel:person:dncc-louisa-terrell-source-scoped", "Louisa Terrell", DNCC_ID, "Senior Advisor", "starintel:source:dnc-2024-convention-leadership-announcement"),
    ("starintel:person:dncc-roger-lau-source-scoped", "Roger Lau", DNCC_ID, "Senior Advisor", "starintel:source:dnc-2024-convention-leadership-announcement"),
    ("starintel:person:dncc-tim-walz-source-scoped", "Tim Walz", RULES_ID, "Co-Chair", "starintel:source:dnc-2024-permanent-convention-rules-release"),
    ("starintel:person:dncc-leah-daughtry-source-scoped", "Leah Daughtry", RULES_ID, "Co-Chair", "starintel:source:dnc-2024-permanent-convention-rules-release"),
    ("starintel:person:dncc-jason-rae-source-scoped", "Jason Rae", DNCC_ID, "Convention Secretary", "starintel:source:dnc-2024-virtual-roll-call-results"),
)

TARGETS = (
    {
        "key": "rules-roster-votes",
        "entity": RULES_ID,
        "label": "complete Rules Committee roster, appointments, meetings, votes, and permanent rules",
        "type": "dncc_rules_committee_complete_record",
        "priority": 1.0,
        "question": "What complete official membership roster, appointment or election basis, role history, meeting record, attendance, agenda, packet, transcript, livestream, motion, vote, amendment, permanent-rule text, dissent, legal analysis, and later implementation record exists for the 2024 Convention Rules Committee?",
        "objectives": [
            "Acquire all 2024 Rules Committee membership lists and create dated person-role relations",
            "Acquire every notice, agenda, packet, minutes, video, transcript, motion, amendment, vote, and adopted rule",
            "Reconcile the reported 157–3 vote to named attendance and voting records if public",
            "Recover the official rules document and archived versions where current links are unavailable",
            "Map committee members to campaigns, state parties, public offices, organizations, vendors, counsel, and outside roles",
        ],
        "next": "Acquire official DNCC records and archives and enumerate every member, meeting, rule version, motion, and vote",
        "sources": ["starintel:source:dnc-2024-permanent-convention-rules-release", "starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "platform-roster-testimony",
        "entity": PLATFORM_ID,
        "label": "complete Platform Committee roster, testimony, hearings, drafts, and votes",
        "type": "dncc_platform_committee_complete_record",
        "priority": 1.0,
        "question": "What complete official membership roster, hearing, written testimony, submitter, community engagement, draft, amendment, vote, final platform, and archival record exists for the 2024 Platform Committee process?",
        "objectives": [
            "Acquire the complete Platform Committee and drafting-body rosters with dated roles",
            "Enumerate every public hearing, witness, written submission, author, organization, coalition, staff liaison, and presenter",
            "Recover every draft, amendment, comparison, vote, meeting record, and final platform file",
            "Create attributed claims and topic relations for testimony and platform provisions without treating policy statements as empirical facts",
            "Map members and submitters to campaigns, government, nonprofits, unions, companies, funders, and advocacy organizations",
        ],
        "next": "Recover the testimony portal, hearing records, rosters, drafts, amendments, vote records, final platform, and archives",
        "sources": ["starintel:source:dnc-2024-platform-final-release", "starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "credentials-roster-challenges",
        "entity": CREDENTIALS_ID,
        "label": "complete Credentials Committee roster, challenges, rulings, and delegate certification",
        "type": "dncc_credentials_committee_complete_record",
        "priority": 0.99,
        "question": "What complete official membership roster, delegate challenge, credentials filing, hearing, evidence, counsel, motion, vote, ruling, appeal, waiver, certification, and final report exists for the 2024 Credentials Committee?",
        "objectives": [
            "Acquire all Credentials Committee and staff rosters with appointment basis and dated roles",
            "Enumerate every delegate challenge, filing, party, counsel, hearing, evidence item, ruling, vote, waiver, settlement, and appeal",
            "Acquire delegate certification records, credentials reports, convention proceedings, and archived materials",
            "Map members, parties, counsel, vendors, and challenged delegations to outside organizations and roles",
        ],
        "next": "Collect DNCC credentials records, delegate certifications, challenges, rulings, reports, proceedings, and archives",
        "sources": ["starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "delegate-roster-petitions",
        "entity": DELEGATES_ID,
        "label": "complete delegate roster, petition signatures, eligibility, affiliations, and verification",
        "type": "dncc_delegate_roster_petition_audit",
        "priority": 1.0,
        "question": "What complete public delegate roster, allocation, pledged or automatic status, constituency, credential status, petition participation, candidate signature, eligibility verification, replacement, vacancy, challenge, and affiliation record exists for the 2024 convention?",
        "objectives": [
            "Acquire all official delegate and alternate lists, allocation tables, credentials records, replacements, vacancies, and corrections",
            "Record each public delegate's jurisdiction, category, pledged or automatic status, constituency, and dated certification",
            "Audit the reported 3,923 petition signers and state limits using public aggregate or named records where officially released",
            "Map delegates to DNC membership, state parties, campaigns, public offices, unions, nonprofits, companies, boards, and vendors",
            "Exclude private contact information and any delegate communications not affirmatively made public",
        ],
        "next": "Recover official delegate lists, allocation tables, credentials records, petition aggregates, corrections, and proceedings",
        "sources": ["starintel:source:dnc-2024-nominating-petition-results", "starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "virtual-roll-call-system",
        "entity": VIRTUAL_ROLL_CALL_ID,
        "label": "virtual roll-call ballot system, vendors, security, verification, and audit trail",
        "type": "dncc_virtual_roll_call_system_audit",
        "priority": 1.0,
        "question": "Which software, vendors, contractors, staff, identity and eligibility checks, authentication controls, ballot-delivery methods, security reviews, support systems, incident procedures, tabulation logic, audit records, certification steps, and archived artifacts comprised the 2024 virtual roll call?",
        "objectives": [
            "Enumerate every publicly named technology provider, contractor, staff owner, counsel, auditor, support vendor, and security reviewer",
            "Acquire public specifications, instructions, ballot forms, verification procedures, incident plans, accessibility records, test evidence, result certifications, and archived interfaces",
            "Reconcile aggregate and state-by-state participation and vote results to official certifications",
            "Record public security claims and independent evidence separately; do not seek credentials, private ballots, private contact data, or exploit details",
            "Map vendors and principals to other party, campaign, election, government, nonprofit, and corporate systems",
        ],
        "next": "Acquire official technical, procurement, security, accessibility, support, tabulation, certification, and results records and identify every public vendor and principal",
        "sources": ["starintel:source:dnc-2024-permanent-convention-rules-release", "starintel:source:dnc-2024-nominating-petition-results", "starintel:source:dnc-2024-virtual-roll-call-results"],
    },
    {
        "key": "roll-call-results",
        "entity": VIRTUAL_ROLL_CALL_ID,
        "label": "state-by-state roll-call results, participation, certification, and discrepancies",
        "type": "dncc_virtual_roll_call_results_audit",
        "priority": 0.99,
        "question": "What complete official state-by-state delegate eligibility, participation, candidate vote, abstention, blank, invalid, challenged, late, corrected, and certification record supports the published 2024 virtual roll-call results?",
        "objectives": [
            "Acquire machine-readable state-by-state and delegate-category result tables and official certifications",
            "Reconcile total eligible delegates, participating delegates, candidate votes, nonvotes, and reported percentages",
            "Capture revisions, corrections, certification signatures, disputes, and media representations",
            "Create transparent calculations and contradiction records for any unresolved differences",
        ],
        "next": "Recover the state-by-state result source behind the published graphic and all official certifications and corrections",
        "sources": ["starintel:source:dnc-2024-virtual-roll-call-results"],
    },
    {
        "key": "convention-leadership-staff-vendors",
        "entity": DNCC_ID,
        "label": "complete convention leadership, staff, consultants, contractors, and vendors",
        "type": "dncc_leadership_staff_vendor_network",
        "priority": 0.98,
        "question": "Who led, staffed, advised, contracted with, funded, or supplied the 2024 DNCC, and which entities handled production, venues, labor, security, technology, data, media, transport, housing, credentials, accessibility, fundraising, legal, compliance, and logistics?",
        "objectives": [
            "Acquire complete current and archived DNCC leadership, staff, consultant, fellowship, intern, and public job rosters",
            "Enumerate legal entities, officers, boards, host committee, venues, unions, contractors, vendors, subcontractors, sponsors, donors, and in-kind providers",
            "Map contracts, payments, FEC records, public procurement, fundraising, grants, reimbursements, and shared campaign infrastructure",
            "Trace every principal to campaigns, party committees, government, corporations, nonprofits, unions, lobbying clients, and prior conventions",
        ],
        "next": "Combine official rosters, FEC filings, host-committee records, contracts, public job posts, archives, venue and vendor disclosures, and published reporting",
        "sources": ["starintel:source:dnc-2024-convention-leadership-announcement", "starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "dempalooza-sessions-partners-tools",
        "entity": DEMPALOOZA_ID,
        "label": "complete DemPalooza sessions, speakers, partners, tools, participants, and vendors",
        "type": "dncc_dempalooza_complete_program_network",
        "priority": 0.96,
        "question": "What complete session schedule, training, panel, speaker, facilitator, partner organization, campaign, state party, tool, application, vendor, sponsor, venue, participant, recording, presentation, handout, and outcome record exists for 2024 DemPalooza?",
        "objectives": [
            "Acquire every official schedule, program, app entry, session description, presenter bio, video, transcript, slide deck, handout, and archive",
            "Enumerate every named speaker, trainer, facilitator, partner, campaign, committee, organization, vendor, tool, and technology platform",
            "Map contracts, payments, program ownership, data or technology dependencies, participant pipelines, and later reuse",
            "Create separate records for official program claims, participant accounts, measured outcomes, and independent evidence",
        ],
        "next": "Recover the complete DemPalooza program and archives and resolve every session, speaker, partner, tool, and vendor",
        "sources": ["starintel:source:dnc-2024-dempalooza-announcement"],
    },
    {
        "key": "official-proceedings",
        "entity": CONVENTION_ID,
        "label": "complete official proceedings, roll calls, reports, resolutions, speeches, and corrections",
        "type": "dncc_official_proceedings_complete_archive",
        "priority": 0.99,
        "question": "What complete official proceedings, daily journal, agenda, delegate roster, roll call, committee report, resolution, platform, rules, credentials report, speech, transcript, video, motion, vote, certification, appendix, correction, and archival record exists for the 2024 Democratic National Convention?",
        "objectives": [
            "Locate the official proceedings publication promised by the Office of the Secretary and Party Affairs",
            "Enumerate every document, speaker, session, committee, motion, vote, resolution, report, certification, and appendix",
            "Create one source and event record per artifact with version, page, date, session, and hash provenance",
            "Compare official proceedings to press releases, livestreams, transcripts, schedules, and archived pages and record omissions or corrections",
        ],
        "next": "Acquire the official proceedings and all related convention publications and convert them into a document-level, event-level, and person-role index",
        "sources": ["starintel:source:dnc-official-proceedings-responsibility"],
    },
    {
        "key": "2025-officer-election",
        "entity": OFFICER_ELECTION_ID,
        "label": "complete 2025 officer-election candidates, rules, electorate, ballots, rounds, results, and vendors",
        "type": "dnc_2025_officer_election_complete_record",
        "priority": 1.0,
        "question": "What complete official candidate, nomination, endorsement, questionnaire, forum, debate, electorate, membership roster, ballot, round-by-round result, abstention, invalid vote, proxy, challenge, rule, waiver, vendor, technology, certification, and archive record exists for the 2025 DNC national officer elections?",
        "objectives": [
            "Acquire all proposed and adopted election rules, amendments, notices, candidate filings, questionnaires, forums, and official communications",
            "Enumerate every candidate, nominator, endorser, electorate member, officer seat, voting round, result, withdrawal, challenge, and certification",
            "Acquire public ballot-system, vendor, security, accessibility, support, tabulation, and audit records without seeking private ballots or credentials",
            "Map candidates and electorate members to campaigns, committees, government, state parties, nonprofits, unions, companies, donors, clients, and vendors",
        ],
        "next": "Collect official election rules, candidate materials, forums, electorate rosters, results by round, certifications, technology records, and archives",
        "sources": ["starintel:source:dnc-2025-officer-election-rules-release", "starintel:source:dnc-official-proceedings-responsibility"],
    },
)

OUT_OF_SCOPE = [
    "private ballots or petition forms",
    "private delegate or staff contact information",
    "credentials, authentication secrets, or exploit details",
    "private residential addresses",
    "non-public personal data",
    "unsupported criminal conclusions",
]
EXCLUDED_SOURCES = ["unsourced reposts", "anonymous claims without underlying artifacts", "people-search or data-broker profiles"]
PREFERRED_SOURCES = [
    "official DNC and DNCC rules, rosters, proceedings, minutes, certifications, reports, and archives",
    "official FEC filings, contracts, public records, vendor disclosures, FCC political files, and platform ad libraries",
    "court records, government records, archival captures, and established published reporting",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed DNC convention governance and exhaustive targets")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def sha_id(prefix: str, *parts: str) -> str:
    return f"starintel:{prefix}:{hashlib.sha256(chr(31).join(parts).encode('utf-8')).hexdigest()}"


def source_document(item: dict[str, Any], when: str) -> dict[str, Any]:
    document = {
        "_id": item["id"],
        "data": {"accessed_at": when, "credibility": 0.99, "kind": item["kind"], "published_at": item["published_at"], "publisher": "Democratic National Committee", "uri": item["uri"]},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": item["summary"],
        "tags": ["dnc", "dncc", "convention", "official-source"],
        "title": item["title"],
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    document["data"] = {key: value for key, value in document["data"].items() if value is not None}
    validate_document(document)
    return document


def org_document(item: tuple[str, str, str, str], source_ids: list[str], when: str) -> dict[str, Any]:
    document_id, name, org_type, summary = item
    document = {
        "_id": document_id,
        "data": {"name": name, "org_type": org_type},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "org",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Democratic National Committee", "scheme": "official_convention_body", "value": document_id.rsplit(":", 1)[-1]}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "dncc", "convention", org_type.replace("_", "-")],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def event_document(document_id: str, title: str, event_type: str, summary: str, source_ids: list[str], start: str | None, end: str | None, when: str) -> dict[str, Any]:
    data: dict[str, Any] = {"event_type": event_type}
    temporal: dict[str, Any] = {}
    if start:
        temporal["start_at"] = start
    if end:
        temporal["end_at"] = end
    document = {
        "_id": document_id,
        "data": data,
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "event",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "dncc", "convention", event_type.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    if temporal:
        document["temporal"] = temporal
    validate_document(document)
    return document


def person_document(document_id: str, name: str, source_id: str, when: str) -> dict[str, Any]:
    document = {
        "_id": document_id,
        "data": {"full_name": name, "identity_resolution": "source_scoped_to_official_convention_role_until_namesake_resolution"},
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [{"canonical": True, "issuer": "Democratic National Committee convention record", "scheme": "source_scoped_name", "value": document_id.rsplit(":", 1)[-1]}],
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id}],
        "status": "recorded",
        "summary": f"Official DNC convention record names {name} in a convention leadership or committee role; identity remains source-scoped pending unique resolution.",
        "tags": ["dnc", "dncc", "convention", "person", "source-scoped-identity"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-listed-name", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def relation_document(subject: str, predicate: str, obj: str, title: str, summary: str, qualifiers: dict[str, Any], source_ids: list[str], when: str) -> dict[str, Any]:
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
        "sources": [{"source_id": source_id} for source_id in source_ids],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "dncc", "convention", "relation", predicate.replace("_", "-")],
        "title": title,
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def target_document(item: dict[str, Any], when: str) -> dict[str, Any]:
    target_id = sha_id("investigation-target", "dnc-convention-governance", item["key"], item["entity"])
    document = {
        "_id": target_id,
        "data": {
            "breadth": 350,
            "depth": 1,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": [
                "official DNC, DNCC, convention, committee, delegate, rules, proceedings, certification, and archive records",
                "public campaign-finance, contracts, procurement, vendor, corporate, nonprofit, union, government, FCC, and platform records",
                "court records, public archives, and established reporting",
            ],
            "max_depth": 8,
            "objectives": item["objectives"],
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": item["priority"],
            "required_dtypes": ["source", "org", "person", "relation", "claim", "event", "financial-observation"],
            "research_question": item["question"],
            "scope_type": "public_source",
            "seed_ids": [item["entity"], DNC_ID, DNCC_ID],
            "source_ids": item["sources"],
            "status": "queued",
            "target": item["label"],
            "target_type": item["type"],
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "investigation-target",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in item["sources"]],
        "status": "recorded",
        "summary": item["question"],
        "tags": ["dnc", "dncc", "convention", "investigation-target", item["key"]],
        "title": item["label"],
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-source", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 8,
            "next_action": item["next"],
            "priority": item["priority"],
            "queue": "dnc-convention-governance",
            "recursion_depth": 1,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def build(when: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    emitted: set[str] = set()

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            return
        emitted.add(document["_id"])
        documents.append(document)

    for source in SOURCES:
        emit(source_document(source, when))
    source_ids = [source["id"] for source in SOURCES]
    for org in ORGS:
        emit(org_document(org, source_ids, when))
    events = (
        event_document(CONVENTION_ID, "2024 Democratic National Convention", "national_party_convention", "Official DNC and DNCC records describe the 2024 convention, its standing committees, delegate votes, platform process, and proceedings.", source_ids, "2024-08-19T00:00:00Z", "2024-08-22T23:59:59Z", when),
        event_document(VIRTUAL_ROLL_CALL_ID, "2024 Democratic presidential virtual roll call", "virtual_nomination_vote", "Official DNC releases report a virtual presidential nominating vote open August 1–5, 2024, followed by certification.", ["starintel:source:dnc-2024-permanent-convention-rules-release", "starintel:source:dnc-2024-nominating-petition-results", "starintel:source:dnc-2024-virtual-roll-call-results"], "2024-08-01T09:00:00-04:00", "2024-08-05T18:00:00-04:00", when),
        event_document(PLATFORM_PROCESS_ID, "2024 Democratic Party platform process", "party_platform_process", "Official DNC records describe hearings, written testimony, community engagement, committee passage on July 16, and delegate consideration at the convention.", ["starintel:source:dnc-2024-platform-final-release"], None, "2024-08-19T23:59:59Z", when),
        event_document(DEMPALOOZA_ID, "2024 DemPalooza", "convention_training_program", "Official DNC records describe daytime convention events, trainings, panels, tools, and partner-led programming in Chicago.", ["starintel:source:dnc-2024-dempalooza-announcement"], "2024-08-19T00:00:00Z", "2024-08-22T23:59:59Z", when),
        event_document(OFFICER_ELECTION_ID, "2025 DNC national officer election", "national_party_officer_election", "Official DNC records describe Rules and Bylaws Committee procedures governing the 2025 election of the DNC chair and national officers.", ["starintel:source:dnc-2025-officer-election-rules-release"], None, None, when),
    )
    for event in events:
        emit(event)
    for org_id in (RULES_ID, PLATFORM_ID, CREDENTIALS_ID, DELEGATES_ID):
        emit(relation_document(org_id, "part_of", DNCC_ID, f"{org_id.rsplit(':', 1)[-1]} is part of the 2024 DNCC", "Official convention records identify this body within the 2024 convention governance structure.", {"cycle": 2024}, source_ids, when))
    emit(relation_document(DNCC_ID, "organized", CONVENTION_ID, "DNCC organized the 2024 Democratic National Convention", "Official DNC records identify the DNCC as the convention organizing committee.", {"cycle": 2024}, source_ids, when))
    emit(relation_document(RULES_ID, "adopted_rules_for", VIRTUAL_ROLL_CALL_ID, "Rules Committee adopted rules governing the virtual roll call", "The official DNC release reports that the Rules Committee adopted permanent rules establishing the virtual nominating process by a 157–3 vote.", {"vote_for": 157, "vote_against": 3, "decision_date": "2024-07-24"}, ["starintel:source:dnc-2024-permanent-convention-rules-release"], when))
    emit(relation_document(PLATFORM_ID, "produced_platform_for", CONVENTION_ID, "Platform Committee produced the 2024 platform", "The official DNC release states that the Platform Committee passed the final platform on July 16 before delegate consideration at the convention.", {"committee_passage_date": "2024-07-16"}, ["starintel:source:dnc-2024-platform-final-release"], when))
    emit(relation_document(DELEGATES_ID, "voted_in", VIRTUAL_ROLL_CALL_ID, "Convention delegates voted in the 2024 virtual roll call", "Official DNC releases describe delegate eligibility, personalized ballots, participation, results, and certification steps.", {"reported_candidate_votes": 4567, "reported_candidate_vote_share_percent": 99}, ["starintel:source:dnc-2024-nominating-petition-results", "starintel:source:dnc-2024-virtual-roll-call-results"], when))
    for person_id, name, org_id, role, source_id in PEOPLE:
        emit(person_document(person_id, name, source_id, when))
        emit(relation_document(person_id, "officially_listed_role_in", org_id, f"{name}: {role}", f"Official DNC convention reporting lists {name} as {role} in the named convention body.", {"role": role, "cycle": 2024}, [source_id], when))
    for target in TARGETS:
        emit(target_document(target, when))
    return sorted(documents, key=lambda document: document["_id"])


def write(output: Path, documents: list[dict[str, Any]], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in documents).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(payload)
    counts = Counter(document["dtype"] for document in documents)
    target_counts = Counter(document["data"]["target_type"] for document in documents if document["dtype"] == "investigation-target")
    manifest = {
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(payload).hexdigest(),
        "generated_at": when,
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(documents),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# DNC convention governance",
        "",
        "Official-source seed and exhaustive target queue for 2024 convention standing committees, delegates, petitioning, virtual voting, platform testimony, leadership, DemPalooza, official proceedings, and the 2025 DNC officer-election process.",
        "",
        f"- StarIntel documents: {len(documents):,}",
        f"- official source records: {counts.get('source', 0):,}",
        f"- organizations: {counts.get('org', 0):,}",
        f"- people: {counts.get('person', 0):,}",
        f"- events: {counts.get('event', 0):,}",
        f"- relations: {counts.get('relation', 0):,}",
        f"- exhaustive investigation targets: {sum(target_counts.values()):,}",
        "",
        "Targets are limited to public records. The virtual-voting audit explicitly excludes private ballots, petition forms, delegate contact information, credentials, authentication secrets, and exploit details.",
        "",
        "## Target families",
        "",
    ]
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(["", "```bash", "python3 scripts/seed_dnc_convention_governance.py", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    documents = build(ns.generated_at)
    write(ns.output, documents, ns.generated_at)
    print(json.dumps({"documents": len(documents), "output": str(ns.output), "targets": sum(1 for document in documents if document["dtype"] == "investigation-target")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
