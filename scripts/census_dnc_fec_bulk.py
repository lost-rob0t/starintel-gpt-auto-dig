#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import import_dnc_fec_individual_contributions as source

OUTPUT = Path("digs/dnc/2026-07-31-fec-individual-census")


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dnc-fec-census-") as tmp:
        archive_path = Path(tmp) / "indiv26.zip"
        source.download(source.bulk_url(source.CYCLE), archive_path)
        row_count = 0
        sub_ids: Counter[str] = Counter()
        entities: Counter[str] = Counter()
        identities: set[tuple[str, str, str, str, str]] = set()
        people: set[tuple[str, str, str, str, str]] = set()
        employers: set[str] = set()
        employment_pairs: set[tuple[tuple[str, str, str, str, str], str, str]] = set()
        member_counts: Counter[str] = Counter()
        with zipfile.ZipFile(archive_path) as archive:
            for member in source.data_members(archive_path):
                with archive.open(member) as raw:
                    text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                    for line_no, values in enumerate(csv.reader(text, delimiter="|"), 1):
                        if len(values) == len(source.FIELDS) + 1 and values[-1] == "":
                            values.pop()
                        if len(values) != len(source.FIELDS):
                            raise RuntimeError(f"unexpected row width in {member}:{line_no}")
                        row = dict(zip(source.FIELDS, values, strict=True))
                        if row["CMTE_ID"] != source.COMMITTEE_ID:
                            continue
                        row_count += 1
                        member_counts[member] += 1
                        sub_ids[row["SUB_ID"].strip()] += 1
                        entity = row["ENTITY_TP"].strip().upper() or "UNKNOWN"
                        entities[entity] += 1
                        key = (
                            entity,
                            norm(row["NAME"]),
                            norm(row["CITY"]),
                            row["STATE"].strip().upper(),
                            row["ZIP_CODE"].strip(),
                        )
                        identities.add(key)
                        if entity in source.PERSON_ENTITY_TYPES:
                            people.add(key)
                            employer = norm(row["EMPLOYER"])
                            occupation = norm(row["OCCUPATION"])
                            if employer and employer not in source.NON_EMPLOYERS:
                                employers.add(employer)
                            employment_pairs.add((key, employer, occupation))
        duplicate_rows = sum(count - 1 for count in sub_ids.values() if count > 1)
        manifest = {
            "committee_id": source.COMMITTEE_ID,
            "cycle": source.CYCLE,
            "duplicate_sub_id_rows": duplicate_rows,
            "entity_type_rows": dict(sorted(entities.items())),
            "matching_rows": row_count,
            "raw_source_members": dict(sorted(member_counts.items())),
            "source_scoped_identities": len(identities),
            "source_scoped_people": len(people),
            "unique_employer_values": len(employers),
            "unique_employment_tuples": len(employment_pairs),
            "unique_fec_sub_ids": len(sub_ids),
            "zip_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        }
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUTPUT / "README.md").write_text(
        "# DNC FEC individual-record census\n\n"
        f"- matching rows: {row_count:,}\n"
        f"- source-scoped people: {len(people):,}\n"
        f"- unique employer values: {len(employers):,}\n"
        f"- unique employment tuples: {len(employment_pairs):,}\n"
        f"- repeated SUB_ID rows: {duplicate_rows:,}\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
