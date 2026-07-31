#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "starintel:org:aipac-political-action-committee": "AIPAC PAC",
    "starintel:org:employees-of-palantir-technologies-inc-pac": "Palantir employee PAC",
}


def first_value(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(text_value(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {text_value(item)}" for key, item in value.items())
    return str(value)


def document_name(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    return str(
        first_value(
            data,
            ("name", "full_name", "candidate_name", "committee_name", "legal_name", "title", "label"),
        )
        or document.get("name")
        or document.get("title")
        or document.get("_id")
        or "unknown"
    )


def party_of(document: dict[str, Any]) -> tuple[str, str]:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    raw = first_value(
        data,
        (
            "party",
            "party_affiliation",
            "candidate_party",
            "party_code",
            "political_party",
            "affiliation",
        ),
    )
    haystack = " ".join(
        [
            text_value(raw),
            text_value(document.get("labels")),
            text_value(document.get("keywords")),
            text_value(data.get("description")),
            document_name(document),
        ]
    ).upper()
    tokens = set(haystack.replace("-", " ").replace("/", " ").replace("[", " ").replace("]", " ").split())
    if {"REP", "REPUBLICAN", "GOP"} & tokens:
        return "Republican", text_value(raw)
    if {"DEM", "DEMOCRAT", "DEMOCRATIC", "DFL"} & tokens:
        return "Democratic", text_value(raw)
    return "Other/unclear", text_value(raw)


def amount_of(data: dict[str, Any]) -> float | None:
    for key in (
        "amount",
        "transaction_amount",
        "disbursement_amount",
        "contribution_amount",
        "value",
        "total_amount",
    ):
        value = data.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace("$", "").replace(",", ""))
            except ValueError:
                pass
    for container_key in ("transaction", "filing", "details", "metadata"):
        nested = data.get(container_key)
        if isinstance(nested, dict):
            value = amount_of(nested)
            if value is not None:
                return value
    return None


def endpoint(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for candidate in ("_id", "id", "entity_id", "document_id"):
            if isinstance(value.get(candidate), str):
                return value[candidate]
    return None


def candidate_like(document: dict[str, Any]) -> bool:
    if document.get("dtype") == "person":
        return True
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    return any(
        data.get(key) not in (None, "", [], {})
        for key in ("candidate_id", "fec_candidate_id", "office", "office_sought", "district", "candidate_status")
    )


def office_of(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    office = first_value(data, ("office_sought", "office", "candidate_office", "position"))
    state = first_value(data, ("state", "candidate_state"))
    district = first_value(data, ("district", "candidate_district"))
    parts = [text_value(item) for item in (office, state, district) if text_value(item)]
    return " · ".join(parts)


def main() -> int:
    packet = Path(sys.argv[1] if len(sys.argv) > 1 else "digs/gop/2026-07-31-fec-wef-depth-3/starintel-documents.jsonl")
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/gop-party-split.json")

    documents: dict[str, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    for line in packet.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        document = json.loads(line)
        document_id = document.get("_id")
        if isinstance(document_id, str):
            documents[document_id] = document
        if document.get("dtype") == "relation":
            relations.append(document)

    source_totals: dict[str, dict[str, float]] = {
        label: {"Republican": 0.0, "Democratic": 0.0, "Other/unclear": 0.0, "total": 0.0}
        for label in SOURCE_IDS.values()
    }
    source_rows: dict[str, dict[str, int]] = {
        label: {"Republican": 0, "Democratic": 0, "Other/unclear": 0, "total": 0}
        for label in SOURCE_IDS.values()
    }
    recipient_amounts: dict[tuple[str, str], float] = defaultdict(float)
    recipient_rows: dict[tuple[str, str], int] = defaultdict(int)
    field_inventory: dict[str, int] = defaultdict(int)
    matched = 0

    for relation in relations:
        data = relation.get("data") if isinstance(relation.get("data"), dict) else {}
        subject = endpoint(data, "subject")
        if subject not in SOURCE_IDS:
            continue
        relation_id = str(relation.get("_id", ""))
        predicate = text_value(first_value(data, ("predicate", "relation_type", "type", "label"))).lower()
        if "fec-disbursement" not in relation_id and not any(word in predicate for word in ("disbur", "contribut", "payment", "paid")):
            continue
        amount = amount_of(data)
        if amount is None:
            continue
        for key in data:
            field_inventory[key] += 1
        object_id = endpoint(data, "object")
        recipient = documents.get(object_id or "", {"_id": object_id or "unresolved", "data": {}})
        party, raw_party = party_of(recipient)
        label = SOURCE_IDS[subject]
        source_totals[label][party] += amount
        source_totals[label]["total"] += amount
        source_rows[label][party] += 1
        source_rows[label]["total"] += 1
        recipient_key = (label, object_id or "unresolved")
        recipient_amounts[recipient_key] += amount
        recipient_rows[recipient_key] += 1
        matched += 1

    recipients: list[dict[str, Any]] = []
    for (source, recipient_id), amount in recipient_amounts.items():
        document = documents.get(recipient_id, {"_id": recipient_id, "data": {}})
        party, raw_party = party_of(document)
        recipients.append(
            {
                "source": source,
                "recipient_id": recipient_id,
                "name": document_name(document),
                "dtype": document.get("dtype"),
                "party": party,
                "raw_party": raw_party,
                "amount": round(amount, 2),
                "rows": recipient_rows[(source, recipient_id)],
                "candidate_like": candidate_like(document),
                "office": office_of(document),
                "data": document.get("data", {}),
            }
        )
    recipients.sort(key=lambda item: (-item["amount"], item["name"]))

    combined = {"Republican": 0.0, "Democratic": 0.0, "Other/unclear": 0.0, "total": 0.0}
    for totals in source_totals.values():
        for key in combined:
            combined[key] += totals[key]

    report = {
        "packet": str(packet),
        "matched_relation_rows": matched,
        "combined": {key: round(value, 2) for key, value in combined.items()},
        "sources": {
            label: {
                "amounts": {key: round(value, 2) for key, value in totals.items()},
                "rows": source_rows[label],
            }
            for label, totals in source_totals.items()
        },
        "top_candidate_recipients": [item for item in recipients if item["candidate_like"]][:50],
        "top_all_recipients": recipients[:100],
        "relation_data_field_inventory": dict(sorted(field_inventory.items())),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["combined"], sort_keys=True))
    print(f"wrote {output} with {len(recipients)} recipients from {matched} relation rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
