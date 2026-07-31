#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import urljoin

import requests

DEFAULT_API_BASE = "https://lda.gov/api/v1/"
DEFAULT_CLIENT = "Palantir Technologies"
DEFAULT_DATASET = "palantir-lobbying"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://starintel.actor; federal-lobbying-research)"
SCHEMA_VERSION = "0.9.0"


class LdaError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchConfig:
    api_base: str
    api_token: str | None
    page_size: int
    sleep_seconds: float
    timeout_seconds: float
    retries: int


class LdaClient:
    def __init__(self, config: FetchConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        })
        if config.api_token:
            self.session.headers["Authorization"] = f"Token {config.api_token}"

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        error = "unknown error"
        for attempt in range(1, self.config.retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout_seconds,
                )
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "5"))
                    time.sleep(max(retry_after, self.config.sleep_seconds))
                    error = "rate limited"
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise LdaError(f"unexpected JSON type from {response.url}: {type(payload).__name__}")
                return payload
            except (requests.RequestException, ValueError, LdaError) as exc:
                error = str(exc)
                if attempt < self.config.retries:
                    time.sleep(self.config.sleep_seconds * attempt)
        raise LdaError(f"GET {url} failed after {self.config.retries} attempts: {error}")

    def iter_filings(self, params: dict[str, Any]) -> Iterator[dict[str, Any]]:
        url = urljoin(self.config.api_base, "filings/")
        query = dict(params)
        query["page_size"] = self.config.page_size
        first = True
        while url:
            payload = self._get(url, query if first else None)
            first = False
            results = payload.get("results", [])
            if not isinstance(results, list):
                raise LdaError("filings response has no list-valued results field")
            for item in results:
                if isinstance(item, dict):
                    yield item
            next_url = payload.get("next")
            url = urljoin(self.config.api_base, next_url) if next_url else ""
            query = {}
            if url:
                time.sleep(self.config.sleep_seconds)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str, limit: int = 120) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (value or "unknown")[:limit].strip("-")


def name_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("display_name") or "").strip()
    return str(value or "").strip()


def entity_id(value: Any) -> str:
    if isinstance(value, dict):
        raw = value.get("id") or value.get("house_registrant_id") or value.get("name")
        return str(raw or "").strip()
    return ""


def normalized_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name_text(value).lower()).strip()


def decimal_amount(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("$", "").strip())
    except InvalidOperation:
        return None


def decimal_json(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    integral = value.to_integral_value()
    return int(integral) if value == integral else float(value)


def filing_amount(filing: dict[str, Any]) -> tuple[Decimal | None, str]:
    income = decimal_amount(filing.get("income"))
    expenses = decimal_amount(filing.get("expenses"))
    registrant = normalized_name(filing.get("registrant"))
    client = normalized_name(filing.get("client"))
    if expenses is not None and (registrant == client or income is None):
        return expenses, "expenses"
    if income is not None:
        return income, "income"
    return expenses, "expenses" if expenses is not None else "unknown"


def lobbyist_name(lobbyist: Any) -> str:
    if not isinstance(lobbyist, dict):
        return name_text(lobbyist)
    direct = lobbyist.get("name")
    if direct:
        return str(direct).strip()
    parts = [
        lobbyist.get("prefix_display") or lobbyist.get("prefix"),
        lobbyist.get("first_name"),
        lobbyist.get("nickname"),
        lobbyist.get("middle_name"),
        lobbyist.get("last_name"),
        lobbyist.get("suffix_display") or lobbyist.get("suffix"),
    ]
    return " ".join(str(part).strip() for part in parts if part).strip()


def government_entity_name(entity: Any) -> str:
    return name_text(entity)


def activity_code(activity: dict[str, Any]) -> str:
    value = activity.get("general_issue_code") or activity.get("general_issue") or activity.get("issue_code")
    if isinstance(value, dict):
        return str(value.get("value") or value.get("name") or "").strip()
    return str(value or "").strip()


def activity_label(activity: dict[str, Any]) -> str:
    value = activity.get("general_issue") or activity.get("general_issue_display") or activity.get("general_issue_code_display")
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or "").strip()
    return str(value or "").strip()


def extract_activities(filing: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for raw in filing.get("lobbying_activities") or []:
        if not isinstance(raw, dict):
            continue
        lobbyists: list[dict[str, Any]] = []
        for item in raw.get("lobbyists") or []:
            if not isinstance(item, dict):
                name = lobbyist_name(item)
                if name:
                    lobbyists.append({"name": name, "covered_position": ""})
                continue
            lobbyists.append({
                "id": item.get("id"),
                "name": lobbyist_name(item),
                "covered_position": str(
                    item.get("covered_position")
                    or item.get("covered_position_description")
                    or ""
                ).strip(),
            })
        entities = [
            government_entity_name(entity)
            for entity in (raw.get("government_entities") or [])
            if government_entity_name(entity)
        ]
        output.append({
            "general_issue_code": activity_code(raw),
            "general_issue": activity_label(raw),
            "specific_issues": str(raw.get("description") or raw.get("specific_issues") or "").strip(),
            "government_entities": sorted(set(entities)),
            "lobbyists": sorted(lobbyists, key=lambda item: (item.get("name") or "").lower()),
        })
    return output


def is_quarterly(filing: dict[str, Any]) -> bool:
    filing_type = str(filing.get("filing_type") or "").upper()
    period = str(filing.get("filing_period") or "").lower()
    display = str(filing.get("filing_type_display") or "").lower()
    return filing_type.startswith(("Q1", "Q2", "Q3", "Q4")) or "quarter" in period or "quarter" in display


def is_amendment(filing: dict[str, Any]) -> bool:
    filing_type = str(filing.get("filing_type") or "").upper()
    display = str(filing.get("filing_type_display") or "").lower()
    return "amend" in display or filing_type.endswith("A") or filing_type.endswith("AY")


def cycle_key(filing: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(filing.get("filing_year") or ""),
        str(filing.get("filing_period") or filing.get("filing_type") or ""),
        entity_id(filing.get("registrant")) or normalized_name(filing.get("registrant")),
        entity_id(filing.get("client")) or normalized_name(filing.get("client")),
    )


def posted_key(filing: dict[str, Any]) -> tuple[str, str]:
    return (str(filing.get("dt_posted") or ""), str(filing.get("filing_uuid") or ""))


def collapse_amendments(filings: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    quarterly: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    passthrough: list[dict[str, Any]] = []
    for filing in filings:
        if is_quarterly(filing):
            quarterly[cycle_key(filing)].append(filing)
        else:
            passthrough.append(filing)

    active = list(passthrough)
    superseded: list[dict[str, Any]] = []
    for group in quarterly.values():
        ordered = sorted(group, key=posted_key)
        active.append(ordered[-1])
        superseded.extend(ordered[:-1])
    return sorted(active, key=posted_key), sorted(superseded, key=posted_key)


def normalize_filing(filing: dict[str, Any], dataset: str, active: bool) -> dict[str, Any]:
    amount, basis = filing_amount(filing)
    activities = extract_activities(filing)
    lobbyists = sorted({
        item["name"]
        for activity in activities
        for item in activity["lobbyists"]
        if item.get("name")
    })
    issue_codes = sorted({activity["general_issue_code"] for activity in activities if activity["general_issue_code"]})
    government_entities = sorted({
        entity
        for activity in activities
        for entity in activity["government_entities"]
    })
    source_url = str(
        filing.get("filing_document_url")
        or filing.get("url")
        or f"https://lda.gov/filings/public/filing/{filing.get('filing_uuid', '')}/print/"
    )
    return {
        "record_type": "federal_lobbying_filing",
        "dataset": dataset,
        "source_system": "U.S. Lobbying Disclosure Act API",
        "filing_uuid": filing.get("filing_uuid"),
        "filing_type": filing.get("filing_type"),
        "filing_type_display": filing.get("filing_type_display"),
        "filing_year": filing.get("filing_year"),
        "filing_period": filing.get("filing_period"),
        "filing_period_display": filing.get("filing_period_display"),
        "dt_posted": filing.get("dt_posted"),
        "active_version": active,
        "amendment": is_amendment(filing),
        "registrant": filing.get("registrant"),
        "client": filing.get("client"),
        "amount": decimal_json(amount),
        "amount_basis": basis,
        "expenses_method": filing.get("expenses_method"),
        "expenses_method_display": filing.get("expenses_method_display"),
        "termination_date": filing.get("termination_date"),
        "lobbying_activities": activities,
        "lobbyists": lobbyists,
        "issue_codes": issue_codes,
        "government_entities": government_entities,
        "source_url": source_url,
        "source_sha256": hashlib.sha256(source_url.encode()).hexdigest(),
    }


def keep_year(record: dict[str, Any], year_start: int | None, year_end: int | None) -> bool:
    try:
        year = int(record.get("filing_year"))
    except (TypeError, ValueError):
        return year_start is None and year_end is None
    return (year_start is None or year >= year_start) and (year_end is None or year <= year_end)


def summarize(records: list[dict[str, Any]], superseded_count: int) -> dict[str, Any]:
    quarterly = [record for record in records if is_quarterly(record)]
    by_year: dict[str, Decimal] = defaultdict(Decimal)
    by_period: dict[str, Decimal] = defaultdict(Decimal)
    by_registrant: dict[str, Decimal] = defaultdict(Decimal)
    issue_codes: Counter[str] = Counter()
    lobbyists: Counter[str] = Counter()
    government_entities: Counter[str] = Counter()
    filing_count_by_year: Counter[str] = Counter()

    for record in quarterly:
        amount, _ = filing_amount(record)
        amount = amount or Decimal(0)
        year = str(record.get("filing_year") or "unknown")
        period = str(record.get("filing_period_display") or record.get("filing_period") or "unknown")
        registrant = name_text(record.get("registrant")) or "unknown"
        by_year[year] += amount
        by_period[f"{year} {period}"] += amount
        by_registrant[registrant] += amount
        filing_count_by_year[year] += 1
        for activity in extract_activities(record):
            if activity["general_issue_code"]:
                issue_codes[activity["general_issue_code"]] += 1
            for person in activity["lobbyists"]:
                if person.get("name"):
                    lobbyists[person["name"]] += 1
            government_entities.update(activity["government_entities"])

    return {
        "generated_at": now_iso(),
        "active_filing_count": len(records),
        "active_quarterly_filing_count": len(quarterly),
        "superseded_filing_count": superseded_count,
        "disclosed_amount_total": decimal_json(sum(by_year.values(), Decimal(0))),
        "amounts_by_year": {key: decimal_json(value) for key, value in sorted(by_year.items())},
        "filings_by_year": dict(sorted(filing_count_by_year.items())),
        "amounts_by_period": {key: decimal_json(value) for key, value in sorted(by_period.items())},
        "amounts_by_registrant": {
            key: decimal_json(value)
            for key, value in sorted(by_registrant.items(), key=lambda item: (-item[1], item[0].lower()))
        },
        "issue_codes": dict(issue_codes.most_common()),
        "lobbyists": dict(lobbyists.most_common()),
        "government_entities": dict(government_entities.most_common()),
    }


def money(value: Any) -> str:
    amount = decimal_amount(value) or Decimal(0)
    return f"${amount:,.0f}"


def summary_markdown(summary: dict[str, Any], client_name: str) -> str:
    lines = [
        f"# {client_name} federal lobbying enumeration",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- Active filings: **{summary['active_filing_count']}**",
        f"- Active quarterly filings: **{summary['active_quarterly_filing_count']}**",
        f"- Superseded filings removed from totals: **{summary['superseded_filing_count']}**",
        f"- Sum of disclosed active quarterly amounts: **{money(summary['disclosed_amount_total'])}**",
        "",
        "## Amounts by year",
        "",
        "| Year | Filings | Disclosed amount |",
        "|---:|---:|---:|",
    ]
    for year, amount in summary["amounts_by_year"].items():
        lines.append(f"| {year} | {summary['filings_by_year'].get(year, 0)} | {money(amount)} |")
    lines.extend(["", "## Registrants", "", "| Registrant | Disclosed amount |", "|---|---:|"])
    for registrant, amount in summary["amounts_by_registrant"].items():
        lines.append(f"| {registrant} | {money(amount)} |")
    lines.extend(["", "## Lobbyists by filing appearances", "", "| Lobbyist | Filing activities |", "|---|---:|"])
    for name, count in list(summary["lobbyists"].items())[:100]:
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## Government entities by activity appearances", "", "| Entity | Appearances |", "|---|---:|"])
    for name, count in list(summary["government_entities"].items())[:100]:
        lines.append(f"| {name} | {count} |")
    lines.extend([
        "",
        "## Interpretation guardrails",
        "",
        "- Quarterly amendments supersede earlier versions for the same registrant, client, year, and period.",
        "- In-house filings report expenses; outside firms report income. Both are disclosed estimates, not audited invoices.",
        "- Subcontractor registrations can duplicate a prime firm's reported income and require manual review before aggregation.",
        "- Lobbying issue alignment documents access and policy focus; it does not prove a contract was improperly awarded.",
        "",
    ])
    return "\n".join(lines)


def starintel_event(record: dict[str, Any], dataset: str, generated_at: str) -> dict[str, Any]:
    filing_uuid = str(record.get("filing_uuid") or "unknown")
    registrant = name_text(record.get("registrant"))
    client = name_text(record.get("client"))
    period = str(record.get("filing_period_display") or record.get("filing_period") or "")
    year = str(record.get("filing_year") or "")
    title = f"{registrant} lobbying disclosure for {client}, {period} {year}".strip()
    return {
        "_id": f"starintel:event:lda:{filing_uuid}",
        "dataset": dataset,
        "dtype": "event",
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": generated_at,
        "date_updated": generated_at,
        "title": title,
        "summary": f"Federal LDA filing reporting {money(record.get('amount'))} on a {record.get('amount_basis')} basis.",
        "description": "",
        "status": "recorded" if record.get("active_version") else "superseded",
        "language": "en",
        "tags": ["palantir", "lobbying", "lda", "federal"],
        "labels": [],
        "aliases": [],
        "keywords": record.get("issue_codes") or [],
        "identifiers": [{"scheme": "LDA filing UUID", "value": filing_uuid}],
        "sources": [{
            "source_id": "sha256:" + str(record.get("source_sha256") or ""),
            "kind": "government_filing",
            "title": title,
            "publisher": "U.S. House Clerk and Secretary of the Senate",
            "url": record.get("source_url"),
            "uri": record.get("source_url"),
            "retrieved_at": generated_at,
            "access_method": "official REST API",
            "credibility": 1.0,
        }],
        "evidence": [],
        "temporal": {
            "observed_at": record.get("dt_posted") or generated_at,
            "collected_at": generated_at,
        },
        "provenance": {
            "collector": "starintel-gpt-auto-dig",
            "collector_type": "script",
            "agent": "palantir-lobbying-enumerator",
            "method": "LDA REST API extraction with amendment collapse",
            "pipeline": "palantir-lobbying",
            "run_id": generated_at,
            "software_version": SCHEMA_VERSION,
        },
        "assessment": {"confidence": 1.0, "completeness": 0.95},
        "verification": {
            "status": "source-backed",
            "verified": True,
            "verified_at": generated_at,
            "methods": ["official-api"],
        },
        "handling": {"visibility": "public", "handling": "public-source-only", "sensitive": False, "pii": False},
        "lineage": {},
        "quality": {"validation_status": "pending_repository_validation", "validator": "scripts/starintel.py validate"},
        "workflow": {},
        "geospatial": {},
        "attachments": [],
        "related_ids": [],
        "notes": [],
        "data": record,
        "extensions": {},
    }


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enumerate Palantir federal lobbying from the official LDA API.")
    parser.add_argument("--client-name", default=DEFAULT_CLIENT)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--api-base", default=os.environ.get("LDA_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--api-token", default=os.environ.get("LDA_API_TOKEN"))
    parser.add_argument("--year-start", type=int)
    parser.add_argument("--year-end", type=int)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--sleep", type=float, default=4.1, help="Delay between pages; anonymous limit is 15 requests/minute.")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/palantir-lobbying"))
    parser.add_argument("--input-jsonl", type=Path, help="Use saved raw filings instead of the network.")
    parser.add_argument("--emit-starintel", action="store_true")
    return parser.parse_args(argv)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            records.append(value)
    return records


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.input_jsonl:
        raw = read_jsonl(args.input_jsonl)
    else:
        config = FetchConfig(
            api_base=args.api_base.rstrip("/") + "/",
            api_token=args.api_token,
            page_size=args.page_size,
            sleep_seconds=args.sleep,
            timeout_seconds=args.timeout,
            retries=args.retries,
        )
        raw = list(LdaClient(config).iter_filings({"client_name": args.client_name}))
        write_jsonl(output_dir / "raw-filings.jsonl", raw)

    raw = [record for record in raw if keep_year(record, args.year_start, args.year_end)]
    active, superseded = collapse_amendments(raw)
    normalized_active = [normalize_filing(record, args.dataset, True) for record in active]
    normalized_superseded = [normalize_filing(record, args.dataset, False) for record in superseded]
    summary = summarize(active, len(superseded))
    summary["client_name"] = args.client_name
    summary["dataset"] = args.dataset
    summary["year_start"] = args.year_start
    summary["year_end"] = args.year_end

    write_jsonl(output_dir / "filings-active.jsonl", normalized_active)
    write_jsonl(output_dir / "filings-superseded.jsonl", normalized_superseded)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_markdown(summary, args.client_name), encoding="utf-8")

    if args.emit_starintel:
        generated_at = summary["generated_at"]
        events = [starintel_event(record, args.dataset, generated_at) for record in normalized_active + normalized_superseded]
        write_jsonl(output_dir / "starintel-events.ndjson", events)

    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        summary = run(args)
    except (LdaError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
