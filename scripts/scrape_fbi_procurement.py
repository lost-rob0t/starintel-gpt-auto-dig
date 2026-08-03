from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

BIZ_FILE_REPOSITORY = "https://biz.fbi.gov/file-repository"
SAM_API = "https://api.sam.gov/opportunities/v2/search"
USASPENDING_API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
DEFAULT_AWARD_IDS = ("15F06725F0001209", "15F06725F0001838")
DEFAULT_KEYWORDS = ("terrorist screening center", "threat screening center")
DEFAULT_USER_AGENT = "StarIntel-FBI-Procurement-Collector/1.0 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"


@dataclass(frozen=True)
class Link:
    title: str
    url: str


class AnchorParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[Link] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self._href = urljoin(self.base_url, href)
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._href is None:
            return
        title = " ".join("".join(self._text).split())
        self.links.append(Link(title=title, url=self._href))
        self._href = None
        self._text = []


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def same_host(url: str, base_url: str) -> bool:
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def parse_links(payload: bytes, base_url: str) -> list[Link]:
    parser = AnchorParser(base_url)
    parser.feed(payload.decode("utf-8", errors="replace"))
    dedup: dict[str, Link] = {}
    for link in parser.links:
        url = canonical_url(link.url)
        if not url.startswith("https://") or not same_host(url, base_url):
            continue
        previous = dedup.get(url)
        if previous is None or (not previous.title and link.title):
            dedup[url] = Link(title=link.title, url=url)
    return sorted(dedup.values(), key=lambda item: (item.url, item.title))


def split_date_ranges(start: date, end: date) -> list[tuple[date, date]]:
    if end < start:
        raise ValueError("end date precedes start date")
    ranges: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        boundary = min(end, cursor.replace(year=cursor.year + 1) - timedelta(days=1))
        ranges.append((cursor, boundary))
        cursor = boundary + timedelta(days=1)
    return ranges


def request_bytes(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 60.0,
    retries: int = 4,
    user_agent: str = DEFAULT_USER_AGENT,
) -> bytes:
    merged_headers = {
        "Accept": "application/json,text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        "User-Agent": user_agent,
    }
    if headers:
        merged_headers.update(headers)
    request = Request(url, data=body, method=method, headers=merged_headers)
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError):
            if attempt + 1 >= retries:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def raw_record(
    *,
    source: str,
    record_type: str,
    source_url: str,
    payload: Any,
    retrieved_at: str,
    content: bytes | None = None,
) -> dict[str, Any]:
    encoded = content if content is not None else json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "source": source,
        "record_type": record_type,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "sha256": sha256_bytes(encoded),
        "payload": payload,
    }


def collect_biz_repository(
    *,
    seed_url: str,
    timeout: float,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    page = request_bytes(seed_url, timeout=timeout, user_agent=user_agent)
    records = [
        raw_record(
            source="fbi-biz",
            record_type="repository-page",
            source_url=seed_url,
            payload={"content_type": "text/html", "bytes": len(page)},
            retrieved_at=retrieved_at,
            content=page,
        )
    ]
    for link in parse_links(page, seed_url):
        if link.url == seed_url:
            continue
        records.append(
            raw_record(
                source="fbi-biz",
                record_type="repository-link",
                source_url=link.url,
                payload={"title": link.title, "url": link.url},
                retrieved_at=retrieved_at,
            )
        )
    return records


def sam_query_url(
    *,
    api_key: str,
    start: date,
    end: date,
    organization_name: str,
    procurement_type: str | None,
    limit: int,
    offset: int,
) -> str:
    query: dict[str, str | int] = {
        "api_key": api_key,
        "postedFrom": start.strftime("%m/%d/%Y"),
        "postedTo": end.strftime("%m/%d/%Y"),
        "organizationName": organization_name,
        "limit": limit,
        "offset": offset,
    }
    if procurement_type:
        query["ptype"] = procurement_type
    return f"{SAM_API}?{urlencode(query)}"


def public_sam_query(url: str) -> str:
    parsed = urlparse(url)
    pairs = []
    for key, value in [part.split("=", 1) for part in parsed.query.split("&") if "=" in part]:
        if key == "api_key":
            value = "REDACTED"
        pairs.append((key, value))
    return parsed._replace(query="&".join(f"{key}={value}" for key, value in pairs)).geturl()


def collect_sam(
    *,
    api_key: str,
    start: date,
    end: date,
    organization_name: str,
    procurement_types: Iterable[str],
    limit: int,
    max_pages: int,
    timeout: float,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_notice_ids: set[str] = set()
    for range_start, range_end in split_date_ranges(start, end):
        for procurement_type in procurement_types:
            offset = 0
            for _ in range(max_pages):
                url = sam_query_url(
                    api_key=api_key,
                    start=range_start,
                    end=range_end,
                    organization_name=organization_name,
                    procurement_type=procurement_type or None,
                    limit=limit,
                    offset=offset,
                )
                payload = json.loads(request_bytes(url, timeout=timeout, user_agent=user_agent))
                opportunities = payload.get("opportunitiesData") or []
                for item in opportunities:
                    notice_id = str(item.get("noticeId") or "")
                    identity = notice_id or sha256_bytes(
                        json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    )
                    if identity in seen_notice_ids:
                        continue
                    seen_notice_ids.add(identity)
                    source_url = str(item.get("uiLink") or item.get("additionalInfoLink") or public_sam_query(url))
                    records.append(
                        raw_record(
                            source="sam-opportunities",
                            record_type="opportunity",
                            source_url=source_url,
                            payload=item,
                            retrieved_at=retrieved_at,
                        )
                    )
                total = int(payload.get("totalRecords") or 0)
                if not opportunities or (offset + 1) * limit >= total:
                    break
                offset += 1
    return sorted(records, key=lambda item: (str(item["payload"].get("postedDate") or ""), str(item["payload"].get("noticeId") or "")))


def usaspending_payload(
    *,
    award_ids: Iterable[str],
    keywords: Iterable[str],
    start: date,
    end: date,
    page: int,
    limit: int,
) -> dict[str, Any]:
    filters: dict[str, Any] = {
        "time_period": [{"start_date": start.isoformat(), "end_date": end.isoformat()}],
        "agencies": [
            {
                "type": "awarding",
                "tier": "subtier",
                "name": "Federal Bureau of Investigation",
                "toptier_name": "Department of Justice",
            }
        ],
        "award_type_codes": ["A", "B", "C", "D"],
    }
    exact_ids = [f'"{value.strip()}"' for value in award_ids if value.strip()]
    terms = [value.strip() for value in keywords if value.strip()]
    if exact_ids:
        filters["award_ids"] = exact_ids
    if terms:
        filters["keywords"] = terms
    return {
        "filters": filters,
        "fields": [
            "Award ID",
            "Recipient Name",
            "Start Date",
            "End Date",
            "Award Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Award Type",
            "Description",
            "generated_unique_award_id",
        ],
        "page": page,
        "limit": limit,
        "sort": "Award ID",
        "order": "asc",
        "subawards": False,
    }


def collect_usaspending(
    *,
    award_ids: Iterable[str],
    keywords: Iterable[str],
    start: date,
    end: date,
    limit: int,
    max_pages: int,
    timeout: float,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        query = usaspending_payload(
            award_ids=award_ids,
            keywords=keywords,
            start=start,
            end=end,
            page=page,
            limit=limit,
        )
        body = json.dumps(query, separators=(",", ":")).encode("utf-8")
        payload = json.loads(
            request_bytes(
                USASPENDING_API,
                method="POST",
                body=body,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
                user_agent=user_agent,
            )
        )
        results = payload.get("results") or []
        for item in results:
            award_id = str(item.get("Award ID") or item.get("generated_unique_award_id") or "")
            identity = award_id or sha256_bytes(
                json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
            if identity in seen:
                continue
            seen.add(identity)
            generated = str(item.get("generated_unique_award_id") or "")
            source_url = (
                f"https://www.usaspending.gov/award/{generated}"
                if generated
                else "https://www.usaspending.gov/search"
            )
            records.append(
                raw_record(
                    source="usaspending",
                    record_type="prime-award",
                    source_url=source_url,
                    payload=item,
                    retrieved_at=retrieved_at,
                )
            )
        page_meta = payload.get("page_metadata") or {}
        if not results or not page_meta.get("hasNext", False):
            break
    return sorted(records, key=lambda item: str(item["payload"].get("Award ID") or ""))


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> int:
    ordered = sorted(
        records,
        key=lambda record: (
            str(record.get("source") or ""),
            str(record.get("record_type") or ""),
            str(record.get("source_url") or ""),
            str(record.get("sha256") or ""),
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return len(ordered)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect deterministic raw FBI procurement evidence from official public sources."
    )
    parser.add_argument("--source", choices=("all", "biz", "sam", "usaspending"), default="all")
    parser.add_argument("--output", type=Path, default=Path("imports/fbi-procurement/raw.jsonl"))
    parser.add_argument("--posted-from", type=parse_date, default=date(2020, 1, 1))
    parser.add_argument("--posted-to", type=parse_date, default=date.today())
    parser.add_argument("--organization-name", default="FEDERAL BUREAU OF INVESTIGATION")
    parser.add_argument("--sam-api-key-env", default="SAM_GOV_API_KEY")
    parser.add_argument("--sam-ptype", action="append", default=[])
    parser.add_argument("--award-id", action="append", default=[])
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 1 or args.limit > 1000:
        raise SystemExit("--limit must be between 1 and 1000")
    if args.max_pages < 1:
        raise SystemExit("--max-pages must be positive")

    retrieved_at = utc_now()
    records: list[dict[str, Any]] = []

    if args.source in {"all", "biz"}:
        records.extend(
            collect_biz_repository(
                seed_url=BIZ_FILE_REPOSITORY,
                timeout=args.timeout,
                user_agent=args.user_agent,
                retrieved_at=retrieved_at,
            )
        )

    if args.source in {"all", "sam"}:
        api_key = os.environ.get(args.sam_api_key_env)
        if not api_key:
            if args.source == "sam":
                raise SystemExit(f"missing {args.sam_api_key_env}")
            print(f"warning: skipping SAM.gov; missing {args.sam_api_key_env}", file=sys.stderr)
        else:
            records.extend(
                collect_sam(
                    api_key=api_key,
                    start=args.posted_from,
                    end=args.posted_to,
                    organization_name=args.organization_name,
                    procurement_types=args.sam_ptype or ("r", "p", "o", "k", "a", "u", "s"),
                    limit=args.limit,
                    max_pages=args.max_pages,
                    timeout=args.timeout,
                    user_agent=args.user_agent,
                    retrieved_at=retrieved_at,
                )
            )

    if args.source in {"all", "usaspending"}:
        records.extend(
            collect_usaspending(
                award_ids=args.award_id or DEFAULT_AWARD_IDS,
                keywords=args.keyword or DEFAULT_KEYWORDS,
                start=args.posted_from,
                end=args.posted_to,
                limit=args.limit,
                max_pages=args.max_pages,
                timeout=args.timeout,
                user_agent=args.user_agent,
                retrieved_at=retrieved_at,
            )
        )

    count = write_jsonl(records, args.output)
    print(json.dumps({"output": str(args.output), "records": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
