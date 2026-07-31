#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
from collections import Counter
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "import_dnc_fec_individual_contributions.py"
spec = importlib.util.spec_from_file_location("fec_import", TARGET)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {TARGET}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

_original_build = module.build
_original_identifiers = module.identifiers


def matching_rows(path: Path, committee_id: str):
    member_names = module.data_members(path)
    output: list[dict[str, str]] = []
    occurrences: Counter[str] = Counter()
    with zipfile.ZipFile(path) as archive:
        for member_name in member_names:
            with archive.open(member_name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                for line_number, values in enumerate(csv.reader(text, delimiter="|"), 1):
                    if len(values) == len(module.FIELDS) + 1 and values[-1] == "":
                        values.pop()
                    if len(values) != len(module.FIELDS):
                        raise RuntimeError(
                            f"unexpected row width in {member_name}:{line_number}: {len(values)}"
                        )
                    row = dict(zip(module.FIELDS, values, strict=True))
                    if row["CMTE_ID"] != committee_id:
                        continue
                    original_id = row["SUB_ID"].strip()
                    if not original_id:
                        raise RuntimeError(f"row {member_name}:{line_number} has no SUB_ID")
                    occurrences[original_id] += 1
                    digest = hashlib.sha256(
                        (member_name + "\x1f" + str(line_number) + "\x1f" + "|".join(values)).encode()
                    ).hexdigest()
                    row["_ORIGINAL_SUB_ID"] = original_id
                    row["_ROW_UID"] = f"{original_id}-{digest[:20]}"
                    row["_SUB_ID_OCCURRENCE"] = str(occurrences[original_id])
                    output.append(row)
                    if len(output) > module.MAX_MATCHING_ROWS:
                        raise RuntimeError("matching rows exceed safety limit")
    if not output:
        raise RuntimeError(f"no rows found for {committee_id}")
    return member_names, output


def identifiers(row: dict[str, str]):
    source_row = dict(row)
    source_row["SUB_ID"] = row.get("_ORIGINAL_SUB_ID", row["SUB_ID"])
    result = _original_identifiers(source_row)
    result.append(
        {
            "scheme": "starintel_fec_bulk_row_uid",
            "value": row.get("_ROW_UID", row["SUB_ID"]),
            "issuer": "StarIntel",
            "canonical": False,
        }
    )
    return result


def build(rows, cycle, committee_id, when, source):
    transformed = []
    for row in rows:
        item = dict(row)
        item["SUB_ID"] = row["_ROW_UID"]
        transformed.append(item)
    return _original_build(transformed, cycle, committee_id, when, source)


module.matching_rows = matching_rows
module.identifiers = identifiers
module.build = build

if __name__ == "__main__":
    raise SystemExit(module.main())
