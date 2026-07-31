#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "0.9.0"
DATASET = "wef"
WEF = "starintel:org:world-economic-forum"
RUN = "wef-annual-meeting-partners-2015-2026"
STAMP = "2026-07-31T05:21:00Z"
PACKET = Path("digs/wef/2026-07-31-annual-meeting-partners-2015-2026")
ROSTER_SHA256 = "8eed599b3abd85e8308e2dc69554f5a012baef1b279c324ee019555f715f08a4"
ROSTER_GZIP_BASE64 = """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"""
ALIASES = {
    "aig": ("american international group",),
    "bny": ("bank of new york mellon", "the bank of new york mellon"),
    "cd and r": ("clayton dubilier and rice",),
    "ey": ("ernst and young",),
    "ge": ("general electric",),
    "hp": ("hp inc", "hewlett packard"),
    "jll": ("jones lang lasalle",),
    "jpmorganchase": ("jpmorgan chase",),
    "meta": ("meta platforms",),
    "msd": ("merck", "merck and co"),
    "pwc": ("pricewaterhousecoopers",),
    "wtw": ("willis towers watson",),
}
SUFFIXES = {
    "co", "company", "corp", "corporation", "group", "holding", "holdings",
    "inc", "incorporated", "international", "llc", "limited", "ltd", "plc",
    "technologies", "technology",
}


def compact(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold().replace("&", " and ")))


def legal(value: str) -> str:
    parts = norm(value).split()
    while parts and parts[-1] in SUFFIXES:
        parts.pop()
    return " ".join(parts)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(value)).strip("-")


def one(path: Path) -> dict[str, Any]:
    lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(lines) != 1:
        raise ValueError(f"{path}: expected one NDJSON record")
    value = json.loads(lines[0])
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def endpoint(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "entity_id", "document_id"):
            if isinstance(value.get(key), str):
                return value[key]
    return None


def embedded_roster(path: Path) -> dict[str, Any]:
    raw = gzip.decompress(base64.b64decode(ROSTER_GZIP_BASE64)).decode()
    if hashlib.sha256(raw.encode()).hexdigest() != ROSTER_SHA256:
        raise ValueError("embedded roster digest mismatch")
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current != raw:
        path.write_text(raw, encoding="utf-8")
    return json.loads(raw)


def source(year: int, meta: dict[str, Any]) -> dict[str, Any]:
    url = str(meta["source_url"])
    return {
        "source_id": f"sha256:{hashlib.sha256(url.encode()).hexdigest()}",
        "kind": "official_partner_roster",
        "title": str(meta["source_title"]),
        "publisher": "World Economic Forum",
        "uri": url,
        "url": url,
        "retrieved_at": STAMP,
        "credibility": 0.99,
        "metadata": {
            "meeting_year": year,
            "coverage_status": str(meta["coverage_status"]),
            "partner_count": int(meta["partner_count"]),
        },
    }


def base(doc_id: str, dtype: str, title: str, summary: str, data: dict[str, Any],
         sources: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "_id": doc_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA,
        "version": 1,
        "date_added": STAMP,
        "date_updated": STAMP,
        "title": title,
        "summary": summary,
        "status": "recorded",
        "language": "en",
        "sources": sources,
        "evidence": evidence,
        "data": data,
        "provenance": {
            "collector": "ChatGPT",
            "collector_type": "research-agent",
            "agent": "GPT-5.6 Thinking",
            "skill": "web-research;create-starintel-documents",
            "tool": "World Economic Forum official meeting archive",
            "run_id": RUN,
            "method": "official roster extraction and canonical-ID reconciliation",
            "created_by": "ChatGPT",
        },
        "handling": {"visibility": "public", "handling": "public-source-only", "pii": False, "sensitive": False},
        "quality": {"validation_status": "pending_repository_validation", "validator": "scripts/starintel.py validate", "warnings": []},
        "workflow": {
            "research_status": "completed",
            "queue": "wef-auto-dig",
            "priority": 0.95,
            "run_id": RUN,
            "recursion_depth": 0,
            "max_depth": 1,
            "root_target_id": "starintel:research-pass:wef-annual-meeting-partners-2015-2026",
        },
    }


def org_doc(name: str, doc_id: str, appearances: list[tuple[int, dict[str, Any]]]) -> dict[str, Any]:
    sources = [source(year, meta) for year, meta in appearances]
    year, meta = appearances[0]
    value = base(
        doc_id, "org", name,
        "Organization listed by WEF as an Annual Meeting partner in at least one exposed yearly roster from 2015 through 2026.",
        {"name": name, "display_name": name, "org_type": "organization"},
        sources,
        [{
            "source_id": sources[0]["source_id"],
            "source_url": meta["source_url"],
            "kind": "documented_observation",
            "role": "supports",
            "observation": f"The official WEF Annual Meeting {year} page lists {name} under Partners.",
            "collected_at": STAMP,
            "confidence": 0.99,
            "status": "verified",
        }],
    )
    value.update({
        "assessment": {"confidence": 0.99, "source_reliability": 0.99, "information_credibility": 0.99},
        "verification": {"status": "confirmed", "verified": True, "verified_by": ["official WEF roster review"], "verified_at": STAMP, "methods": ["official-page extraction", "cross-year label normalization"]},
        "tags": ["wef", "annual-meeting", "partner-organization"],
        "related_ids": [WEF],
    })
    return value


def relation_doc(name: str, subject: str, year: int, meta: dict[str, Any]) -> dict[str, Any]:
    src = source(year, meta)
    value = base(
        f"starintel:relation:wef-annual-meeting-{year}:{slug(name)}",
        "relation",
        f"{name} was listed as a WEF Annual Meeting {year} partner",
        f"The official WEF Annual Meeting {year} roster lists {name} as a partner.",
        {
            "subject": subject,
            "predicate": "partner",
            "object": WEF,
            "directed": True,
            "confidence": 0.99,
            "qualifiers": {
                "meeting": "World Economic Forum Annual Meeting",
                "year": year,
                "roster_label": name,
                "source_url": meta["source_url"],
                "coverage_status": meta["coverage_status"],
            },
        },
        [src],
        [{
            "source_id": src["source_id"],
            "source_url": meta["source_url"],
            "kind": "documented_observation",
            "role": "supports",
            "observation": f"The official WEF Annual Meeting {year} partner roster lists {name}.",
            "collected_at": STAMP,
            "confidence": 0.99,
            "status": "verified",
        }],
    )
    value.update({
        "assessment": {"confidence": 0.99, "source_reliability": 0.99, "information_credibility": 0.99},
        "verification": {"status": "confirmed", "verified": True, "verified_by": ["official WEF roster review"], "verified_at": STAMP, "methods": ["official-page extraction"]},
        "tags": ["wef", "annual-meeting", "partner", str(year)],
        "related_ids": [subject, WEF],
    })
    return value


def coverage_doc(roster: dict[str, Any], relation_ids: list[str]) -> dict[str, Any]:
    findings, sources, evidence, gaps = [], [], [], []
    for year_text, meta in roster["years"].items():
        year = int(year_text)
        sources.append(source(year, meta))
        findings.append({
            "year": year,
            "partner_count": int(meta["partner_count"]),
            "coverage_status": str(meta["coverage_status"]),
            "source_url": str(meta["source_url"]),
            "notes": str(meta["notes"]),
        })
        evidence.append({
            "source_url": meta["source_url"],
            "kind": "archive_coverage_observation",
            "role": "supports",
            "observation": f"Current official archive exposure for {year}: {meta['partner_count']} partner entries ({meta['coverage_status']}).",
            "collected_at": STAMP,
            "confidence": 0.99,
            "status": "verified",
            "metadata": {"year": year, "partner_count": int(meta["partner_count"])},
        })
        if meta["coverage_status"] not in ("roster_exposed", "roster_exposed_on_about_page"):
            gaps.append(f"{year}: {meta['coverage_status']}")
    value = base(
        "starintel:research-pass:wef-annual-meeting-partners-2015-2026",
        "research-pass",
        "WEF Annual Meeting partner roster import, 2015–2026",
        "Imported every partner entry exposed by the current official WEF archive while preserving empty, unavailable, and partial years as gaps.",
        {
            "research_question": "Which organizations are listed as partners for each archived WEF Annual Meeting year from 2015 through 2026?",
            "method": "Extract official WEF rosters, normalize exact label variants, reconcile canonical organization IDs, and emit one year-specific partner relation per observation.",
            "classification_rules": [
                "A listing supports partner status for that meeting year only.",
                "Repeated yearly listings remain separate observations.",
                "Empty or unavailable routes are gaps, not zero-partner claims.",
                "The visibly short 2016 page is partial.",
            ],
            "finding_ids": relation_ids,
            "findings": findings,
            "supporting_record_ids": relation_ids,
            "counterevidence_ids": [],
            "unresolved_target_ids": [],
            "source_ids": [entry["source_id"] for entry in sources],
            "agent_identity": "GPT-5.6 Thinking",
            "narrative_role": "bounded historical roster import",
            "started_at": STAMP,
            "completed_at": STAMP,
            "iteration": 1,
        },
        sources,
        evidence,
    )
    value.update({
        "assessment": {"confidence": 0.99, "source_reliability": 0.99, "information_credibility": 0.99, "completeness": 0.75, "gaps": gaps},
        "verification": {"status": "source-backed-with-archive-gaps", "verified": True, "verified_by": ["official WEF archive review"], "verified_at": STAMP, "methods": ["official-page extraction", "count reconciliation"], "unresolved": gaps},
        "tags": ["wef", "annual-meeting", "partners", "historical-roster", "import"],
        "related_ids": [WEF, *relation_ids],
    })
    value["quality"]["warnings"] = gaps
    return value


def indexes(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
    names: dict[str, set[str]] = defaultdict(set)
    legal_names: dict[str, set[str]] = defaultdict(set)
    ids: set[str] = set()
    for path in sorted((root / "db" / "org").glob("*.ndjson")):
        doc = one(path)
        doc_id = str(doc["_id"])
        ids.add(doc_id)
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        values = [data.get(k) for k in ("name", "display_name", "legal_name", "short_name")]
        values += [doc.get("title")]
        values += doc.get("aliases", []) if isinstance(doc.get("aliases"), list) else []
        for value in values:
            if isinstance(value, str) and value.strip():
                names[norm(value)].add(doc_id)
                if legal(value):
                    legal_names[legal(value)].add(doc_id)
    return names, legal_names, ids


def unique(index: dict[str, set[str]], key: str) -> str | None:
    values = index.get(key, set())
    return next(iter(values)) if len(values) == 1 else None


def resolve(name: str, names: dict[str, set[str]], legal_names: dict[str, set[str]]) -> tuple[str | None, str]:
    key = norm(name)
    match = unique(names, key)
    if match:
        return match, "exact_name"
    for alias in ALIASES.get(key, ()):
        match = unique(names, alias) or unique(legal_names, alias)
        if match:
            return match, "explicit_alias"
    match = unique(legal_names, legal(name)) if legal(name) else None
    return (match, "unique_legal_name") if match else (None, "new_org")


def existing_relations(root: Path) -> tuple[set[tuple[str, int]], set[str]]:
    keys, ids = set(), set()
    for path in sorted((root / "db" / "relation").glob("*.ndjson")):
        doc = one(path)
        if isinstance(doc.get("_id"), str):
            ids.add(doc["_id"])
        data = doc.get("data")
        if not isinstance(data, dict) or data.get("predicate") != "partner" or endpoint(data.get("object")) != WEF:
            continue
        q = data.get("qualifiers")
        subject = endpoint(data.get("subject"))
        year = q.get("year") if isinstance(q, dict) else None
        if isinstance(year, str) and year.isdigit():
            year = int(year)
        if subject and isinstance(year, int):
            keys.add((subject, year))
    return keys, ids


def canonical(roster: dict[str, Any]) -> tuple[dict[int, list[str]], dict[str, list[tuple[int, dict[str, Any]]]]]:
    replacements = {str(k): str(v) for k, v in roster["normalization"].items()}
    per_year, appearances = {}, defaultdict(list)
    for year_text, meta in roster["years"].items():
        year = int(year_text)
        values = list(dict.fromkeys(replacements.get(str(x), str(x)).strip() for x in meta["partners"] if str(x).strip()))
        if len(values) != int(meta["partner_count"]):
            raise ValueError(f"{year}: normalized count mismatch")
        per_year[year] = values
        for name in values:
            appearances[name].append((year, meta))
    if sum(map(len, per_year.values())) != int(roster["expected_partner_observations"]):
        raise ValueError("partner observation count mismatch")
    if len(appearances) != int(roster["expected_unique_normalized_partners"]):
        raise ValueError("unique partner count mismatch")
    return per_year, appearances


def write_jsonl(path: Path, docs: list[dict[str, Any]]) -> str:
    payload = "".join(compact(doc) + "\n" for doc in docs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--no-import", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    roster_path = root / PACKET / "partners-by-year.json"
    roster = embedded_roster(roster_path)
    if roster["canonical_wef_id"] != WEF:
        raise ValueError("roster target mismatch")
    wef_path = root / "db" / "org" / f"{WEF}.ndjson"
    if not wef_path.exists() or one(wef_path).get("_id") != WEF:
        raise FileNotFoundError("canonical WEF organization missing")

    per_year, appearances = canonical(roster)
    name_index, legal_index, existing_org_ids = indexes(root)
    reserved, resolution, org_docs = set(), {}, []
    for name in sorted(appearances):
        doc_id, method = resolve(name, name_index, legal_index)
        if not doc_id:
            base_id = f"starintel:org:{slug(name)}"
            doc_id = base_id
            if doc_id in existing_org_ids or doc_id in reserved:
                doc_id = f"{base_id}-{hashlib.sha256(name.encode()).hexdigest()[:8]}"
            reserved.add(doc_id)
            org_docs.append(org_doc(name, doc_id, appearances[name]))
        resolution[name] = {"id": doc_id, "method": method}

    existing_keys, existing_ids = existing_relations(root)
    relations, skipped, collisions = [], 0, []
    for year in sorted(per_year):
        meta = roster["years"][str(year)]
        for name in per_year[year]:
            subject = resolution[name]["id"]
            candidate = relation_doc(name, subject, year, meta)
            if (subject, year) in existing_keys:
                skipped += 1
            elif candidate["_id"] in existing_ids:
                collisions.append(candidate["_id"])
            else:
                relations.append(candidate)
                existing_keys.add((subject, year))
                existing_ids.add(candidate["_id"])

    coverage_path = root / "db" / "research-pass" / "starintel:research-pass:wef-annual-meeting-partners-2015-2026.ndjson"
    coverage = [] if coverage_path.exists() else [coverage_doc(roster, [x["_id"] for x in relations])]
    docs = [*org_docs, *relations, *coverage]

    sys.path.insert(0, str(root))
    from starintel_doc.validation import validate_document
    for doc in docs:
        validate_document(doc)

    output = root / PACKET / "starintel-documents.jsonl"
    digest = write_jsonl(output, docs)
    counts = Counter(x["dtype"] for x in docs)
    methods = Counter(x["method"] for x in resolution.values())
    report = {
        "dataset": DATASET,
        "schema_version": SCHEMA,
        "canonical_wef_id": WEF,
        "source_partner_observations": sum(map(len, per_year.values())),
        "normalized_partner_names": len(appearances),
        "created_org_documents": len(org_docs),
        "reused_org_documents": len(appearances) - len(org_docs),
        "organization_resolution_methods": dict(sorted(methods.items())),
        "created_relation_documents": len(relations),
        "existing_relation_observations": skipped,
        "relation_id_collisions": collisions,
        "packet_documents": len(docs),
        "counts_by_dtype": dict(sorted(counts.items())),
        "packet_sha256": digest,
        "import_executed": not args.no_import,
        "coverage_by_year": {
            year: {"partner_count": int(meta["partner_count"]), "coverage_status": meta["coverage_status"], "source_url": meta["source_url"]}
            for year, meta in roster["years"].items()
        },
    }
    report_path = root / "reports" / "wef-annual-meeting-partners-import.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = "\n".join(f"| {y} | {v['partner_count']} | {v['coverage_status']} |" for y, v in report["coverage_by_year"].items())
    (root / PACKET / "README.md").write_text(
        f"""# WEF Annual Meeting partners, 2015–2026

Canonical WEF node: `{WEF}`

- Source observations: **{report['source_partner_observations']}**
- Normalized partner names: **{report['normalized_partner_names']}**
- New organizations: **{report['created_org_documents']}**
- Reused organizations: **{report['reused_org_documents']}**
- New yearly `partner` relations: **{report['created_relation_documents']}**
- Existing yearly relations skipped: **{report['existing_relation_observations']}**
- Packet SHA-256: `{digest}`

| Year | Entries | Current archive status |
|---:|---:|---|
{rows}

Empty, unavailable, and visibly partial routes are coverage gaps, not zero-partner claims.
""",
        encoding="utf-8",
    )
    (root / PACKET / "manifest.json").write_text(json.dumps({
        "dataset": DATASET,
        "schema_version": SCHEMA,
        "canonical_wef_id": WEF,
        "record_count": len(docs),
        "counts_by_dtype": dict(sorted(counts.items())),
        "hash_algorithm": "sha256",
        "content_hash": digest,
        "generated_at": STAMP,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.with_suffix(".md").write_text(
        f"# WEF Annual Meeting partner import\n\n"
        f"- Canonical WEF ID: `{WEF}`\n"
        f"- Source observations: {report['source_partner_observations']}\n"
        f"- Normalized partners: {report['normalized_partner_names']}\n"
        f"- New organizations: {report['created_org_documents']}\n"
        f"- New relations: {report['created_relation_documents']}\n"
        f"- Packet documents: {report['packet_documents']}\n"
        f"- Packet SHA-256: `{digest}`\n",
        encoding="utf-8",
    )

    if not args.no_import:
        subprocess.run([sys.executable, str(root / "scripts" / "starintel.py"), "import", str(output), "--root", str(root)], check=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
