from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def sanitize_audit(path: Path) -> None:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    rejected = data.pop("rejected_candidates", [])
    data.pop("query_urls", None)

    kind_counts = Counter(str(item.get("kind", "unknown")) for item in rejected)
    reason_counts = Counter(
        str(reason)
        for item in rejected
        for reason in item.get("reasons", [])
    )

    examples: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in rejected:
        record = item.get("record", {})
        name = str(record.get("contributor_name") or record.get("recipient_name") or "")
        employer = str(record.get("contributor_employer") or "")
        state = str(record.get("contributor_state") or record.get("recipient_state") or "")
        if employer and "TOLEDO" in employer.upper():
            key = "university-of-toledo"
            example = {
                "name": name,
                "employer": employer,
                "state": state,
                "disposition": "excluded because employer and location do not match Laurence D. Fink of BlackRock",
            }
        elif name and not any(part == "FINK" for part in name.upper().replace(",", " ").split()):
            key = "fuzzy-surname"
            example = {
                "name_pattern": "fuzzy FINK search result whose surname was not exactly FINK",
                "disposition": "excluded by exact-surname-token rule",
            }
        elif item.get("kind") == "disbursement" and state != "NY":
            key = "out-of-state-refund"
            example = {
                "name": name,
                "state": state,
                "disposition": "excluded because refund geography did not match the accepted New York identity evidence",
            }
        else:
            continue
        if key not in seen:
            seen.add(key)
            examples.append(example)

    data["query_families"] = [
        {
            "endpoint": "/v1/schedules/schedule_a/",
            "filters": ["FINK, LAURENCE", "FINK, LARRY", "surname FINK plus employer BLACKROCK"],
            "purpose": "individual receipt candidates",
        },
        {
            "endpoint": "/v1/schedules/schedule_b/",
            "filters": ["FINK, LAURENCE", "FINK, LARRY"],
            "purpose": "explicit contribution-refund candidates",
        },
        {
            "endpoint": "/v1/committee/{committee_id}/",
            "purpose": "recipient committee name, party, and designation enrichment",
        },
    ]
    data["rejected_candidate_summary"] = {
        "total": len(rejected),
        "by_kind": dict(sorted(kind_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "minimal_examples": examples,
    }
    data["privacy"] = (
        "Rejected homonym records are aggregated. Street addresses, ZIP codes, "
        "transaction identifiers, dates, and amounts for unrelated people are not retained."
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    sanitize_audit(args.path)
