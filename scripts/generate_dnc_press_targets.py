#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
GENERATED_AT = "2026-07-31T22:48:00Z"
INPUT = Path("digs/dnc/2026-07-31-official-press-archive/source/archive-records.jsonl")
OUTPUT = Path("digs/dnc/2026-07-31-official-press-targets")
RUN_ID = "dnc-official-press-recursive-targets-2026-07-31"
BATCH_SIZE = 100
PARTITIONS = 32
MAX_RECORDS = 20_000

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
    "official DNC press-release pages and archived snapshots",
    "Federal Election Commission and state campaign-finance records",
    "official organization, campaign, government, corporate, and nonprofit records",
    "court dockets, opinions, legislative records, and agency publications",
    "established reporting and direct counter-sources",
]

ARTICLE_AXES = (
    {
        "key": "full-text-provenance",
        "label": "full text, revisions, links, and provenance",
        "target_type": "press_release_full_text_provenance",
        "penalty": 0.00,
        "question": "What is the complete official text, revision history, quoted material, outbound-link graph, embedded media, authorship signal, and archival provenance of the DNC press release {title}?",
        "objectives": [
            "Capture the official article text without navigation, donation, or template boilerplate",
            "Preserve publication and modification timestamps, canonical URL, title, headings, quotations, links, media captions, and content hash",
            "Acquire archived snapshots and record material additions, deletions, corrections, redirects, or URL changes",
            "Create source records for every cited official document, filing, speech, report, article, video, or social post",
        ],
        "next": "Fetch the canonical page and available archives, extract the article body and outbound evidence graph, and hash every captured version",
    },
    {
        "key": "entities-claims-crosslinks",
        "label": "people, organizations, claims, events, and graph cross-links",
        "target_type": "press_release_entities_claims_crosslinks",
        "penalty": 0.01,
        "question": "Which people, organizations, campaigns, committees, public offices, agencies, companies, vendors, places, events, policies, and factual claims appear in {title}, and how do they connect to the existing DNC graph?",
        "objectives": [
            "Extract every named person, organization, office, agency, committee, company, vendor, place, event, policy, program, and publication",
            "Resolve exact entities without merging namesakes or similarly named organizations",
            "Represent each material factual assertion as an attributed claim with quotation context and source location",
            "Link entities and claims to FEC records, DNC leadership, state parties, vendors, litigation, government records, and independent reporting",
            "Record contradictions, corrections, missing support, rhetorical characterization, and unresolved references separately from verified facts",
        ],
        "next": "Run structured entity, claim, citation, and event extraction, then resolve each result against primary records and the existing StarIntel corpus",
    },
)

BATCH_AXES = (
    {
        "key": "person-role-resolution",
        "label": "resolve every named person and public role",
        "target_type": "press_batch_person_role_resolution",
        "penalty": 0.00,
        "question": "Across press-release batch {batch}, who is named, quoted, endorsed, criticized, appointed, elected, employed, or otherwise assigned a role, and which primary records establish each identity and dated role?",
        "objectives": [
            "Enumerate every person mention and quoted speaker",
            "Resolve namesakes using offices, organizations, dates, jurisdictions, and source context",
            "Map current and historical campaign, party, government, corporate, nonprofit, union, board, and vendor roles",
            "Create dated relations and contradiction records for disputed or changing roles",
        ],
        "next": "Extract all person mentions in the batch and verify each identity and role against official biographies, filings, rosters, and archives",
    },
    {
        "key": "organization-committee-vendor-resolution",
        "label": "resolve every organization, committee, company, and vendor",
        "target_type": "press_batch_organization_resolution",
        "penalty": 0.005,
        "question": "Across press-release batch {batch}, which organizations, campaigns, committees, PACs, agencies, companies, vendors, unions, nonprofits, media outlets, and coalitions are named or implied, and what are their complete public structures and cross-links?",
        "objectives": [
            "Enumerate every named organization and source-scoped unresolved organization mention",
            "Resolve legal entities, aliases, former names, affiliates, parents, subsidiaries, sponsors, and committees",
            "Map leaders, members, staff, contractors, funders, clients, grants, transactions, and shared infrastructure",
            "Create recursive organization-membership and cross-tie targets for newly discovered entities",
        ],
        "next": "Extract all organization mentions and resolve each through official registrations, filings, websites, archives, and the existing graph",
    },
    {
        "key": "claim-evidence-audit",
        "label": "audit factual claims, citations, quotations, and counter-evidence",
        "target_type": "press_batch_claim_evidence_audit",
        "penalty": 0.01,
        "question": "Across press-release batch {batch}, what factual claims, numerical assertions, quotations, causal statements, legal characterizations, and predictions are made, and what primary evidence or credible counter-evidence supports, qualifies, or contradicts each one?",
        "objectives": [
            "Extract each material claim with exact article, paragraph, speaker, and quotation context",
            "Locate underlying laws, executive actions, budgets, votes, filings, court records, datasets, reports, speeches, and transcripts",
            "Separate official DNC assertions, quoted third-party assertions, inference, opinion, rhetoric, and independently verified fact",
            "Record support, contradiction, correction, uncertainty, and unresolved evidence gaps without collapsing competing claims",
        ],
        "next": "Build an attributed claim ledger for the batch and verify each material assertion against primary records and credible counter-sources",
    },
    {
        "key": "fec-campaign-government-links",
        "label": "link campaign-finance, elections, government, and litigation records",
        "target_type": "press_batch_fec_government_crosslinks",
        "penalty": 0.005,
        "question": "Which FEC committees, candidates, elections, expenditures, donors, vendors, public offices, agencies, legislation, executive actions, court cases, and government records connect to press-release batch {batch}?",
        "objectives": [
            "Resolve every candidate and committee through FEC and state campaign-finance identifiers",
            "Link elections, primaries, nominations, endorsements, spending, transfers, and vendors to raw filing records",
            "Resolve public offices, agencies, bills, rules, executive actions, votes, dockets, judgments, and official statistics",
            "Create evidence-qualified event and relation records with exact dates and jurisdictions",
        ],
        "next": "Join extracted entities and events to FEC, state election, legislative, executive, agency, and court records",
    },
    {
        "key": "narrative-temporal-network",
        "label": "map narrative, issue, geography, repetition, and timing patterns",
        "target_type": "press_batch_narrative_temporal_network",
        "penalty": 0.02,
        "question": "What recurring narratives, issue frames, targets, slogans, geographic campaigns, release sequences, cross-posts, and event-timing patterns appear in press-release batch {batch}?",
        "objectives": [
            "Cluster releases by issue, entity, geography, election, campaign, event, and repeated language",
            "Identify press-release series, coordinated state amplification, repeated quotations, template reuse, and linked rapid-response events",
            "Map publication timing against votes, filings, speeches, court actions, news events, fundraising, and campaign milestones",
            "Separate measured textual similarity and timing facts from hypotheses about coordination or intent",
        ],
        "next": "Compute transparent similarity, entity, geography, and event-time features and create source-backed clusters without inferring intent from correlation alone",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate recursive targets for the official DNC press archive")
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    return parser.parse_args()


def sha_id(*parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"starintel:investigation-target:dnc-press-{digest}"


def press_source_id(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"starintel:source:dnc-press-release-{digest[:32]}"


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"press archive inventory is missing: {path}")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise RuntimeError(f"press inventory line {line_number} is not an object")
        required = {"archive_page", "link", "published_date", "slug", "title"}
        if not required <= record.keys():
            raise RuntimeError(f"press inventory line {line_number} lacks fields: {sorted(required - record.keys())}")
        url = str(record["link"])
        if url in seen:
            raise RuntimeError(f"duplicate press-release URL: {url}")
        seen.add(url)
        date.fromisoformat(str(record["published_date"]))
        records.append(record)
        if len(records) > MAX_RECORDS:
            raise RuntimeError("press inventory exceeds safety cap")
    if not records:
        raise RuntimeError("press inventory is empty")
    return sorted(records, key=lambda item: (str(item["published_date"]), str(item["link"])))


def priority_for(record: dict[str, Any]) -> float:
    year = int(str(record["published_date"])[:4])
    if year >= 2026:
        return 0.97
    if year >= 2024:
        return 0.93
    if year >= 2020:
        return 0.89
    if year >= 2016:
        return 0.85
    return 0.81


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
                "official press-release pages and public archives",
                "official campaign, party, government, court, corporate, nonprofit, and union records",
                "public campaign-finance, lobbying, legislative, agency, and election records",
                "established reporting and direct counter-sources",
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
        "sources": [{"source_id": source_id} for source_id in source_ids[:20]],
        "status": "recorded",
        "summary": summary,
        "tags": ["dnc", "press-release", "investigation-target", *tags],
        "title": target_title,
        "verification": {"last_reviewed_at": when, "status": "deterministically-derived-from-official-archive", "verified": True},
        "version": 1,
        "workflow": {
            "max_depth": 7,
            "next_action": next_action,
            "priority": priority,
            "queue": "dnc-official-press-archive",
            "recursion_depth": depth,
            "research_status": "queued",
            "root_target_id": target_id,
            "run_id": RUN_ID,
        },
    }
    validate_document(document)
    return document


def build(records: list[dict[str, Any]], batch_size: int, when: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if batch_size < 25 or batch_size > 500:
        raise RuntimeError("batch-size must be between 25 and 500")
    documents: list[dict[str, Any]] = []
    emitted: set[str] = set()
    batches: list[dict[str, Any]] = []

    def emit(document: dict[str, Any]) -> None:
        if document["_id"] in emitted:
            raise RuntimeError(f"duplicate generated target ID: {document['_id']}")
        emitted.add(document["_id"])
        documents.append(document)

    for record in records:
        source_id = press_source_id(str(record["link"]))
        base_priority = priority_for(record)
        for axis in ARTICLE_AXES:
            question = axis["question"].format(title=record["title"])
            target_id = sha_id("article", str(record["link"]), str(axis["key"]))
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"{record['title']}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[DNC_ID, source_id],
                    source_ids=[source_id],
                    priority=round(base_priority - float(axis["penalty"]), 4),
                    when=when,
                    tags=["article", str(record["published_date"])[:4], str(axis["key"])],
                    depth=1,
                    breadth=80,
                )
            )

    total_batches = math.ceil(len(records) / batch_size)
    for batch_index, start in enumerate(range(0, len(records), batch_size), 1):
        batch_records = records[start : start + batch_size]
        source_ids = [press_source_id(str(record["link"])) for record in batch_records]
        date_start = str(batch_records[0]["published_date"])
        date_end = str(batch_records[-1]["published_date"])
        batch_label = f"{batch_index:04d}/{total_batches:04d} ({date_start} through {date_end})"
        priority = max(priority_for(record) for record in batch_records)
        target_ids: list[str] = []
        for axis in BATCH_AXES:
            target_id = sha_id("batch", str(batch_index), date_start, date_end, str(axis["key"]))
            question = axis["question"].format(batch=batch_label)
            target_ids.append(target_id)
            emit(
                target_document(
                    target_id=target_id,
                    target_title=f"DNC press batch {batch_label}: {axis['label']}",
                    summary=question,
                    research_question=question,
                    objectives=list(axis["objectives"]),
                    next_action=str(axis["next"]),
                    target_type=str(axis["target_type"]),
                    seed_ids=[DNC_ID, *source_ids],
                    source_ids=source_ids,
                    priority=round(priority - float(axis["penalty"]), 4),
                    when=when,
                    tags=["batch", f"batch-{batch_index:04d}", str(axis["key"])],
                    depth=2,
                    breadth=min(500, len(batch_records) * 5),
                )
            )
        batches.append(
            {
                "batch": batch_index,
                "date_end": date_end,
                "date_start": date_start,
                "first_url": batch_records[0]["link"],
                "last_url": batch_records[-1]["link"],
                "records": len(batch_records),
                "source_ids": source_ids,
                "target_ids": target_ids,
            }
        )
    return documents, batches


def partition(document: dict[str, Any]) -> int:
    digest = hashlib.sha256(document["_id"].encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % PARTITIONS


def write(output: Path, documents: list[dict[str, Any]], batches: list[dict[str, Any]], records: list[dict[str, Any]], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    buckets: list[list[dict[str, Any]]] = [[] for _ in range(PARTITIONS)]
    for document in documents:
        buckets[partition(document)].append(document)
    stream_hash = hashlib.sha256()
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

    batch_bytes = "".join(
        json.dumps(batch, ensure_ascii=False, separators=(",", ":")) + "\n"
        for batch in batches
    ).encode("utf-8")
    (output / "source/batches.jsonl").write_bytes(batch_bytes)
    counts = Counter(document["data"]["target_type"] for document in documents)
    manifest = {
        "batch_size": BATCH_SIZE,
        "batches": len(batches),
        "dataset": DATASET,
        "document_stream_sha256": stream_hash.hexdigest(),
        "generated_at": when,
        "partition_count": PARTITIONS,
        "partitions": partitions,
        "press_releases": len(records),
        "schema_version": "0.9.0",
        "target_counts": dict(sorted(counts.items())),
        "total_targets": len(documents),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# DNC official press archive target queue",
        "",
        "Deterministic recursive targets over every press-release record in the official DNC archive.",
        "",
        f"- press releases: {len(records):,}",
        f"- per-article targets: {len(records) * len(ARTICLE_AXES):,}",
        f"- batches: {len(batches):,}",
        f"- batch-level targets: {len(batches) * len(BATCH_AXES):,}",
        f"- total investigation targets: {len(documents):,}",
        f"- GitHub-safe partitions: {PARTITIONS}",
        "",
        "Article targets acquire complete official text and provenance, then extract and resolve entities, claims, events, and graph cross-links. Batch targets force exhaustive person, organization, evidence, campaign-finance, government, litigation, and transparent narrative/timing passes. Attributed DNC claims remain attributed until independently verified.",
        "",
        "## Target families",
        "",
    ]
    for target_type, count in sorted(counts.items()):
        lines.append(f"- `{target_type}`: {count:,}")
    lines.extend(
        [
            "",
            "```bash",
            "python3 scripts/generate_dnc_press_targets.py",
            "python3 scripts/validate-for-merge.py --site",
            "```",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ns = parse_args()
    records = read_records(ns.input)
    documents, batches = build(records, ns.batch_size, ns.generated_at)
    write(ns.output, documents, batches, records, ns.generated_at)
    print(
        json.dumps(
            {
                "batches": len(batches),
                "output": str(ns.output),
                "press_releases": len(records),
                "targets": len(documents),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
