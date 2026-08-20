#!/usr/bin/env python3
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "payload" / "starintel-documents.jsonl.gz.b64"
OUTPUT = ROOT / "starintel-documents.jsonl"
MANIFEST = ROOT / "manifest.json"

encoded = "".join(PAYLOAD.read_text(encoding="ascii").split())
raw = gzip.decompress(base64.b64decode(encoded))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
expected = manifest["payload"]["materialized_sha256"]
actual = hashlib.sha256(raw).hexdigest()
if actual != expected:
    raise SystemExit(f"sha256 mismatch: expected {expected}, got {actual}")

OUTPUT.write_bytes(raw)

lines = [line for line in raw.splitlines() if line.strip()]
records = [json.loads(line) for line in lines]
ids = [record["_id"] for record in records]
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate _id values detected")

print(f"wrote {OUTPUT} ({len(records)} records, sha256={actual})")
