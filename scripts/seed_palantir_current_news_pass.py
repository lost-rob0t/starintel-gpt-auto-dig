#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import compact
from starintel_doc.validation import validate_document


SCHEMA = "0.9.0"
DATASET = "wef"
STAMP = "2026-08-17T22:40:00Z"
RUN_ID = "hourly-news-palantir-wef-2026-08-17"
OUTPUT = ROOT / "digs/wef/2026-08-17-palantir-current-news-pass"
PACKET = OUTPUT / "starintel-documents.jsonl"
PALANTIR = "starintel:org:palantir-technologies-inc"
HQ_PASS = "starintel:research-pass:palantir-principal-office-enrichment-2026-08-17"
ENTITY_TARGET = "starintel:investigation-target:palantir-org-id-resolution"
COUNCIL_TARGET = "starintel:investigation-target:wef-data-governance-council-member-carryover-2020-2026"
ANALYSIS = "starintel:analysis:palantir-wef-current-news-materiality-2026-08-17"
RESEARCH_PASS = "starintel:research-pass:palantir-wef-current-news-materiality-2026-08-17"

SEARCH_METHOD = (
    "Current web/news search performed only after the HQ/location phase had passed its dedicated canonical "
    "Nim build and `bin/validate-for-merge --site` gate. Previous successful WEF recursion activity was visible "
    "around 2026-08-17T22:22:00Z; the news overlap window was widened to 2026-08-17T21:45:00Z through "
    "2026-08-17T22:40:00Z to catch late indexing. Twelve bounded search-engine queries were executed in three "
    "passes: (1) `Palantir latest news August 17 2026`; `World Economic Forum Palantir August 17 2026 news`; "
    "`Katherine Hsiao Palantir August 17 2026`; `Palantir WEF data equity latest August 2026`; (2) `Palantir "
    "August 17 2026 site:palantir.com OR site:investors.palantir.com`; `Palantir Aug 17 2026 news`; `World "
    "Economic Forum August 17 2026 Palantir`; `Katherine Hsiao August 17 2026`; and (3) 24-hour recency checks "
    "for `Palantir news`, `World Economic Forum Palantir`, `Katherine Hsiao Palantir`, and `WEF data equity "
    "Palantir`. Source/result limits: only the search engine's returned top result set was reviewed for each query; "
    "no pagination or exhaustive web crawl was attempted. Publication date and underlying event date were "
    "checked where exposed. No result published or materially updated inside the overlap window passed the "
    "new-event/new-evidence/material-change/correction/counterevidence/new-relation gate, so zero news records "
    "were ingested. The nearest relevant indexed coverage was from prior days and was therefore excluded as "
    "pre-window rather than duplicated."
)


def base(
    doc_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, Any],
    *,
    related_ids: list[str],
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA,
        "version": 1,
        "date_added": STAMP,
        "date_updated": STAMP,
        "title": title,
        "summary": summary,
        "sources": [],
        "evidence": [],
        "data": data,
        "related_ids": related_ids,
        "verification": {
            "status": "search-complete-no-material-news",
            "verified": True,
            "verified_by": ["current web/news search"],
            "verified_at": STAMP,
            "last_reviewed_at": STAMP,
            "methods": ["bounded current-news search", "materiality gate", "publication-date review"],
        },
        "handling": {"visibility": "public", "sensitive": False, "pii": False},
        "provenance": {
            "collector": "OpenAI GPT-5.6 Sol",
            "collector_type": "research-agent",
            "method": "post-HQ current-news materiality pass",
            "pipeline": "starintel-auto-dig",
            "run_id": RUN_ID,
        },
    }


def build_documents() -> list[dict[str, Any]]:
    analysis = base(
        ANALYSIS,
        "analysis",
        "Palantir / WEF current-news materiality check — 2026-08-17",
        "No current-news result in the post-HQ overlap window passed the ingestion materiality gate; no filler article records were created.",
        {
            "question": "Did current news published or materially updated since the previous successful WEF run add meaningful evidence to the selected Palantir/WEF corpus?",
            "method": SEARCH_METHOD,
            "scope": "Existing Palantir and WEF datasets/topics, Palantir Technologies Inc., Katherine Hsiao, the WEF Data Equity thread, and active related investigation targets.",
            "findings": [
                "No result published or materially updated inside the 2026-08-17T21:45:00Z through 2026-08-17T22:40:00Z overlap window passed the materiality gate.",
                "Relevant indexed Palantir coverage returned by the searches was published before the overlap window and was not re-ingested.",
                "No new current-news source established an HQ/location change, correction, counterevidence, supported relation, or significant update to the active WEF/Palantir targets during the window.",
            ],
            "conclusions": [
                "Zero canonical news records should be ingested for this hourly run.",
                "The absence of qualifying results is a bounded search result, not evidence that no relevant event occurred anywhere on the web.",
            ],
            "recommendations": ["Carry the existing recursive targets forward rather than creating a filler news target."],
            "counterarguments": ["Older Palantir coverage remains potentially useful corpus evidence, but it falls outside this run's incremental news window and should not be duplicated as hourly news."],
            "limitations": [
                "Search was limited to the engine's top returned result set for twelve queries with no pagination.",
                "Late-indexed reporting may appear in a future run and should be caught by the configured overlap window.",
            ],
            "unresolved": [
                "Canonical Palantir organization ID resolution remains open.",
                "The WEF data-governance council-member carryover root remains queued for recursive research.",
            ],
            "confidence": 0.98,
        },
        related_ids=[PALANTIR, HQ_PASS, ENTITY_TARGET, COUNCIL_TARGET],
    )

    research_pass = base(
        RESEARCH_PASS,
        "research-pass",
        "Hourly current-news pass — Palantir / WEF — 2026-08-17",
        "Post-HQ current-news search found no material in-window evidence to ingest; search scope, overlap window, queries, source limits, and zero-ingestion decision are preserved.",
        {
            "research_question": "What current news since the previous successful WEF run materially updates existing Palantir/WEF records or targets?",
            "method": SEARCH_METHOD,
            "classification_rules": [
                "Run news search only after the HQ/location slice has completed and passed its canonical merge/site gate.",
                "Require a new event, new evidence, material organizational change, HQ/location change, correction, counterevidence, supported relation, or significant target update before ingestion.",
                "Do not ingest pre-window coverage merely because it ranks highly in current search results.",
                "Keep what a source reports distinct from independently established facts.",
                "Create no filler records when zero results pass materiality.",
            ],
            "finding_ids": [ANALYSIS],
            "findings": [
                {
                    "finding": "No search result published or materially updated inside the overlap window passed the news materiality gate; zero news records were ingested.",
                    "confidence": 0.98,
                }
            ],
            "supporting_record_ids": [PALANTIR, HQ_PASS, ANALYSIS],
            "counterevidence_ids": [],
            "unresolved_target_ids": [ENTITY_TARGET, COUNCIL_TARGET],
            "source_ids": [],
            "agent_identity": "OpenAI GPT-5.6 Sol",
            "narrative_role": "hourly post-HQ current-news materiality pass",
            "started_at": "2026-08-17T22:36:00Z",
            "completed_at": STAMP,
            "iteration": 1,
        },
        related_ids=[PALANTIR, HQ_PASS, ENTITY_TARGET, COUNCIL_TARGET, ANALYSIS],
    )

    docs = [analysis, research_pass]
    seen: set[str] = set()
    for document in docs:
        validate_document(document)
        if document["_id"] in seen:
            raise ValueError(f"duplicate generated id: {document['_id']}")
        seen.add(document["_id"])
    return docs


def main() -> int:
    docs = build_documents()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PACKET.write_text("".join(compact(doc) + "\n" for doc in docs), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/starintel.py"), "import", str(PACKET), "--root", str(ROOT)],
        cwd=ROOT,
        check=True,
    )
    print(json.dumps({
        "packet": str(PACKET.relative_to(ROOT)),
        "documents": len(docs),
        "news_records_ingested": 0,
        "search_queries": 12,
        "overlap_window": ["2026-08-17T21:45:00Z", "2026-08-17T22:40:00Z"],
        "ids": [doc["_id"] for doc in docs],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
