from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from .model import discover
from .people import (
    _bio_page,
    _directory_page,
    _endpoint_ids,
    _inject_navigation,
    _inject_root_launch,
    _latest_documents,
    _person_record,
)


def build_people_directory(input_root: Path, output: Path, assets: Path) -> dict[str, Any]:
    """Build the full people directory with endpoint-indexed relation lookups.

    The legacy implementation scanned every relation for every person. The DNC
    corpus contains more than 100,000 people, so that quadratic walk dominated
    CI. This preserves the exact output format while only passing each person
    the relations that actually reference that person's ID.
    """
    packets = discover(input_root)
    document_targets: dict[str, set[str]] = defaultdict(set)
    all_documents: list[dict[str, Any]] = []
    for packet in packets:
        for document in packet.documents:
            document_targets[str(document["_id"])].add(packet.target)
            all_documents.append(document)

    documents = _latest_documents(all_documents)
    by_id = {str(document["_id"]): document for document in documents}
    relations_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for document in documents:
        if document.get("dtype") != "relation":
            continue
        data = document.get("data", {})
        endpoint_ids = {
            *_endpoint_ids(data.get("subject")),
            *_endpoint_ids(data.get("object")),
        }
        for endpoint_id in endpoint_ids:
            relations_by_endpoint[endpoint_id].append(document)

    people = [document for document in documents if document.get("dtype") == "person"]
    records = [
        _person_record(
            person,
            relations_by_endpoint.get(str(person["_id"]), []),
            by_id,
            document_targets,
        )
        for person in people
    ]
    records.sort(key=lambda record: record["name"].lower())

    people_output = output / "people"
    if people_output.exists():
        shutil.rmtree(people_output)
    people_output.mkdir(parents=True)
    asset_output = output / "assets"
    asset_output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(assets / "people.css", asset_output / "people.css")
    shutil.copy2(assets / "people.js", asset_output / "people.js")

    serializable = [{key: value for key, value in record.items() if key != "person_document"} for record in records]
    (people_output / "people.json").write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (people_output / "index.html").write_text(_directory_page(records), encoding="utf-8")
    for record in records:
        (people_output / record["url"]).write_text(_bio_page(record, document_targets), encoding="utf-8")

    _inject_navigation(output)
    _inject_root_launch(output, len(records))
    return {
        "people": len(records),
        "alumni": sum("alumni" in record["statuses"] for record in records),
        "organizations": len({item for record in records for item in record["organizations"]}),
        "output": str(people_output),
    }
