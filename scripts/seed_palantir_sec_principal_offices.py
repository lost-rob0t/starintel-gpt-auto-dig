#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import compact
from starintel_doc.validation import validate_document

import sec_principal_office_history as sec_offices


SCHEMA = "0.9.0"
DATASET = "palantir-deep-dive-2026-07-25"
RUN_ID = "hourly-hq-palantir-sec-principal-offices-2026-08-17"
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

ADDRESS_DENVER_1200 = "starintel:address:palantir-principal-office-1200-17th-denver"
ADDRESS_DENVER_518 = "starintel:address:palantir-principal-office-518-17th-denver"
ADDRESS_AVENTURA = "starintel:address:palantir-principal-office-19505-biscayne-aventura"
TARGET_ENTITY_RESOLUTION = "starintel:investigation-target:palantir-org-id-resolution"
ANALYSIS = "starintel:analysis:palantir-sec-principal-office-history-2026-08-17"
RESEARCH_PASS = "starintel:research-pass:palantir-sec-principal-office-history-2026-08-17"

FILINGS = [
    {
        "form": "8-K",
        "filing_date": "2025-11-03",
        "accession": "0001321655-25-000130",
        "url": "https://www.sec.gov/Archives/edgar/data/1321655/000132165525000130/pltr-20251103.htm",
    },
    {
        "form": "8-K",
        "filing_date": "2026-02-02",
        "accession": "0001321655-26-000004",
        "url": "https://www.sec.gov/Archives/edgar/data/1321655/000132165526000004/pltr-20260202.htm",
    },
    {
        "form": "10-K",
        "filing_date": "2026-02-17",
        "accession": "0001321655-26-000011",
        "url": "https://www.sec.gov/Archives/edgar/data/1321655/000132165526000011/pltr-20251231.htm",
    },
    {
        "form": "8-K",
        "filing_date": "2026-06-09",
        "accession": "0001321655-26-000033",
        "url": "https://www.sec.gov/Archives/edgar/data/1321655/000132165526000033/pltr-20260603.htm",
    },
]


def source_ref(filing: dict[str, str]) -> dict[str, Any]:
    url = filing["url"]
    return {
        "source_id": f"sha256:{hashlib.sha256(url.encode()).hexdigest()}",
        "kind": "regulatory_filing",
        "title": f"Palantir Technologies Inc. {filing['form']} filed {filing['filing_date']}",
        "publisher": "U.S. Securities and Exchange Commission",
        "uri": url,
        "url": url,
        "retrieved_at": STAMP,
        "credibility": 0.99,
        "metadata": {
            "accession": filing["accession"],
            "form": filing["form"],
            "filing_date": filing["filing_date"],
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
            "verified_by": ["SEC filing cover-page review"],
            "verified_at": STAMP,
            "last_reviewed_at": STAMP,
            "methods": ["SEC filing cover-page extraction", "StarIntel schema validation"],
        },
        "handling": {"visibility": "public", "sensitive": False, "pii": False},
        "provenance": {
            "collector": "OpenAI GPT-5.6 Sol",
            "collector_type": "research-agent",
            "method": "SEC principal-executive-office extraction",
            "pipeline": "starintel-auto-dig",
            "run_id": RUN_ID,
        },
    }


def address_id(office: dict[str, str]) -> str:
    address = office["address"].casefold()
    if "1200 17th street" in address:
        return ADDRESS_DENVER_1200
    if "518 17th street" in address:
        return ADDRESS_DENVER_518
    if "19505 biscayne" in address:
        return ADDRESS_AVENTURA
    digest = hashlib.sha256(address.encode()).hexdigest()[:16]
    return f"starintel:address:palantir-sec-principal-office-{digest}"


def fetch_observations() -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for filing in FILINGS:
        raw = sec_offices.fetch_text(filing["url"])
        office = sec_offices.extract_principal_executive_office(raw)
        item = sec_offices.office_observation(
            org_id=PALANTIR,
            office=office,
            form=filing["form"],
            filing_date=filing["filing_date"],
            accession=filing["accession"],
            filing_url=filing["url"],
            retrieved_at=STAMP,
        )
        item["value"]["address_id"] = address_id(office)
        observations.append(item)
    return observations


def load_palantir() -> dict[str, Any]:
    lines = [line for line in PALANTIR_DB.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{PALANTIR_DB}: expected one normalized record")
    doc = json.loads(lines[0])
    if doc.get("_id") != PALANTIR or doc.get("dtype") != "org":
        raise ValueError("unexpected Palantir normalized record identity")
    return doc


def build_documents(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filing_by_url = {filing["url"]: filing for filing in FILINGS}
    sources = [source_ref(filing) for filing in FILINGS]
    unique_offices: dict[str, dict[str, str]] = {}
    for item in observations:
        value = item["value"]
        unique_offices[value["address_id"]] = {
            "address": value["address"],
            "street": value["street"],
            "city": value["city"],
            "region": value["region"],
            "postal": value["postal"],
            "country": value["country"],
        }

    docs: list[dict[str, Any]] = []
    for location_id, office in sorted(unique_offices.items()):
        docs.append(base(
            location_id,
            "address",
            f"Palantir SEC-reported principal executive office: {office['city']}, {office['region']}",
            "A public organizational address reported by Palantir on an SEC filing cover page as an address of principal executive offices; this does not encode a private residence or an inferred move date.",
            {
                "name": f"Palantir principal executive office — {office['city']}",
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
        ))

    for item in observations:
        value = item["value"]
        filing = filing_by_url[value["filing_url"]]
        slug = filing["accession"].replace("-", "")
        docs.append(base(
            f"starintel:observation:palantir-principal-office-{slug}",
            "observation",
            f"Palantir principal executive office reported in {filing['form']} filed {filing['filing_date']}",
            f"Palantir's SEC filing cover page reports {value['address']} as its address of principal executive offices.",
            item,
            sources=[source_ref(filing)],
            related_ids=[PALANTIR, value["address_id"]],
        ))
        docs.append(base(
            f"starintel:relation:palantir-principal-office-{slug}",
            "relation",
            f"Palantir SEC-reported principal executive office — {filing['filing_date']}",
            "Source-bounded relation between Palantir and the address explicitly labeled on the filing cover page; filing date is an observation boundary, not an inferred physical move date.",
            {
                "subject": PALANTIR,
                "predicate": "sec_reported_principal_executive_office",
                "object": value["address_id"],
                "qualifiers": {
                    "filing_date": filing["filing_date"],
                    "form": filing["form"],
                    "accession": filing["accession"],
                    "source_semantics": "Address of principal executive offices",
                },
                "confidence": 0.99,
                "note": "No physical move date is inferred from the filing date.",
            },
            sources=[source_ref(filing)],
            related_ids=[PALANTIR, value["address_id"]],
        ))

    palantir = deepcopy(load_palantir())
    palantir["version"] = max(int(palantir.get("version", 1)) + 1, 2)
    palantir["date_updated"] = STAMP
    palantir.setdefault("data", {})["location_ids"] = sorted(unique_offices)
    palantir["sources"] = list({source.get("url") or source.get("uri"): source for source in [*palantir.get("sources", []), *sources]}.values())
    palantir["related_ids"] = sorted(set([*palantir.get("related_ids", []), *unique_offices]))
    palantir["notes"] = [
        *palantir.get("notes", []),
        "SEC cover-page addresses are separately modeled as principal_executive_office address records. Filing dates are evidence dates, not assumed physical move dates.",
    ]
    palantir["verification"] = {
        "status": "source-backed",
        "verified": True,
        "verified_by": ["SEC filing cover pages"],
        "verified_at": STAMP,
        "last_reviewed_at": STAMP,
        "methods": ["primary regulatory filing review", "canonical StarIntel validation"],
    }
    palantir["provenance"] = {
        **palantir.get("provenance", {}),
        "collector": "OpenAI GPT-5.6 Sol",
        "collector_type": "research-agent",
        "method": "intentional v2 enrichment from SEC principal-executive-office filings",
        "pipeline": "starintel-auto-dig",
        "run_id": RUN_ID,
    }
    docs.append(palantir)

    docs.append(base(
        ANALYSIS,
        "analysis",
        "Palantir SEC principal-executive-office history",
        "SEC cover pages establish three successive public organizational principal-executive-office addresses across late 2025 and 2026 without supplying exact physical relocation dates.",
        {
            "question": "What public organizational office chronology can be defensibly attached to the existing Palantir record from primary SEC filings?",
            "method": "Extract only addresses explicitly labeled 'Address of principal executive offices' on primary SEC filing cover pages; preserve filing date separately from physical validity.",
            "scope": "Palantir Technologies Inc. SEC cover-page principal-executive-office addresses from November 2025 through June 2026.",
            "findings": [
                "An 8-K filed 2025-11-03 reports 1200 17th Street, Floor 15, Denver, Colorado 80202.",
                "An 8-K filed 2026-02-02 reports 518 17th Street, Suite 1015, Denver, Colorado 80202 and separately identifies the 1200 17th Street address as former.",
                "The 10-K filed 2026-02-17 reports 19505 Biscayne Blvd., Suite 2350, Aventura, Florida 33180 and separately shows 518 17th Street as a former address.",
                "An 8-K filed 2026-06-09 again reports the Aventura address, corroborating it after the 10-K.",
            ],
            "conclusions": [
                "The current normalized Palantir organization can be linked to three source-bounded principal-executive-office address records.",
                "The filings support an ordered reported-address chronology but not exact physical move timestamps.",
            ],
            "recommendations": ["Resolve the duplicate Palantir organization IDs before propagating location links across WEF-facing records."],
            "counterarguments": ["SEC business/mailing address metadata alone is not used here as proof of headquarters; only filing cover text explicitly labeling principal executive offices is promoted."],
            "limitations": ["No geocoding was performed; precise coordinates would add no evidentiary value to this address-history slice."],
            "unresolved": ["Canonical identity resolution between starintel:org:palantir-technologies-inc and starintel:org:palantir-technologies."],
            "confidence": 0.99,
        },
        sources=sources,
        related_ids=[PALANTIR, PALANTIR_WEF_ALIAS, *sorted(unique_offices)],
    ))

    docs.append(base(
        TARGET_ENTITY_RESOLUTION,
        "investigation-target",
        "Resolve duplicate Palantir organization IDs",
        "The normalized corpus contains both a regulatory/company record and a WEF-facing Palantir organization record; resolve canonical identity before cross-dataset location propagation.",
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
            "selection_reason": ["Duplicate organization IDs block safe propagation of source-backed office history."],
            "status": "queued",
        },
        sources=sources,
        related_ids=[PALANTIR, PALANTIR_WEF_ALIAS],
    ))

    finding_ids = [ANALYSIS]
    supporting = [PALANTIR, *[doc["_id"] for doc in docs if doc["dtype"] in {"address", "observation", "relation"}]]
    docs.append(base(
        RESEARCH_PASS,
        "research-pass",
        "Hourly HQ pass — Palantir SEC principal-executive-office history",
        "Reproducibly selected an existing WEF-linked organization with weak temporal HQ provenance, connected primary SEC cover-page evidence, and materialized typed address, observation, relation, analysis, and follow-up records.",
        {
            "research_question": "Can the existing Palantir organization be enriched with source-faithful temporal office geography without inferring headquarters or move dates beyond the filings?",
            "method": RANDOM_METHOD,
            "classification_rules": [
                "Only text explicitly labeled as an address of principal executive offices is promoted into this office-history graph.",
                "SEC business/mailing metadata is not silently reclassified as headquarters.",
                "Filing dates are evidence/observation boundaries, not physical move dates.",
                "No coordinates are generated without a separate defensible geocoder result.",
            ],
            "finding_ids": finding_ids,
            "findings": [
                {"finding": "Three distinct principal-executive-office addresses are directly supported from late 2025 through mid-2026.", "confidence": 0.99},
                {"finding": "The duplicate Palantir org IDs require entity resolution before cross-dataset propagation.", "confidence": 0.99},
            ],
            "supporting_record_ids": supporting,
            "counterevidence_ids": [],
            "unresolved_target_ids": [TARGET_ENTITY_RESOLUTION],
            "source_ids": [source["source_id"] for source in sources],
            "agent_identity": "OpenAI GPT-5.6 Sol",
            "narrative_role": "hourly HQ/location enrichment pass before news ingestion",
            "started_at": STAMP,
            "completed_at": STAMP,
            "iteration": 1,
        },
        sources=sources,
        related_ids=[PALANTIR, TARGET_ENTITY_RESOLUTION],
    ))

    seen: set[str] = set()
    for document in docs:
        validate_document(document)
        doc_id = document["_id"]
        if doc_id in seen:
            raise ValueError(f"duplicate generated id: {doc_id}")
        seen.add(doc_id)
    return docs


def main() -> int:
    observations = fetch_observations()
    docs = build_documents(observations)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PACKET.write_text("".join(compact(doc) + "\n" for doc in docs), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/starintel.py"), "import", str(PACKET), "--root", str(ROOT), "--replace"],
        cwd=ROOT,
        check=True,
    )
    print(json.dumps({
        "packet": str(PACKET.relative_to(ROOT)),
        "documents": len(docs),
        "random_seed": RANDOM_SEED,
        "random_method": RANDOM_METHOD,
        "ids": [doc["_id"] for doc in docs],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
