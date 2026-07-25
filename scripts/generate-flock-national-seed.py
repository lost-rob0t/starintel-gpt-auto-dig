#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from starintel_doc.validation import validate_document

GENERATED_AT = "2026-07-25T17:58:54-04:00"
DATASET = "flock-safety-national-state-locality-seed-2026-07-25"
OUTPUT_DIR = Path("digs/flock-safety/2026-07-25-national-state-locality-seed")
ATLAS_SEARCH = "https://www.atlasofsurveillance.org/search?sort=state_asc&technologies=automated-license-plate-readers"
ATLAS_DOWNLOAD = "https://kiosk.atlasofsurveillance.org/download.csv?sort=state_asc&technologies%5B%5D=automated-license-plate-readers"
FLOCK_OFFICIAL = "https://www.flocksafety.com/products/license-plate-readers"

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

EXTRA_STATE_SOURCES = {
    "NH": [("https://gc.nh.gov/rules/state_agencies/saf-c7200.html", "New Hampshire ALPR registration rules", "New Hampshire General Court")],
    "VT": [
        ("https://legislature.vermont.gov/statutes/section/23/015/01607", "Vermont ALPR statute §1607", "Vermont Legislature"),
        ("https://legislature.vermont.gov/statutes/fullchapter/23/015", "Vermont automated law-enforcement statutes", "Vermont Legislature"),
    ],
    "MT": [("https://law.justia.com/codes/montana/title-46/chapter-5/part-1/section-46-5-118/", "Montana captured license plate data retention law", "Montana Code / Justia")],
    "CT": [("https://www.flocksafety.com/legal/state-required-provisions", "Flock state-specific contractual provisions", "Flock Safety")],
    "OR": [("https://www.flocksafety.com/legal/state-required-provisions", "Flock state-specific contractual provisions", "Flock Safety")],
}

WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90,
}


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:120] or "unknown"


def normalize_url(value: object) -> str | None:
    text = clean(value)
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"}:
        return text
    if re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}/", text):
        return f"https://{text}"
    return None


def extract_camera_count(summary: str | None) -> int | None:
    if not summary:
        return None
    for pattern in (
        r"operates?\s+(\d+)\s+Flock",
        r"(\d+)\s+Flock Safety automated license plate readers",
        r"(\d+)\s+(?:fixed\s+)?Flock",
        r"has\s+(\d+)\s+Flock",
        r"uses?\s+(\d+)\s+Flock",
    ):
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            return int(match.group(1))
    match = re.search(r"operates?\s+(" + "|".join(WORDS) + r")\s+Flock", summary, re.IGNORECASE)
    return WORDS.get(match.group(1).lower()) if match else None


def source(url: str, title: str, publisher: str | None = None, kind: str = "web") -> dict[str, object]:
    record: dict[str, object] = {
        "kind": kind,
        "url": url,
        "uri": url,
        "name": title,
        "title": title,
    }
    if publisher:
        record["publisher"] = publisher
    return record


def document(
    document_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, object],
    sources: list[dict[str, object]],
    **extra: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "_id": document_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": "0.9.0",
        "version": 1,
        "date_added": GENERATED_AT,
        "date_updated": GENERATED_AT,
        "title": title,
        "summary": summary,
        "sources": sources,
        "evidence": [],
        "data": data,
    }
    record.update(extra)
    validate_document(record)
    return record


def download_rows() -> tuple[list[dict[str, str]], int]:
    request = urllib.request.Request(ATLAS_DOWNLOAD, headers={"User-Agent": "starintel-gpt-auto-dig/0.9"})
    with urllib.request.urlopen(request, timeout=120) as response:
        text = response.read().decode("utf-8-sig")
    all_rows = list(csv.DictReader(text.splitlines()))
    rows = [row for row in all_rows if "flock" in (clean(row.get("Vendor")) or "").lower()]
    for row in rows:
        if row.get("State") == "PS" and row.get("City") == "Des Peres":
            row["State"] = "MO"
    return rows, len(all_rows)


def build_documents(rows: list[dict[str, str]], total_alpr_rows: int) -> tuple[list[dict[str, object]], dict[str, int], list[str], int, int]:
    atlas_search_source = source(ATLAS_SEARCH, "Atlas of Surveillance ALPR search", "Electronic Frontier Foundation")
    atlas_download_source = source(ATLAS_DOWNLOAD, "Atlas of Surveillance ALPR CSV export", "Electronic Frontier Foundation", "dataset")
    flock_source = source(FLOCK_OFFICIAL, "Flock Safety license plate readers", "Flock Safety")

    by_state: dict[str, list[dict[str, str]]] = {state: [] for state in STATE_NAMES}
    for row in rows:
        state = clean(row.get("State"))
        if state in by_state:
            row["_camera_count"] = extract_camera_count(clean(row.get("Summary")))  # type: ignore[assignment]
            by_state[state].append(row)

    docs: list[dict[str, object]] = []
    flock_id = "starintel:org:flock-safety"
    atlas_source_id = "starintel:source:atlas-of-surveillance-alpr-export-2026-07-25"
    national_target_id = "starintel:investigation-target:flock-national"

    docs.append(document(
        flock_id,
        "org",
        "Flock Safety",
        "Public-safety technology vendor whose products include networked automated license plate readers.",
        {
            "etype": "company",
            "name": "Flock Safety",
            "legal_name": "Flock Group Inc.",
            "org_type": "public-safety-technology-company",
            "jurisdiction": "United States",
            "country": "United States",
            "website": "https://www.flocksafety.com/",
        },
        [flock_source],
        assessment={"confidence": 0.99},
        verification={"status": "vendor-identified", "verified": True},
        handling={"visibility": "public", "pii": False, "sensitive": False},
    ))

    docs.append(document(
        atlas_source_id,
        "source",
        "Atlas of Surveillance ALPR export",
        "Downloaded nationwide ALPR dataset filtered for records naming Flock Safety as vendor.",
        {
            "source_id": atlas_source_id,
            "kind": "dataset",
            "type": "csv",
            "name": "Atlas of Surveillance ALPR export",
            "publisher": "Electronic Frontier Foundation / Atlas of Surveillance",
            "url": ATLAS_DOWNLOAD,
            "uri": ATLAS_DOWNLOAD,
            "retrieved_at": GENERATED_AT,
            "access_method": "direct CSV download",
        },
        [atlas_search_source, atlas_download_source],
        verification={"status": "downloaded-and-parsed", "verified": True},
        handling={"visibility": "public", "pii": False, "sensitive": False},
        notes=[f"The export contained {total_alpr_rows:,} ALPR records and {len(rows):,} records naming Flock Safety. Des Peres, Missouri was miscoded as state PS and normalized to MO."],
    ))

    docs.append(document(
        national_target_id,
        "investigation-target",
        "Map Flock Safety across every U.S. state and locality",
        "Root target for nationwide state and locality research into Flock deployments, lobbying, procurement, personnel, policy, data sharing, audits, and terminations.",
        {
            "actor": "starintel-auto-dig",
            "target": "Flock Safety nationwide network",
            "target_id": flock_id,
            "target_type": "national-corporate-government-network",
            "query": "\"Flock Safety\" OR \"Flock Group\" contracts lobbying procurement police sheriff city county state",
            "research_question": "How does Flock Safety enter, expand, administer, lobby, share data across, and exit state and local government systems throughout the United States?",
            "objectives": [
                "Complete all 50 state passes",
                "Recursively investigate every indexed locality",
                "Discover omitted public and private deployments",
                "Map implementation personnel and corporate-government contact chains",
            ],
            "scope_type": "national",
            "seed_ids": [flock_id, atlas_source_id],
            "required_dtypes": ["org", "person", "relation", "contract", "procurement", "grant", "lobbying-filing", "policy", "event", "analysis", "investigation-target"],
            "depth": 0,
            "max_depth": 3,
            "breadth": 50,
            "priority": 1.0,
            "score": 1.0,
            "status": "active",
        },
        [atlas_search_source, atlas_download_source, flock_source],
        workflow={"research_status": "active", "queue": "flock-national", "priority": 1.0, "recursion_depth": 0, "max_depth": 3, "root_target_id": national_target_id},
        assessment={"priority": 1.0, "confidence": 0.95},
        verification={"status": "active", "verified": False},
        handling={"visibility": "public", "pii": False, "sensitive": False},
        related_ids=[flock_id, atlas_source_id],
    ))

    state_targets: dict[str, str] = {}
    state_analyses: dict[str, str] = {}
    locality_target_ids: list[str] = []
    missing_states: list[str] = []
    lower_bound_camera_total = 0
    quantified_rows = 0

    for state, state_name in STATE_NAMES.items():
        state_rows = by_state[state]
        location_id = f"starintel:location:us-state:{state.lower()}"
        analysis_id = f"starintel:analysis:flock-state:{state.lower()}:2026-07-25"
        target_id = f"starintel:investigation-target:flock-state:{state.lower()}"
        state_targets[state] = target_id
        state_analyses[state] = analysis_id

        docs.append(document(
            location_id,
            "location",
            state_name,
            "U.S. state parent jurisdiction for the Flock Safety recursive research tree.",
            {"name": state_name, "location_type": "state", "state": state_name, "country": "United States", "country_code": "US"},
            [atlas_search_source],
            geospatial={"state": state_name, "country": "United States", "country_code": "US", "jurisdiction": state_name},
            handling={"visibility": "public", "pii": False, "sensitive": False},
        ))

        state_sources = [atlas_search_source, atlas_download_source, flock_source]
        for url, title, publisher in EXTRA_STATE_SOURCES.get(state, []):
            state_sources.append(source(url, title, publisher))

        if state_rows:
            camera_counts = [int(row["_camera_count"]) for row in state_rows if isinstance(row.get("_camera_count"), int)]
            camera_total = sum(camera_counts)
            lower_bound_camera_total += camera_total
            quantified_rows += len(camera_counts)
            cities = {clean(row.get("City")) for row in state_rows if clean(row.get("City"))}
            counties = {clean(row.get("County")) for row in state_rows if clean(row.get("County"))}
            top_rows = sorted(
                [row for row in state_rows if isinstance(row.get("_camera_count"), int)],
                key=lambda row: int(row["_camera_count"]),
                reverse=True,
            )[:5]
            top = [
                {
                    "agency": clean(row.get("Agency")),
                    "city": clean(row.get("City")),
                    "county": clean(row.get("County")),
                    "camera_count": int(row["_camera_count"]),
                }
                for row in top_rows
            ]
            findings = [
                f"{len(state_rows)} Atlas-indexed Flock agency records",
                f"{len(cities)} cities and {len(counties)} counties represented",
                f"At least {camera_total} cameras across {len(camera_counts)} rows with parseable quantities",
            ]
            summary = f"{state_name}: {len(state_rows)} Atlas-indexed Flock agency records; {camera_total} cameras quantified as a lower bound."
            analysis_data = {
                "question": f"What is the documented Flock footprint in {state_name}?",
                "method": "Filtered the July 25, 2026 Atlas ALPR CSV for Flock Safety and the state code.",
                "scope": state_name,
                "findings": findings,
                "conclusions": [f"{len(state_rows)} locality recursion targets were generated for {state_name}."],
                "limitations": ["Atlas is incomplete and records may be historical.", "Camera total is a lower bound."],
                "unresolved": ["State lobbying registrations", "State procurement vehicles and grants", "Current locality contracts, policies, sharing, audits, personnel, and termination status"],
                "confidence": 0.88,
            }
            extension = {
                "starintel.national_flock_seed": {
                    "atlas_record_count": len(state_rows),
                    "city_count": len(cities),
                    "county_count": len(counties),
                    "parseable_camera_total_lower_bound": camera_total,
                    "top_quantified_deployments": top,
                }
            }
            verification = {"status": "dataset-indexed", "verified": False}
        else:
            missing_states.append(state)
            summary = f"{state_name}: no Flock row in the Atlas export; verification target retained."
            analysis_data = {
                "question": f"Does Flock Safety have deployments or data-access relationships in {state_name}?",
                "method": "Checked the July 25, 2026 Atlas ALPR CSV for Flock Safety.",
                "scope": state_name,
                "findings": ["No Flock Safety row appeared in the export."],
                "conclusions": ["Absence from the export is not proof of absence."],
                "limitations": ["Recent, private, reseller, pilot, mobile, or data-access arrangements may be omitted."],
                "unresolved": ["Search procurement systems, police records, universities, fusion centers, retailers, HOAs, and intelligence-network access."],
                "confidence": 0.74,
            }
            extension = {"starintel.national_flock_seed": {"atlas_record_count": 0, "absence_of_evidence_only": True}}
            verification = {"status": "absence-in-index-only", "verified": False}

        docs.append(document(
            analysis_id,
            "analysis",
            f"Flock Safety state seed: {state_name}",
            summary,
            analysis_data,
            state_sources,
            geospatial={"state": state_name, "country": "United States", "country_code": "US", "jurisdiction": state_name},
            assessment={"confidence": analysis_data["confidence"]},
            verification=verification,
            workflow={"research_status": "seeded", "queue": "flock-national-state-recursion", "recursion_depth": 1, "max_depth": 3, "root_target_id": national_target_id},
            handling={"visibility": "public", "pii": False, "sensitive": False},
            related_ids=[location_id, flock_id, atlas_source_id, target_id],
            extensions=extension,
        ))

        priority = min(1.0, 0.3 + len(state_rows) / 250)
        docs.append(document(
            target_id,
            "investigation-target",
            f"Investigate Flock Safety in {state_name}",
            f"State-level target for deployments, contracts, lobbying, grants, implementation personnel, data sharing, audits, policy, opposition, and terminations in {state_name}.",
            {
                "actor": "starintel-auto-dig",
                "target": f"Flock Safety in {state_name}",
                "target_id": location_id,
                "target_type": "state-jurisdiction",
                "query": f"\"Flock Safety\" OR \"Flock Group\" OR \"ForceMetrics\" OR \"Falcon\" {state_name} contract procurement lobbyist police sheriff council",
                "research_question": f"Map all Flock Safety activity and responsible personnel in {state_name}.",
                "objectives": ["Find state lobbying and procurement records", "Enumerate public and private deployments", "Capture contracts, prices, funding, policies, sharing, audits, and terminations", "Identify implementation and oversight personnel"],
                "scope_type": "state",
                "seed_ids": [analysis_id, location_id, flock_id, atlas_source_id],
                "required_dtypes": ["org", "person", "relation", "contract", "procurement", "lobbying-filing", "policy", "event", "analysis", "investigation-target"],
                "depth": 1,
                "max_depth": 3,
                "breadth": max(10, len(state_rows)),
                "priority": priority,
                "score": priority,
                "status": "queued",
            },
            state_sources,
            geospatial={"state": state_name, "country": "United States", "country_code": "US", "jurisdiction": state_name},
            workflow={"research_status": "queued", "queue": "flock-national-state-recursion", "priority": priority, "recursion_depth": 1, "max_depth": 3, "root_target_id": national_target_id, "selected_from": [analysis_id]},
            assessment={"priority": priority, "confidence": 0.9},
            verification={"status": "queued", "verified": False},
            handling={"visibility": "public", "pii": False, "sensitive": False},
            related_ids=[analysis_id, location_id, flock_id, atlas_source_id],
        ))

    for row in sorted(rows, key=lambda item: (clean(item.get("State")) or "", clean(item.get("County")) or "", clean(item.get("City")) or "", clean(item.get("Agency")) or "")):
        state = clean(row.get("State"))
        if state not in STATE_NAMES:
            continue
        state_name = STATE_NAMES[state]
        aos = clean(row.get("AOSNUMBER")) or clean(row.get("NEWAOSNUMBER (ORI9)")) or hashlib.sha1(f"{state}|{row.get('Agency')}|{row.get('City')}".encode()).hexdigest()[:12]
        target_id = f"starintel:investigation-target:{slug(aos)}:locality"
        locality_target_ids.append(target_id)
        agency = clean(row.get("Agency")) or "Unknown agency"
        city = clean(row.get("City"))
        county = clean(row.get("County"))
        place = ", ".join(value for value in (city, county, state_name) if value)
        summary = clean(row.get("Summary")) or f"Atlas indexes {agency} as a Flock Safety ALPR user."
        camera_count = row.get("_camera_count") if isinstance(row.get("_camera_count"), int) else None
        priority = 0.72 if camera_count is None else min(1.0, 0.72 + int(camera_count) / 500)
        target_sources = [atlas_search_source]
        link = normalize_url(row.get("Link 1"))
        if link:
            target_sources.append(source(link, clean(row.get("Link 1 Source")) or link))
        extension: dict[str, object] = {
            "starintel.atlas_seed": {
                "aos_number": clean(row.get("AOSNUMBER")),
                "ori9": clean(row.get("NEWAOSNUMBER (ORI9)")),
                "agency": agency,
                "city": city,
                "county": county,
                "state_code": state,
                "atlas_summary": summary,
            }
        }
        if camera_count is not None:
            extension["starintel.atlas_seed"]["reported_camera_count"] = int(camera_count)  # type: ignore[index]
        docs.append(document(
            target_id,
            "investigation-target",
            f"Investigate {agency} Flock implementation",
            f"Locality recursion target for {agency} in {place}.",
            {
                "actor": "starintel-auto-dig",
                "target": f"{agency} Flock Safety implementation",
                "target_type": "local-government-or-law-enforcement-implementation",
                "query": f"\"{agency}\" \"Flock Safety\" contract purchase council policy audit lobbyist",
                "research_question": f"Who implemented, funded, approved, administered, audited, renewed, opposed, or terminated Flock Safety at {agency}, and what sharing relationships exist?",
                "objectives": ["Find contracts, purchase orders, grants, renewals, prices, and resellers", "Identify officials, administrators, records staff, vendor personnel, and lobbyists", "Obtain policy, retention, sharing, user rosters, audits, misuse investigations, and termination records"],
                "scope_type": "locality",
                "seed_ids": [state_targets[state], flock_id, atlas_source_id],
                "required_dtypes": ["org", "person", "relation", "contract", "procurement", "lobbying-filing", "policy", "event", "analysis", "investigation-target"],
                "depth": 2,
                "max_depth": 3,
                "breadth": 10,
                "priority": priority,
                "score": priority,
                "selection_reason": [summary],
                "status": "queued",
            },
            target_sources,
            geospatial={"city": city or "", "county": county or "", "state": state_name, "country": "United States", "country_code": "US", "jurisdiction": place},
            workflow={"research_status": "queued", "queue": f"flock-locality-{state.lower()}", "priority": priority, "recursion_depth": 2, "max_depth": 3, "root_target_id": national_target_id, "selected_from": [state_targets[state]]},
            assessment={"priority": priority, "confidence": 0.82},
            verification={"status": "atlas-indexed-lead", "verified": False},
            handling={"visibility": "public", "pii": False, "sensitive": False},
            related_ids=[state_targets[state], flock_id, atlas_source_id],
            extensions=extension,
        ))

    research_pass_id = "starintel:research-pass:flock-national-state-locality-seed:2026-07-25"
    docs.append(document(
        research_pass_id,
        "research-pass",
        "Flock Safety national state and locality seed pass",
        f"Generated 50 state targets and {len(locality_target_ids):,} locality targets from the current Atlas ALPR export.",
        {
            "research_question": "What state and locality targets should seed nationwide recursive Flock Safety research?",
            "method": "Downloaded and filtered the Atlas of Surveillance ALPR CSV for Flock Safety, normalized one clear state-code error, summarized all 50 states, and emitted locality investigation targets.",
            "classification_rules": ["Atlas records are leads pending primary-source verification", "No-entry states are absence of evidence only", "Camera totals are lower bounds"],
            "findings": [
                {"finding": "Atlas ALPR rows", "value": total_alpr_rows},
                {"finding": "Flock-linked agency rows", "value": len(rows)},
                {"finding": "States represented", "value": len([state for state in STATE_NAMES if by_state[state]])},
                {"finding": "No-entry states", "value": [STATE_NAMES[state] for state in missing_states]},
                {"finding": "Lower-bound quantified cameras", "value": lower_bound_camera_total},
            ],
            "supporting_record_ids": [atlas_source_id, flock_id, *state_analyses.values()],
            "unresolved_target_ids": [national_target_id, *state_targets.values(), *locality_target_ids],
            "source_ids": [atlas_source_id],
            "agent_identity": "OpenAI GPT-5.6 Thinking",
            "narrative_role": "evidence-first national target seeding",
            "started_at": GENERATED_AT,
            "completed_at": GENERATED_AT,
            "iteration": 1,
        },
        [atlas_search_source, atlas_download_source, flock_source],
        workflow={"research_status": "completed", "queue": "flock-national", "priority": 1.0, "recursion_depth": 0, "max_depth": 3, "root_target_id": national_target_id, "completed_at": GENERATED_AT},
        assessment={"confidence": 0.91, "completeness": 0.58},
        verification={"status": "validated-seed", "verified": True},
        handling={"visibility": "public", "pii": False, "sensitive": False},
        related_ids=[national_target_id, flock_id, atlas_source_id],
    ))

    return docs, {state: len(by_state[state]) for state in STATE_NAMES}, missing_states, quantified_rows, lower_bound_camera_total


def validate_corpus(docs: list[dict[str, object]]) -> None:
    ids = [str(record["_id"]) for record in docs]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate document IDs")
    id_set = set(ids)
    for record in docs:
        validate_document(record)
        for related_id in record.get("related_ids", []):
            if related_id not in id_set:
                raise RuntimeError(f"unresolved related ID {related_id!r} in {record['_id']}")
        if record["dtype"] == "investigation-target":
            data = record["data"]
            for seed_id in data.get("seed_ids", []):
                if seed_id not in id_set:
                    raise RuntimeError(f"unresolved seed ID {seed_id!r} in {record['_id']}")
        for item in record["sources"]:
            url = item.get("url")
            if url and urlparse(str(url)).scheme not in {"http", "https"}:
                raise RuntimeError(f"invalid source URL {url!r} in {record['_id']}")


def write_packet(docs: list[dict[str, object]], total_alpr_rows: int, state_counts: dict[str, int], missing_states: list[str], quantified_rows: int, lower_bound_camera_total: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    documents_path = OUTPUT_DIR / "starintel-documents.jsonl"
    with documents_path.open("w", encoding="utf-8") as handle:
        for record in docs:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    content_hash = hashlib.sha256(documents_path.read_bytes()).hexdigest()
    counts = Counter(str(record["dtype"]) for record in docs)

    state_table = "\n".join(f"| {STATE_NAMES[state]} | {state_counts[state]} |" for state in STATE_NAMES)
    readme = f"""# Flock Safety national state and locality seed

Generated: `{GENERATED_AT}`

This packet starts a nationwide recursive StarIntel dig into Flock Safety. It completes the state-first seed pass and emits locality targets for every Flock-linked agency in the July 25, 2026 Atlas of Surveillance ALPR export.

## Output

- 50 state jurisdiction records
- 50 state analysis records
- 50 state investigation targets
- {sum(state_counts.values()):,} locality investigation targets
- one Flock Safety organization record
- one Atlas dataset source record
- one national root target
- one research-pass record
- **{len(docs):,} canonical StarIntel v0.9.0 documents total**

## National seed findings

- Atlas ALPR export rows: {total_alpr_rows:,}
- Rows naming Flock Safety: {sum(state_counts.values()):,}
- States represented: {len([state for state, count in state_counts.items() if count])}
- States without a Flock row in this export: {', '.join(STATE_NAMES[state] for state in missing_states)}
- Rows with parseable camera quantities: {quantified_rows:,}
- Lower-bound camera total from parseable summaries: {lower_bound_camera_total:,}

The no-entry states are encoded as absence-of-evidence targets. The packet does not claim that Flock has no deployment, reseller sale, private installation, pilot, mobile unit, or indirect data-access relationship in those states.

Flock advertises more than 5,000 law-enforcement customers and more than 6,000 communities. The difference between those vendor claims and the Atlas rows is itself a research target.

## State queue

| State | Atlas-indexed Flock agency records |
|---|---:|
{state_table}

## Recursion model

- depth 0: national corporate-government network
- depth 1: all 50 states
- depth 2: every Atlas-indexed locality or agency
- depth 3: contracts, grants, lobbyists, officials, administrators, resellers, policies, audits, sharing relationships, controversies, renewals, and terminations

Every locality target requires primary-source verification before its Atlas-derived lead is promoted into stronger entity, relation, contract, lobbying, policy, or event records.

## Validation

The generator validates every record with `starintel_doc.validate_document`, then checks unique IDs, target seed references, related-document references, and source URL schemes.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    sources_text = f"""# Sources and evidence boundaries

## Primary national index

- Atlas of Surveillance ALPR search: {ATLAS_SEARCH}
- Atlas ALPR CSV export downloaded July 25, 2026: {ATLAS_DOWNLOAD}

The CSV contained {total_alpr_rows:,} automated-license-plate-reader records. Filtering the `Vendor` field for `Flock` produced {sum(state_counts.values()):,} agency records.

A single clear data-quality error was normalized: Des Peres Department of Public Safety had Missouri ORI data and a Missouri locality but the `State` field contained `PS`; this packet records it under Missouri.

## Vendor scope claim

- Flock Safety license plate reader product page: {FLOCK_OFFICIAL}

The vendor page states that Flock is trusted by more than 5,000 law-enforcement agencies and more than 6,000 communities. Those categories are not necessarily identical to Atlas agency rows and are not treated as a direct count comparison.

## State legal context used for no-entry and current-law targets

- New Hampshire ALPR registration rules: https://gc.nh.gov/rules/state_agencies/saf-c7200.html
- Vermont ALPR statute: https://legislature.vermont.gov/statutes/section/23/015/01607
- Vermont automated-law-enforcement chapter: https://legislature.vermont.gov/statutes/fullchapter/23/015
- Montana captured-license-plate-data retention law: https://law.justia.com/codes/montana/title-46/chapter-5/part-1/section-46-5-118/
- Flock state-specific contractual provisions: https://www.flocksafety.com/legal/state-required-provisions

## Evidence boundaries

- An Atlas row is encoded as a locality investigation lead, not conclusive proof that the deployment remains active.
- Camera counts parsed from summaries are lower bounds.
- No-entry states remain active targets.
- This seed pass does not claim comprehensive lobbying, procurement, grant, personnel, policy, audit, or data-sharing coverage.
- Follow-on state and locality passes must prefer official contracts, legislative packets, lobbying registries, purchase orders, policies, audits, and public-records releases.
"""
    (OUTPUT_DIR / "sources.md").write_text(sources_text, encoding="utf-8")

    manifest = {
        "dataset": DATASET,
        "schema_version": "0.9.0",
        "generated_at": GENERATED_AT,
        "files": ["README.md", "sources.md", "starintel-documents.jsonl"],
        "total": len(docs),
        "counts": dict(sorted(counts.items())),
        "atlas_export_rows": total_alpr_rows,
        "atlas_flock_rows": sum(state_counts.values()),
        "states_represented": len([state for state, count in state_counts.items() if count]),
        "no_entry_states": [STATE_NAMES[state] for state in missing_states],
        "locality_targets": sum(state_counts.values()),
        "rows_with_parseable_camera_counts": quantified_rows,
        "lower_bound_camera_total": lower_bound_camera_total,
        "hash_algorithm": "sha256",
        "starintel_documents_sha256": content_hash,
        "validation": {
            "starintel_doc_validate_document": "passed",
            "unique_ids": "passed",
            "target_seed_references": "passed",
            "related_id_references": "passed",
            "source_urls": "passed",
        },
        "state_counts": state_counts,
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows, total_alpr_rows = download_rows()
    docs, state_counts, missing_states, quantified_rows, lower_bound_camera_total = build_documents(rows, total_alpr_rows)
    validate_corpus(docs)
    write_packet(docs, total_alpr_rows, state_counts, missing_states, quantified_rows, lower_bound_camera_total)
    print(f"generated {len(docs):,} documents at {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
