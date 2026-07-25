from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.open.fec.gov/v1"
API_KEY = os.environ.get("FEC_API_KEY", "DEMO_KEY")
OUT = Path(os.environ.get(
    "FEC_OUTPUT",
    "digs/larry-fink/2026-07-25-fec-personal-ledger",
))
CYCLES = list(range(1980, 2028, 2))
NAME_QUERIES = [
    "FINK, LAURENCE",
    "FINK, LAURENCE D",
    "FINK, LARRY",
    "LAURENCE FINK",
    "LAURENCE D FINK",
    "LARRY FINK",
]
EXECUTIVE_TERMS = (
    "CHAIR", "CEO", "CHIEF EXECUTIVE", "EXECUTIVE", "INVESTMENT",
    "MANAGING DIRECTOR", "FINANCE", "ASSET MANAGEMENT",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def api_get(endpoint: str, params: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    urls: list[str] = []
    page = 1
    while True:
        query = dict(params)
        query.update({"api_key": API_KEY, "per_page": 100, "page": page})
        url = f"{BASE}{endpoint}?{urlencode(query, doseq=True)}"
        public_url = url.replace(f"api_key={API_KEY}", "api_key=REDACTED")
        urls.append(public_url)
        request = Request(url, headers={"User-Agent": "starintel-gpt-auto-dig/1.0"})
        for attempt in range(5):
            try:
                with urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        results = payload.get("results", [])
        rows.extend(results)
        pagination = payload.get("pagination", {})
        pages = int(pagination.get("pages") or 1)
        if page >= pages or not results:
            break
        page += 1
    return rows, urls


def dedupe_by_sub_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("sub_id") or json.dumps(row, sort_keys=True))
        old = by_id.get(key)
        marker = (str(row.get("load_date") or ""), int(row.get("file_number") or 0))
        old_marker = (str(old.get("load_date") or ""), int(old.get("file_number") or 0)) if old else ("", -1)
        if old is None or marker >= old_marker:
            by_id[key] = row
    return list(by_id.values())


def normalized_name(value: Any) -> str:
    return re.sub(r"[^A-Z ]+", " ", str(value or "").upper()).strip()


def identity_score(row: dict[str, Any], kind: str) -> tuple[float, list[str]]:
    name_key = "contributor_name" if kind == "receipt" else "recipient_name"
    city_key = "contributor_city" if kind == "receipt" else "recipient_city"
    state_key = "contributor_state" if kind == "receipt" else "recipient_state"
    zip_key = "contributor_zip" if kind == "receipt" else "recipient_zip"
    employer = normalized_name(row.get("contributor_employer"))
    occupation = normalized_name(row.get("contributor_occupation"))
    name = normalized_name(row.get(name_key))
    city = normalized_name(row.get(city_key))
    state = normalized_name(row.get(state_key))
    zip_code = str(row.get(zip_key) or "")
    reasons: list[str] = []
    score = 0.0
    if "FINK" in name and ("LAURENCE" in name or "LARRY" in name):
        score += 0.45
        reasons.append("exact first-name/surname variant")
    else:
        return 0.0, ["name did not match Laurence/Larry Fink"]
    if "BLACKROCK" in employer or "BLACK ROCK" in employer:
        score += 0.35
        reasons.append("BlackRock employer")
    elif "FIRST BOSTON" in employer:
        score += 0.25
        reasons.append("historical First Boston employer")
    elif employer and employer not in {"NONE", "NOT EMPLOYED", "RETIRED", "SELF EMPLOYED", "SELF-EMPLOYED"}:
        reasons.append(f"other employer: {employer}")
    if any(term in occupation for term in EXECUTIVE_TERMS):
        score += 0.12
        reasons.append("executive/finance occupation")
    if state == "NY":
        score += 0.04
        reasons.append("New York state")
    if city in {"NEW YORK", "NEW YORK CITY", "MANHATTAN", "NORTH SALEM"}:
        score += 0.03
        reasons.append("consistent New York locality")
    if zip_code.startswith("100") or zip_code.startswith("105"):
        score += 0.01
        reasons.append("consistent New York ZIP prefix")
    return min(score, 1.0), reasons


def latest_transactions(rows: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        committee = row.get("committee_id") or row.get("recipient_committee_id")
        txn = row.get("transaction_id") or row.get("back_reference_transaction_id")
        if txn:
            key = (committee, txn)
        else:
            date_key = row.get("contribution_receipt_date") if kind == "receipt" else row.get("disbursement_date")
            amount_key = row.get("contribution_receipt_amount") if kind == "receipt" else row.get("disbursement_amount")
            name_key = row.get("contributor_name") if kind == "receipt" else row.get("recipient_name")
            key = (committee, name_key, date_key, amount_key, row.get("image_number"))
        old = groups.get(key)
        marker = (int(row.get("file_number") or 0), str(row.get("load_date") or ""), str(row.get("sub_id") or ""))
        old_marker = (int(old.get("file_number") or 0), str(old.get("load_date") or ""), str(old.get("sub_id") or "")) if old else (-1, "", "")
        if old is None or marker >= old_marker:
            groups[key] = row
    return list(groups.values())


def committee_lookup(ids: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    result: dict[str, dict[str, Any]] = {}
    urls: list[str] = []
    for committee_id in sorted(ids):
        rows, used = api_get(f"/committee/{committee_id}/", {})
        urls.extend(used)
        if rows:
            result[committee_id] = rows[0]
    return result, urls


def safe_row(row: dict[str, Any], kind: str) -> dict[str, Any]:
    keys = [
        "sub_id", "committee_id", "recipient_committee_id", "candidate_id",
        "contributor_name", "recipient_name", "contributor_city", "recipient_city",
        "contributor_state", "recipient_state", "contributor_zip", "recipient_zip",
        "contributor_employer", "contributor_occupation", "contribution_receipt_date",
        "contribution_receipt_amount", "disbursement_date", "disbursement_amount",
        "disbursement_description", "memo_text", "memoed_subtotal", "line_number",
        "image_number", "file_number", "transaction_id", "back_reference_transaction_id",
        "amendment_indicator", "report_type", "two_year_transaction_period",
        "conduit_committee_id", "conduit_committee_name", "load_date",
    ]
    return {key: row.get(key) for key in keys if row.get(key) is not None}


def source_for(row: dict[str, Any], kind: str) -> dict[str, Any]:
    sub_id = row.get("sub_id")
    image = row.get("image_number")
    if kind == "receipt":
        url = f"https://www.fec.gov/data/receipts/individual-contributions/?sub_id={sub_id}"
        title = "FEC Schedule A individual-contribution record"
    else:
        url = f"https://www.fec.gov/data/disbursements/?sub_id={sub_id}"
        title = "FEC Schedule B disbursement record"
    source = {
        "url": url,
        "title": title,
        "publisher": "Federal Election Commission",
        "source_type": "official-filing-record",
        "accessed": utc_now()[:10],
        "reliability": 0.98,
    }
    if image:
        source["filing_image_url"] = f"https://docquery.fec.gov/cgi-bin/fecimg/?{image}"
    return source


def main() -> None:
    fetched_receipts: list[dict[str, Any]] = []
    fetched_refunds: list[dict[str, Any]] = []
    query_urls: list[str] = []
    for name in NAME_QUERIES:
        rows, urls = api_get("/schedules/schedule_a/", {
            "contributor_name": name,
            "two_year_transaction_period": CYCLES,
            "is_individual": "true",
            "sort": "-contribution_receipt_date",
        })
        fetched_receipts.extend(rows)
        query_urls.extend(urls)
        rows, urls = api_get("/schedules/schedule_b/", {
            "recipient_name": name,
            "two_year_transaction_period": CYCLES,
            "sort": "-disbursement_date",
        })
        fetched_refunds.extend(rows)
        query_urls.extend(urls)
    rows, urls = api_get("/schedules/schedule_a/", {
        "contributor_name": "FINK",
        "contributor_employer": "BLACKROCK",
        "two_year_transaction_period": CYCLES,
        "is_individual": "true",
        "sort": "-contribution_receipt_date",
    })
    fetched_receipts.extend(rows)
    query_urls.extend(urls)

    receipt_candidates = dedupe_by_sub_id(fetched_receipts)
    refund_candidates = dedupe_by_sub_id(fetched_refunds)
    accepted_receipts: list[tuple[dict[str, Any], float, list[str]]] = []
    rejected: list[dict[str, Any]] = []
    for row in receipt_candidates:
        score, reasons = identity_score(row, "receipt")
        if score >= 0.75:
            accepted_receipts.append((row, score, reasons))
        else:
            rejected.append({"kind": "receipt", "score": score, "reasons": reasons, "record": safe_row(row, "receipt")})
    accepted_refunds: list[tuple[dict[str, Any], float, list[str]]] = []
    for row in refund_candidates:
        score, reasons = identity_score(row, "refund")
        purpose = normalized_name(row.get("disbursement_description") or row.get("memo_text"))
        if score >= 0.70 and "REFUND" in purpose:
            accepted_refunds.append((row, score, reasons + ["refund purpose"] ))
        else:
            rejected.append({"kind": "disbursement", "score": score, "reasons": reasons, "record": safe_row(row, "refund")})

    receipt_scores = {str(row.get("sub_id")): (score, reasons) for row, score, reasons in accepted_receipts}
    refund_scores = {str(row.get("sub_id")): (score, reasons) for row, score, reasons in accepted_refunds}
    receipts = latest_transactions([row for row, _, _ in accepted_receipts], "receipt")
    refunds = latest_transactions([row for row, _, _ in accepted_refunds], "refund")
    committee_ids = {str(row.get("committee_id")) for row in receipts + refunds if row.get("committee_id")}
    committees, committee_urls = committee_lookup(committee_ids)
    query_urls.extend(committee_urls)

    generated = utc_now()
    dataset = "larry-fink-fec-personal-ledger-2026-07-25"
    docs: list[dict[str, Any]] = []
    docs.append({
        "_id": "starintel:source:fec-open-api",
        "dataset": dataset,
        "dtype": "source",
        "version": "0.8.0",
        "date_added": generated,
        "date_updated": generated,
        "title": "OpenFEC transaction-level API",
        "description": "Official FEC Schedule A and Schedule B transaction data, updated nightly. API keys are removed from the published audit.",
        "sources": [{
            "url": "https://api.open.fec.gov/developers/",
            "title": "OpenFEC API documentation",
            "publisher": "Federal Election Commission",
            "source_type": "official-documentation",
            "accessed": generated[:10],
            "reliability": 0.98,
        }],
        "confidence": 0.98,
        "verification": {"status": "verified"},
        "tags": ["fec", "campaign-finance", "official-data"],
    })

    gross = 0.0
    memo_amount = 0.0
    by_committee: dict[str, dict[str, Any]] = defaultdict(lambda: {"gross": 0.0, "refunds": 0.0, "transactions": 0})
    for row in sorted(receipts, key=lambda r: str(r.get("contribution_receipt_date") or "")):
        amount = float(row.get("contribution_receipt_amount") or 0)
        memoed = bool(row.get("memoed_subtotal"))
        if memoed:
            memo_amount += amount
        else:
            gross += amount
            cid = str(row.get("committee_id") or "unknown")
            by_committee[cid]["gross"] += amount
            by_committee[cid]["transactions"] += 1
        score, reasons = receipt_scores.get(str(row.get("sub_id")), (0.75, []))
        cid = str(row.get("committee_id") or "unknown")
        committee_name = committees.get(cid, {}).get("name") or cid
        docs.append({
            "_id": f"starintel:event:fec-receipt-{row.get('sub_id')}",
            "dataset": dataset,
            "dtype": "event",
            "version": "0.8.0",
            "date_added": generated,
            "date_updated": generated,
            "title": f"FEC receipt: {committee_name} — ${amount:,.2f}",
            "summary": "Resolved federal contribution record attributed to Laurence D. Fink. Memo entries are retained but excluded from gross totals.",
            "subject": {"entity_id": "starintel:person:laurence-d-fink", "name": "Laurence D. Fink"},
            "transaction": safe_row(row, "receipt") | {"committee_name": committee_name, "counted_in_gross_total": not memoed},
            "identity_resolution": {"score": round(score, 3), "reasons": reasons},
            "sources": [source_for(row, "receipt")],
            "confidence": round(score, 3),
            "verification": {"status": "verified" if score >= 0.90 else "high-confidence-match"},
            "tags": ["fec", "personal-contribution", "larry-fink", "memo-entry" if memoed else "counted-receipt"],
        })

    refund_total = 0.0
    for row in sorted(refunds, key=lambda r: str(r.get("disbursement_date") or "")):
        amount = float(row.get("disbursement_amount") or 0)
        refund_total += amount
        cid = str(row.get("committee_id") or "unknown")
        by_committee[cid]["refunds"] += amount
        score, reasons = refund_scores.get(str(row.get("sub_id")), (0.70, []))
        committee_name = committees.get(cid, {}).get("name") or cid
        docs.append({
            "_id": f"starintel:event:fec-refund-{row.get('sub_id')}",
            "dataset": dataset,
            "dtype": "event",
            "version": "0.8.0",
            "date_added": generated,
            "date_updated": generated,
            "title": f"FEC refund: {committee_name} — ${amount:,.2f}",
            "summary": "Schedule B disbursement explicitly identified as a contribution refund to Laurence/Larry Fink.",
            "subject": {"entity_id": "starintel:person:laurence-d-fink", "name": "Laurence D. Fink"},
            "transaction": safe_row(row, "refund") | {"committee_name": committee_name},
            "identity_resolution": {"score": round(score, 3), "reasons": reasons},
            "sources": [source_for(row, "refund")],
            "confidence": round(score, 3),
            "verification": {"status": "verified" if score >= 0.90 else "high-confidence-match"},
            "tags": ["fec", "contribution-refund", "larry-fink"],
        })

    committee_summary = []
    for cid, values in sorted(by_committee.items()):
        info = committees.get(cid, {})
        committee_summary.append({
            "committee_id": cid,
            "committee_name": info.get("name") or cid,
            "party": info.get("party_full") or info.get("party"),
            "designation": info.get("designation_full") or info.get("designation"),
            "gross_receipts": round(values["gross"], 2),
            "refunds": round(values["refunds"], 2),
            "net": round(values["gross"] - values["refunds"], 2),
            "counted_receipt_transactions": values["transactions"],
        })

    docs.append({
        "_id": "starintel:financial-observation:larry-fink-fec-ledger-summary",
        "dataset": dataset,
        "dtype": "financial-observation",
        "version": "0.8.0",
        "date_added": generated,
        "date_updated": generated,
        "title": "Laurence D. Fink resolved federal contribution ledger",
        "summary": "Transaction-level FEC ledger after identity scoring, amendment reconciliation, memo-entry exclusion from totals, and a separate Schedule B refund search.",
        "subject": {"entity_id": "starintel:person:laurence-d-fink", "name": "Laurence D. Fink"},
        "coverage": {"cycles": CYCLES, "generated_at": generated},
        "totals": {
            "gross_counted_receipts": round(gross, 2),
            "explicit_refunds": round(refund_total, 2),
            "net_counted_amount": round(gross - refund_total, 2),
            "memo_entries_excluded_from_gross": round(memo_amount, 2),
            "counted_receipts": sum(1 for row in receipts if not row.get("memoed_subtotal")),
            "memo_entries": sum(1 for row in receipts if row.get("memoed_subtotal")),
            "refund_records": len(refunds),
        },
        "by_recipient_committee": committee_summary,
        "method": [
            "Queried six Laurence/Larry Fink name variants across every two-year FEC period from 1979-1980 through 2025-2026.",
            "Added a surname-plus-BlackRock-employer query to catch formatting variants.",
            "Accepted only records scoring at least 0.75 using name, employer, occupation, state, locality, and ZIP consistency.",
            "Kept the newest filing version for each committee/transaction key.",
            "Excluded memoed Schedule A entries from gross totals to avoid counting earmark/pass-through disclosures twice.",
            "Counted Schedule B records as refunds only when the disbursement description or memo explicitly contained REFUND.",
            "Omitted street-address fields from public output.",
        ],
        "sources": [{
            "url": "https://www.fec.gov/data/individual-contributions/",
            "title": "FEC individual contributions search",
            "publisher": "Federal Election Commission",
            "source_type": "official-database",
            "accessed": generated[:10],
            "reliability": 0.98,
        }],
        "confidence": 0.93,
        "verification": {"status": "verified-with-identity-resolution"},
        "tags": ["fec", "campaign-finance", "larry-fink", "ledger"],
    })

    docs.append({
        "_id": "starintel:research-pass:larry-fink-fec-ledger-resolution",
        "dataset": dataset,
        "dtype": "research-pass",
        "version": "0.8.0",
        "date_added": generated,
        "date_updated": generated,
        "title": "Agent pass: resolve Larry Fink's personal FEC ledger",
        "research_question": "Which federal contribution and refund records can be attributed to Laurence D. Fink without merging homonyms, amendments, or memoed earmark disclosures?",
        "method": "Live OpenFEC Schedule A and B retrieval, identity scoring, filing-version reconciliation, memo exclusion, committee enrichment, and public-field minimization.",
        "findings": [
            "The accepted ledger is published as one event document per resolved transaction.",
            "Gross, refunds, net, memo exclusions, and recipient-committee totals are computed from the reconciled transaction set.",
            "Ambiguous candidates remain in a redacted query audit and are not presented as Fink transactions.",
        ],
        "supporting_record_ids": ["starintel:financial-observation:larry-fink-fec-ledger-summary"],
        "counterevidence": [
            "Name-only matches are insufficient because FINK and LARRY FINK can identify unrelated people.",
            "A memoed earmark entry can mirror a contribution already reported by a joint fundraising committee.",
            "Committee amendments can produce multiple versions of the same transaction.",
        ],
        "open_targets": [],
        "agent": {"name": "GPT-5.6 Thinking", "role": "evidence-resolution and neutral narrative"},
        "sources": [{
            "url": "https://api.open.fec.gov/developers/",
            "title": "OpenFEC API documentation",
            "publisher": "Federal Election Commission",
            "source_type": "official-documentation",
            "accessed": generated[:10],
            "reliability": 0.98,
        }],
        "confidence": 0.93,
        "verification": {"status": "verified-with-methodological-caveats"},
        "tags": ["research-pass", "fec", "identity-resolution", "larry-fink"],
    })

    OUT.mkdir(parents=True, exist_ok=True)
    docs.sort(key=lambda doc: doc["_id"])
    (OUT / "starintel-documents.jsonl").write_text(
        "".join(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in docs),
        encoding="utf-8",
    )
    audit = {
        "generated_at": generated,
        "query_urls": sorted(set(query_urls)),
        "receipt_candidates": len(receipt_candidates),
        "refund_candidates": len(refund_candidates),
        "accepted_receipt_versions": len(receipts),
        "accepted_refund_versions": len(refunds),
        "rejected_candidates": rejected,
        "privacy": "Street-address fields were not retained.",
    }
    (OUT / "query-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Larry Fink personal FEC ledger\n\n"
        f"Generated from live OpenFEC Schedule A and Schedule B data at `{generated}`.\n\n"
        f"- Counted receipts: {sum(1 for row in receipts if not row.get('memoed_subtotal'))}\n"
        f"- Memo entries excluded from gross totals: {sum(1 for row in receipts if row.get('memoed_subtotal'))}\n"
        f"- Explicit refund records: {len(refunds)}\n"
        f"- Gross counted receipts: ${gross:,.2f}\n"
        f"- Explicit refunds: ${refund_total:,.2f}\n"
        f"- Net counted amount: ${gross - refund_total:,.2f}\n\n"
        "The packet omits street addresses, preserves FEC transaction and filing identifiers, and records rejected homonym candidates in `query-audit.json`.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "documents": len(docs),
        "receipts": len(receipts),
        "refunds": len(refunds),
        "gross": round(gross, 2),
        "refund_total": round(refund_total, 2),
        "net": round(gross - refund_total, 2),
    }, indent=2))


if __name__ == "__main__":
    main()
