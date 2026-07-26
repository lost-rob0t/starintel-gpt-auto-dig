#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from starintel_doc.validation import validate_document

HERE = Path(__file__).resolve().parent
records = [
    json.loads(line)
    for line in (HERE / "starintel-documents.jsonl").read_text().splitlines()
    if line.strip()
]

ids = [record["_id"] for record in records]
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate StarIntel document IDs")

for record in records:
    errors = validate_document(record)
    if errors:
        raise SystemExit(f"{record['_id']}: {errors}")

print(
    json.dumps(
        {
            "records": len(records),
            "counts": dict(Counter(record["dtype"] for record in records)),
        },
        indent=2,
    )
)
