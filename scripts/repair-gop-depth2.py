#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from starintel_doc.validation import validate_document

ALEX_PATH = Path("db/person/starintel:person:alex-karp.ndjson")
ALEX_DEPTH2_PATH = Path("/tmp/alex-karp-depth-2.ndjson")

LEGACY_ORG_FIELDS = {
    Path("db/org/starintel:org:aipac-political-action-committee.ndjson"): (
        "connected_organization_id",
    ),
    Path("db/org/starintel:org:employees-of-palantir-technologies-inc-pac.ndjson"): (
        "connected_organization_id",
    ),
    Path("db/org/starintel:org:united-democracy-project.ndjson"): (
        "fec_committee_id",
    ),
}


def unique_strings(*values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for collection in values:
        for value in collection or []:
            text = str(value)
            if text not in seen:
                seen.add(text)
                result.append(text)
    return result


def source_key(source: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(source.get("url") or source.get("uri") or ""),
        str(source.get("publisher") or source.get("name") or ""),
        str(source.get("title") or ""),
    )


def write_document(path: Path, document: dict[str, Any]) -> None:
    validate_document(document)
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def enrich_alex_karp() -> None:
    current = json.loads(ALEX_PATH.read_text(encoding="utf-8"))
    depth2 = json.loads(ALEX_DEPTH2_PATH.read_text(encoding="utf-8"))

    sources: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str, str]] = set()
    for source in [*(current.get("sources") or []), *(depth2.get("sources") or [])]:
        key = source_key(source)
        if key not in seen_sources:
            seen_sources.add(key)
            sources.append(source)

    current["aliases"] = unique_strings(current.get("aliases", []), ["Alex Karp"])
    current["tags"] = unique_strings(current.get("tags", []), depth2.get("tags", []))
    current["sources"] = sources
    current["summary"] = current.get("summary") or depth2.get("summary", "")

    data = current.setdefault("data", {})
    depth2_data = depth2.get("data", {})
    data.setdefault("full_name", depth2_data.get("full_name", "Alexander C. Karp"))
    data.setdefault("positions", depth2_data.get("positions", []))
    data.setdefault("employers", depth2_data.get("employers", []))

    assessment = current.setdefault("assessment", {})
    for key, value in (depth2.get("assessment") or {}).items():
        assessment.setdefault(key, value)
    assessment["confidence"] = max(
        float(assessment.get("confidence", 0.0)),
        float((depth2.get("assessment") or {}).get("confidence", 0.0)),
    )

    verification = {
        **(current.get("verification") or {}),
        **(depth2.get("verification") or {}),
    }
    verification["methods"] = unique_strings(
        (current.get("verification") or {}).get("methods", []),
        (depth2.get("verification") or {}).get("methods", []),
    )
    verification["verified_by"] = unique_strings(
        (current.get("verification") or {}).get("verified_by", []),
        (depth2.get("verification") or {}).get("verified_by", []),
    )
    current["verification"] = verification

    extensions = current.setdefault("extensions", {})
    extensions["gop.depth-2"] = {
        "dataset": depth2.get("dataset"),
        "provenance": depth2.get("provenance"),
        "workflow": depth2.get("workflow"),
        "original_title": depth2.get("title"),
    }

    def parse_time(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    current_updated = current.get("date_updated")
    depth2_updated = depth2.get("date_updated")
    if depth2_updated and (
        not current_updated or parse_time(depth2_updated) > parse_time(current_updated)
    ):
        current["date_updated"] = depth2_updated

    current["version"] = max(
        int(current.get("version", 1)), int(depth2.get("version", 1))
    ) + 1
    write_document(ALEX_PATH, current)
    print(f"alex_karp_sources={len(sources)}")


def normalize_org_fields() -> None:
    for path, fields in LEGACY_ORG_FIELDS.items():
        document = json.loads(path.read_text(encoding="utf-8"))
        data = document.setdefault("data", {})
        legacy = document.setdefault("extensions", {}).setdefault("legacy_data", {})
        for field in fields:
            if field in data:
                legacy.setdefault(field, data.pop(field))
        write_document(path, document)
        print(f"normalized={path}")


def main() -> None:
    enrich_alex_karp()
    normalize_org_fields()


if __name__ == "__main__":
    main()
