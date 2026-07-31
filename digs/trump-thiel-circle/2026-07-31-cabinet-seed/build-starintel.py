#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import json
from pathlib import Path
from typing import Any

DATASET = "trump-thiel-circle"
SCHEMA_VERSION = "0.9.0"
RUN_ID = "trump-thiel-circle-seed-2026-07-31"
STAMP = "2026-07-31T06:39:00Z"


def load_payload(seed_dir: Path) -> dict[str, Any]:
    parts = sorted(seed_dir.glob("seed-part-*.b64"))
    if not parts:
        raise FileNotFoundError(f"no seed parts in {seed_dir}")
    encoded = "".join(path.read_text(encoding="ascii") for path in parts)
    packed = base64.b64decode("".join(encoded.split()), validate=True)
    payload = json.loads(gzip.decompress(packed))
    if payload.get("dataset") != DATASET:
        raise ValueError("unexpected dataset")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected schema version")
    records = payload.get("records", [])
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate record id")
    return payload


def source_ref(record: dict[str, Any]) -> dict[str, Any]:
    ref = {
        "source_id": record["id"],
        "kind": record.get("kind", ""),
        "title": record.get("title", ""),
        "publisher": record.get("publisher", ""),
        "url": record.get("url", ""),
        "uri": record.get("url", ""),
        "accessed_at": STAMP,
    }
    if record.get("credibility") is not None:
        ref["credibility"] = record["credibility"]
    if record.get("notes"):
        ref["notes"] = record["notes"]
    return ref


def envelope(record: dict[str, Any]) -> dict[str, Any]:
    dtype = record["type"]
    doc: dict[str, Any] = {
        "_id": record["id"],
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": STAMP,
        "date_updated": STAMP,
        "title": record.get("title", ""),
        "tags": [DATASET, dtype, "cabinet-seed"],
        "sources": [],
        "evidence": [],
        "assessment": {"confidence": 0.85, "relevance": 1.0},
        "verification": {"status": "seeded", "verified": False},
        "workflow": {
            "research_status": "seeded",
            "queue": "recursive-investigation",
            "recursion_depth": 0,
            "max_depth": 6,
            "run_id": RUN_ID,
        },
        "provenance": {
            "agent": "GPT-5.6 Thinking",
            "run_id": RUN_ID,
            "skill": "auto-dig;web-research;create-starintel-documents;select-recursive-targets",
            "method": "current-cabinet seed, issue classification, organization expansion, connection-path mapping",
        },
    }

    if dtype == "source":
        doc["summary"] = f"Source record for {record.get('title', record['id'])}."
        doc["data"] = {
            "kind": record.get("kind", ""),
            "publisher": record.get("publisher", ""),
            "title": record.get("title", ""),
            "url": record.get("url", ""),
            "uri": record.get("url", ""),
            "accessed_at": STAMP,
            "credibility": record.get("credibility", 0.8),
        }
        if record.get("notes"):
            doc["data"]["notes"] = record["notes"]
        doc["sources"] = [source_ref(record)]
        doc["assessment"]["confidence"] = record.get("credibility", 0.8)
        doc["verification"] = {"status": "source-backed", "verified": True}

    elif dtype == "person":
        name = record.get("name") or record.get("title", "")
        doc["summary"] = f"Person node in the {DATASET} cabinet seed."
        doc["data"] = {
            "etype": "person",
            "name": name,
            "display_name": name,
            "full_name": name,
            "public_roles": record.get("roles", []),
            "positions": record.get("positions", []),
            "professional_affiliations": record.get("affiliations", []),
        }

    elif dtype == "org":
        name = record.get("name") or record.get("title", "")
        doc["summary"] = "Organization node connected to the current-cabinet seed."
        doc["data"] = {
            "etype": "organization",
            "name": name,
            "display_name": name,
            "org_type": record.get("org_type", ""),
            "website": record.get("website", ""),
            "member_ids": record.get("member_ids", []),
            "executive_ids": record.get("executive_ids", []),
            "owner_ids": record.get("owner_ids", []),
        }

    elif dtype == "relation":
        doc["summary"] = f"{record.get('subject')} {record.get('predicate')} {record.get('object')}"
        doc["data"] = {
            "subject": record.get("subject"),
            "predicate": record.get("predicate", ""),
            "object": record.get("object"),
            "directed": True,
            "confidence": record.get("confidence", 0.85),
            "active": True,
        }
        if record.get("note"):
            doc["data"]["note"] = record["note"]
        doc["related_ids"] = [
            item for item in (record.get("subject"), record.get("object"))
            if isinstance(item, str) and item.startswith("starintel:")
        ]

    elif dtype == "claim":
        doc["summary"] = record.get("claim", "")
        doc["data"] = {
            "claim": record.get("claim", ""),
            "subject_ids": record.get("subject_ids", []),
            "predicate": record.get("predicate", ""),
            "object": {
                "classification": record.get("classification", ""),
                "connected_org_ids": record.get("connected_org_ids", []),
                "clear_connection_paths": record.get("clear_connection_paths", []),
            },
            "claim_type": record.get("claim_type", ""),
            "polarity": "asserted",
            "certainty": record.get("certainty", 0.75),
            "supporting_evidence_ids": record.get("supporting_evidence_ids", []),
            "contradicting_evidence_ids": record.get("contradicting_evidence_ids", []),
            "status": record.get("status", ""),
            "adjudication": record.get("adjudication", ""),
        }
        doc["assessment"] = {
            "confidence": record.get("certainty", 0.75),
            "analytic_confidence": record.get("certainty", 0.75),
            "relevance": 1.0,
        }
        doc["verification"] = {
            "status": record.get("status", "seeded"),
            "verified": record.get("status") in {
                "official-finding",
                "official-corrective-action",
                "documented-connection",
                "investigated-no-action",
            },
            "methods": ["source review", "evidence-status classification"],
        }
        doc["related_ids"] = list(dict.fromkeys(
            record.get("subject_ids", []) + record.get("connected_org_ids", [])
        ))

    elif dtype == "research-pass":
        doc["summary"] = "Cabinet-wide corruption, ethics, conflict, and power-network seed."
        doc["data"] = record.get("data", {})
        doc["assessment"] = record.get("assessment", {})
        doc["verification"] = {
            "status": "mixed",
            "verified": True,
            "methods": [
                "current roster verification",
                "source classification",
                "connection-path construction",
            ],
        }
        doc["workflow"]["research_status"] = "completed-seed"

    else:
        raise ValueError(f"unsupported dtype: {dtype}")

    return doc


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument("--seed-dir", type=Path, default=root / "seed-parts")
    parser.add_argument("--output", type=Path, default=root / "starintel-documents.jsonl")
    parser.add_argument("--queue-output", type=Path, default=root / "research-queue.json")
    args = parser.parse_args()

    payload = load_payload(args.seed_dir)
    documents = [envelope(record) for record in payload["records"]]
    args.output.write_text(
        "".join(json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n" for doc in documents),
        encoding="utf-8",
    )
    args.queue_output.write_text(
        json.dumps(payload["research_queue"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    counts: dict[str, int] = {}
    for doc in documents:
        counts[doc["dtype"]] = counts.get(doc["dtype"], 0) + 1
    print(json.dumps({
        "dataset": DATASET,
        "records": len(documents),
        "counts": counts,
        "documents": str(args.output),
        "queue": str(args.queue_output),
    }, indent=2))


if __name__ == "__main__":
    main()
