#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import html
from html.parser import HTMLParser
import json
import os
import re
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT",
    "StarIntel-Auto-Dig/0.9.0 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)",
)
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
STREET_BOUNDARY = re.compile(
    r"^(?P<street>.+?(?:"
    r"(?:Suite|Ste\.?|Floor|Fl\.?|Unit)\s*[A-Za-z0-9#.-]+|"
    r"(?:Street|St\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Road|Rd\.?|Drive|Dr\.?|"
    r"Lane|Ln\.?|Way|Parkway|Pkwy\.?|Highway|Hwy\.?|Court|Ct\.?|Circle|Cir\.?|"
    r"Plaza|Place|Pl\.?|Trail|Trl\.?)"
    r"))\s+(?P<city>[A-Za-z][A-Za-z .'-]*)$",
    re.IGNORECASE,
)
NOTICE_PATTERN = re.compile(
    r"Effective\s+(?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4}),\s+the\s+principal\s+executive\s+office\s+address\s+of\s+.+?\s+is\s+"
    r"(?P<street>.+),\s+(?P<city>[^,]+),\s+(?P<region>[A-Za-z][A-Za-z .'-]*?)\s+(?P<postal>\d{5}(?:-\d{4})?)\.?",
    re.IGNORECASE,
)


class _TextBlocks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._current: list[str] = []
        self.blocks: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self._current.append(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "hr"}:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"div", "p", "td", "th", "tr", "li", "h1", "h2", "h3", "h4"}:
            self._flush()

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        if not self._current:
            return
        value = " ".join(self._current).strip()
        self._current.clear()
        if value:
            self.blocks.append(value)


def html_blocks(raw_html: str) -> list[str]:
    parser = _TextBlocks()
    parser.feed(raw_html)
    parser.close()
    return [html.unescape(item).replace("\xa0", " ").strip() for item in parser.blocks if item.strip()]


def _parse_city_region_postal(value: str) -> tuple[str, str, str] | None:
    match = re.fullmatch(
        r"(?P<city>.+?),\s*(?P<region>[A-Za-z][A-Za-z .'-]*?)\s+(?P<postal>\d{5}(?:-\d{4})?)",
        value.strip(),
    )
    if not match:
        return None
    return match.group("city").strip(), match.group("region").strip(), match.group("postal")


def _parse_city_region(value: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"(?P<city>.+?),\s*(?P<region>[A-Za-z][A-Za-z .'-]*)", value.strip())
    if not match:
        return None
    return match.group("city").strip(), match.group("region").strip()


def _parse_combined_street_city_region(value: str) -> tuple[str, str, str] | None:
    """Parse SEC cover cells that collapse street + city/state into one text block."""
    city_region = _parse_city_region(value)
    if not city_region:
        return None
    left, region = city_region
    match = STREET_BOUNDARY.fullmatch(left.strip())
    if not match:
        return None
    return match.group("street").strip(), match.group("city").strip(), region


def _plausible_street(value: str) -> bool:
    lowered = value.casefold()
    if "address of principal executive offices" in lowered:
        return False
    if "state or other jurisdiction" in lowered or "employer identification" in lowered:
        return False
    return bool(re.search(r"\d", value)) and len(value) <= 180


def extract_principal_executive_office(raw_html: str) -> dict[str, str]:
    blocks = html_blocks(raw_html)
    marker_index = next(
        (index for index, value in enumerate(blocks) if "address of principal executive offices" in value.casefold()),
        None,
    )
    if marker_index is None:
        raise ValueError("SEC filing does not expose an 'Address of principal executive offices' marker")

    window = blocks[max(0, marker_index - 8):marker_index]
    street: str | None = None
    city: str | None = None
    region: str | None = None
    postal: str | None = None

    if window and re.fullmatch(r"\d{5}(?:-\d{4})?", window[-1]):
        postal = window[-1]
        if len(window) >= 2:
            combined = _parse_combined_street_city_region(window[-2])
            if combined:
                street, city, region = combined
            else:
                city_region = _parse_city_region(window[-2])
                if city_region:
                    city, region = city_region
                    for candidate in reversed(window[:-2]):
                        if _plausible_street(candidate):
                            street = candidate
                            break
    else:
        for index in range(len(window) - 1, -1, -1):
            parsed = _parse_city_region_postal(window[index])
            if not parsed:
                continue
            city_candidate, region_candidate, postal_candidate = parsed
            combined = _parse_combined_street_city_region(f"{city_candidate}, {region_candidate}")
            if combined:
                street, city, region = combined
                postal = postal_candidate
                break
            city, region, postal = city_candidate, region_candidate, postal_candidate
            for candidate in reversed(window[:index]):
                if _plausible_street(candidate):
                    street = candidate
                    break
            break

    if not all((street, city, region, postal)):
        context = " | ".join(window[-5:])
        raise ValueError(f"could not parse principal executive office near SEC cover marker: {context}")

    address = f"{street}, {city}, {region} {postal}"
    return {
        "address": address,
        "street": street,
        "city": city,
        "region": region,
        "postal": postal,
        "country": "United States",
    }


def extract_principal_office_notice(raw_html: str) -> dict[str, str]:
    """Extract an explicit effective-date principal-office change from company IR HTML."""
    text = " ".join(html_blocks(raw_html))
    match = NOTICE_PATTERN.search(text)
    if not match:
        raise ValueError("company notice does not expose an effective principal executive office address")
    effective_date = datetime.strptime(match.group("date"), "%B %d, %Y").date().isoformat()
    street = match.group("street").strip()
    city = match.group("city").strip()
    region = match.group("region").strip()
    postal = match.group("postal")
    return {
        "address": f"{street}, {city}, {region} {postal}",
        "street": street,
        "city": city,
        "region": region,
        "postal": postal,
        "country": "United States",
        "effective_date": effective_date,
    }


def office_observation(
    *,
    org_id: str,
    office: dict[str, str],
    form: str,
    filing_date: str,
    accession: str,
    filing_url: str,
    retrieved_at: str,
) -> dict[str, Any]:
    return {
        "subject_id": org_id,
        "observation_type": "sec_reported_principal_executive_office",
        "value": {
            **office,
            "location_type": "principal_executive_office",
            "source_semantics": "Address of principal executive offices",
            "form": form,
            "filing_date": filing_date,
            "accession": accession,
            "filing_url": filing_url,
            "retrieved_at": retrieved_at,
        },
        "method": "SEC filing cover-page extraction",
        "instrument": "sec.gov filing HTML",
        "observed_at": f"{filing_date}T00:00:00Z",
    }


def deduplicate_history(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = (str(item.get("address", "")), str(item.get("filing_date", "")))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def fetch_text(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    opener: Callable[..., Any] = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
    attempts: int = 3,
    timeout: float = 30.0,
) -> str:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    for attempt in range(1, attempts + 1):
        try:
            with opener(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP or attempt == attempts:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else float(attempt)
            sleeper(delay)
        except URLError:
            if attempt == attempts:
                raise
            sleeper(float(attempt))
    raise RuntimeError("unreachable retry loop")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a source-faithful principal-executive-office observation from an SEC filing cover page."
    )
    parser.add_argument("filing_url")
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--form", required=True)
    parser.add_argument("--filing-date", required=True)
    parser.add_argument("--accession", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    raw = fetch_text(args.filing_url, user_agent=args.user_agent)
    office = extract_principal_executive_office(raw)
    observation = office_observation(
        org_id=args.org_id,
        office=office,
        form=args.form,
        filing_date=args.filing_date,
        accession=args.accession,
        filing_url=args.filing_url,
        retrieved_at=args.retrieved_at,
    )
    print(json.dumps(observation, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
