#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
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


def document_name(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    return str(
        first_value(data, ("name", "full_name", "candidate_name", "committee_name", "legal_name", "title", "label"))
        or document.get("title")
        or document.get("name")
        or document.get("_id")
        or "unknown"
    )


def classify_party(raw: Any) -> str:
    value = str(raw or "").strip().upper()
    if value in {"REP", "R", "GOP", "REPUBLICAN"}:
        return "Republican"
    if value in {"DEM", "D", "DFL", "DEMOCRAT", "DEMOCRATIC"}:
        return "Democratic"
    return "Other/unclear"


def amount_of(data: dict[str, Any]) -> float | None:
    for key in ("amount", "transaction_amount", "disbursement_amount", "contribution_amount", "value", "total_amount"):
        value = data.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace("$", "").replace(",", ""))
            except ValueError:
                pass
    for key in ("qualifiers", "transaction", "filing", "details", "metadata", "extensions"):
        nested = data.get(key)
        if isinstance(nested, dict):
            value = amount_of(nested)
            if value is not None:
                return value
    return None


def office_of(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    office = first_value(data, ("office_sought", "office", "candidate_office", "position"))
    state = first_value(data, ("state", "candidate_state"))
    district = first_value(data, ("district", "candidate_district"))
    return " · ".join(str(item) for item in (office, state, district) if item not in (None, ""))


def main() -> int:
    packet = Path(sys.argv[1] if len(sys.argv) > 1 else "digs/gop/2026-07-31-fec-wef-depth-3/starintel-documents.jsonl")
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/gop-party-split.json")

    documents: dict[str, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    dtype_counts: Counter[str] = Counter()
    for line in packet.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        document = json.loads(line)
        dtype_counts[str(document.get("dtype"))] += 1
        document_id = document.get("_id")
        if isinstance(document_id, str):
            documents[document_id] = document
        if document.get("dtype") == "relation":
            relations.append(document)

    source_totals = {
        label: {"Republican": 0.0, "Democratic": 0.0, "Other/unclear": 0.0, "total": 0.0}
        for label in SOURCE_IDS.values()
    }
    source_rows = {
        label: {"Republican": 0, "Democratic": 0, "Other/unclear": 0, "total": 0}
        for label in SOURCE_IDS.values()
    }
    recipient_amounts: dict[tuple[str, str], float] = defaultdict(float)
    recipient_rows: dict[tuple[str, str], int] = defaultdict(int)
    recipient_parties: dict[tuple[str, str], str] = {}
    recipient_committee_ids: dict[tuple[str, str], set[str]] = defaultdict(set)
    matched = 0

    for relation in relations:
        relation_id = str(relation.get("_id", ""))
        if "fec-disbursement" not in relation_id:
            continue
        data = relation.get("data") if isinstance(relation.get("data"), dict) else {}
        subject = data.get("subject")
        if subject not in SOURCE_IDS:
            continue
        qualifiers = data.get("qualifiers") if isinstance(data.get("qualifiers"), dict) else {}
        amount = amount_of(data)
        if amount is None:
            continue
        party = classify_party(qualifiers.get("recipient_party"))
        source = SOURCE_IDS[subject]
        source_totals[source][party] += amount
        source_totals[source]["total"] += amount
        source_rows[source][party] += 1
        source_rows[source]["total"] += 1

        candidate_document_id = str(qualifiers.get("candidate_document_id") or "").strip()
        object_id = str(data.get("object") or "").strip()
        recipient_id = candidate_document_id or object_id or "unresolved"
        key = (source, recipient_id)
        recipient_amounts[key] += amount
        recipient_rows[key] += 1
        recipient_parties[key] = party
        committee_id = str(qualifiers.get("fec_recipient_committee_id") or "").strip()
        if committee_id:
            recipient_committee_ids[key].add(committee_id)
        matched += 1

    recipients: list[dict[str, Any]] = []
    for (source, recipient_id), amount in recipient_amounts.items():
        document = documents.get(recipient_id, {"_id": recipient_id, "data": {}})
        recipients.append(
            {
                "source": source,
                "recipient_id": recipient_id,
                "name": document_name(document),
                "dtype": document.get("dtype"),
                "party": recipient_parties[(source, recipient_id)],
                "amount": round(amount, 2),
                "rows": recipient_rows[(source, recipient_id)],
                "candidate_like": recipient_id.startswith("starintel:person:fec-candidate-"),
                "office": office_of(document),
                "fec_recipient_committee_ids": sorted(recipient_committee_ids[(source, recipient_id)]),
                "data": document.get("data", {}),
            }
        )
    recipients.sort(key=lambda item: (-item["amount"], item["name"]))

    combined_recipients: dict[str, dict[str, Any]] = {}
    for item in recipients:
        recipient_id = item["recipient_id"]
        aggregate = combined_recipients.setdefault(
            recipient_id,
            {
                "recipient_id": recipient_id,
                "name": item["name"],
                "dtype": item["dtype"],
                "party": item["party"],
                "amount": 0.0,
                "rows": 0,
                "candidate_like": item["candidate_like"],
                "office": item["office"],
                "sources": {},
                "fec_recipient_committee_ids": set(),
                "data": item["data"],
            },
        )
        aggregate["amount"] += item["amount"]
        aggregate["rows"] += item["rows"]
        aggregate["sources"][item["source"]] = round(item["amount"], 2)
        aggregate["fec_recipient_committee_ids"].update(item["fec_recipient_committee_ids"])

    combined_recipient_list: list[dict[str, Any]] = []
    for aggregate in combined_recipients.values():
        aggregate["amount"] = round(aggregate["amount"], 2)
        aggregate["fec_recipient_committee_ids"] = sorted(aggregate["fec_recipient_committee_ids"])
        combined_recipient_list.append(aggregate)
    combined_recipient_list.sort(key=lambda item: (-item["amount"], item["name"]))

    combined = {"Republican": 0.0, "Democratic": 0.0, "Other/unclear": 0.0, "total": 0.0}
    for totals in source_totals.values():
        for key in combined:
            combined[key] += totals[key]

    report = {
        "packet": str(packet),
        "dtype_counts": dict(dtype_counts),
        "matched_relation_rows": matched,
        "combined": {key: round(value, 2) for key, value in combined.items()},
        "sources": {
            label: {
                "amounts": {key: round(value, 2) for key, value in totals.items()},
                "rows": source_rows[label],
            }
            for label, totals in source_totals.items()
        },
        "top_candidate_recipients_combined": [item for item in combined_recipient_list if item["candidate_like"]][:75],
        "top_all_recipients_combined": combined_recipient_list[:125],
        "top_candidate_recipients_by_source": [item for item in recipients if item["candidate_like"]][:75],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["combined"], sort_keys=True))
    print(f"wrote {output} with {len(combined_recipient_list)} combined recipients from {matched} relation rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
