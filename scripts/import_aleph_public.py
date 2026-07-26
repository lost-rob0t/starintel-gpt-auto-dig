#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.model import Document, stable_id

DEFAULT_HOST = "https://aleph.occrp.org"


def values(entity: dict[str, Any], key: str) -> list[str]:
    raw = (entity.get("properties") or {}).get(key) or []
    if not isinstance(raw, list):
        raw = [raw]
    return [str(item).strip() for item in raw if str(item).strip()]


def first(entity: dict[str, Any], *keys: str) -> str:
    for key in keys:
        found = values(entity, key)
        if found:
            return found[0]
    return ""


def dataset_name(entity: dict[str, Any]) -> str:
    collection = entity.get("collection") or {}
    label = str(collection.get("label") or collection.get("name") or "").strip()
    collection_id = str(entity.get("collection_id") or collection.get("id") or "public").strip()
    token = "-".join((label or collection_id).lower().replace("_", "-").split())
    return f"occrp-aleph-{token or 'public'}"


def endpoint(value: str, label: str) -> dict[str, Any]:
    return {"external_id": value, "label": label or value, "unresolved": True}


def relation_data(entity: dict[str, Any], schema: str) -> dict[str, Any] | None:
    maps = {
        "Directorship": ("director", "organization", "directs"),
        "Ownership": ("owner", "asset", "owns"),
        "Membership": ("member", "organization", "member_of"),
        "Family": ("person", "relative", "family_of"),
        "Associate": ("person", "associate", "associated_with"),
        "Payment": ("payer", "beneficiary", "paid"),
    }
    if schema not in maps:
        return None
    subject_key, object_key, predicate = maps[schema]
    subject = first(entity, subject_key)
    object_id = first(entity, object_key)
    if not subject or not object_id:
        return None
    return {
        "subject": endpoint(subject, first(entity, f"{subject_key}Caption")),
        "predicate": predicate,
        "object": endpoint(object_id, first(entity, f"{object_key}Caption")),
        "directed": True,
        "relation_type": f"followthemoney:{schema}",
        "qualifiers": entity.get("properties") or {},
    }


def entity_document(entity: dict[str, Any], host: str) -> dict[str, Any] | None:
    entity_id = str(entity.get("id") or "").strip()
    schema = str(entity.get("schema") or "Entity").strip()
    if not entity_id:
        return None
    dataset = dataset_name(entity)
    title = str(entity.get("name") or first(entity, "name", "title", "caption") or entity_id)
    schema_map = {
        "Person": "person",
        "Company": "org",
        "Organization": "org",
        "PublicBody": "org",
        "LegalEntity": "entity",
        "Address": "address",
    }
    relation = relation_data(entity, schema)
    if relation is not None:
        dtype = "relation"
        data = relation
    else:
        dtype = schema_map.get(schema, "entity")
        if dtype == "person":
            data = {"name": title, "full_name": title}
            nationalities = values(entity, "nationality")
            if nationalities:
                data["nationalities"] = nationalities
        elif dtype == "org":
            data = {"name": title, "legal_name": title, "org_type": schema}
            jurisdiction = first(entity, "jurisdiction", "country")
            if jurisdiction:
                data["jurisdiction"] = jurisdiction
            registration = first(entity, "registrationNumber")
            if registration:
                data["registration_number"] = registration
        elif dtype == "address":
            data = {"name": title, "address": title, "location_type": "address"}
            country = first(entity, "country")
            if country:
                data["country"] = country
        else:
            data = {"name": title, "display_name": title, "etype": schema}

    url = f"{host.rstrip('/')}/entities/{urllib.parse.quote(entity_id)}"
    document = Document.create(
        dtype,
        dataset,
        doc_id=stable_id(dtype, "occrp-aleph", entity_id),
        title=title,
        summary=f"FollowTheMoney {schema} entity imported from OCCRP Aleph.",
        data=data,
        tags=["occrp", "aleph", "followthemoney", schema.lower()],
        identifiers=[{"scheme": "occrp-aleph-entity", "value": entity_id, "issuer": "OCCRP"}],
        sources=[
            {
                "kind": "database",
                "title": "OCCRP Aleph",
                "publisher": "Organized Crime and Corruption Reporting Project",
                "url": url,
                "access_method": "Aleph API",
            }
        ],
        provenance={
            "collector": "starintel-gpt-auto-dig",
            "method": "Aleph API import",
            "pipeline": "scripts/import_aleph_public.py",
            "imported_from": f"{host.rstrip('/')}/api/2/entities",
            "original_id": entity_id,
            "original_schema_version": "FollowTheMoney",
            "metadata": {"aleph_entity": entity},
        },
        verification={"status": "source-recorded", "verified": False},
        handling={"visibility": "public", "sensitive": False, "pii": dtype in {"person", "address"}},
    )
    return document.to_dict()


def request_json(url: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "starintel-gpt-auto-dig/0.9"})
    if api_key:
        request.add_header("Authorization", api_key)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def iter_entities(host: str, queries: list[str], collection: str, limit: int, api_key: str) -> Iterable[dict[str, Any]]:
    emitted = 0
    for query in queries:
        offset = 0
        while emitted < limit:
            params: dict[str, Any] = {"q": query, "limit": min(100, limit - emitted), "offset": offset}
            if collection:
                params["filter:collection_id"] = collection
            url = f"{host.rstrip('/')}/api/2/entities?{urllib.parse.urlencode(params)}"
            payload = request_json(url, api_key)
            results = payload.get("results") or []
            if not results:
                break
            for entity in results:
                yield entity
                emitted += 1
                if emitted >= limit:
                    return
            next_url = payload.get("next")
            if not next_url:
                break
            offset += len(results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import public or authorized OCCRP Aleph entities as validated StarIntel JSONL.")
    parser.add_argument("--host", default=os.environ.get("ALEPH_HOST", DEFAULT_HOST))
    parser.add_argument("--api-key", default=os.environ.get("ALEPH_API_KEY", ""))
    parser.add_argument("--query", action="append", required=True)
    parser.add_argument("--collection", default="")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--import-db", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8") as handle:
        for entity in iter_entities(args.host, args.query, args.collection, args.limit, args.api_key):
            doc = entity_document(entity, args.host)
            if doc is None:
                continue
            handle.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    if count == 0:
        args.output.unlink(missing_ok=True)
        raise SystemExit("Aleph returned no accessible entities. Supply ALEPH_API_KEY or use a public query/collection available to the current account.")
    if args.import_db:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "starintel.py"), "import", str(args.output)], check=True)
    print(f"wrote {count} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
