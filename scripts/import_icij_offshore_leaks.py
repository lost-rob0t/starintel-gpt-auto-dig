#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.model import Document, stable_id

ARCHIVE_URL = "https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.LATEST.zip"
SOURCE_URL = "https://offshoreleaks.icij.org/pages/database"
INVESTIGATION_DATASETS = {
    "offshore leaks": "offshore-leaks",
    "paradise papers": "paradise-papers",
    "panama papers": "panama-papers",
    "bahamas leaks": "bahamas-leaks",
    "pandora papers": "pandora-papers",
}
NODE_TYPES = {
    "entities": "org",
    "officers": "entity",
    "intermediaries": "entity",
    "addresses": "address",
    "others": "entity",
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def dataset_for(source_id: str) -> str:
    lowered = clean(source_id).lower()
    for needle, dataset in INVESTIGATION_DATASETS.items():
        if needle in lowered:
            return dataset
    return "offshore-leaks"


def selected_source(source_id: str, investigations: set[str], include_all: bool) -> bool:
    if include_all:
        return True
    return dataset_for(source_id) in investigations


def find_csv(root: Path, needle: str) -> Path | None:
    candidates = sorted(root.rglob("*.csv"))
    for path in candidates:
        name = path.name.lower()
        if needle in name and "relationships" not in name:
            return path
    return None


def relation_csv(root: Path) -> Path | None:
    for path in sorted(root.rglob("*.csv")):
        if "relationship" in path.name.lower():
            return path
    return None


def read_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def source_record(source_id: str) -> dict[str, Any]:
    return {
        "kind": "dataset",
        "title": f"ICIJ Offshore Leaks Database: {clean(source_id) or 'record'}",
        "publisher": "International Consortium of Investigative Journalists",
        "url": SOURCE_URL,
        "license": "ODbL-1.0 / CC-BY-SA",
        "access_method": "official CSV archive",
    }


def common_metadata(row: dict[str, str], node_id: str, source_id: str, *, pii: bool) -> dict[str, Any]:
    return {
        "identifiers": [{"scheme": "icij-offshore-leaks-node", "value": node_id, "issuer": "ICIJ"}],
        "sources": [source_record(source_id)],
        "provenance": {
            "collector": "starintel-gpt-auto-dig",
            "method": "official CSV import",
            "pipeline": "scripts/import_icij_offshore_leaks.py",
            "imported_from": ARCHIVE_URL,
            "original_id": node_id,
            "metadata": {"source_id": source_id, "raw": row},
        },
        "verification": {
            "status": "source-recorded",
            "verified": False,
            "checks": ["Imported from the official ICIJ CSV archive"],
        },
        "handling": {"visibility": "public", "sensitive": False, "pii": pii},
        "assessment": {
            "caveats": [
                "Inclusion in the ICIJ Offshore Leaks Database does not by itself imply illegal or improper conduct.",
                "Identity matches require corroboration because names may be shared or stale.",
            ]
        },
    }


def node_document(kind: str, row: dict[str, str]) -> dict[str, Any] | None:
    node_id = clean(row.get("node_id") or row.get("NODE_ID") or row.get("id"))
    if not node_id:
        return None
    source_id = clean(row.get("sourceID") or row.get("source_id") or row.get("source"))
    dataset = dataset_for(source_id)
    dtype = NODE_TYPES[kind]
    name = clean(row.get("name") or row.get("original_name") or row.get("address") or node_id)
    jurisdiction = clean(row.get("jurisdiction_description") or row.get("jurisdiction") or row.get("countries"))
    status = clean(row.get("status"))

    if dtype == "org":
        data: dict[str, Any] = {
            "name": name,
            "legal_name": clean(row.get("original_name")) or name,
            "org_type": clean(row.get("company_type")) or "offshore entity",
        }
        if jurisdiction:
            data["jurisdiction"] = jurisdiction
        if status:
            data["status"] = status
        registration = clean(row.get("internal_id") or row.get("ibcRUC"))
        if registration:
            data["registration_number"] = registration
    elif dtype == "address":
        data = {"name": name, "address": name, "location_type": "registered address"}
        country = clean(row.get("countries") or row.get("country_codes"))
        if country:
            data["country"] = country
    else:
        data = {"name": name, "display_name": name, "etype": kind.rstrip("s")}
        if jurisdiction:
            data["jurisdiction"] = jurisdiction
        if status:
            data["status"] = status

    document = Document.create(
        dtype,
        dataset,
        doc_id=stable_id(dtype, "icij-offshore-leaks", node_id),
        title=name,
        summary=f"ICIJ {kind.rstrip('s')} record from {source_id or 'the Offshore Leaks Database'}.",
        data=data,
        tags=["icij", "offshore-leaks", dataset, kind.rstrip("s")],
        **common_metadata(row, node_id, source_id, pii=kind in {"officers", "addresses"}),
    )
    return document.to_dict()


def relation_document(row: dict[str, str], node_ids: dict[str, str]) -> dict[str, Any] | None:
    start = clean(row.get("node_id_start") or row.get("START_ID") or row.get("start_id"))
    end = clean(row.get("node_id_end") or row.get("END_ID") or row.get("end_id"))
    if start not in node_ids or end not in node_ids:
        return None
    source_id = clean(row.get("sourceID") or row.get("source_id") or row.get("source"))
    predicate = clean(row.get("rel_type") or row.get("TYPE") or row.get("link") or "related_to").lower().replace(" ", "_")
    dataset = dataset_for(source_id)
    data: dict[str, Any] = {
        "subject": node_ids[start],
        "predicate": predicate,
        "object": node_ids[end],
        "directed": True,
        "relation_type": "icij-offshore-leaks",
        "qualifiers": {key: value for key, value in row.items() if clean(value)},
    }
    document = Document.create(
        "relation",
        dataset,
        doc_id=stable_id("relation", "icij-offshore-leaks", start, predicate, end, source_id),
        title=f"{start} {predicate.replace('_', ' ')} {end}",
        summary=f"Relationship imported from the ICIJ {source_id or 'Offshore Leaks'} dataset.",
        data=data,
        tags=["icij", "offshore-leaks", dataset, "relationship"],
        **common_metadata(row, f"{start}:{predicate}:{end}", source_id, pii=False),
    )
    return document.to_dict()


def download_archive(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ARCHIVE_URL, timeout=120) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert the official ICIJ Offshore Leaks CSV archive into validated StarIntel JSONL.")
    parser.add_argument("--archive", type=Path, help="Path to full-oldb.LATEST.zip")
    parser.add_argument("--download", action="store_true", help="Download the current official archive")
    parser.add_argument("--investigation", action="append", choices=sorted(INVESTIGATION_DATASETS.values()), default=[])
    parser.add_argument("--all", action="store_true", help="Import every investigation in the archive")
    parser.add_argument("--limit", type=int, default=0, help="Maximum node records; 0 means unlimited")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--import-db", action="store_true", help="Import the resulting JSONL through scripts/starintel.py")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    investigations = set(args.investigation or ["paradise-papers", "offshore-leaks"])
    with tempfile.TemporaryDirectory(prefix="starintel-icij-") as tmp:
        temp = Path(tmp)
        archive = args.archive
        if args.download:
            archive = download_archive(temp / "full-oldb.LATEST.zip")
        if archive is None or not archive.exists():
            raise SystemExit("Provide --archive or use --download")
        extract = temp / "archive"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extract)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        node_ids: dict[str, str] = {}
        written = 0
        with args.output.open("w", encoding="utf-8") as out:
            for kind in NODE_TYPES:
                path = find_csv(extract, kind)
                if path is None:
                    continue
                for row in read_rows(path):
                    source_id = clean(row.get("sourceID") or row.get("source_id") or row.get("source"))
                    if not selected_source(source_id, investigations, args.all):
                        continue
                    doc = node_document(kind, row)
                    if doc is None:
                        continue
                    original_id = clean(row.get("node_id") or row.get("NODE_ID") or row.get("id"))
                    node_ids[original_id] = doc["_id"]
                    out.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
                    written += 1
                    if args.limit and written >= args.limit:
                        break
                if args.limit and written >= args.limit:
                    break

            path = relation_csv(extract)
            if path is not None:
                for row in read_rows(path):
                    source_id = clean(row.get("sourceID") or row.get("source_id") or row.get("source"))
                    if not selected_source(source_id, investigations, args.all):
                        continue
                    doc = relation_document(row, node_ids)
                    if doc is not None:
                        out.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")

    if args.import_db:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "starintel.py"), "import", str(args.output)], check=True)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
