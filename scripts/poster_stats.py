#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from starintel_site.model import discover

REVIEWED_TOKENS = (
    "reviewed", "verified", "validated", "confirmed", "corroborated",
    "source-backed", "source backed", "resolved",
)
UNREVIEWED_TOKENS = (
    "unreviewed", "unverified", "pending", "draft", "queued", "unknown",
    "unclassified", "needs-review", "needs review", "not-reviewed",
    "not reviewed", "proposed",
)


def latest_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for doc in documents:
        old = by_id.get(doc["_id"])
        if old is None or str(doc["date_updated"]) >= str(old["date_updated"]):
            by_id[doc["_id"]] = doc
    return sorted(by_id.values(), key=lambda doc: doc["_id"])


def review_state(doc: dict[str, Any]) -> str:
    verification = doc.get("verification") or {}
    workflow = doc.get("workflow") or {}
    raw = (
        verification.get("status")
        or workflow.get("review_status")
        or workflow.get("status")
        or doc.get("status")
        or ""
    )
    status = str(raw).strip().lower().replace("_", "-")
    if any(token in status for token in UNREVIEWED_TOKENS):
        return "unreviewed"
    if any(token in status for token in REVIEWED_TOKENS):
        return "reviewed"
    return "unreviewed"


def endpoint_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return [value["id"]]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(endpoint_ids(item))
        return out
    return []


def is_bulk_campaign(doc: dict[str, Any]) -> bool:
    dataset = str(doc.get("dataset") or "").strip().lower().replace("_", "-")
    return dataset == "dnc" or dataset.startswith("dnc-") or dataset.startswith("dataset-dnc")


def label(doc_id: str, by_id: dict[str, dict[str, Any]]) -> str:
    doc = by_id.get(doc_id) or {}
    data = doc.get("data") or {}
    value = data.get("display_name") or data.get("full_name") or data.get("name") or doc.get("title") or doc.get("name")
    if value and not str(value).startswith("starintel:"):
        return str(value)
    tail = doc_id.rsplit(":", 1)[-1].replace("-", " ").replace("_", " ")
    return " ".join(part.capitalize() for part in tail.split())


def source_key(source: Any) -> str | None:
    if isinstance(source, str):
        return source.strip() or None
    if not isinstance(source, dict):
        return None
    for key in ("url", "uri", "href"):
        value = source.get(key)
        if value:
            return str(value).strip()
    name = source.get("name") or source.get("title")
    return str(name).strip() if name else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("digs"))
    parser.add_argument("--output", type=Path, default=Path("poster-stats.json"))
    args = parser.parse_args()

    packets = discover(args.input_root)
    docs = latest_documents([doc for packet in packets for doc in packet.documents])
    docs = [doc for doc in docs if not is_bulk_campaign(doc)]

    by_id = {str(doc.get("_id")): doc for doc in docs if doc.get("_id")}
    people = {doc_id for doc_id, doc in by_id.items() if doc.get("dtype") == "person"}

    dtype_counts = Counter(str(doc.get("dtype") or "unknown") for doc in docs if doc.get("dtype") != "relation")
    predicate_counts: Counter[str] = Counter()
    all_degree: Counter[str] = Counter()
    reviewed_degree: Counter[str] = Counter()
    counterpart_counts: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_by_person: dict[str, Counter[str]] = defaultdict(Counter)
    reviewed_relation_edges = 0
    all_relation_edges = 0

    for doc in docs:
        if doc.get("dtype") != "relation":
            continue
        data = doc.get("data") or {}
        predicate = str(data.get("predicate") or "related").replace("_", " ")
        subjects = endpoint_ids(data.get("subject"))
        objects = endpoint_ids(data.get("object"))
        relation_reviewed = review_state(doc) == "reviewed"
        for subject in subjects:
            for object_id in objects:
                all_relation_edges += 1
                predicate_counts[predicate] += 1
                for person_id, other_id in ((subject, object_id), (object_id, subject)):
                    if person_id not in people:
                        continue
                    all_degree[person_id] += 1
                    counterpart_counts[person_id][other_id] += 1
                    predicate_by_person[person_id][predicate] += 1
                    if (
                        relation_reviewed
                        and review_state(by_id.get(person_id, {})) == "reviewed"
                        and review_state(by_id.get(other_id, {})) == "reviewed"
                    ):
                        reviewed_degree[person_id] += 1
                if (
                    relation_reviewed
                    and review_state(by_id.get(subject, {})) == "reviewed"
                    and review_state(by_id.get(object_id, {})) == "reviewed"
                ):
                    reviewed_relation_edges += 1

    ranking_mode = "reviewed"
    ranked = reviewed_degree.most_common()
    if len([count for _, count in ranked if count > 0]) < 5:
        ranking_mode = "published"
        ranked = all_degree.most_common()

    top_people = []
    for person_id, count in ranked[:10]:
        top_people.append({
            "id": person_id,
            "name": label(person_id, by_id),
            "connections": count,
            "published_connections": all_degree.get(person_id, 0),
            "reviewed_connections": reviewed_degree.get(person_id, 0),
            "top_predicates": [
                {"predicate": pred, "count": n}
                for pred, n in predicate_by_person[person_id].most_common(4)
            ],
            "top_counterparts": [
                {"id": other_id, "name": label(other_id, by_id), "count": n}
                for other_id, n in counterpart_counts[person_id].most_common(4)
            ],
        })

    daily = Counter()
    for doc in docs:
        raw = str(doc.get("date_added") or "")
        if len(raw) >= 10:
            daily[raw[:10]] += 1

    sources = set()
    for doc in docs:
        for source in doc.get("sources") or []:
            key = source_key(source)
            if key:
                sources.add(key)

    dataset_counts = Counter(str(doc.get("dataset") or "unknown") for doc in docs)

    result = {
        "scope": "comparative corpus excluding bulk campaign imports",
        "documents": len(docs),
        "people": len(people),
        "unique_sources": len(sources),
        "source_datasets": len({str(doc.get("dataset") or "unknown") for doc in docs}),
        "non_relation_dtype_counts": dtype_counts.most_common(),
        "relation_predicate_counts": predicate_counts.most_common(),
        "all_relation_edges": all_relation_edges,
        "reviewed_relation_edges": reviewed_relation_edges,
        "ranking_mode": ranking_mode,
        "top_people": top_people,
        "daily_documents": sorted(daily.items()),
        "dataset_counts": dataset_counts.most_common(20),
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("POSTER_STATS_JSON=" + json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
