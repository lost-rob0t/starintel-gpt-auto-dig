#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, json, re, shutil, sys, unicodedata, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
ROSTER_DATE = "2025-01-10"
GENERATED_AT = "2026-07-31T06:15:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-membership-roster-2025")
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1bQKIP3W1NWChRjSbsE0O5k5s7OdgXrJi5-CMfFECIBU/gviz/tq?tqx=out:csv"
SHEET_VIEW = "https://docs.google.com/spreadsheets/d/1bQKIP3W1NWChRjSbsE0O5k5s7OdgXrJi5-CMfFECIBU/"
ARTICLE = "https://prospect.org/2025/01/10/2025-01-10-opening-dncs-black-box/"
PARTIES = "https://democrats.org/find-a-state-party/"
UA = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
GEO = dict(x.split("=", 1) for x in """AK=Alaska
AL=Alabama
AR=Arkansas
AS=American Samoa
AZ=Arizona
CA=California
CO=Colorado
CT=Connecticut
DA=Democrats Abroad
DC=District of Columbia
DE=Delaware
FL=Florida
GA=Georgia
GU=Guam
HI=Hawaii
IA=Iowa
ID=Idaho
IL=Illinois
IN=Indiana
KS=Kansas
KY=Kentucky
LA=Louisiana
MA=Massachusetts
MD=Maryland
ME=Maine
MI=Michigan
MN=Minnesota
MO=Missouri
MP=Northern Mariana Islands
MS=Mississippi
MT=Montana
NC=North Carolina
ND=North Dakota
NE=Nebraska
NH=New Hampshire
NJ=New Jersey
NM=New Mexico
NV=Nevada
NY=New York
OH=Ohio
OK=Oklahoma
OR=Oregon
PA=Pennsylvania
PR=Puerto Rico
RI=Rhode Island
SC=South Carolina
SD=South Dakota
TN=Tennessee
TX=Texas
UT=Utah
VA=Virginia
VI=U.S. Virgin Islands
VT=Vermont
WA=Washington
WI=Wisconsin
WV=West Virginia
WY=Wyoming""".splitlines())
STATE_TITLES = {"state chair", "state vice chair", "state-elected dnc member"}
CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9&./ +'()-]{0,79}$")
SHEET_SOURCE = "starintel:source:dnc-member-sheet-2025-01-10"
ARTICLE_SOURCE = "starintel:source:american-prospect-dnc-members-2025-01-10"
PARTY_SOURCE = "starintel:source:dnc-state-party-directory-2026-07-31"


def cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import a dated public DNC roster")
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--offline-csv", type=Path)
    p.add_argument("--generated-at", default=GENERATED_AT)
    return p.parse_args()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def slug(s: str) -> str:
    return norm(s).replace(" ", "-") or "unknown"


def rid(subject: str, predicate: str, obj: str, *parts: str) -> str:
    raw = "\x1f".join((subject, predicate, obj, *parts)).encode()
    return "starintel:relation:" + hashlib.sha256(raw).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res:
        data = res.read(10_000_001)
    if len(data) > 10_000_000:
        raise RuntimeError("roster source exceeds 10 MB")
    return data


def read_roster(ns: argparse.Namespace) -> tuple[bytes, list[tuple[str, str, str]]]:
    raw = ns.offline_csv.read_bytes() if ns.offline_csv else fetch(SHEET_CSV)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or not {"State", "Name", "Title"} <= set(reader.fieldnames):
        raise RuntimeError(f"unexpected columns: {reader.fieldnames!r}")
    rows, seen = [], set()
    for item in reader:
        row = (clean(item["State"]).upper(), clean(item["Name"]), clean(item["Title"]))
        if not all(row) or row in seen:
            continue
        if CODE_RE.fullmatch(row[0]) is None:
            raise RuntimeError(f"invalid affiliation code: {row[0]!r}")
        seen.add(row)
        rows.append(row)
    if not 440 <= len(rows) <= 470:
        raise RuntimeError(f"unexpected roster count: {len(rows)}")
    return raw, rows


def docs(root: Path, skip: Path) -> Iterable[dict[str, Any]]:
    skip = skip.resolve()
    for pattern in ("db/**/*.ndjson", "digs/**/*.jsonl"):
        for path in root.glob(pattern):
            try:
                path.resolve().relative_to(skip)
                continue
            except ValueError:
                pass
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def corpus_index(output: Path) -> tuple[set[str], dict[str, list[str]]]:
    ids, people = set(), defaultdict(list)
    for doc in docs(Path.cwd(), output):
        doc_id = str(doc.get("_id", ""))
        if doc_id:
            ids.add(doc_id)
        if doc.get("dtype") != "person" or not doc_id:
            continue
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        for value in (doc.get("title"), data.get("name"), data.get("full_name")):
            key = norm(str(value or ""))
            if key and doc_id not in people[key]:
                people[key].append(doc_id)
    return ids, people


def mk(doc_id: str, dtype: str, title: str, summary: str, data: dict[str, Any],
       when: str, sources: list[str], status: str, verified: bool, tags: list[str]) -> dict[str, Any]:
    return {"_id": doc_id, "data": data, "dataset": DATASET, "date_added": when,
            "date_updated": when, "dtype": dtype, "evidence": [],
            "handling": {"handling": "public-source-only", "pii": False,
                         "sensitive": False, "visibility": "public"},
            "schema_version": "0.9.0", "sources": [{"source_id": x} for x in sources],
            "status": "recorded", "summary": summary, "tags": tags, "title": title,
            "verification": {"last_reviewed_at": when, "status": status, "verified": verified},
            "version": 1}


def party_name(code: str) -> str:
    if code == "DA": return "Democrats Abroad"
    if code == "DC": return "District of Columbia Democratic Party"
    return f"{GEO[code]} Democratic Party"


def category_label(code: str) -> str:
    return "DNC national roster" if code == "DNC" else f"DNC historical roster category: {code}"


def source_docs(when: str) -> list[dict[str, Any]]:
    return [
        mk(ARTICLE_SOURCE, "source", "American Prospect DNC membership investigation",
           "Article publishing a previously nonpublic January 2025 roster of 449 names and reporting that 448 were voting members.",
           {"accessed_at": when, "credibility": 0.86, "kind": "investigative_report",
            "published_at": "2025-01-10T00:00:00Z", "publisher": "The American Prospect", "uri": ARTICLE},
           when, [], "source-backed", True, ["dnc", "membership", "source"]),
        mk(SHEET_SOURCE, "source", "Public January 2025 DNC member spreadsheet",
           "Public sheet containing a geographic or national-affiliation code, member name, and roster title; contact details are not imported.",
           {"accessed_at": when, "credibility": 0.78, "kind": "published_roster_snapshot",
            "published_at": "2025-01-10T00:00:00Z", "publisher": "The American Prospect", "uri": SHEET_VIEW},
           when, [ARTICLE_SOURCE], "source-backed", True, ["dnc", "membership", "source"]),
        mk(PARTY_SOURCE, "source", "Official DNC state-party directory",
           "Official directory for state and territorial Democratic Party organizations and Democrats Abroad.",
           {"accessed_at": when, "credibility": 0.99, "kind": "official_organization_directory",
            "publisher": "Democratic National Committee", "uri": PARTIES},
           when, [], "source-backed", True, ["dnc", "state-parties", "source"]),
    ]


def build(rows: list[tuple[str, str, str]], when: str, existing: set[str],
          people: dict[str, list[str]]) -> list[dict[str, Any]]:
    out, emitted = [], set()
    def emit(doc: dict[str, Any]) -> None:
        doc_id = doc["_id"]
        if doc_id in existing: return
        if doc_id in emitted: raise RuntimeError(f"duplicate generated ID: {doc_id}")
        validate_document(doc); emitted.add(doc_id); out.append(doc)

    for doc in source_docs(when): emit(doc)
    for code, jurisdiction in sorted(GEO.items()):
        org_id = f"starintel:org:dnc-state-party-{code.lower()}"
        emit(mk(org_id, "org", party_name(code),
                f"Democratic Party organization for {jurisdiction}, listed by the DNC.",
                {"jurisdiction": jurisdiction, "name": party_name(code),
                 "org_type": "democratic_party_affiliate" if code == "DA" else "state_party_committee"},
                when, [PARTY_SOURCE], "source-backed", True, ["dnc", "state-party", code.lower()]))
        emit(mk(rid(org_id, "affiliate_of", DNC_ID), "relation",
                f"{party_name(code)} is affiliated with the DNC",
                f"The official DNC directory lists the Democratic Party organization for {jurisdiction}.",
                {"confidence": 0.98, "directed": True, "object": DNC_ID,
                 "predicate": "affiliate_of", "subject": org_id},
                when, [PARTY_SOURCE], "source-backed", True, ["dnc", "state-party", "relation"]))

    category_ids = {}
    for code in sorted({x[0] for x in rows} - GEO.keys() - {"DNC"}):
        org_id = f"starintel:org:dnc-roster-affiliation-{slug(code)}"
        category_ids[code] = org_id
        emit(mk(org_id, "org", category_label(code),
                "Source-scoped category appearing in the January 2025 DNC roster; the code is preserved without external identity resolution.",
                {"name": category_label(code), "org_type": "historical_roster_affiliation_category"},
                when, [SHEET_SOURCE], "historical-roster-category-unresolved", False,
                ["dnc", "membership", "roster-category", slug(code)]))
        emit(mk(rid(org_id, "roster_category_of", DNC_ID, ROSTER_DATE), "relation",
                f"{category_label(code)} appears in the DNC roster",
                "The January 2025 roster uses this source-specific category code for DNC members.",
                {"confidence": 0.78, "directed": True, "object": DNC_ID,
                 "predicate": "roster_category_of",
                 "qualifiers": {"historical_snapshot": True, "raw_roster_code": code,
                                "snapshot_date": ROSTER_DATE}, "subject": org_id},
                when, [SHEET_SOURCE], "historical-roster-category-unresolved", False,
                ["dnc", "membership", "roster-category", "relation"]))

    for row_no, (code, name, title) in enumerate(rows, 2):
        matches = people.get(norm(name), [])
        if len(matches) == 1:
            person_id, resolution = matches[0], "resolved_exact_name_existing"
        else:
            person_id = f"starintel:person:dnc-roster-2025-{slug(f'{code}-{title}-{name}')}"
            resolution = "source_scoped_unresolved"
            label = GEO.get(code, category_label(code))
            pdata: dict[str, Any] = {"full_name": name, "name": name,
                "political_affiliations": ["Democratic Party"],
                "public_roles": [f"DNC roster: {title} (January 2025 snapshot)"]}
            if code in GEO: pdata["jurisdiction"] = label
            else: pdata["professional_affiliations"] = [label]
            emit(mk(person_id, "person", name,
                    f"Historical roster record: {name} was listed as {title} under {label} on January 10, 2025; current status is unresolved.",
                    pdata, when, [SHEET_SOURCE], "historical-roster-unresolved-current-status", False,
                    ["dnc", "member", "historical-roster", slug(code)]))

        label = GEO.get(code, category_label(code))
        emit(mk(rid(person_id, "member_of", DNC_ID, ROSTER_DATE, code, title), "relation",
                f"{name} listed as {title} on the January 2025 DNC roster",
                f"The published roster lists {name} under {code} as {title}; current status is unresolved.",
                {"confidence": 0.78, "directed": True, "object": DNC_ID, "predicate": "member_of",
                 "qualifiers": {"current_status": "unresolved", "historical_snapshot": True,
                    "identity_resolution": resolution, "roster_affiliation_code": code,
                    "roster_affiliation_label": label, "roster_row": row_no, "roster_title": title,
                    "snapshot_date": ROSTER_DATE,
                    "voting_status": "reported_non_voting_chair" if norm(name) == "jaime harrison" and norm(title) == "chair" else "reported_voting_member"},
                 "subject": person_id}, when, [SHEET_SOURCE, ARTICLE_SOURCE],
                "historical-roster-unresolved-current-status", False,
                ["dnc", "membership", "relation", "historical-roster"]))

        if code in GEO and norm(title) in STATE_TITLES:
            org_id = f"starintel:org:dnc-state-party-{code.lower()}"
            emit(mk(rid(person_id, "representative_of", org_id, ROSTER_DATE, title), "relation",
                    f"{name} listed as a representative of {party_name(code)}",
                    f"The January 2025 roster lists {name} as {title} for {GEO[code]}; current status is unresolved.",
                    {"confidence": 0.76, "directed": True, "object": org_id,
                     "predicate": "representative_of",
                     "qualifiers": {"current_status": "unresolved", "historical_snapshot": True,
                                    "roster_title": title, "snapshot_date": ROSTER_DATE},
                     "subject": person_id}, when, [SHEET_SOURCE],
                    "historical-roster-unresolved-current-status", False,
                    ["dnc", "state-party", "representation", "historical-roster"]))
        elif code in category_ids:
            org_id = category_ids[code]
            emit(mk(rid(person_id, "listed_under_roster_category", org_id, ROSTER_DATE, title), "relation",
                    f"{name} listed under {category_label(code)}",
                    "The January 2025 roster places this person under a source-specific national or affiliate category.",
                    {"confidence": 0.78, "directed": True, "object": org_id,
                     "predicate": "listed_under_roster_category",
                     "qualifiers": {"current_status": "unresolved", "historical_snapshot": True,
                                    "raw_roster_code": code, "roster_title": title,
                                    "snapshot_date": ROSTER_DATE}, "subject": person_id},
                    when, [SHEET_SOURCE], "historical-roster-unresolved-current-status", False,
                    ["dnc", "membership", "roster-category", "relation"]))
    return sorted(out, key=lambda x: x["_id"])


def write(output: Path, raw: bytes, rows: list[tuple[str, str, str]],
          documents: list[dict[str, Any]], when: str) -> None:
    if output.exists(): shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    buf = io.StringIO(); csv.writer(buf, lineterminator="\n").writerows([("State", "Name", "Title"), *rows])
    csv_data = buf.getvalue().encode()
    (output / "source/dnc-member-list-2025-01-10.csv").write_bytes(csv_data)
    jsonl = "".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in documents).encode()
    (output / "starintel-documents.jsonl").write_bytes(jsonl)
    counts, codes = Counter(x["dtype"] for x in documents), sorted({x[0] for x in rows})
    manifest = {"counts": dict(sorted(counts.items())), "dataset": DATASET,
        "document_sha256": hashlib.sha256(jsonl).hexdigest(), "generated_at": when,
        "handling": {"current_status": "unresolved", "historical_snapshot": True,
                     "identity_resolution": "unique exact-name match or source-scoped unresolved person"},
        "roster_affiliation_codes": codes, "roster_date": ROSTER_DATE, "roster_rows": len(rows),
        "schema_version": "0.9.0", "source_csv_sha256": hashlib.sha256(csv_data).hexdigest(),
        "source_download_sha256": hashlib.sha256(raw).hexdigest(), "total_documents": len(documents)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (output / "README.md").write_text(f"""# DNC membership roster — January 2025 historical snapshot

Imports the public spreadsheet published with *The American Prospect* on January 10, 2025.

- roster rows: {len(rows):,}
- StarIntel documents: {len(documents):,}
- people: {counts.get('person', 0):,}
- organizations: {counts.get('org', 0):,}
- relations: {counts.get('relation', 0):,}
- sources: {counts.get('source', 0):,}
- roster affiliation codes: {len(codes):,}

This is a dated historical roster, not a claim that every person remains a DNC member. Geographic delegations are linked to official state-party organizations. National and affiliate codes are preserved as source-scoped roster categories unless independently resolved. No phone numbers or email addresses are imported.

```bash
python3 scripts/import_dnc_membership_roster.py
python3 scripts/validate-for-merge.py --site
```
""")


def main() -> int:
    ns = cli(); raw, rows = read_roster(ns); existing, people = corpus_index(ns.output)
    if DNC_ID not in existing: raise RuntimeError(f"missing required organization: {DNC_ID}")
    documents = build(rows, ns.generated_at, existing, people)
    write(ns.output, raw, rows, documents, ns.generated_at)
    print(json.dumps({"documents": len(documents), "output": str(ns.output), "roster_rows": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
