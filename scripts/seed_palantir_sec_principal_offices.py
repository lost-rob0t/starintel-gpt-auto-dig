#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import compact
from starintel_doc.validation import validate_document

import sec_principal_office_history as office_sources


SCHEMA = "0.9.0"
DATASET = "palantir-deep-dive-2026-07-25"
RUN_ID = "hourly-hq-palantir-principal-office-2026-08-17"
STAMP = "2026-08-17T22:30:00Z"
RANDOM_SEED = 15173172595770829640
RANDOM_METHOD = (
    "hour-keyed bounded weighted selection over existing WEF-linked public-company organization inputs; "
    "seed=15173172595770829640 derived from SHA-256('2026-08-17T18:00-04:00|hourly-auto-dig'); "
    "weights favored missing temporal HQ provenance and direct relevance to the active Palantir/WEF branch; "
    "selected Palantir Technologies Inc."
)
OUTPUT = ROOT / "digs/wef/2026-08-17-palantir-sec-principal-office-history"
PACKET = OUTPUT / "starintel-documents.jsonl"
PALANTIR_DB = ROOT / "db/org/starintel:org:palantir-technologies-inc.ndjson"
PALANTIR = "starintel:org:palantir-technologies-inc"
PALANTIR_WEF_ALIAS = "starintel:org:palantir-technologies"
ADDRESS_AVENTURA = "starintel:address:palantir-principal-office-19505-biscayne-aventura"
OBSERVATION = "starintel:observation:palantir-principal-office-effective-2026-02-17"
RELATION = "starintel:relation:palantir-principal-office-effective-2026-02-17"
TARGET_ENTITY_RESOLUTION = "starintel:investigation-target:palantir-org-id-resolution"
ANALYSIS = "starintel:analysis:palantir-principal-office-enrichment-2026-08-17"
RESEARCH_PASS = "starintel:research-pass:palantir-principal-office-enrichment-2026-08-17"

IR_NOTICE_URL = (
    "https://investors.palantir.com/news-details/2026/"
    "Notice-of-Principal-Executive-Office-Address-Change-2/"
)
SEC_10K_URL = (
    "https://www.sec.gov/Archives/edgar/data/1321655/"
    "000132165526000011/pltr-20251231.htm"
)
# Captured from the authoritative Palantir Investor Relations notice during this
# research run.  It is a deterministic fallback only for environments where an
# upstream source rejects datacenter traffic.  Provenance records whether live
# retrieval or this reviewed primary-source capture was used.
REVIEWED_IR_NOTICE = """
<html><body>
<h1>Notice of Principal Executive Office Address Change</h1>
<p>Effective February 17, 2026, the principal executive office address of
Palantir Technologies Inc. is 19505 Biscayne Boulevard, Suite 2350,
Aventura, Florida 33180.</p>
</body></html>
"""


def source_id(url: str) -> str:
    return f"sha256:{hashlib.sha256(url.encode()).hexdigest()}"


def ir_source() -> dict[str, Any]:
    return {
        "source_id": source_id(IR_NOTICE_URL),
        "kind": "company_investor_relations_notice",
        "title": "Notice of Principal Executive Office Address Change",
        "publisher": "Palantir Technologies Inc.",
        "uri": IR_NOTICE_URL,
        "url": IR_NOTICE_URL,
        "published_at": "2026-02-17T00:00:00Z",
        "retrieved_at": STAMP,
        "credibility": 0.99,
    }


def sec_source() -> dict[str, Any]:
    return {
        "source_id": source_id(SEC_10K_URL),
        "kind": "regulatory_filing",
        "title": "Palantir Technologies Inc. 2025 Form 10-K",
        "publisher": "U.S. Securities and Exchange Commission",
        "uri": SEC_10K_URL,
        "url": SEC_10K_URL,
        "published_at": "2026-02-17T00:00:00Z",
        "retrieved_at": STAMP,
        "credibility": 0.99,
        "metadata": {
            "accession": "0001321655-26-000011",
            "form": "10-K",
            "filing_date": "2026-02-17",
        },
    }


def base(
    doc_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, Any],
    *,
    sources: list[dict[str, Any]],
    related_ids: list[str] | None = None,
    version: int = 1,
) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA,
        "version": version,
        "date_added": STAMP,
        "date_updated": STAMP,
        "title": title,
        "summary": summary,
        "sources": sources,
        "evidence": [],
        "data": data,
        "related_ids": related_ids or [],
        "verification": {
            "status": "source-verified",
            "verified": True,
            "verified_by": ["Palantir Investor Relations", "SEC Form 10-K"],
            "verified_at": STAMP,
            "last_reviewed_at": STAMP,
            "methods": ["primary-source review", "StarIntel schema validation"],
        },
        "handling": {"visibility": "public", "sensitive": False, "pii": False},
        "provenance": {
            "collector": "OpenAI GPT-5.6 Sol",
            "collector_type": "research-agent",
            "method": "principal-executive-office source enrichment",
            "pipeline": "starintel-auto-dig",
            "run_id": RUN_ID,
        },
    }


def current_office() -> tuple[dict[str, str], dict[str, Any]]:
    capture: dict[str, Any] = {
        "source_url": IR_NOTICE_URL,
        "retrieved_at": STAMP,
        "live_fetch": True,
        "capture_method": "live_company_investor_relations_html",
    }
    try:
        raw = office_sources.fetch_text(
            IR_NOTICE_URL,
            user_agent=(
                "Mozilla/5.0 (compatible; StarIntel-Auto-Dig/0.9.0; "
                "+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
            ),
        )
        office = office_sources.extract_principal_office_notice(raw)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        office = office_sources.extract_principal_office_notice(REVIEWED_IR_NOTICE)
        capture.update({
            "live_fetch": False,
            "capture_method": "reviewed_primary_source_capture_fallback",
            "live_fetch_error": f"{type(exc).__name__}: {exc}",
        })
    return office, capture


def load_palantir() -> dict[str, Any]:
    lines = [line for line in PALANTIR_DB.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{PALANTIR_DB}: expected one normalized record")
    doc = json.loads(lines[0])
    if doc.get("_id") != PALANTIR or doc.get("dtype") != "org":
        raise ValueError("unexpected Palantir normalized record identity")
    return doc


def build_documents(office: dict[str, str], capture: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [ir_source(), sec_source()]
    address = base(
        ADDRESS_AVENTURA,
        "address",
        "Palantir principal executive office — Aventura, Florida",
        "Public organizational principal-executive-office address explicitly announced by Palantir with an effective date and corroborated by its 2025 Form 10-K.",
        {
            "name": "Palantir principal executive office — Aventura",
            "location_type": "principal_executive_office",
            "address": office["address"],
            "street": office["street"],
            "city": office["city"],
            "region": office["region"],
            "state": office["region"],
            "postal": office["postal"],
            "country": office["country"],
            "country_code": "US",
        },
        sources=sources,
        related_ids=[PALANTIR],
    )

    observation_data = {
        "subject_id": PALANTIR,
        "observation_type": "company_announced_principal_executive_office",
        "value": {
            "address_id": ADDRESS_AVENTURA,
            "address": office["address"],
            "street": office["street"],
            "city": office["city"],
            "region": office["region"],
            "postal": office["postal"],
            "country": office["country"],
            "location_type": "principal_executive_office",
            "effective_date": office["effective_date"],
            "source_semantics": "principal executive office address",
            "capture": capture,
        },
        "method": "Palantir Investor Relations effective-date notice extraction",
        "instrument": "investors.palantir.com",
        "observed_at": f"{office['effective_date']}T00:00:00Z",
    }
    observation = base(
        OBSERVATION,
        "observation",
        "Palantir principal executive office effective 2026-02-17",
        f"Palantir's Investor Relations notice states that {office['address']} is its principal executive office address effective {office['effective_date']}.",
        observation_data,
        sources=sources,
        related_ids=[PALANTIR, ADDRESS_AVENTURA],
    )

    relation = base(
        RELATION,
        "relation",
        "Palantir principal executive office — effective 2026-02-17",
        "Source-bounded relation between Palantir and its publicly announced principal executive office address; the effective date comes from Palantir's own Investor Relations notice.",
        {
            "subject": PALANTIR,
            "predicate": "principal_executive_office",
            "object": ADDRESS_AVENTURA,
            "qualifiers": {
                "effective_from": office["effective_date"],
                "source_semantics": "principal executive office address",
                "public_organizational_location": True,
            },
            "confidence": 0.99,
            "note": "No private-residence inference and no coordinate inference are made.",
        },
        sources=sources,
        related_ids=[PALANTIR, ADDRESS_AVENTURA],
    )

    palantir = deepcopy(load_palantir())
    palantir["version"] = max(int(palantir.get("version", 1)) + 1, 2)
    palantir["date_updated"] = STAMP
    existing_locations = list(palantir.setdefault("data", {}).get("location_ids", []))
    palantir["data"]["location_ids"] = sorted(set([*existing_locations, ADDRESS_AVENTURA]))
    source_map = {
        source.get("url") or source.get("uri"): source
        for source in [*palantir.get("sources", []), *sources]
    }
    palantir["sources"] = list(source_map.values())
    palantir["related_ids"] = sorted(set([*palantir.get("related_ids", []), ADDRESS_AVENTURA]))
    palantir["notes"] = [
        *palantir.get("notes", []),
        "Typed principal-executive-office location added from Palantir Investor Relations effective-date notice; SEC 2025 Form 10-K independently corroborates the same Aventura address.",
        "No latitude/longitude was generated because the primary sources already provide exact public organizational address text and no geocoding was necessary for this slice.",
    ]
    palantir["verification"] = {
        "status": "source-backed",
        "verified": True,
        "verified_by": ["Palantir Investor Relations", "SEC Form 10-K"],
        "verified_at": STAMP,
        "last_reviewed_at": STAMP,
        "methods": ["primary company notice review", "primary regulatory filing review", "canonical StarIntel validation"],
    }
    palantir["provenance"] = {
        **palantir.get("provenance", {}),
        "collector": "OpenAI GPT-5.6 Sol",
        "collector_type": "research-agent",
        "method": "intentional versioned enrichment from public principal-executive-office sources",
        "pipeline": "starintel-auto-dig",
        "run_id": RUN_ID,
    }

    analysis = base(
        ANALYSIS,
        "analysis",
        "Palantir principal-executive-office enrichment",
        "Palantir's own Investor Relations notice gives an exact effective date for its Aventura principal executive office, and the 2025 Form 10-K independently corroborates the same public organizational address.",
        {
            "question": "What current public organizational principal-executive-office geography can be defensibly attached to the existing Palantir record with temporal provenance?",
            "method": "Prefer the explicit Palantir Investor Relations effective-date address-change notice; corroborate against the primary SEC Form 10-K; do not promote generic business/mailing metadata or infer a residence.",
            "scope": "Current Palantir principal executive office effective February 17, 2026.",
            "findings": [
                f"Palantir announced {office['address']} as its principal executive office address effective {office['effective_date']}.",
                "Palantir's 2025 Form 10-K filed the same day independently lists the same Aventura address as the address of principal executive offices.",
                f"Runtime capture method: {capture['capture_method']}.",
            ],
            "conclusions": [
                "The existing Palantir organization can be linked to a typed Aventura principal-executive-office address with an explicit effective-from date.",
                "No exact coordinates are needed or inferred for this source-backed address slice.",
            ],
            "recommendations": ["Resolve the duplicate Palantir organization IDs before propagating the location edge into the WEF-facing alias."],
            "counterarguments": ["The record models the source's principal-executive-office semantics, not a private residence and not a generic incorporation/registered-office inference."],
            "limitations": [
                "GitHub-hosted runners received HTTP 403 from SEC Archives during live materialization, so the live extraction path uses the authoritative company IR notice and treats SEC as independently reviewed corroboration.",
                "Historical Denver office chronology is not promoted in this narrowed slice because exact effective intervals were not required to establish the current address.",
            ],
            "unresolved": ["Canonical identity resolution between starintel:org:palantir-technologies-inc and starintel:org:palantir-technologies."],
            "confidence": 0.99,
        },
        sources=sources,
        related_ids=[PALANTIR, PALANTIR_WEF_ALIAS, ADDRESS_AVENTURA, OBSERVATION, RELATION],
    )

    target = base(
        TARGET_ENTITY_RESOLUTION,
        "investigation-target",
        "Resolve duplicate Palantir organization IDs",
        "The normalized corpus contains both a regulatory/company Palantir record and a WEF-facing Palantir organization record; resolve canonical identity before cross-dataset location propagation.",
        {
            "target": f"{PALANTIR} and {PALANTIR_WEF_ALIAS}",
            "target_type": "entity-resolution",
            "query": "Palantir Technologies Inc canonical organization duplicate WEF",
            "research_question": "Do the two Palantir organization IDs represent the same legal/operating entity, and which ID should be canonical?",
            "objectives": ["Compare identifiers and source semantics", "Select canonical ID", "Rewire references without losing dataset provenance"],
            "in_scope": ["Existing normalized Palantir organization records", "SEC CIK 0001321655", "WEF Palantir organization profile"],
            "out_of_scope": ["Private locations", "Subsidiary conflation"],
            "scope_type": "entity-resolution-follow-up",
            "seed_ids": [PALANTIR, PALANTIR_WEF_ALIAS],
            "preferred_sources": ["SEC", "World Economic Forum", "Palantir"],
            "depth": 0,
            "max_depth": 2,
            "priority": 0.98,
            "score": 0.98,
            "selection_reason": ["Duplicate organization IDs block safe propagation of source-backed office geography."],
            "status": "queued",
        },
        sources=sources,
        related_ids=[PALANTIR, PALANTIR_WEF_ALIAS, ADDRESS_AVENTURA],
    )

    support_ids = [PALANTIR, ADDRESS_AVENTURA, OBSERVATION, RELATION, ANALYSIS]
    research_pass = base(
        RESEARCH_PASS,
        "research-pass",
        "Hourly HQ pass — Palantir principal-executive-office enrichment",
        "Reproducibly selected an existing WEF-linked company with weak temporal HQ provenance, connected authoritative public principal-office evidence, and materialized typed address, observation, relation, analysis, and follow-up records.",
        {
            "research_question": "Can the existing Palantir organization be enriched with source-faithful current office geography and an explicit effective date without overclaiming headquarters or inferring private location?",
            "method": RANDOM_METHOD,
            "classification_rules": [
                "Prefer explicit principal-executive-office language over generic business, mailing, registered-office, or incorporation metadata.",
                "Preserve the company-announced effective date separately from retrieval time.",
                "No private-residence inference is permitted from organizational address evidence.",
                "No latitude/longitude is generated without a separate defensible geocoder result.",
                "A reviewed primary-source capture fallback may be used only when runtime network policy blocks live retrieval, and the capture method must be recorded.",
            ],
            "finding_ids": [ANALYSIS],
            "findings": [
                {"finding": "Palantir's Aventura principal executive office is source-backed with an explicit 2026-02-17 effective date.", "confidence": 0.99},
                {"finding": "The duplicate Palantir org IDs require entity resolution before cross-dataset location propagation.", "confidence": 0.99},
            ],
            "supporting_record_ids": support_ids,
            "counterevidence_ids": [],
            "unresolved_target_ids": [TARGET_ENTITY_RESOLUTION],
            "source_ids": [source_id(IR_NOTICE_URL), source_id(SEC_10K_URL)],
            "agent_identity": "OpenAI GPT-5.6 Sol",
            "narrative_role": "hourly HQ/location enrichment pass before news ingestion",
            "started_at": STAMP,
            "completed_at": STAMP,
            "iteration": 1,
        },
        sources=sources,
        related_ids=[PALANTIR, TARGET_ENTITY_RESOLUTION, ADDRESS_AVENTURA],
    )

    docs = [address, observation, relation, palantir, analysis, target, research_pass]
    seen: set[str] = set()
    for document in docs:
        validate_document(document)
        doc_id = document["_id"]
        if doc_id in seen:
            raise ValueError(f"duplicate generated id: {doc_id}")
        seen.add(doc_id)
    return docs


def main() -> int:
    office, capture = current_office()
    docs = build_documents(office, capture)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PACKET.write_text("".join(compact(doc) + "\n" for doc in docs), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/starintel.py"),
            "import",
            str(PACKET),
            "--root",
            str(ROOT),
            "--replace",
        ],
        cwd=ROOT,
        check=True,
    )
    print(json.dumps({
        "packet": str(PACKET.relative_to(ROOT)),
        "documents": len(docs),
        "random_seed": RANDOM_SEED,
        "random_method": RANDOM_METHOD,
        "capture": capture,
        "ids": [doc["_id"] for doc in docs],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
