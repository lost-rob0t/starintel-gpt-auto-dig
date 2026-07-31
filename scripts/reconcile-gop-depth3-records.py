#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from starintel_doc.validation import validate_document

OLD_FINAL = "9d9d37c56148d06884d09989f576bf273b644335"
MODIFIED_PATHS = (
    "db/investigation-target/starintel:investigation-target:aipac-gop-donation-recipient-resolution-depth-3.ndjson",
    "db/investigation-target/starintel:investigation-target:palantir-pac-recipient-network-depth-3.ndjson",
    "db/investigation-target/starintel:investigation-target:udp-candidate-spending-resolution-depth-3.ndjson",
    "db/investigation-target/starintel:investigation-target:wef-palantir-historical-network-depth-3.ndjson",
    "db/org/starintel:org:aipac-political-action-committee.ndjson",
    "db/org/starintel:org:employees-of-palantir-technologies-inc-pac.ndjson",
)


def unique_scalars(*collections: list[Any] | None) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for collection in collections:
        for value in collection or []:
            key = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                result.append(value)
    return result


def deep_merge(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    for key, value in right.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def source_key(source: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(source.get("url") or source.get("uri") or ""),
        str(source.get("publisher") or source.get("name") or ""),
        str(source.get("title") or ""),
    )


def merge_sources(current: list[dict[str, Any]], desired: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for source in [*current, *desired]:
        key = source_key(source)
        if key not in seen:
            seen.add(key)
            merged.append(source)
    return merged


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def earliest(first: str | None, second: str | None) -> str | None:
    values = [(parse_time(value), value) for value in (first, second) if value]
    return min(values, key=lambda item: item[0])[1] if values else None


def latest(first: str | None, second: str | None) -> str | None:
    values = [(parse_time(value), value) for value in (first, second) if value]
    return max(values, key=lambda item: item[0])[1] if values else None


def merge_document(current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    if current["_id"] != desired["_id"] or current["dtype"] != desired["dtype"]:
        raise ValueError(f"canonical mismatch for {current.get('_id')}")

    result = dict(desired)
    result["date_added"] = earliest(current.get("date_added"), desired.get("date_added"))
    result["date_updated"] = latest(current.get("date_updated"), desired.get("date_updated"))
    result["version"] = max(int(current.get("version", 1)), int(desired.get("version", 1))) + 1

    for field in ("aliases", "tags", "keywords", "related_ids", "notes", "identifiers", "evidence", "attachments"):
        if field in current or field in desired:
            result[field] = unique_scalars(current.get(field), desired.get(field))

    result["sources"] = merge_sources(current.get("sources", []), desired.get("sources", []))
    result["extensions"] = deep_merge(current.get("extensions", {}), desired.get("extensions", {}))
    result["extensions"]["gop.depth-3-reconciliation"] = {
        "preserved_current_dataset": current.get("dataset"),
        "preserved_current_provenance": current.get("provenance"),
        "desired_source_commit": OLD_FINAL,
    }

    if current.get("handling"):
        result["handling"] = deep_merge(desired.get("handling", {}), current["handling"])
    if current.get("lineage"):
        result["lineage"] = deep_merge(current["lineage"], desired.get("lineage", {}))

    result["assessment"] = deep_merge(current.get("assessment", {}), desired.get("assessment", {}))
    confidence = max(
        float((current.get("assessment") or {}).get("confidence", 0.0)),
        float((desired.get("assessment") or {}).get("confidence", 0.0)),
    )
    if confidence:
        result.setdefault("assessment", {})["confidence"] = confidence

    current_verification = current.get("verification", {})
    desired_verification = desired.get("verification", {})
    result["verification"] = deep_merge(current_verification, desired_verification)
    for field in ("methods", "verified_by"):
        if field in current_verification or field in desired_verification:
            result["verification"][field] = unique_scalars(
                current_verification.get(field), desired_verification.get(field)
            )

    validate_document(result)
    return result


def main() -> None:
    desired_root = Path("/tmp/gop-depth3-modified")
    for relative in MODIFIED_PATHS:
        current_path = Path(relative)
        desired_path = desired_root / relative
        if not current_path.exists() or not desired_path.exists():
            raise SystemExit(f"missing reconciliation input: {relative}")
        current = json.loads(current_path.read_text(encoding="utf-8"))
        desired = json.loads(desired_path.read_text(encoding="utf-8"))
        merged = merge_document(current, desired)
        current_path.write_text(
            json.dumps(merged, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"reconciled={relative}")


if __name__ == "__main__":
    main()
