#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import iter_corpus
from starintel_doc.validation import validate_document

DATASET = "dnc"
GENERATED_AT = "2026-07-31T08:25:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-person-employment-targets")
RUN_ID = "dnc-person-employment-enumeration-2026-07-31"
PART_SIZE = 30_000_000
OUT_OF_SCOPE = [
    "private residential addresses",
    "private contact information",
    "credentials or access tokens",
    "non-public personal data",
    "unsupported criminal conclusions",
]
IN_SCOPE = [
    "official biographies, staff directories, and archived rosters",
    "Federal Election Commission records",
    "corporate and nonprofit filings",
    "public lobbying, ethics, procurement, and court records",
    "published reporting and archived official websites",
]
PREFERRED_SOURCES = [
    "Federal Election Commission",
    "official employer and organization records",
    "state corporate and charity registries",
    "IRS nonprofit filings",
    "public lobbying and ethics disclosures",
    "court dockets and opinions",
    "archived official websites",
]
EXCLUDED_SOURCES = [
    "people-search and data-broker profiles",
    "unsourced reposts",
    "anonymous claims without underlying artifacts",
]
PERSON_AXES = (
    {
        "key": "identity-resolution",
        "label": "identity resolution",
        "penalty": 0.00,
        "type": "person_identity_resolution",
        "question": "What public records establish the exact identity of {person}, distinguish namesakes, and connect all source-scoped records without false merges?",
        "objectives": [
            "Resolve full public name, aliases, jurisdiction, and stable public identifiers",
            "Separate namesakes and contradictory biographical records",
            "Link source-scoped FEC, roster, officer, vendor, and publication records",
        ],
        "next": "Resolve the person against primary-source biographies, filings, rosters, and stable public identifiers",
    },
    {
        "key": "employment-history",
        "label": "complete employment history",
        "penalty": 0.005,
        "type": "person_employment_history",
        "question": "What is the complete public employment, consulting, officer, board, campaign, government, and contractor history of {person}, with exact dates and evidence?",
        "objectives": [
            "Enumerate every public employer, title, department, client, and contractor role",
            "Separate direct employment from consulting, board, volunteer, and committee roles",
            "Capture start dates, end dates, promotions, overlaps, and gaps",
            "Reconcile filer-reported employer and occupation values against independent records",
        ],
        "next": "Build a dated employment timeline from official biographies, filings, archives, and employer records",
    },
    {
        "key": "fec-records",
        "label": "complete FEC record reconciliation",
        "penalty": 0.01,
        "type": "person_fec_record_reconciliation",
        "question": "Which FEC records may refer to {person}, and how do amendments, memo entries, refunds, conduits, employer fields, occupations, and committee roles reconcile?",
        "objectives": [
            "Collect every matching FEC contribution, refund, committee-role, filing, and transaction record",
            "Preserve amendments, memo entries, conduits, reattributions, and transaction identifiers",
            "Avoid treating source-scoped records as a unique donor total until identity resolution is complete",
        ],
        "next": "Enumerate matching FEC rows and reconcile transaction, amendment, memo, conduit, and identity fields",
    },
    {
        "key": "institutional-ties",
        "label": "institutional and political ties",
        "penalty": 0.015,
        "type": "person_institutional_ties",
        "question": "Which campaigns, party committees, PACs, public offices, agencies, nonprofits, companies, vendors, boards, and advocacy groups connect to {person}?",
        "objectives": [
            "Map all public organizational memberships, officer roles, boards, and advisory positions",
            "Trace campaign, government, lobbying, nonprofit, corporate, and vendor overlaps",
            "Record shared employers, committees, funders, clients, contractors, and principals",
        ],
        "next": "Search official organization, campaign, government, lobbying, corporate, nonprofit, and archival records",
    },
    {
        "key": "public-records",
        "label": "public filings and accountability records",
        "penalty": 0.025,
        "type": "person_public_record_profile",
        "question": "What public corporate, nonprofit, lobbying, ethics, procurement, litigation, and regulatory records identify roles or material relationships involving {person}?",
        "objectives": [
            "Search public corporate officer, nonprofit, lobbying, ethics, procurement, and court records",
            "Link each record to exact organizations, dates, roles, amounts, and jurisdictions",
            "Separate verified records, attributed claims, contradictions, and unresolved matches",
        ],
        "next": "Run the resolved identity through public filing, lobbying, ethics, procurement, and court systems",
    },
)
EMPLOYMENT_AXES = (
    {
        "key": "verify",
        "label": "employment verification",
        "penalty": 0.00,
        "type": "employment_record_verification",
        "question": "What primary records verify the reported role {role} for {person}{organization}, including title, dates, employment type, location, and whether the record is current?",
        "objectives": [
            "Verify employer legal identity and the person's exact title",
            "Determine start date, end date, employment type, department, and location",
            "Resolve discrepancies between FEC-reported fields, biographies, rosters, and employer records",
        ],
        "next": "Acquire primary employer, biography, roster, filing, and archival evidence for the reported role",
    },
    {
        "key": "employer-network",
        "label": "employer ownership and political network",
        "penalty": 0.015,
        "type": "employment_employer_network",
        "question": "Who owns, governs, funds, contracts with, and politically connects to the employer linked to {person}'s reported role {role}{organization}?",
        "objectives": [
            "Resolve employer legal entities, parents, subsidiaries, owners, and executives",
            "Trace campaign, PAC, lobbying, government, nonprofit, and vendor relationships",
            "Map other employees and officers connected to DNC records",
        ],
        "next": "Resolve the employer and enumerate ownership, leadership, contracts, filings, political ties, and shared personnel",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate exhaustive DNC person and employment targets")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    return parser.parse_args()


def title(record: dict[str, Any]) -> str:
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    for value in (record.get("title"), data.get("full_name"), data.get("name")):
        if isinstance(value, str) and value.strip():
            return re.sub(r"\s+", " ", value).strip()
    return str(record["_id"])


def latest_records() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for located in iter_corpus(ROOT):
        record = located.document
        if record.get("dataset") != DATASET or record.get("schema_version") != "0.9.0":
            continue
        doc_id = str(record.get("_id") or "")
        if not doc_id:
            continue
        current = records.get(doc_id)
        if current is None:
            records[doc_id] = record
            continue
        candidate = (int(record.get("version", 0)), str(record.get("date_updated", "")))
        previous = (int(current.get("version", 0)), str(current.get("date_updated", "")))
        if candidate > previous:
            records[doc_id] = record
    return records


def source_ids(*records: dict[str, Any], limit: int = 20) -> list[str]:
    values: list[str] = []
    for record in records:
        for source in record.get("sources", []):
            if not isinstance(source, dict):
                continue
            source_id = source.get("source_id")
            if isinstance(source_id, str) and source_id and source_id not in values:
                values.append(source_id)
                if len(values) >= limit:
                    return values
    return values


def relation_endpoints(record: dict[str, Any]) -> tuple[str, str, str] | None:
    if record.get("dtype") != "relation":
        return None
    data = record.get("data") if isinstance(record.get("data"), dict) else {}
    subject, predicate, obj = data.get("subject"), data.get("predicate"), data.get("object")
    if all(isinstance(value, str) and value for value in (subject, predicate, obj)):
        return subject, predicate, obj
    return None


def digest_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:investigation-target:dnc-{kind}-{digest}"


def person_priority(
    person: dict[str, Any],
    degree: int,
    employment_count: int,
    fec_count: int,
) -> float:
    data = person.get("data") if isinstance(person.get("data"), dict) else {}
    roles = " ".join(str(value) for value in data.get("public_roles", [])).lower()
    if any(marker in roles for marker in ("chair", "treasurer", "executive director", "officer")):
        base = 0.94
    elif "dnc member" in roles or "committee member" in roles:
        base = 0.90
    elif "contributor" in roles:
        base = 0.70
    else:
        base = 0.76
    bonus = min(0.06, math.log2(max(1, degree + 1)) * 0.008)
    bonus += min(0.05, math.log2(max(1, employment_count + 1)) * 0.01)
    bonus += min(0.04, math.log2(max(1, fec_count + 1)) * 0.006)
    return round(min(1.0, base + bonus), 4)


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
    depth: int,
    breadth: int,
) -> dict[str, Any]:
    doc = {
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
            "required_dtypes": [
                "source", "person", "org", "employment", "relation",
                "campaign-finance", "claim",
            ],
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
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id} for source_id in sources],
        "status": "recorded",
        "summary": question,
        "tags": ["dnc", "investigation-target", *tags],
        "title": target_title,
        "verification": {
            "last_reviewed_at": when,
            "status": "deterministically-derived-from-corpus",
            "verified": True,
        },
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-person-employment-enumeration",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(doc)
    return doc


def build(records: dict[str, dict[str, Any]], when: str):
    people = {doc_id: record for doc_id, record in records.items() if record.get("dtype") == "person"}
    orgs = {doc_id: record for doc_id, record in records.items() if record.get("dtype") == "org"}
    employments = {
        doc_id: record for doc_id, record in records.items() if record.get("dtype") == "employment"
    }
    degree: Counter[str] = Counter()
    employment_by_person: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fec_by_person: Counter[str] = Counter()

    for record in records.values():
        endpoints = relation_endpoints(record)
        if endpoints:
            subject, _, obj = endpoints
            degree[subject] += 1
            degree[obj] += 1
        if record.get("dtype") == "campaign-finance":
            data = record.get("data") if isinstance(record.get("data"), dict) else {}
            for key in ("donor_id", "entity_id"):
                person_id = data.get(key)
                if person_id in people:
                    fec_by_person[person_id] += 1
                    break

    for employment in employments.values():
        data = employment.get("data") if isinstance(employment.get("data"), dict) else {}
        person_id = data.get("person_id")
        if person_id in people:
            employment_by_person[person_id].append(employment)

    documents: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    emitted: set[str] = set()

    def emit(doc: dict[str, Any]) -> None:
        if doc["_id"] in emitted:
            raise RuntimeError(f"duplicate target ID: {doc['_id']}")
        emitted.add(doc["_id"])
        documents.append(doc)

    ranked_people = sorted(
        people.items(),
        key=lambda item: (
            -person_priority(
                item[1], degree[item[0]], len(employment_by_person[item[0]]), fec_by_person[item[0]]
            ),
            title(item[1]).lower(),
            item[0],
        ),
    )
    for rank, (person_id, person) in enumerate(ranked_people, 1):
        name = title(person)
        priority = person_priority(
            person, degree[person_id], len(employment_by_person[person_id]), fec_by_person[person_id]
        )
        sources = source_ids(person, *employment_by_person[person_id])
        target_ids: list[str] = []
        for axis in PERSON_AXES:
            target_id = digest_id("person", person_id, axis["key"])
            target_ids.append(target_id)
            axis_priority = round(max(0.5, priority - float(axis["penalty"])), 4)
            question = axis["question"].format(person=name)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{name}: {axis['label']}",
                    question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["type"]),
                    seed_ids=[person_id],
                    sources=sources,
                    priority=axis_priority,
                    when=when,
                    tags=["person", str(axis["key"])],
                    depth=1,
                    breadth=max(20, min(200, 20 + degree[person_id] + fec_by_person[person_id])),
                )
            )
        inventory.append(
            {
                "rank": rank,
                "person_id": person_id,
                "person": name,
                "priority": priority,
                "relation_degree": degree[person_id],
                "employment_records": len(employment_by_person[person_id]),
                "fec_records": fec_by_person[person_id],
                "source_count": len(sources),
                "target_ids": target_ids,
            }
        )

    for employment_id, employment in sorted(employments.items()):
        data = employment.get("data") if isinstance(employment.get("data"), dict) else {}
        person_id = data.get("person_id")
        if person_id not in people:
            continue
        org_id = data.get("organization_id") if data.get("organization_id") in orgs else ""
        person_name = title(people[person_id])
        org_name = title(orgs[org_id]) if org_id else ""
        role = str(data.get("title") or employment.get("title") or "reported role")
        person_base = person_priority(
            people[person_id], degree[person_id], len(employment_by_person[person_id]), fec_by_person[person_id]
        )
        sources = source_ids(employment, people[person_id], *( [orgs[org_id]] if org_id else [] ))
        organization_phrase = f" at {org_name}" if org_name else ""
        for axis in EMPLOYMENT_AXES:
            if axis["key"] == "employer-network" and not org_id:
                continue
            target_id = digest_id("employment", employment_id, axis["key"])
            question = axis["question"].format(
                person=person_name,
                role=role,
                organization=organization_phrase,
            )
            seed_ids = [person_id, employment_id]
            if org_id:
                seed_ids.append(org_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{person_name} / {role}{organization_phrase}: {axis['label']}",
                    question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["type"]),
                    seed_ids=seed_ids,
                    sources=sources,
                    priority=round(max(0.5, person_base - float(axis["penalty"])), 4),
                    when=when,
                    tags=["employment", str(axis["key"])],
                    depth=2,
                    breadth=35,
                )
            )

    return sorted(documents, key=lambda doc: doc["_id"]), inventory


def write_parts(base_path: Path, payload: bytes) -> list[str]:
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


def write(output: Path, documents: list[dict[str, Any]], inventory: list[dict[str, Any]], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    jsonl = "".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in documents
    ).encode("utf-8")
    document_parts = write_parts(output / "starintel-documents.jsonl.gz.b64", jsonl)
    inventory_bytes = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in inventory
    ).encode("utf-8")
    inventory_parts = write_parts(
        output / "source" / "person-priority-inventory.jsonl.gz.b64", inventory_bytes
    )
    counts = Counter(doc["data"]["target_type"] for doc in documents)
    manifest = {
        "dataset": DATASET,
        "document_part_count": len(document_parts),
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "employment_records": counts.get("employment_record_verification", 0),
        "generated_at": when,
        "inventory_part_count": len(inventory_parts),
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "people": len(inventory),
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(counts.items())),
        "total_targets": len(documents),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# DNC person and employment target queue",
        "",
        f"- people: {len(inventory):,}",
        f"- investigation targets: {len(documents):,}",
        "- five target lanes per person",
        "- one verification target per employment/status record",
        "- one employer-network target per employment record with an organization",
        "",
        "## Highest-priority people",
        "",
        "| Rank | Person | Priority | Employments | FEC records | Degree |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for item in inventory[:50]:
        lines.append(
            f"| {item['rank']} | {item['person'].replace('|', '/')} | {item['priority']:.4f} | {item['employment_records']} | {item['fec_records']} | {item['relation_degree']} |"
        )
    lines.extend(
        [
            "",
            "FEC contributor identities and employer values remain source-scoped until independently resolved. Targets exclude private addresses, private contact details, and data-broker records.",
            "",
            "```bash",
            "python3 scripts/generate_dnc_person_employment_targets.py",
            "python3 scripts/validate-for-merge.py --site",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    records = latest_records()
    documents, inventory = build(records, ns.generated_at)
    if not inventory:
        raise RuntimeError("no DNC people found")
    if not documents:
        raise RuntimeError("no person or employment targets generated")
    write(ns.output, documents, inventory, ns.generated_at)
    print(
        json.dumps(
            {"people": len(inventory), "targets": len(documents), "output": str(ns.output)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
