#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = ROOT / "payload"
DEFAULT_OUTPUT = ROOT / "starintel-documents.jsonl"
EXPECTED_RECORDS = 156
EXPECTED_SHA256 = "52281167da70f4f421455c4e70489d9d473f92b7171064b47228982ce7c40f50"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize and validate the trump-thiel-circle depth-2 StarIntel payload."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    encoded = "".join(
        path.read_text(encoding="ascii")
        for path in sorted(PARTS.glob("depth2-part-*.b64"))
    )
    raw = gzip.decompress(base64.b64decode(encoded))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"payload SHA-256 mismatch: {digest}")

    records = []
    ids = set()
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        record = json.loads(line)
        record_id = record.get("_id")
        if not isinstance(record_id, str) or not record_id:
            raise SystemExit(f"line {number}: missing _id")
        if record_id in ids:
            raise SystemExit(f"line {number}: duplicate _id {record_id}")
        if record.get("dataset") != "trump-thiel-circle":
            raise SystemExit(f"line {number}: wrong dataset")
        if record.get("schema_version") != "0.9.0":
            raise SystemExit(f"line {number}: wrong schema_version")
        ids.add(record_id)
        records.append(record)

    if len(records) != EXPECTED_RECORDS:
        raise SystemExit(f"expected {EXPECTED_RECORDS} records, got {len(records)}")

    try:
        sys.path.insert(0, str(ROOT.parents[2]))
        from starintel_doc.validation import validate_document
    except ImportError:
        validate_document = None

    if validate_document is not None:
        for record in records:
            validate_document(record)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    counts = Counter(record["dtype"] for record in records)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records": len(records),
                "sha256": digest,
                "dtypes": dict(sorted(counts.items())),
                "schema_validation": validate_document is not None,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
