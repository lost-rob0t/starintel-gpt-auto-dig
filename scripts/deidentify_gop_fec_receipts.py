#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DEFAULT_OUTPUT = Path("digs/gop/2026-07-31-fec-individual-contributions-2026")
DOCUMENT_BASENAME = "starintel-documents.jsonl.gz.b64"
PART_SIZE = 30_000_000
GOP_ID = "starintel:org:republican-national-committee"
SAFE_METADATA = {
    "amndt_ind",
    "cmte_id",
    "entity_tp",
    "file_num",
    "image_num",
    "memo_cd",
    "other_id",
    "rpt_tp",
    "sub_id",
    "tran_id",
    "transaction_amt",
    "transaction_dt",
    "transaction_pgi",
    "transaction_tp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove private contributor identities from a generated GOP FEC receipt packet"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def part_manifest(base: Path) -> Path:
    return base.parent / f"{base.name}.parts"


def read_payload(base: Path) -> bytes:
    manifest = part_manifest(base)
    if not manifest.is_file():
        raise RuntimeError(f"missing document parts manifest: {manifest}")
    names = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not names:
        raise RuntimeError("document parts manifest is empty")
    encoded = "".join((base.parent / name).read_text(encoding="utf-8").strip() for name in names)
    return gzip.decompress(base64.b64decode(encoded))


def remove_parts(base: Path) -> None:
    for path in base.parent.glob(f"{base.name}.part-*"):
        path.unlink()
    part_manifest(base).unlink(missing_ok=True)


def write_payload(base: Path, payload: bytes) -> list[str]:
    remove_parts(base)
    encoded = base64.b64encode(gzip.compress(payload, compresslevel=9, mtime=0)).decode("ascii")
    names: list[str] = []
    for index, start in enumerate(range(0, len(encoded), PART_SIZE)):
        name = f"{base.name}.part-{index:04d}"
        (base.parent / name).write_text(encoded[start : start + PART_SIZE] + "\n", encoding="utf-8")
        names.append(name)
    part_manifest(base).write_text("".join(f"{name}\n" for name in names), encoding="utf-8")
    return names


def fec_sub_id(doc: dict[str, Any]) -> str:
    for identifier in doc.get("identifiers", []):
        if identifier.get("scheme") == "fec_sub_id":
            return str(identifier.get("value") or "")
    return ""


def scrub_source(doc: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(doc)
    cleaned["summary"] = (
        "Official FEC individual-contribution bulk source filtered to the Republican National Committee. "
        "Published StarIntel records omit contributor names, locations, employers, occupations, and source-scoped identities."
    )
    data = dict(cleaned.get("data") or {})
    data["privacy_transform"] = (
        "Contributor identity, location, employer, occupation, and raw contributor rows are intentionally omitted."
    )
    cleaned["data"] = data
    cleaned["handling"] = {
        "handling": "public-source-only",
        "pii": False,
        "sensitive": False,
        "visibility": "public",
    }
    validate_document(cleaned)
    return cleaned


def scrub_finance(doc: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(doc)
    data = dict(cleaned.get("data") or {})
    data.pop("donor_id", None)
    data.pop("entity_id", None)
    data["counterparty_ids"] = [GOP_ID]
    data["recipient_id"] = GOP_ID
    data["methodology"] = (
        "Direct row import from the official FEC individual-contributions bulk file with contributor identity fields omitted."
    )
    cleaned["data"] = data

    sub_id = fec_sub_id(cleaned)
    cleaned["title"] = f"FEC contribution {sub_id}" if sub_id else "FEC contribution record"
    amount = data.get("amount")
    amount_text = f"${float(amount):,.2f}" if isinstance(amount, (int, float)) else "a reported amount"
    cleaned["summary"] = (
        f"Official FEC row reports {amount_text} as an itemized contribution or related receipt record to the "
        "Republican National Committee; contributor identity is intentionally omitted from this dataset."
    )
    cleaned["handling"] = {
        "handling": "public-source-only",
        "pii": False,
        "sensitive": False,
        "visibility": "public",
    }

    sources = []
    for source in cleaned.get("sources", []):
        source_copy = dict(source)
        metadata = source_copy.get("metadata")
        if isinstance(metadata, dict):
            source_copy["metadata"] = {
                key: value for key, value in metadata.items() if key in SAFE_METADATA
            }
        sources.append(source_copy)
    cleaned["sources"] = sources
    validate_document(cleaned)
    return cleaned


def main() -> int:
    ns = parse_args()
    output = ns.output
    base = output / DOCUMENT_BASENAME
    payload = read_payload(base)
    original = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line.strip()]

    kept: list[dict[str, Any]] = []
    for doc in original:
        dtype = doc.get("dtype")
        if dtype == "source" and "fec-individual-contributions" in str(doc.get("_id", "")):
            kept.append(scrub_source(doc))
        elif dtype == "campaign-finance":
            kept.append(scrub_finance(doc))

    if not kept:
        raise RuntimeError("privacy transform removed every generated document")

    kept.sort(key=lambda doc: doc["_id"])
    jsonl = "".join(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in kept
    ).encode("utf-8")
    document_parts = write_payload(base, jsonl)

    source_dir = output / "source"
    if source_dir.exists():
        for path in sorted(source_dir.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        source_dir.rmdir()

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = Counter(doc["dtype"] for doc in kept)
    manifest["counts"] = dict(sorted(counts.items()))
    manifest["document_part_count"] = len(document_parts)
    manifest["document_sha256"] = hashlib.sha256(jsonl).hexdigest()
    manifest["total_documents"] = len(kept)
    manifest["contributor_identity_emitted"] = False
    manifest["contributor_location_emitted"] = False
    manifest["contributor_employment_emitted"] = False
    manifest["raw_source_rows_embedded"] = False
    manifest["privacy_transform"] = "deidentified-fec-receipt-ledger-v1"
    manifest.pop("identity_resolution", None)
    manifest.pop("raw_source_psv_part_count", None)
    manifest.pop("raw_source_psv_sha256", None)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    raw_rows = int(manifest.get("raw_matching_rows") or 0)
    (output / "README.md").write_text(
        f"""# GOP FEC de-identified individual-receipt ledger — {manifest.get('cycle', 2026)} cycle

Official FEC individual-contribution rows filtered to `{manifest.get('committee_id', 'C00003418')}`.

- raw matching FEC rows: {raw_rows:,}
- published StarIntel documents: {len(kept):,}
- campaign-finance observations: {counts.get('campaign-finance', 0):,}
- contributor names emitted: no
- contributor locations emitted: no
- contributor employers/occupations emitted: no
- raw contributor rows embedded: no

Each published campaign-finance record retains FEC transaction identifiers, amount/date/report metadata, amendment/memo status, and the RNC recipient linkage. Private contributor identity fields are intentionally omitted. Amendments and memo rows remain separate and are not netted.

```bash
python3 scripts/run_gop_fec_variant.py import_dnc_fec_individual_contributions.py
python3 scripts/deidentify_gop_fec_receipts.py
python3 scripts/validate-for-merge.py --site
```
""",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "documents": len(kept),
                "raw_rows": raw_rows,
                "privacy_transform": manifest["privacy_transform"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
