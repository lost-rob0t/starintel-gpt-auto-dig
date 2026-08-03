from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKETS = (
    ROOT / "digs/fed/2026-08-02-bae-thiel-wef-think-tank-cross-dataset-depth-4/starintel-documents.jsonl",
    ROOT / "digs/fed/2026-08-02-fbi-tsc-ai-procurement-lineage-depth-2/starintel-documents.jsonl",
    ROOT / "digs/fed/2026-08-02-fbi-tsc-bae-analysis-services-depth-3/starintel-documents.jsonl",
    ROOT / "digs/fed/2026-08-02-fbi-tsc-historical-vendor-lineage-depth-4/starintel-documents.jsonl",
)

INVALID_DATA_FIELDS = {
    "org": {"aliases", "headquarters_country", "misc"},
    "research-pass": {"next_action", "status"},
}


def repair(path: Path) -> int:
    changed = 0
    documents: list[dict[str, object]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        document = json.loads(raw)
        if not isinstance(document, dict):
            raise TypeError(f"{path}:{number}: expected JSON object")
        data = document.get("data")
        if not isinstance(data, dict):
            raise TypeError(f"{path}:{number}: expected data object")
        for field in INVALID_DATA_FIELDS.get(str(document.get("dtype")), set()):
            if field in data:
                del data[field]
                changed += 1
        documents.append(document)

    rendered = "".join(
        json.dumps(document, ensure_ascii=False, sort_keys=False, separators=(",", ":")) + "\n"
        for document in documents
    )
    if rendered != path.read_text(encoding="utf-8"):
        path.write_text(rendered, encoding="utf-8")
    return changed


def main() -> int:
    total = 0
    for path in PACKETS:
        total += repair(path)
    print(f"removed_invalid_data_fields={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
