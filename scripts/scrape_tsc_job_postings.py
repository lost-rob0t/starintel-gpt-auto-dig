from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LEVER_POSTINGS_API = "https://api.lever.co/v0/postings/{site}"
DEFAULT_SITES = ("agile-defense",)
DEFAULT_TERMS = (
    "threat screening",
    "identity resolution",
    "intelligence analysis",
    "information sharing",
    "personal identifiers",
    "biometric data",
    "national security mission support",
    "ci polygraph",
)
DEFAULT_LOCATIONS = ("Vienna, VA", "Vienna, Virginia")
DEFAULT_USER_AGENT = (
    "StarIntel-Public-Job-Posting-Collector/1.0 "
    "(+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def html_to_text(value: Any) -> str:
    if value in (None, ""):
        return ""
    parser = TextExtractor()
    parser.feed(unescape(str(value)))
    return " ".join(" ".join(parser.parts).split())


def normalized_posting(posting: dict[str, Any]) -> dict[str, Any]:
    categories = posting.get("categories")
    if not isinstance(categories, dict):
        categories = {}
    lists = posting.get("lists")
    list_sections: list[dict[str, str]] = []
    if isinstance(lists, list):
        for item in lists:
            if not isinstance(item, dict):
                continue
            list_sections.append(
                {
                    "heading": html_to_text(item.get("text")),
                    "content": html_to_text(item.get("content")),
                }
            )
    urls = posting.get("urls")
    if not isinstance(urls, dict):
        urls = {}
    return {
        "id": str(posting.get("id") or ""),
        "title": html_to_text(posting.get("text")),
        "description": html_to_text(posting.get("description")),
        "description_plain": html_to_text(posting.get("descriptionPlain")),
        "additional": html_to_text(posting.get("additional")),
        "lists": list_sections,
        "categories": {
            "location": html_to_text(categories.get("location")),
            "all_locations": [
                html_to_text(value)
                for value in categories.get("allLocations", [])
                if value not in (None, "")
            ]
            if isinstance(categories.get("allLocations"), list)
            else [],
            "commitment": html_to_text(categories.get("commitment")),
            "team": html_to_text(categories.get("team")),
            "department": html_to_text(categories.get("department")),
        },
        "workplace_type": html_to_text(posting.get("workplaceType")),
        "hosted_url": str(posting.get("hostedUrl") or urls.get("show") or ""),
        "apply_url": str(posting.get("applyUrl") or urls.get("apply") or ""),
        "created_at": posting.get("createdAt"),
        "updated_at": posting.get("updatedAt"),
        "requisition_code": html_to_text(posting.get("reqCode")),
        "requisition_codes": [
            html_to_text(value)
            for value in posting.get("requisitionCodes", [])
            if value not in (None, "")
        ]
        if isinstance(posting.get("requisitionCodes"), list)
        else [],
    }


def searchable_text(posting: dict[str, Any]) -> str:
    sections = posting.get("lists") or []
    return " ".join(
        [
            str(posting.get("title") or ""),
            str(posting.get("description") or ""),
            str(posting.get("description_plain") or ""),
            str(posting.get("additional") or ""),
            str((posting.get("categories") or {}).get("location") or ""),
            *(
                f"{section.get('heading', '')} {section.get('content', '')}"
                for section in sections
                if isinstance(section, dict)
            ),
        ]
    ).lower()


def extract_requisition_codes(posting: dict[str, Any]) -> list[str]:
    found = {
        value
        for value in [
            str(posting.get("requisition_code") or "").strip(),
            *(
                str(value).strip()
                for value in posting.get("requisition_codes", [])
                if value not in (None, "")
            ),
        ]
        if value
    }
    text = searchable_text(posting)
    found.update(re.findall(r"\brequisition\s*#?\s*:?\s*([A-Za-z0-9._-]+)", text, flags=re.I))
    return sorted(found)


def match_posting(
    posting: dict[str, Any],
    *,
    terms: Iterable[str],
    locations: Iterable[str],
) -> tuple[list[str], list[str]]:
    text = searchable_text(posting)
    term_matches = sorted(
        {
            term.strip()
            for term in terms
            if term.strip() and term.strip().lower() in text
        }
    )
    location_text = " ".join(
        [
            str((posting.get("categories") or {}).get("location") or ""),
            *(
                str(value)
                for value in (posting.get("categories") or {}).get("all_locations", [])
            ),
        ]
    ).lower()
    location_matches = sorted(
        {
            location.strip()
            for location in locations
            if location.strip() and location.strip().lower() in location_text
        }
    )
    return term_matches, location_matches


def request_json(
    url: str,
    *,
    timeout: float,
    retries: int,
    user_agent: str,
) -> Any:
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": user_agent},
    )
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError):
            if attempt + 1 >= retries:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def listing_url(site: str, *, skip: int, limit: int) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", site):
        raise ValueError(f"invalid Lever site slug: {site!r}")
    return f"{LEVER_POSTINGS_API.format(site=site)}?{urlencode({'mode': 'json', 'skip': skip, 'limit': limit})}"


def collect_site(
    site: str,
    *,
    terms: Iterable[str],
    locations: Iterable[str],
    limit: int,
    max_pages: int,
    timeout: float,
    retries: int,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(max_pages):
        skip = page * limit
        url = listing_url(site, skip=skip, limit=limit)
        payload = request_json(
            url,
            timeout=timeout,
            retries=retries,
            user_agent=user_agent,
        )
        if not isinstance(payload, list):
            raise TypeError(f"Lever site {site!r} returned a non-list payload")
        for raw_posting in payload:
            if not isinstance(raw_posting, dict):
                continue
            posting = normalized_posting(raw_posting)
            posting_id = str(posting.get("id") or "")
            identity = posting_id or sha256_bytes(
                json.dumps(
                    posting,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            if identity in seen:
                continue
            seen.add(identity)
            term_matches, location_matches = match_posting(
                posting,
                terms=terms,
                locations=locations,
            )
            if not term_matches and not location_matches:
                continue
            canonical = json.dumps(
                posting,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            records.append(
                {
                    "source": "lever-public-postings",
                    "record_type": "public-job-posting",
                    "site": site,
                    "posting_id": posting_id,
                    "source_url": posting.get("hosted_url") or url,
                    "retrieved_at": retrieved_at,
                    "sha256": sha256_bytes(canonical),
                    "matched_terms": term_matches,
                    "matched_locations": location_matches,
                    "requisition_codes": extract_requisition_codes(posting),
                    "payload": posting,
                }
            )
        if len(payload) < limit:
            break
    return sorted(
        records,
        key=lambda record: (
            str(record.get("site") or ""),
            str((record.get("payload") or {}).get("title") or ""),
            str(record.get("posting_id") or ""),
        ),
    )


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> int:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            str(record.get("site") or ""),
            str(record.get("posting_id") or record.get("sha256") or ""),
        )
        unique[key] = record
    ordered = [unique[key] for key in sorted(unique)]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")
    return len(ordered)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect public contractor job postings that expose FBI TSC mission, "
            "staffing and labor-category evidence without accessing applicant data."
        )
    )
    parser.add_argument("--site", action="append", default=[])
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--location", action="append", default=[])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("imports/fbi-procurement/tsc-job-postings.jsonl"),
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100")
    if args.max_pages < 1:
        raise SystemExit("--max-pages must be positive")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if args.retries < 1:
        raise SystemExit("--retries must be positive")

    records: list[dict[str, Any]] = []
    retrieved_at = utc_now()
    for site in args.site or DEFAULT_SITES:
        records.extend(
            collect_site(
                site,
                terms=args.term or DEFAULT_TERMS,
                locations=args.location or DEFAULT_LOCATIONS,
                limit=args.limit,
                max_pages=args.max_pages,
                timeout=args.timeout,
                retries=args.retries,
                user_agent=args.user_agent,
                retrieved_at=retrieved_at,
            )
        )
    count = write_jsonl(records, args.output)
    print(json.dumps({"output": str(args.output), "records": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
