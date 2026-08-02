#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.9.0"
DATASET = "global-shapers"
SITE_ID = "dd50c6e8-1ae1-439d-a23b-925650946bd1"
API_BASE = (
    "https://www.globalshapers.org/api/communities/v1/public/sites/"
    f"{SITE_ID}/members"
)
SHAPERS_PAGE = "https://www.globalshapers.org/shapers"
GLOBAL_SHAPERS_ID = "starintel:org:global-shapers-community"
WEF_ID = "starintel:org:world-economic-forum"
RUN = "global-shapers-current-members-api"
PACKET_DIR = ROOT / "digs" / DATASET / RUN
REPORT_JSON = ROOT / "reports" / "global-shapers-current-api.json"
REPORT_MD = ROOT / "reports" / "global-shapers-current-api.md"
HUB_URL_FILE = ROOT / "imports" / "global-shapers" / "generated-hub-urls.txt"
PROFILE_SEED_FILE = ROOT / "imports" / "global-shapers" / "generated-current-profile-seeds.jsonl"
PROFILE_ID_RE = re.compile(r"/profiles/(?P<id>[A-Za-z0-9]{15,18})/", re.I)
HUB_NAME_RE = re.compile(r"(?:^|,\s*)(?P<hub>[^,]{2,100}?\s+Hub)$", re.I)
MEMBER_COUNT_RE = re.compile(r"(?P<count>[\d,]+)\s+Members\b", re.I)


def now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")


def source_id(uri: str) -> str:
    return f"sha256:{hashlib.sha256(uri.encode()).hexdigest()}"


def official_source(uri: str, title: str, retrieved_at: str) -> dict[str, Any]:
    return {
        "source_id": source_id(uri),
        "kind": "official",
        "publisher": "World Economic Forum / Global Shapers Community",
        "title": title,
        "uri": uri,
        "url": uri,
        "retrieved_at": retrieved_at,
    }


def base_document(
    doc_id: str,
    dtype: str,
    data: dict[str, Any],
    retrieved_at: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": retrieved_at,
        "date_updated": retrieved_at,
        "sources": sources,
        "evidence": [],
        "data": data,
        "provenance": {
            "collector": "scripts/import_global_shapers_members_api.py",
            "collector_type": "official-api-importer",
            "method": "paginated public API enumeration and deterministic identity reconciliation",
            "run_id": RUN,
            "source_endpoint": API_BASE,
        },
        "handling": {"visibility": "public", "pii": False, "sensitive": False},
        "quality": {
            "validation_status": "pending_repository_validation",
            "validator": "scripts/starintel.py validate",
            "warnings": [],
        },
    }


def request_json(
    client: requests.Session,
    page: int,
    timeout: float,
    attempts: int,
) -> tuple[dict[str, Any], str]:
    params = {
        "filters": "true",
        "order_by": "asc",
        "page": str(page),
        "sort_by": "name",
    }
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = client.get(API_BASE, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError(f"page {page}: expected object, got {type(payload).__name__}")
            return payload, response.url
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"page {page}: request failed after {attempts} attempts: {last_error}")


def live_member_count(client: requests.Session, timeout: float) -> int | None:
    try:
        response = client.get(SHAPERS_PAGE, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return None
    match = MEMBER_COUNT_RE.search(response.text)
    if not match:
        return None
    return int(match.group("count").replace(",", ""))


def clean_text(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def profile_id(record: dict[str, Any]) -> str:
    for key in ("photoUrl", "thumbnailUrl", "photo_url", "thumbnail_url"):
        value = clean_text(record.get(key))
        match = PROFILE_ID_RE.search(value)
        if match:
            return match.group("id")
    return ""


def hub_name(position: str) -> str:
    match = HUB_NAME_RE.search(position)
    return clean_text(match.group("hub")) if match else ""


def identity_key(record: dict[str, Any]) -> tuple[str, str]:
    identifier = profile_id(record)
    if identifier:
        return "wef-profile-id", identifier.casefold()
    linkedin = clean_text(record.get("linkedinUrl") or record.get("linkedin_url"))
    if linkedin:
        parsed = urlparse(linkedin)
        canonical = f"{parsed.netloc.casefold()}{parsed.path.rstrip('/').casefold()}"
        return "linkedin", canonical
    name = clean_text(record.get("name"))
    position = clean_text(record.get("position"))
    organization = clean_text(record.get("organization"))
    return "name-hub", f"{slug(name)}|{slug(hub_name(position))}|{slug(organization)}"


def person_id(kind: str, key: str) -> str:
    if kind == "wef-profile-id":
        return f"starintel:person:global-shaper:{key.casefold()}"
    digest = hashlib.sha256(f"{kind}:{key}".encode()).hexdigest()[:24]
    return f"starintel:person:global-shaper:{digest}"


def hub_id(name: str) -> str:
    return f"starintel:org:global-shapers-hub:{slug(name)}"


def infer_status(position: str) -> str:
    folded = position.casefold()
    return "alumni" if "alumni" in folded else "current"


def infer_roles(position: str) -> list[str]:
    if not position:
        return []
    prefix = HUB_NAME_RE.sub("", position).strip(" ,")
    return [part.strip() for part in re.split(r"\s+(?:and|&)\s+|/", prefix) if part.strip()]


def merge_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[identity_key(record)].append(record)

    merged: list[dict[str, Any]] = []
    duplicate_groups: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items()):
        names = [clean_text(item.get("name")) for item in values if clean_text(item.get("name"))]
        positions = [clean_text(item.get("position")) for item in values if clean_text(item.get("position"))]
        organizations = [clean_text(item.get("organization")) for item in values if clean_text(item.get("organization"))]
        linkedins = [clean_text(item.get("linkedinUrl") or item.get("linkedin_url")) for item in values]
        photos = [clean_text(item.get("photoUrl") or item.get("photo_url")) for item in values]
        thumbnails = [clean_text(item.get("thumbnailUrl") or item.get("thumbnail_url")) for item in values]
        hubs = [hub_name(position) for position in positions if hub_name(position)]
        statuses = [infer_status(position) for position in positions]
        roles = [role for position in positions for role in infer_roles(position)]
        merged.append(
            {
                "identity_kind": key[0],
                "identity_key": key[1],
                "name": names[0] if names else "Unknown Global Shaper",
                "alternate_names": sorted(set(names[1:])),
                "positions": sorted(set(positions)),
                "organizations": sorted(set(organizations)),
                "linkedin_urls": sorted(set(value for value in linkedins if value)),
                "photo_urls": sorted(set(value for value in photos if value)),
                "thumbnail_urls": sorted(set(value for value in thumbnails if value)),
                "hub_names": sorted(set(hubs)),
                "statuses": sorted(set(statuses)),
                "roles": sorted(set(roles)),
                "wef_profile_id": profile_id(values[0]),
                "source_rows": len(values),
            }
        )
        if len(values) > 1:
            duplicate_groups.append(
                {
                    "identity_kind": key[0],
                    "identity_key": key[1],
                    "rows": len(values),
                    "names": sorted(set(names)),
                    "positions": sorted(set(positions)),
                }
            )
    return merged, {
        "raw_rows": len(records),
        "unique_identities": len(merged),
        "duplicate_rows_removed": len(records) - len(merged),
        "duplicate_groups": duplicate_groups,
    }


def organization_document(name: str, retrieved_at: str, endpoint_source: dict[str, Any]) -> dict[str, Any]:
    identifier = hub_id(name)
    value = base_document(
        identifier,
        "org",
        {
            "name": name,
            "display_name": name,
            "short_name": name.removesuffix(" Hub"),
            "org_type": "Global Shapers local hub",
            "parent_id": GLOBAL_SHAPERS_ID,
        },
        retrieved_at,
        [endpoint_source],
    )
    value["title"] = name
    value["summary"] = f"Official Global Shapers local hub identified through the public members API: {name}."
    value["tags"] = ["global-shapers", "hub", "official-api"]
    value["related_ids"] = [GLOBAL_SHAPERS_ID, WEF_ID]
    return value


def relation_document(
    person: str,
    target: str,
    predicate: str,
    retrieved_at: str,
    endpoint_source: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(f"{person}|{predicate}|{target}".encode()).hexdigest()[:24]
    value = base_document(
        f"starintel:relation:global-shapers-api:{digest}",
        "relation",
        {
            "subject": person,
            "predicate": predicate,
            "object": target,
            "source": person,
            "target": target,
            "directed": True,
            "note": note,
        },
        retrieved_at,
        [endpoint_source],
    )
    value["tags"] = ["global-shapers", predicate, "official-api"]
    value["related_ids"] = [person, target]
    return value


def person_document(
    record: dict[str, Any],
    retrieved_at: str,
    endpoint_source: dict[str, Any],
) -> dict[str, Any]:
    identifier = person_id(record["identity_kind"], record["identity_key"])
    data: dict[str, Any] = {
        "full_name": record["name"],
        "name": record["name"],
        "positions": record["positions"],
        "organizations": record["organizations"],
        "hub_names": record["hub_names"],
        "statuses": record["statuses"],
        "roles": record["roles"],
        "identity_key": record["identity_key"],
        "identity_kind": record["identity_kind"],
    }
    optional = {
        "alternate_names": record["alternate_names"],
        "linkedin_urls": record["linkedin_urls"],
        "photo_urls": record["photo_urls"],
        "thumbnail_urls": record["thumbnail_urls"],
        "wef_profile_id": record["wef_profile_id"],
    }
    data.update({key: value for key, value in optional.items() if value})
    sources = [endpoint_source]
    for url in record["linkedin_urls"]:
        sources.append(
            {
                "source_id": source_id(url),
                "kind": "profile",
                "publisher": "LinkedIn",
                "uri": url,
                "url": url,
                "retrieved_at": retrieved_at,
            }
        )
    value = base_document(identifier, "person", data, retrieved_at, sources)
    value["title"] = record["name"]
    position = record["positions"][0] if record["positions"] else "Global Shapers Community member"
    organization = record["organizations"][0] if record["organizations"] else ""
    value["summary"] = f"{record['name']} — {position}{f' at {organization}' if organization else ''}."
    value["tags"] = ["global-shapers", "official-api", *record["statuses"]]
    value["related_ids"] = [
        GLOBAL_SHAPERS_ID,
        WEF_ID,
        *(hub_id(name) for name in record["hub_names"]),
    ]
    value["extensions"] = {
        "global_shapers_api": {
            "source_rows": record["source_rows"],
            "wef_profile_id": record["wef_profile_id"],
        }
    }
    return value


def build_documents(
    records: list[dict[str, Any]],
    retrieved_at: str,
    endpoint_url: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    merged, identity_report = merge_records(records)
    endpoint_source = official_source(endpoint_url, "Global Shapers public members API", retrieved_at)
    hubs = sorted({name for record in merged for name in record["hub_names"]})
    documents: list[dict[str, Any]] = []
    documents.extend(organization_document(name, retrieved_at, endpoint_source) for name in hubs)
    status_counts: Counter[str] = Counter()
    identity_kinds: Counter[str] = Counter()
    profile_seeds: list[dict[str, Any]] = []
    for record in merged:
        person = person_document(record, retrieved_at, endpoint_source)
        documents.append(person)
        identity_kinds[record["identity_kind"]] += 1
        status_counts.update(record["statuses"])
        profile_seeds.append(
            {
                "person_id": person["_id"],
                "name": record["name"],
                "hub_names": record["hub_names"],
                "statuses": record["statuses"],
                "wef_profile_id": record["wef_profile_id"],
                "linkedin_urls": record["linkedin_urls"],
            }
        )
        predicate = "alumnus_of" if record["statuses"] == ["alumni"] else "member_of"
        documents.append(
            relation_document(
                person["_id"],
                GLOBAL_SHAPERS_ID,
                predicate,
                retrieved_at,
                endpoint_source,
                "Status derived from the official public member position field.",
            )
        )
        for name in record["hub_names"]:
            documents.append(
                relation_document(
                    person["_id"],
                    hub_id(name),
                    predicate,
                    retrieved_at,
                    endpoint_source,
                    f"Hub affiliation parsed from the official API position field: {name}.",
                )
            )
    return documents, {
        **identity_report,
        "hubs": len(hubs),
        "hub_names": hubs,
        "status_counts": dict(sorted(status_counts.items())),
        "identity_kinds": dict(sorted(identity_kinds.items())),
        "profile_seeds": profile_seeds,
    }


def write_packet(
    documents: Iterable[dict[str, Any]],
    packet_dir: Path,
    chunk_size: int,
) -> dict[str, Any]:
    lines = [compact(document) + "\n" for document in documents]
    payload = "".join(lines).encode()
    counts = Counter(json.loads(line)["dtype"] for line in lines)
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    packet_dir.mkdir(parents=True, exist_ok=True)
    for old in packet_dir.glob("starintel-documents.jsonl*"):
        old.unlink()
    parts: list[str] = []
    for offset in range(0, len(encoded), chunk_size):
        name = f"starintel-documents.jsonl.gz.b64.part-{offset // chunk_size:03d}"
        (packet_dir / name).write_text(encoded[offset:offset + chunk_size] + "\n", encoding="utf-8")
        parts.append(name)
    (packet_dir / "starintel-documents.jsonl.gz.b64.parts").write_text("\n".join(parts) + "\n", encoding="utf-8")
    return {
        "documents": len(lines),
        "counts_by_dtype": dict(sorted(counts.items())),
        "jsonl_sha256": hashlib.sha256(payload).hexdigest(),
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "base64_parts": parts,
    }


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in sorted(set(values))), encoding="utf-8")


def write_profile_seeds(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in sorted(values, key=lambda item: item["person_id"]):
            handle.write(compact(value) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import the complete currently exposed Global Shapers roster from the official paginated public members API.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--minimum-people", type=int, default=4600)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--chunk-size", type=int, default=850_000)
    parser.add_argument("--packet-dir", type=Path, default=PACKET_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_JSON)
    args = parser.parse_args()
    if args.root.resolve() != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    client = requests.Session()
    client.headers.update(
        {
            "User-Agent": "StarIntel-AutoDig/0.9 (+https://starintel.actor; official public roster import)",
            "Accept": "application/json,text/plain,*/*",
        }
    )
    retrieved_at = now()
    expected_live_count = live_member_count(client, args.timeout)
    raw_records: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    seen_page_digests: set[str] = set()
    endpoint_url = API_BASE
    for page in range(1, args.max_pages + 1):
        payload, response_url = request_json(client, page, args.timeout, args.attempts)
        endpoint_url = response_url
        data = payload.get("data")
        if not isinstance(data, list):
            raise RuntimeError(f"page {page}: response has no data array")
        digest = hashlib.sha256(compact(data).encode()).hexdigest()
        pages.append({"page": page, "rows": len(data), "sha256": digest, "url": response_url})
        if not data:
            break
        if digest in seen_page_digests:
            raise RuntimeError(f"page {page}: repeated page payload {digest}")
        seen_page_digests.add(digest)
        for record in data:
            if not isinstance(record, dict):
                raise RuntimeError(f"page {page}: member row is {type(record).__name__}, expected object")
            raw_records.append(record)
    else:
        raise RuntimeError(f"API did not terminate within {args.max_pages} pages")

    documents, identity = build_documents(raw_records, retrieved_at, endpoint_url)
    unique_people = identity["unique_identities"]
    status = "complete" if unique_people >= args.minimum_people else "incomplete"
    packet = write_packet(documents, args.packet_dir, args.chunk_size)
    write_lines(HUB_URL_FILE, (f"https://www.globalshapers.org/hubs/{slug(name)}" for name in identity["hub_names"]))
    write_profile_seeds(PROFILE_SEED_FILE, identity.pop("profile_seeds"))
    report = {
        "status": status,
        "dataset": DATASET,
        "run": RUN,
        "retrieved_at": retrieved_at,
        "api_base": API_BASE,
        "official_page": SHAPERS_PAGE,
        "minimum_people": args.minimum_people,
        "expected_live_member_count": expected_live_count,
        "pages": pages,
        "page_count_with_data": sum(page["rows"] > 0 for page in pages),
        "raw_rows": len(raw_records),
        "people": unique_people,
        "identity": identity,
        "packet": packet,
        "packet_path": str(args.packet_dir.relative_to(ROOT)),
        "hub_url_file": str(HUB_URL_FILE.relative_to(ROOT)),
        "profile_seed_file": str(PROFILE_SEED_FILE.relative_to(ROOT)),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# Current Global Shapers public API import\n\n"
        f"- API rows: **{len(raw_records):,}**\n"
        f"- Unique identities: **{unique_people:,}**\n"
        f"- Duplicate rows removed: **{identity['duplicate_rows_removed']:,}**\n"
        f"- Hubs parsed from positions: **{identity['hubs']:,}**\n"
        f"- Current status records: **{identity['status_counts'].get('current', 0):,}**\n"
        f"- Alumni-labelled records: **{identity['status_counts'].get('alumni', 0):,}**\n"
        f"- Official page headline: **{expected_live_count if expected_live_count is not None else 'unavailable'}**\n"
        f"- Canonical documents: **{packet['documents']:,}**\n\n"
        "Records are deduplicated by WEF profile identifier, then LinkedIn URL, then normalized name, hub and organization.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": status,
        "raw_rows": len(raw_records),
        "people": unique_people,
        "duplicates_removed": identity["duplicate_rows_removed"],
        "hubs": identity["hubs"],
        "expected_live_member_count": expected_live_count,
        "pages": len(pages),
        "documents": packet["documents"],
    }, indent=2))
    return 0 if status == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
