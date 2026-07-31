#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
GENERATED_AT = "2026-07-31T07:20:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-organization-member-targets")
RUN_ID = "dnc-organization-member-enumeration-2026-07-31"
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
IN_SCOPE = [
    "official organization pages and archived rosters",
    "public filings and government records",
    "corporate and nonprofit records",
    "court records and published reporting",
    "archived public media and event programs",
]
PREFERRED_SOURCES = [
    "official organization records",
    "Federal Election Commission",
    "state corporate and charity registries",
    "IRS filings and nonprofit disclosures",
    "court dockets and opinions",
    "archived official websites",
]
AFFILIATION_MARKERS = (
    "member", "representative", "employ", "staff", "work", "found", "officer",
    "director", "chair", "executive", "advisor", "principal", "owner", "manage",
    "treasurer", "secretary", "delegate", "affiliate", "leadership", "board",
)
ORG_AXES = (
    {
        "key": "complete-membership",
        "label": "complete public membership roster",
        "penalty": 0.00,
        "question": "What is the complete current and historical public membership roster of {name}, including role titles, appointment or election basis, start and end dates, and source provenance?",
        "objectives": [
            "Acquire every official current and archived membership roster",
            "Create one person record and dated membership relation per named member",
            "Resolve duplicate names without collapsing ambiguous identities",
            "Record vacancies, ex officio seats, voting status, and roster effective dates",
        ],
        "next": "Locate the newest official roster and enumerate every named member with dated role evidence",
        "target_type": "organization_membership_roster",
    },
    {
        "key": "governance",
        "label": "leadership and governance",
        "penalty": 0.01,
        "question": "Who governs {name}, through which officer, board, committee, delegate, or advisory roles, and how have those roles changed over time?",
        "objectives": [
            "Enumerate officers, directors, trustees, committees, delegates, and advisory bodies",
            "Capture bylaws, appointment powers, election procedures, terms, and vacancies",
            "Map every governance person to other organizations and public offices",
        ],
        "next": "Acquire bylaws and the latest officer, board, committee, and delegate lists",
        "target_type": "organization_governance",
    },
    {
        "key": "staff-contractors",
        "label": "staff, consultants, and contractors",
        "penalty": 0.02,
        "question": "Who works for or contracts with {name}, in what role, during what dates, and through which payroll, consulting, technology, legal, communications, or fundraising entities?",
        "objectives": [
            "Enumerate executives, employees, consultants, contractors, and retained firms",
            "Separate direct employment from vendor, subcontractor, and pass-through relationships",
            "Map prior and subsequent campaign, government, nonprofit, and corporate roles",
        ],
        "next": "Collect staff directories, filings, payroll/vendor records, archived bios, and contract disclosures",
        "target_type": "organization_staff_and_contractors",
    },
    {
        "key": "ownership-funding-control",
        "label": "ownership, funding, and control",
        "penalty": 0.03,
        "question": "Who legally owns, funds, controls, or materially influences {name}, through which entities, instruments, grants, donations, contracts, investors, or governance rights?",
        "objectives": [
            "Resolve legal entities, former names, parents, subsidiaries, and related organizations",
            "Identify founders, owners, major funders, lenders, creditors, investors, and controlling officers",
            "Trace grants, donations, contracts, shared vendors, and inter-organization transfers",
        ],
        "next": "Resolve the legal entity and collect corporate, nonprofit, campaign-finance, and funding records",
        "target_type": "organization_ownership_funding_control",
    },
    {
        "key": "political-cross-ties",
        "label": "political and institutional cross-ties",
        "penalty": 0.015,
        "question": "Which campaigns, party committees, PACs, public offices, agencies, lobbying clients, advocacy groups, and vendors connect to {name} through shared people, money, contracts, or governance?",
        "objectives": [
            "Map every known member, executive, board member, founder, and principal to outside organizations",
            "Trace campaign, committee, PAC, lobbying, government, nonprofit, and corporate roles",
            "Create evidence-qualified cross-organization relations and contradiction records",
        ],
        "next": "Run every known person and principal through public role, filing, lobbying, and organization records",
        "target_type": "organization_cross_ties",
    },
)
MEMBER_AXES = (
    {
        "key": "role-verification",
        "label": "role and identity verification",
        "penalty": 0.01,
        "question": "What public records establish {person}'s exact identity, role, authority, dates, and membership status in {org}?",
        "objectives": [
            "Resolve the person without merging namesakes",
            "Verify exact role title, appointment or election basis, dates, and voting or decision authority",
            "Collect primary-source roster, biography, filing, or archival evidence",
        ],
        "next": "Verify the named person's role against the newest and historical primary-source rosters",
        "target_type": "organization_member_role_verification",
    },
    {
        "key": "cross-ties",
        "label": "outside affiliations and cross-ties",
        "penalty": 0.025,
        "question": "Which campaigns, committees, public offices, employers, boards, vendors, funders, clients, and advocacy organizations connect {person} to or through {org}?",
        "objectives": [
            "Enumerate current and historical public employment, board, campaign, committee, PAC, government, and nonprofit roles",
            "Trace donations, contracts, lobbying, vendor relationships, and shared organizational principals",
            "Separate verified facts, attributed claims, contradictions, and unresolved identity matches",
        ],
        "next": "Search official bios, filings, corporate records, lobbying disclosures, archives, and published reporting",
        "target_type": "organization_member_cross_ties",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate exhaustive DNC organization and member targets")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def iter_records(root: Path, output: Path) -> Iterable[dict[str, Any]]:
    skip = output.resolve()
    paths = list(root.glob("db/**/*.ndjson")) + list(root.glob("digs/dnc/**/*.jsonl"))
    for path in sorted(set(paths)):
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
            if not isinstance(record, dict):
                continue
            if record.get("dataset") != DATASET:
                continue
            if record.get("schema_version") != "0.9.0":
                continue
            if not record.get("_id") or not record.get("dtype"):
                continue
            yield record


def latest_records(root: Path, output: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in iter_records(root, output):
        doc_id = str(record["_id"])
        current = records.get(doc_id)
        if current is None:
            records[doc_id] = record
            continue
        candidate_key = (int(record.get("version", 0)), str(record.get("date_updated", "")))
        current_key = (int(current.get("version", 0)), str(current.get("date_updated", "")))
        if candidate_key > current_key:
            records[doc_id] = record
    return records


def title(record: dict[str, Any]) -> str:
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    for value in (record.get("title"), data.get("name"), data.get("full_name")):
        if isinstance(value, str) and value.strip():
            return re.sub(r"\s+", " ", value).strip()
    return str(record["_id"])


def source_ids(*records: dict[str, Any], limit: int = 20) -> list[str]:
    result: list[str] = []
    for record in records:
        for source in record.get("sources", []):
            if isinstance(source, dict):
                value = source.get("source_id")
            else:
                value = None
            if isinstance(value, str) and value and value not in result:
                result.append(value)
                if len(result) >= limit:
                    return result
    return result


def digest_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:investigation-target:dnc-{kind}-{digest}"


def relation_endpoints(record: dict[str, Any]) -> tuple[str, str, str] | None:
    if record.get("dtype") != "relation":
        return None
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    subject, predicate, obj = data.get("subject"), data.get("predicate"), data.get("object")
    if not all(isinstance(value, str) and value for value in (subject, predicate, obj)):
        return None
    return subject, predicate, obj


def org_kind(record: dict[str, Any]) -> str:
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    value = str(data.get("org_type") or "organization").lower()
    if "state_party" in value or "party_committee" in value or "national_party" in value:
        return "party"
    if any(marker in value for marker in ("vendor", "technology", "consult", "payroll", "fundraising")):
        return "vendor"
    if any(marker in value for marker in ("pac", "political_action", "campaign")):
        return "political-organization"
    if any(marker in value for marker in ("nonprofit", "foundation", "advocacy", "media")):
        return "nonprofit-or-media"
    if any(marker in value for marker in ("agency", "government")):
        return "government"
    return "organization"


def base_priority(record: dict[str, Any], degree: int, known_people: int) -> float:
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    org_type = str(data.get("org_type") or "").lower()
    if record["_id"] == "starintel:org:dnc":
        base = 1.0
    elif "national_party" in org_type:
        base = 0.99
    elif any(marker in org_type for marker in ("political_consult", "political_technology", "campaign_technology", "fundraising_technology", "digital_fundraising")):
        base = 0.96
    elif "state_party" in org_type or "political_action" in org_type:
        base = 0.92
    elif any(marker in org_type for marker in ("vendor", "payroll", "technology")):
        base = 0.88
    elif any(marker in org_type for marker in ("nonprofit", "media", "advocacy")):
        base = 0.86
    elif any(marker in org_type for marker in ("agency", "government")):
        base = 0.78
    elif "fec_reported_payee" in org_type:
        base = 0.72
    else:
        base = 0.80
    evidence_bonus = min(0.05, math.log2(max(1, degree + 1)) * 0.01)
    people_bonus = min(0.04, math.log2(max(1, known_people + 1)) * 0.01)
    return round(min(1.0, base + evidence_bonus + people_bonus), 4)


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
    sources: list[str],
    priority: float,
    when: str,
    tags: list[str],
    breadth: int,
    depth: int,
) -> dict[str, Any]:
    document = {
        "_id": target_id,
        "data": {
            "breadth": breadth,
            "depth": depth,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": IN_SCOPE,
            "max_depth": 7,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": PREFERRED_SOURCES,
            "priority": priority,
            "required_dtypes": ["source", "org", "person", "relation", "claim"],
            "research_question": research_question,
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
        "sources": [{"source_id": source_id} for source_id in sources],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "investigation-target", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-corpus", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-organization-enumeration",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def build(records: dict[str, dict[str, Any]], when: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    orgs = {doc_id: record for doc_id, record in records.items() if record.get("dtype") == "org"}
    people = {doc_id: record for doc_id, record in records.items() if record.get("dtype") == "person"}
    relations = [record for record in records.values() if record.get("dtype") == "relation"]
    degree: Counter[str] = Counter()
    member_pairs: dict[tuple[str, str], dict[str, Any]] = {}

    for relation in relations:
        endpoints = relation_endpoints(relation)
        if endpoints is None:
            continue
        subject, predicate, obj = endpoints
        degree[subject] += 1
        degree[obj] += 1
        normalized_predicate = predicate.lower().replace("-", "_")
        if not any(marker in normalized_predicate for marker in AFFILIATION_MARKERS):
            continue
        if subject in people and obj in orgs:
            person_id, org_id = subject, obj
        elif obj in people and subject in orgs:
            person_id, org_id = obj, subject
        else:
            continue
        pair = member_pairs.setdefault(
            (person_id, org_id),
            {"predicates": set(), "relation_ids": [], "relations": []},
        )
        pair["predicates"].add(predicate)
        pair["relation_ids"].append(relation["_id"])
        pair["relations"].append(relation)

    people_by_org: dict[str, set[str]] = defaultdict(set)
    for person_id, org_id in member_pairs:
        people_by_org[org_id].add(person_id)

    inventory: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    emitted: set[str] = set()

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            raise RuntimeError(f"duplicate generated target ID: {document['_id']}")
        emitted.add(document["_id"])
        documents.append(document)

    ranked_orgs = sorted(
        orgs.items(),
        key=lambda item: (
            -base_priority(item[1], degree[item[0]], len(people_by_org[item[0]])),
            title(item[1]).lower(),
            item[0],
        ),
    )

    for rank, (org_id, org) in enumerate(ranked_orgs, 1):
        name = title(org)
        org_sources = source_ids(org)
        priority = base_priority(org, degree[org_id], len(people_by_org[org_id]))
        target_ids: list[str] = []
        for axis in ORG_AXES:
            axis_priority = round(max(0.5, priority - float(axis["penalty"])), 4)
            target_id = digest_id("org", org_id, axis["key"])
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{name}: {axis['label']}",
                    summary=axis["question"].format(name=name),
                    research_question=axis["question"].format(name=name),
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[org_id],
                    sources=org_sources,
                    priority=axis_priority,
                    when=when,
                    tags=["organization", org_kind(org), str(axis["key"])],
                    breadth=max(20, min(250, 20 + degree[org_id] + len(people_by_org[org_id]))),
                    depth=1,
                )
            )
        data = org.get("data") if isinstance(org.get("data"), dict) else {}
        inventory.append(
            {
                "rank": rank,
                "organization_id": org_id,
                "organization": name,
                "org_type": data.get("org_type", "organization"),
                "lead_kind": org_kind(org),
                "priority": priority,
                "relation_degree": degree[org_id],
                "known_people": len(people_by_org[org_id]),
                "source_count": len(org_sources),
                "organization_target_ids": target_ids,
            }
        )

    ranked_pairs = sorted(
        member_pairs.items(),
        key=lambda item: (
            -base_priority(orgs[item[0][1]], degree[item[0][1]], len(people_by_org[item[0][1]])),
            title(orgs[item[0][1]]).lower(),
            title(people[item[0][0]]).lower(),
            item[0],
        ),
    )
    for (person_id, org_id), pair in ranked_pairs:
        person, org = people[person_id], orgs[org_id]
        person_name, org_name = title(person), title(org)
        org_priority = base_priority(org, degree[org_id], len(people_by_org[org_id]))
        pair_sources = source_ids(person, org, *pair["relations"])
        predicates = sorted(str(value) for value in pair["predicates"])
        seed_ids = [person_id, org_id, *sorted(pair["relation_ids"])]
        for axis in MEMBER_AXES:
            priority = round(max(0.5, org_priority - float(axis["penalty"])), 4)
            target_id = digest_id("member", person_id, org_id, axis["key"])
            question = axis["question"].format(person=person_name, org=org_name)
            objectives = list(axis["objectives"])
            objectives.append(f"Preserve and verify known predicates: {', '.join(predicates)}")
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{person_name} / {org_name}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=objectives,
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=seed_ids,
                    sources=pair_sources,
                    priority=priority,
                    when=when,
                    tags=["person", "organization-member", str(axis["key"])],
                    breadth=30,
                    depth=2,
                )
            )

    return sorted(documents, key=lambda document: document["_id"]), inventory


def write(output: Path, documents: list[dict[str, Any]], inventory: list[dict[str, Any]], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    jsonl = "".join(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        for document in documents
    ).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(jsonl)
    inventory_bytes = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in inventory
    ).encode("utf-8")
    (output / "source/organization-leads.jsonl").write_bytes(inventory_bytes)
    counts = Counter(document["data"]["target_type"] for document in documents)
    manifest = {
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "organization_leads": len(inventory),
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(counts.items())),
        "total_targets": len(documents),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    top = inventory[:25]
    lines = [
        "# DNC organization and member target queue",
        "",
        "Deterministic target expansion over every DNC-dataset organization and every evidence-qualified person–organization affiliation relation.",
        "",
        f"- organization leads: {len(inventory):,}",
        f"- investigation targets: {len(documents):,}",
        "- five organization targets per organization",
        "- two verification and cross-tie targets per known person–organization pair",
        "",
        "## Highest-priority organization leads",
        "",
        "| Rank | Organization | Type | Priority | Known people | Relation degree |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for item in top:
        lines.append(
            f"| {item['rank']} | {item['organization'].replace('|', '/')} | {item['org_type']} | {item['priority']:.4f} | {item['known_people']} | {item['relation_degree']} |"
        )
    lines.extend(
        [
            "",
            "Targets are public-source-only. Historical roster relations remain historical unless current primary records confirm continuation. Ambiguous names remain source-scoped until resolved.",
            "",
            "```bash",
            "python3 scripts/generate_dnc_organization_targets.py",
            "python3 scripts/validate-for-merge.py --site",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    records = latest_records(Path.cwd(), ns.output)
    documents, inventory = build(records, ns.generated_at)
    if not inventory:
        raise RuntimeError("no DNC organization leads found")
    if not documents:
        raise RuntimeError("no DNC targets generated")
    write(ns.output, documents, inventory, ns.generated_at)
    print(
        json.dumps(
            {
                "organization_leads": len(inventory),
                "output": str(ns.output),
                "targets": len(documents),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
