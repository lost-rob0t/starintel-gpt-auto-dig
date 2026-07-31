#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

SCHEMA_VERSION = "0.9.0"
DATASET = "wef"
GLOBAL_SHAPERS_ID = "starintel:org:global-shapers-community"
WEF_ID = "starintel:org:world-economic-forum"
LEGACY_GLOBAL_SHAPERS_ID = "019d5d9a24e3d1f867260975ab573cdf"
LEGACY_WEF_ID = "97187dfc9da19d72911a388dd7b77a2a"
SOURCE_PATH = "/home/unseen/Documents/Projects/starintel-old/starintel/bots/starintel-spiders/shapers_alumni.jl"


def compact(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def timestamp(value: int | float) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def publisher(uri: str) -> str:
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


def sources(urls: Iterable[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in urls:
        if not isinstance(raw, str):
            continue
        uri = raw.strip()
        if not uri or uri in seen:
            continue
        seen.add(uri)
        out.append(
            {
                "source_id": f"sha256:{hashlib.sha256(uri.encode()).hexdigest()}",
                "kind": "profile",
                "publisher": publisher(uri),
                "uri": uri,
                "url": uri,
            }
        )
    return out


def base(doc_id: str, dtype: str, added: int, updated: int, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": timestamp(added),
        "date_updated": timestamp(updated),
        "sources": [],
        "evidence": [],
        "data": data,
        "provenance": {
            "collector": "starintel-spiders/shapers_alumni",
            "collector_type": "legacy-spider",
            "imported_from": SOURCE_PATH,
            "original_schema_version": "0.1",
            "original_path": SOURCE_PATH,
            "transform": "starintel-0.1-flat-to-autodig-0.9.0",
        },
        "lineage": {
            "migration_from": "starintel-0.1",
            "migration_notes": [
                "Legacy person IDs preserved.",
                "Legacy relation IDs replaced with deterministic AutoDig IDs.",
                "Legacy organization IDs mapped to canonical AutoDig organization IDs.",
            ],
            "transform": "shapers-alumni-v0.1-to-autodig-v0.9.0",
            "generation": 1,
        },
        "handling": {"visibility": "public", "pii": False, "sensitive": False},
        "quality": {
            "validation_status": "pending_repository_validation",
            "validator": "scripts/validate-for-merge.py",
            "warnings": [],
        },
    }


def relation_id(person_id: str, organization: str) -> str:
    return f"starintel:relation:legacy-shaper:{person_id}:{organization}"


def relation(person_id: str, organization_id: str, organization: str, added: int, updated: int) -> dict[str, Any]:
    value = base(
        relation_id(person_id, organization),
        "relation",
        added,
        updated,
        {
            "subject": person_id,
            "predicate": "member_of",
            "object": organization_id,
            "source": person_id,
            "target": organization_id,
            "directed": True,
            "note": "Migrated from the legacy shapers_alumni member relation.",
        },
    )
    value["tags"] = ["wef", "global-shapers", "membership", "legacy-import"]
    value["related_ids"] = [person_id, organization_id]
    value["extensions"] = {
        "legacy_starintel": {
            "relation": "member",
            "legacy_target_id": LEGACY_GLOBAL_SHAPERS_ID if organization == "global-shapers" else LEGACY_WEF_ID,
        }
    }
    return value


def organization(added: int) -> dict[str, Any]:
    value = base(
        GLOBAL_SHAPERS_ID,
        "org",
        added,
        added,
        {
            "name": "Global Shapers Community",
            "display_name": "Global Shapers Community",
            "short_name": "Global Shapers",
            "org_type": "World Economic Forum community",
            "website": "https://www.globalshapers.org/",
            "parent_id": WEF_ID,
        },
    )
    value["title"] = "Global Shapers Community"
    value["summary"] = "Canonical organization node for Global Shapers alumni imported from the legacy StarIntel spider dataset."
    value["sources"] = sources(["https://www.globalshapers.org/", "https://www.weforum.org/communities/global-shapers/"])
    value["tags"] = ["wef", "global-shapers", "community", "legacy-import"]
    value["related_ids"] = [WEF_ID]
    value["extensions"] = {"legacy_starintel": {"legacy_id": LEGACY_GLOBAL_SHAPERS_ID}}
    return value


def person(row: list[Any]) -> tuple[dict[str, Any], int, int]:
    if len(row) != 12:
        raise ValueError(f"expected 12 compact fields, got {len(row)}")
    doc_id, added, updated, fname, mname, lname, gender, bio, dob, etype, eid, misc = row
    names = [value.strip() for value in (fname, mname, lname) if isinstance(value, str) and value.strip()]
    data: dict[str, Any] = {}
    for key, value in (("fname", fname), ("mname", mname), ("lname", lname), ("gender", gender), ("bio", bio)):
        if isinstance(value, str) and value:
            data[key] = value
    if names:
        data["full_name"] = " ".join(names)
    if isinstance(misc, list):
        data["misc"] = list(dict.fromkeys(value for value in misc if isinstance(value, str) and value))
    value = base(str(doc_id), "person", int(added), int(updated), data)
    if names:
        value["title"] = " ".join(names)
    value["sources"] = sources(misc if isinstance(misc, list) else [])
    value["tags"] = ["wef", "global-shapers", "alumni", "legacy-import"]
    value["related_ids"] = [GLOBAL_SHAPERS_ID, WEF_ID]
    value["extensions"] = {
        "legacy_starintel": {
            "original_id": doc_id,
            "dob": dob,
            "etype": etype,
            "eid": eid,
            "embedded_org_ids": [LEGACY_GLOBAL_SHAPERS_ID, LEGACY_WEF_ID],
        }
    }
    if isinstance(dob, str) and dob.strip():
        value["quality"]["warnings"].append("Unnormalized legacy dob preserved in extensions.")
    return value, int(added), int(updated)


def migrate(source: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    people: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    earliest: int | None = None
    seen: set[str] = set()
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, list):
            raise ValueError(f"{source}:{number}: expected compact JSON array")
        record, added, updated = person(row)
        if record["_id"] in seen:
            raise ValueError(f"{source}:{number}: duplicate person ID {record['_id']}")
        seen.add(record["_id"])
        earliest = added if earliest is None else min(earliest, added)
        people.append(record)
        relations.append(relation(record["_id"], GLOBAL_SHAPERS_ID, "global-shapers", added, updated))
        relations.append(relation(record["_id"], WEF_ID, "wef", added, updated))
    if earliest is None:
        raise ValueError("compact source is empty")
    documents = [organization(earliest), *people, *relations]
    counts = Counter(doc["dtype"] for doc in documents)
    return documents, {
        "dataset": DATASET,
        "schema_version": SCHEMA_VERSION,
        "input_people": len(people),
        "output_documents": len(documents),
        "counts_by_dtype": dict(sorted(counts.items())),
        "relation_predicate": "member_of",
        "legacy_person_ids_preserved": True,
        "legacy_relation_ids_preserved": False,
        "canonical_wef_id_reused": WEF_ID,
        "referential_integrity": "pending repository validation",
    }


def write_jsonl(path: Path, documents: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for document in documents:
            line = compact(document) + "\n"
            handle.write(line)
            digest.update(line.encode())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Port the legacy Global Shapers alumni data into AutoDig StarIntel 0.9 JSONL.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    documents, report = migrate(args.source)
    report["output_sha256"] = write_jsonl(args.output, documents)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
