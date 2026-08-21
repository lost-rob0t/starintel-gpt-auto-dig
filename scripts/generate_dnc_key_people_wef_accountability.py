#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from starintel_doc.store import iter_corpus
from starintel_doc.validation import validate_document

DATASET = "dnc"
OUTPUT = Path("digs/dnc/2026-08-01-key-people-wef-accountability")
GENERATED_AT = "2026-08-02T03:02:00Z"
PARTITIONS = 64
RUN_ID = "dnc-key-people-wef-accountability-2026-08-01"

CURRENT_DNC_LEADERS = (
    ("Ken Martin", "Chair"),
    ("Jane Kleeb", "ASDC President, Vice Chair"),
    ("Reyna Walters-Morgan", "Vice Chair for Civic Engagement and Voter Participation"),
    ("Malcolm Kenyatta", "Vice Chair"),
    ("Artie Blanco", "Vice Chair"),
    ("Shasti Conrad", "Vice Chair"),
    ("Jason Rae", "Secretary"),
    ("Virginia McGregor", "Treasurer"),
    ("Chris Korge", "National Finance Chair"),
    ("Joyce Beatty", "Associate Chair"),
    ("Stuart Appelbaum", "Associate Chair"),
)

OFFICIAL_DNC_LEADERSHIP_URL = "https://democrats.org/leadership/"
WEF_ORG_ID = "starintel:org:world-economic-forum"
DNC_ORG_ID = "starintel:org:dnc"

OUT_OF_SCOPE = [
    "private residential addresses",
    "private contact information",
    "credentials, access tokens, or authentication data",
    "non-public personal records",
    "unsupported criminal or corruption conclusions",
]

EXCLUDED_SOURCES = [
    "anonymous claims without underlying artifacts",
    "unsourced reposts",
    "people-search and data-broker profiles",
    "synthetic or AI-generated allegations",
]

WEF_PREFERRED_SOURCES = [
    "official World Economic Forum people profiles",
    "official Forum for Young Global Leaders class and alumni pages",
    "official Global Shapers Community hub and alumni pages",
    "official World Economic Forum meeting programmes, session pages, speaker lists, reports, press releases, videos, and contributor pages",
    "official employer, board, foundation, government, campaign, and party records corroborating the identity and role",
]

ACCOUNTABILITY_PREFERRED_SOURCES = [
    "official congressional, state, municipal, judicial, and executive-branch ethics records",
    "official FEC MUR, ADR, audit, administrative-fine, filing, and enforcement records",
    "official DOJ, inspector-general, attorney-general, state ethics, campaign-finance, and professional-discipline records",
    "court dockets, opinions, judgments, settlements, and charging documents",
    "official financial disclosures, lobbying disclosures, procurement records, nonprofit filings, labor-organization reports, and corporate filings",
    "established reporting that links directly to underlying records",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DNC people-first WEF and accountability queues")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--all-people", action="store_true", default=True)
    parser.add_argument("--accountability-min-score", type=float, default=0.62)
    parser.add_argument("--max-accountability-people", type=int, default=5000)
    return parser.parse_args()


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", value)


def stable_id(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return f"starintel:{prefix}:{hashlib.sha256(raw).hexdigest()}"


def person_name(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    for value in (
        data.get("full_name"),
        data.get("display_name"),
        data.get("name"),
        document.get("title"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def source_document(when: str) -> dict[str, Any]:
    document = {
        "_id": "starintel:source:dnc-current-leadership-2026-08-01",
        "data": {
            "accessed_at": when,
            "credibility": 1.0,
            "kind": "official_dnc_leadership_page",
            "publisher": "Democratic National Committee",
            "uri": OFFICIAL_DNC_LEADERSHIP_URL,
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
        "summary": "Official DNC leadership page used to seed the current national-officer people-first investigation queue.",
        "tags": ["dnc", "leadership", "official-source", "key-people"],
        "title": "DNC leadership page, accessed 2026-08-01",
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def person_document(name: str, role: str, when: str) -> dict[str, Any]:
    normalized = normalize_name(name).replace(" ", "-")
    document = {
        "_id": f"starintel:person:dnc-current-leader-{normalized}",
        "data": {
            "full_name": name,
            "name": name,
            "political_affiliations": ["Democratic National Committee"],
            "positions": [role],
            "public_roles": [f"DNC {role}"],
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "person",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": "starintel:source:dnc-current-leadership-2026-08-01"}],
        "status": "recorded",
        "summary": f"The official DNC leadership page lists {name} as {role}. Identity resolution against pre-existing records remains source-aware.",
        "tags": ["dnc", "current-leadership", "key-person"],
        "title": name,
        "verification": {"last_reviewed_at": when, "status": "official-dnc-role", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def role_relation(person_id: str, name: str, role: str, when: str) -> dict[str, Any]:
    document = {
        "_id": stable_id("relation", person_id, "holds_dnc_leadership_role", role),
        "data": {
            "confidence": 1.0,
            "directed": True,
            "object": DNC_ORG_ID,
            "predicate": "holds_dnc_leadership_role",
            "qualifiers": {"role": role, "observed_at": when},
            "subject": person_id,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": "starintel:source:dnc-current-leadership-2026-08-01"}],
        "status": "recorded",
        "summary": f"The official DNC leadership page lists {name} in the role {role}.",
        "tags": ["dnc", "leadership", "relation"],
        "title": f"{name} — DNC {role}",
        "verification": {"last_reviewed_at": when, "status": "official-dnc-role", "verified": True},
        "version": 1,
    }
    validate_document(document)
    return document


def target_document(person_id: str, name: str, target_type: str, priority: float, score: float, when: str) -> dict[str, Any]:
    if target_type == "wef_link_verification":
        question = (
            f"What verified direct or indirect links connect {name} to the World Economic Forum, Forum for Young Global Leaders, "
            "Global Shapers Community, Forum councils, centres, initiatives, partner organizations, contributors, speakers, participants, "
            "employees, fellows, or alumni? Distinguish a profile, membership, employment, event participation, quotation, incidental mention, "
            "institutional partnership, and unsupported name match."
        )
        objectives = [
            "Search exact and variant names across official WEF people, YGL, Global Shapers, contributor, meeting, session, video, report, press-release, and archive pages",
            "Resolve identity using role, employer, geography, dates, biographies, and linked institutions",
            "Create a relation only when an official source establishes the link type",
            "Record failed exact-name probes as search metadata, not as proof that no link exists",
            "Trace employer, board, foundation, campaign, government, and nonprofit paths that may create an indirect institutional link",
        ]
        preferred = WEF_PREFERRED_SOURCES
        queue = "dnc-key-people-wef"
        next_action = "Run exact-name and variant-name probes against official WEF/YGL/Global Shapers surfaces, then resolve every candidate match"
        required = ["source", "person", "org", "relation", "event", "claim"]
    elif target_type == "accountability_record":
        question = (
            f"What complete public accountability record exists for {name}, including ethics complaints, campaign-finance matters, audits, "
            "administrative fines, inspector-general findings, litigation, criminal or civil proceedings, lobbying and financial disclosures, "
            "conflicts of interest, procurement or nonprofit issues, settlements, dismissals, reversals, exonerating outcomes, and corrections?"
        )
        objectives = [
            "Search official federal, state, local, judicial, ethics, campaign-finance, inspector-general, professional-discipline, lobbying, financial-disclosure, procurement, nonprofit, labor, and corporate records",
            "Acquire the underlying complaint, response, investigative report, vote, order, judgment, settlement, dismissal, appeal, and closure documents",
            "Separate allegations, investigations, findings, admissions, settlements without admission, convictions, acquittals, dismissals, reversals, and no-action outcomes",
            "Map relevant organizations, officers, counsel, donors, vendors, employers, boards, contracts, and financial interests",
            "Do not use the word corruption as a finding unless a competent source actually makes and supports that finding",
        ]
        preferred = ACCOUNTABILITY_PREFERRED_SOURCES
        queue = "dnc-key-people-accountability"
        next_action = "Search official enforcement, ethics, court, filing, disclosure, lobbying, nonprofit, labor, procurement, and corporate sources; acquire every disposition"
        required = ["source", "person", "org", "relation", "claim", "event", "legal-case", "financial-observation"]
    else:
        question = (
            f"What complete public network surrounds {name}, including party and campaign roles, employers, boards, foundations, unions, nonprofits, "
            "companies, government offices, vendors, funders, consultants, counsel, lobbying relationships, and shared institutional affiliations?"
        )
        objectives = [
            "Enumerate current and historical public roles with dates and source provenance",
            "Resolve every organization and person without merging namesakes",
            "Map money, employment, governance, advisory, vendor, consulting, legal, lobbying, and campaign relationships",
            "Identify paths to WEF-linked people and organizations without treating graph proximity as membership or wrongdoing",
        ]
        preferred = [*WEF_PREFERRED_SOURCES, *ACCOUNTABILITY_PREFERRED_SOURCES]
        queue = "dnc-key-people-network"
        next_action = "Enumerate public roles and organizations, then recurse through members, officers, vendors, funders, counsel, and outside affiliations"
        required = ["source", "person", "org", "relation", "event", "financial-observation"]

    target_id = stable_id("investigation-target", RUN_ID, person_id, target_type)
    document = {
        "_id": target_id,
        "data": {
            "breadth": 120,
            "depth": 2,
            "excluded_sources": EXCLUDED_SOURCES,
            "in_scope": ["public official, institutional, filing, archive, court, and established-reporting records"],
            "max_depth": 8,
            "objectives": objectives,
            "out_of_scope": OUT_OF_SCOPE,
            "preferred_sources": preferred,
            "priority": round(priority, 4),
            "required_dtypes": required,
            "research_question": question,
            "scope_type": "public_source",
            "seed_ids": [person_id],
            "source_ids": [],
            "status": "queued",
            "target": f"{name}: {target_type.replace('_', ' ')}",
            "target_type": f"dnc_person_{target_type}",
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "investigation-target",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": question,
        "tags": ["dnc", "key-people", "investigation-target", target_type.replace("_", "-")],
        "title": f"{name}: {target_type.replace('_', ' ')}",
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-research-target", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 8,
            "next_action": next_action,
            "priority": round(priority, 4),
            "queue": queue,
            "recursion_depth": 2,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def collect_people(root: Path) -> tuple[dict[str, dict[str, Any]], Counter[str], dict[str, set[str]]]:
    people: dict[str, dict[str, Any]] = {}
    degree: Counter[str] = Counter()
    predicates: dict[str, set[str]] = defaultdict(set)
    for located in iter_corpus(root):
        document = located.document
        if str(document.get("dataset", "")).lower() != DATASET:
            continue
        dtype = document.get("dtype")
        if dtype == "person":
            name = person_name(document)
            if name:
                people.setdefault(str(document["_id"]), document)
        elif dtype == "relation":
            data = document.get("data") if isinstance(document.get("data"), dict) else {}
            predicate = str(data.get("predicate") or "")
            endpoints = [data.get("subject"), data.get("object")]
            for endpoint in endpoints:
                values = endpoint if isinstance(endpoint, list) else [endpoint]
                for value in values:
                    identifier = value.get("id") if isinstance(value, dict) else value
                    if isinstance(identifier, str):
                        degree[identifier] += 1
                        if predicate:
                            predicates[identifier].add(predicate)
    return people, degree, predicates


def score_person(document: dict[str, Any], degree: int, predicates: set[str]) -> float:
    name = person_name(document)
    normalized = normalize_name(name)
    current = {normalize_name(item[0]) for item in CURRENT_DNC_LEADERS}
    text = " ".join(strings(document)).lower()
    score = 0.0
    if normalized in current:
        score += 0.72
    if any(token in text for token in ("dnc", "democratic national committee", "asdc", "state democratic party")):
        score += 0.18
    if any(token in text for token in ("chair", "vice chair", "secretary", "treasurer", "finance chair", "associate chair", "governor", "senator", "representative", "mayor", "candidate")):
        score += 0.08
    if any("member" in predicate or "chair" in predicate or "employ" in predicate or "officer" in predicate for predicate in predicates):
        score += 0.06
    score += min(0.22, math.log1p(max(0, degree)) / 28.0)
    if "source-scoped" in text and degree <= 2 and normalized not in current:
        score -= 0.18
    return max(0.0, min(1.0, score))


def partition(document: dict[str, Any]) -> int:
    digest = hashlib.sha256(str(document["_id"]).encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % PARTITIONS


def write_packet(output: Path, root_docs: list[dict[str, Any]], generated_docs: list[dict[str, Any]], inventory: list[dict[str, Any]], when: str) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    root_payload = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in root_docs).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(root_payload)
    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    for document in generated_docs:
        buckets[partition(document)].append(document)
    partitions: list[dict[str, Any]] = []
    stream_hash = hashlib.sha256(root_payload)
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
    source_dir = output / "source"
    source_dir.mkdir()
    inventory_payload = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in inventory).encode("utf-8")
    (source_dir / "people-priority-inventory.jsonl").write_bytes(inventory_payload)
    all_documents = [*root_docs, *generated_docs]
    counts = Counter(document["dtype"] for document in all_documents)
    target_counts = Counter(document["data"]["target_type"] for document in generated_docs if document["dtype"] == "investigation-target")
    manifest = {
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_stream_sha256": stream_hash.hexdigest(),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory_payload).hexdigest(),
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(target_counts.items())),
        "total_documents": len(all_documents),
        "total_people_inventory": len(inventory),
        "total_targets": sum(target_counts.values()),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# DNC key people: WEF and accountability queue",
        "",
        "This packet creates a WEF-link verification target for every DNC person record and deeper accountability/network targets for current officers and high-priority people.",
        "",
        f"- people inventoried: {len(inventory):,}",
        f"- StarIntel documents: {len(all_documents):,}",
        f"- investigation targets: {sum(target_counts.values()):,}",
        "",
        "A failed WEF profile probe is search metadata, not proof of no relationship. Allegations, investigations, findings, settlements, dismissals, reversals, acquittals, exonerating outcomes, and corrections must remain separate.",
        "",
        "## Target families",
        "",
    ]
    for target_type, count in sorted(target_counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(["", "```bash", "python3 scripts/generate_dnc_key_people_wef_accountability.py --all-people", "python3 scripts/validate-for-merge.py --site", "```", ""])
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    root_docs: list[dict[str, Any]] = [source_document(args.generated_at)]
    current_by_name: dict[str, tuple[str, str]] = {}
    for name, role in CURRENT_DNC_LEADERS:
        person = person_document(name, role, args.generated_at)
        root_docs.append(person)
        root_docs.append(role_relation(person["_id"], name, role, args.generated_at))
        current_by_name[normalize_name(name)] = (person["_id"], role)

    people, degree, predicates = collect_people(args.root)
    for name, role in CURRENT_DNC_LEADERS:
        normalized = normalize_name(name)
        if not any(normalize_name(person_name(document)) == normalized for document in people.values()):
            person_id = current_by_name[normalized][0]
            people[person_id] = next(document for document in root_docs if document.get("_id") == person_id)

    scored: list[tuple[float, str, str, dict[str, Any]]] = []
    for person_id, document in people.items():
        name = person_name(document)
        score = score_person(document, degree[person_id], predicates[person_id])
        scored.append((score, name, person_id, document))
    scored.sort(key=lambda item: (-item[0], item[1].lower(), item[2]))

    accountability_ids = {
        person_id
        for score, _name, person_id, _document in scored[: args.max_accountability_people]
        if score >= args.accountability_min_score
    }
    accountability_ids.update(person_id for person_id, _role in current_by_name.values())

    generated_docs: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for rank, (score, name, person_id, document) in enumerate(scored, 1):
        current_role = ""
        current_entry = current_by_name.get(normalize_name(name))
        if current_entry:
            current_role = current_entry[1]
        generated_docs.append(target_document(person_id, name, "wef_link_verification", min(1.0, 0.55 + score * 0.45), score, args.generated_at))
        if person_id in accountability_ids:
            generated_docs.append(target_document(person_id, name, "accountability_record", min(1.0, 0.58 + score * 0.42), score, args.generated_at))
            generated_docs.append(target_document(person_id, name, "public_network", min(1.0, 0.56 + score * 0.40), score, args.generated_at))
        inventory.append(
            {
                "accountability_queued": person_id in accountability_ids,
                "current_dnc_role": current_role or None,
                "degree": degree[person_id],
                "name": name,
                "person_id": person_id,
                "predicates": sorted(predicates[person_id]),
                "priority_rank": rank,
                "priority_score": round(score, 6),
                "wef_verification_queued": True,
            }
        )

    manifest = write_packet(args.output, root_docs, generated_docs, inventory, args.generated_at)
    print(json.dumps({"documents": manifest["total_documents"], "people": manifest["total_people_inventory"], "targets": manifest["total_targets"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
