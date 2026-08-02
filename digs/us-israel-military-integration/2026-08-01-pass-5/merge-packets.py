#!/usr/bin/env python3
from __future__ import annotations
import base64, gzip, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "merged-quasar-manifest.json"
OUT_JSONL = HERE / "merged-starintel-documents.jsonl"
OUT_TRANSPORT = HERE / "merged-starintel-documents.jsonl.gz.b64"

def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    merged: dict[str, dict] = {}
    order: list[str] = []
    for entry in manifest["data"]["files"]:
        path = (HERE / entry["path"]).resolve()
        raw = base64.b64decode(path.read_text(encoding="ascii"))
        decoded = gzip.decompress(raw)
        digest = hashlib.sha256(decoded).hexdigest()
        if digest != entry["decoded_content_hash"]:
            raise SystemExit(f"hash mismatch: {path}: {digest}")
        for line in decoded.decode("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            record_id = record["_id"]
            if record_id not in merged:
                order.append(record_id)
            merged[record_id] = record
    payload = "".join(
        json.dumps(merged[record_id], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record_id in order
    ).encode("utf-8")
    OUT_JSONL.write_bytes(payload)
    gz = gzip.compress(payload, compresslevel=9, mtime=0)
    OUT_TRANSPORT.write_text(base64.b64encode(gz).decode("ascii") + "\n", encoding="ascii")
    print(json.dumps({
        "records": len(merged),
        "jsonl_sha256": hashlib.sha256(payload).hexdigest(),
        "gzip_sha256": hashlib.sha256(gz).hexdigest(),
        "transport_sha256": hashlib.sha256(OUT_TRANSPORT.read_bytes()).hexdigest(),
    }, indent=2))

if __name__ == "__main__":
    main()
