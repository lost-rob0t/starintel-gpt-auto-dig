#!/usr/bin/env python3
"""Generate URL/finding drafts from the supplied, day-precision observations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE / "observations.json"
OUTPUT = HERE / "starintel-documents.jsonl"
RECEIPT = HERE / "generation-receipt.json"
RUN_ID = "columbus-election-official-listings-2026-10-10"
NOTE = (
    "Source retrieval date supplied: 2026-10-10; exact time not supplied. "
    "Prepared from supplied verified public-page observations without additional browsing. "
    "Neutral institutional records only; historical dataset naming implies no violence or wrongdoing. "
    "No people or employee records, political-belief inferences, or employee-equals-member/endorsement assumptions."
)


def doc_id(dtype: str, key: str) -> str:
    return f"starintel:{dtype}:{RUN_ID}-{key}"


def draft(dtype: str, key: str, fields: dict) -> dict:
    value = {
        "runId": RUN_ID, "sourceKinds": ["web"], "visibility": "public",
        "sensitivity": "public", "notes": NOTE, **fields,
    }
    return json.loads(subprocess.check_output([
        sys.executable, str(ROOT / "scripts/starintel.py"), "create", dtype,
        "--dataset", "anarchist-violence", "--id", doc_id(dtype, key),
        "--fields", json.dumps(value),
    ], cwd=ROOT, text=True))


def generate() -> tuple[bytes, bytes]:
    control = json.loads((ROOT / "config/auto-dig-control.json").read_text())
    if control.get("enabled") is not True or control.get("state") != "running":
        raise ValueError("Auto-Dig control is not running; generation is paused")
    subprocess.run([
        sys.executable, str(ROOT / "scripts/schema-release.py"), "check",
    ], cwd=ROOT, capture_output=True, text=True, check=True)
    inputs = json.loads(INPUT.read_text())
    if inputs["retrievalDate"] != "2026-10-10":
        raise ValueError("review retrieval-date notes before changing this bounded input")
    urls = {row["key"]: row for row in inputs["urls"]}
    if len(urls) != len(inputs["urls"]):
        raise ValueError("duplicate source key")
    records = [draft("url", row["key"], {
        "url": row["url"], "sourceUrls": [row["url"]], "sources": [],
        "notes": NOTE + " Observation: " + row["observation"],
    }) for row in inputs["urls"]]
    for finding in inputs["findings"]:
        references = [{"schema": "url", "id": doc_id("url", key)} for key in finding["sources"]]
        records.append(draft("finding", finding["key"], {
            "title": finding["title"], "description": finding["description"],
            "sourceUrls": [urls[key]["url"] for key in finding["sources"]],
            "sources": references, "evidence": references,
        }))
    if len({row["id"] for row in records}) != len(records):
        raise ValueError("duplicate output IDs")
    packet = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in records).encode()
    receipt = {
        "format": "columbus-official-listings-generation.v1",
        "input": "observations.json",
        "inputSha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "output": "starintel-documents.jsonl",
        "outputSha256": hashlib.sha256(packet).hexdigest(),
        "recordIds": [row["id"] for row in records],
        "recordCounts": {"url": len(inputs["urls"]), "finding": len(inputs["findings"])},
        "retrievalDate": inputs["retrievalDate"],
        "retrievalPrecision": inputs["retrievalPrecision"],
        "timestampPolicy": "No integer timestamp is invented from date-only evidence; retrieval date and precision are explicit in notes.",
        "scope": inputs["observationBasis"],
    }
    return packet, (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, data in zip((OUTPUT, RECEIPT), generate(), strict=True):
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                raise ValueError(f"generated artifact differs: {path}")
        else:
            path.write_bytes(data)
    print("Verified" if args.check else "Generated", "12 records: 8 URL observations and 4 bounded findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
