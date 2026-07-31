#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCHEMA_VERSION = "0.9.0"
DEFAULT_DATASET = "wef"
DEFAULT_SOURCE_PATH = "/home/unseen/Documents/Projects/starintel-old/starintel/bots/starintel-spiders/shapers_alumni.jl"
GLOBAL_SHAPERS_ID = "019d5d9a24e3d1f867260975ab573cdf"
WEF_ID = "97187dfc9da19d72911a388dd7b77a2a"
COMMON_REQUIRED = {
    "_id",
    "dataset",
    "dtype",
    "schema_version",
    "version",
    "date_added",
    "date_updated",
    "sources",
    "evidence",
    "data",
}


def compact(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def timestamp(value: Any) -> str:
    if not isinstance(value, (int, float)):
        raise ValueError(f"invalid legacy timestamp: {value!r}")
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def source_name(uri: str) -> str:
    host = urlparse(uri).netloc.lower()
    if "weforum.org" in host:
        return "World Economic Forum"
    if "linkedin.com" in host:
        return "LinkedIn"
    if "facebook.com" in host:
        return "Facebook"
    if host in {"twitter.com", "x.com", "www.x.com"}:
        return "X/Twitter"
    return host or "Legacy source"


def sources_from_urls(urls: Iterable[Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for raw in urls:
        if not isinstance(raw, str):
            continue
        uri = raw.strip()
        if not uri or uri in seen:
            continue
        seen.add(uri)
        out.append(
            {
                "source_id": f"sha256:{hashlib.sha256(uri.encode('utf-8')).hexdigest()}",
                "kind": "profile",
                "publisher": source_name(uri),
                "uri": uri,
            }
        )
    return out


def full_name(doc: dict[str, Any]) -> str:
    return " ".join(
        value.strip()
        for value in (doc.get("fname", ""), doc.get("mname", ""), doc.get("lname", ""))
        if isinstance(value, str) and value.strip()
    )


def base_document(doc: dict[str, Any], dataset: str, source_path: str) -> dict[str, Any]:
    return {
        "_id": doc["_id"],
        "dataset": dataset,
        "dtype": doc["dtype"],
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": timestamp(doc["date_added"]),
        "date_updated": timestamp(doc["date_updated"]),
        "sources": [],
        "evidence": [],
        "provenance": {
            "collector": "starintel-spiders/shapers_alumni",
            "collector_type": "legacy-spider",
            "imported_from": source_path,
            "original_id": doc["_id"],
            "original_schema_version": "0.1",
            "original_path": source_path,
            "transform": "starintel-0.1-flat-to-0.9.0",
        },
        "lineage": {
            "migration_from": "starintel-0.1",
            "migration_notes": [
                "Legacy IDs preserved.",
                "Legacy Unix timestamps converted to RFC 3339 UTC.",
            ],
            "transform": "shapers-alumni-v0.1-to-v0.9.0",
            "generation": 1,
        },
        "quality": {
            "validation_status": "validated",
            "validator": "import_legacy_shapers_alumni.py",
            "warnings": [],
        },
        "data": {},
        "extensions": {
            "legacy_starintel": {
                "original_dataset": doc.get("dataset", ""),
                "original_dtype": doc.get("dtype", ""),
            }
        },
    }


def migrate_person(doc: dict[str, Any], dataset: str, source_path: str) -> dict[str, Any]:
    out = base_document(doc, dataset, source_path)
    name = full_name(doc)
    data: dict[str, Any] = {}
    for field in ("fname", "mname", "lname", "gender", "bio"):
        value = doc.get(field)
        if isinstance(value, str) and value:
            data[field] = value
    if name:
        data["full_name"] = name
        out["title"] = name
    misc = [value for value in doc.get("misc", []) if isinstance(value, str) and value]
    if misc:
        data["misc"] = list(dict.fromkeys(misc))
    dob = doc.get("dob")
    if isinstance(dob, str) and dob.strip():
        out["quality"]["warnings"].append("Legacy dob was preserved in extensions because it was not normalized to RFC 3339.")
        out["extensions"]["legacy_starintel"]["dob"] = dob
    out["sources"] = sources_from_urls(misc)
    out["tags"] = ["wef", "global-shapers", "alumni"]
    out["data"] = data
    out["extensions"]["legacy_starintel"].update(
        {
            "etype": doc.get("etype", ""),
            "eid": doc.get("eid", ""),
            "embedded_org_ids": [
                org.get("_id")
                for org in doc.get("orgs", [])
                if isinstance(org, dict) and isinstance(org.get("_id"), str)
            ],
        }
    )
    return out


def migrate_relation(doc: dict[str, Any], dataset: str, source_path: str) -> dict[str, Any]:
    out = base_document(doc, dataset, source_path)
    predicate = "member_of" if doc.get("relation") == "member" else str(doc.get("relation") or "related_to").replace("-", "_")
    source = str(doc.get("source") or "")
    target = str(doc.get("target") or "")
    if not source or not target:
        raise ValueError(f"relation {doc['_id']} has an empty endpoint")
    out["tags"] = ["wef", "global-shapers", "membership"]
    out["data"] = {
        "subject": source,
        "predicate": predicate,
        "object": target,
        "source": source,
        "target": target,
        "directed": True,
        "note": "Migrated from legacy relation field.",
    }
    out["extensions"]["legacy_starintel"]["relation"] = doc.get("relation", "")
    return out


def organization_document(
    org_id: str,
    name: str,
    org_type: str,
    dataset: str,
    source_path: str,
    added: int,
    website: str | None = None,
) -> dict[str, Any]:
    legacy = {
        "_id": org_id,
        "dataset": "Star Intel",
        "dtype": "org",
        "date_added": added,
        "date_updated": added,
    }
    out = base_document(legacy, dataset, source_path)
    out["title"] = name
    out["tags"] = ["wef", "global-shapers"]
    out["data"] = {
        "name": name,
        "display_name": name,
        "org_type": org_type,
    }
    if website:
        out["data"]["website"] = website
        out["sources"] = sources_from_urls([website])
    else:
        out["sources"] = [
            {
                "kind": "legacy-record",
                "name": "Embedded organization record in shapers_alumni.jl",
            }
        ]
    out["extensions"]["legacy_starintel"]["embedded_org"] = True
    return out


def merge_duplicate(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    left = {key: value for key, value in existing.items() if key not in {"date_added", "date_updated"}}
    right = {key: value for key, value in incoming.items() if key not in {"date_added", "date_updated"}}
    if compact(left) != compact(right):
        raise ValueError(f"conflicting duplicate _id {existing.get('_id')}")
    merged = dict(existing)
    merged["date_added"] = min(existing["date_added"], incoming["date_added"])
    merged["date_updated"] = max(existing["date_updated"], incoming["date_updated"])
    return merged


def load_legacy(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    docs: OrderedDict[str, dict[str, Any]] = OrderedDict()
    duplicate_rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(doc, dict) or not isinstance(doc.get("_id"), str):
                raise ValueError(f"invalid document on line {line_number}")
            doc_id = doc["_id"]
            if doc_id in docs:
                duplicate_rows += 1
                docs[doc_id] = merge_duplicate(docs[doc_id], doc)
            else:
                docs[doc_id] = doc
    counts = Counter(doc.get("dtype") for doc in docs.values())
    return list(docs.values()), {
        "input_unique": len(docs),
        "duplicate_rows_removed": duplicate_rows,
        "legacy_persons": counts["person"],
        "legacy_relations": counts["relation"],
    }


def validate_document(doc: dict[str, Any]) -> None:
    missing = COMMON_REQUIRED - doc.keys()
    if missing:
        raise ValueError(f"{doc.get('_id')}: missing required fields {sorted(missing)}")
    if doc["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"{doc['_id']}: wrong schema_version")
    if doc["dataset"] == "":
        raise ValueError(f"{doc['_id']}: empty dataset")
    if not isinstance(doc["version"], int) or doc["version"] < 1:
        raise ValueError(f"{doc['_id']}: invalid version")
    for field in ("date_added", "date_updated"):
        value = doc[field]
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError(f"{doc['_id']}: invalid {field}")
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(doc["sources"], list) or not isinstance(doc["evidence"], list):
        raise ValueError(f"{doc['_id']}: sources/evidence must be arrays")
    if not isinstance(doc["data"], dict):
        raise ValueError(f"{doc['_id']}: data must be an object")
    if doc["dtype"] == "relation":
        required = {"subject", "predicate", "object"}
        if required - doc["data"].keys():
            raise ValueError(f"{doc['_id']}: incomplete relation")


def migrate(path: Path, dataset: str, source_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    legacy, stats = load_legacy(path)
    added = min(int(doc["date_added"]) for doc in legacy)
    people: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    for doc in legacy:
        dtype = doc.get("dtype")
        if dtype == "person":
            people.append(migrate_person(doc, dataset, source_path))
        elif dtype == "relation":
            relations.append(migrate_relation(doc, dataset, source_path))
        else:
            raise ValueError(f"unsupported legacy dtype {dtype!r}")
    orgs = [
        organization_document(
            GLOBAL_SHAPERS_ID,
            "Global Shapers",
            "NGO",
            dataset,
            source_path,
            added,
        ),
        organization_document(
            WEF_ID,
            "World Economic Forum",
            "NGO",
            dataset,
            source_path,
            added,
            "https://www.weforum.org/",
        ),
    ]
    migrated = orgs + people + relations
    seen: set[str] = set()
    for doc in migrated:
        validate_document(doc)
        if doc["_id"] in seen:
            raise ValueError(f"duplicate migrated _id {doc['_id']}")
        seen.add(doc["_id"])
    counts = Counter(doc["dtype"] for doc in migrated)
    target_ids = {doc["data"]["object"] for doc in relations}
    missing_targets = sorted(target_ids - seen)
    if missing_targets:
        raise ValueError(f"missing relation targets: {missing_targets}")
    source_ids = {doc["data"]["subject"] for doc in relations}
    missing_sources = sorted(source_ids - seen)
    if missing_sources:
        raise ValueError(f"missing relation sources: {missing_sources[:10]}")
    report = {
        **stats,
        "dataset": dataset,
        "schema_version": SCHEMA_VERSION,
        "output_documents": len(migrated),
        "counts_by_dtype": dict(sorted(counts.items())),
        "organization_nodes_added": len(orgs),
        "relation_predicate": "member_of",
        "referential_integrity": "ok",
    }
    return migrated, report


def write_jsonl(path: Path, docs: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for doc in docs:
            line = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def request_json(
    url: str,
    method: str = "GET",
    payload: Any | None = None,
    token: str | None = None,
    timeout: int = 300,
    attempts: int = 4,
) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(attempts):
        try:
            request = Request(url, data=body, headers=headers, method=method)
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
                raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(f"request failed for {url}: {exc}") from exc
        time.sleep(2**attempt)
    raise RuntimeError(f"request failed for {url}")


def batches(values: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def ingest(api: str, docs: list[dict[str, Any]], batch_size: int, token: str | None) -> dict[str, Any]:
    if not 1 <= batch_size <= 500:
        raise ValueError("batch size must be between 1 and 500")
    base = api.rstrip("/")
    request_json(f"{base}/health", token=token, timeout=15)
    totals = Counter(total=0, succeeded=0, failed=0, batches=0)
    for number, batch in enumerate(batches(docs, batch_size), 1):
        result = request_json(f"{base}/documents/bulk", method="POST", payload=batch, token=token)
        if not isinstance(result, dict):
            raise RuntimeError(f"batch {number}: invalid response {result!r}")
        totals["batches"] += 1
        totals["total"] += int(result.get("total", 0))
        totals["succeeded"] += int(result.get("succeeded", 0))
        totals["failed"] += int(result.get("failed", 0))
        print(
            f"batch {number}: {result.get('succeeded', 0)}/{result.get('total', len(batch))} published",
            file=sys.stderr,
        )
        if result.get("failed"):
            raise RuntimeError(f"batch {number} had publish failures: {result.get('errors', [])}")
    return dict(totals)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate the legacy Global Shapers alumni JSONL into AutoDig StarIntel 0.9 import JSONL.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("shapers_alumni_v0.9.0.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("shapers_alumni_v0.9.0.report.json"))
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--source-path", default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--api", help="StarIntel API base URL; when present, publish via /documents/bulk")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--token", default=os.environ.get("STARINTEL_TOKEN"))
    args = parser.parse_args()

    docs, report = migrate(args.input, args.dataset, args.source_path)
    report["output_sha256"] = write_jsonl(args.output, docs)
    report["output_path"] = str(args.output)
    if args.api:
        report["ingest"] = ingest(args.api, docs, args.batch_size, args.token)
        report["api"] = args.api.rstrip("/")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
