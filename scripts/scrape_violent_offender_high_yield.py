#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

import scrape_violent_offender_localities as core

DEFAULT_OUTPUT = Path("artifacts/violent-offender-localities/high-yield")

SOURCES = {
    "allen": {
        "locality": "Lima / Allen County, Ohio",
        "kind": "newworld",
        "url": "https://cadwebview.acso-oh.us/NewWorld.InmateInquiry/OH0020000",
        "publisher": "Allen County Sheriff's Office",
    },
    "hancock": {
        "locality": "Findlay / Hancock County, Ohio",
        "kind": "newworld",
        "url": "https://inmates.findlayohio.gov/NewWorld.InmateInquiry/OH0320000",
        "publisher": "Hancock County Sheriff's Office",
    },
    "muskingum": {
        "locality": "Zanesville / Muskingum County, Ohio",
        "kind": "newworld",
        "url": "https://inmatesearch.corp1840.ohiomuskingumsheriff.org/NewWorld.InmateInquiry/OH0600000",
        "publisher": "Muskingum County Sheriff's Office",
    },
    "mahoning": {
        "locality": "Youngstown / Mahoning County, Ohio",
        "kind": "mahoning",
        "url": "https://pii.mahoningcountyoh.gov/",
        "publisher": "Mahoning County Sheriff's Office",
    },
}

NEWORLD_LABELS = {
    "booking date",
    "release date",
    "scheduled release date",
    "prisoner type",
    "classification",
    "housing facility",
    "total bond amount",
    "total bail amount",
    "booking origin",
    "bond number",
    "bond type",
    "bond amount",
    "charges",
    "court date",
    "court",
    "court room",
    "number",
    "charge description",
    "offense date",
    "docket number",
    "sentence date",
    "disposition",
    "disposition date",
    "sentence length",
    "crime class",
    "arresting agency",
    "attempt/commit",
    "bond",
}


def newworld_case_numbers(text: str) -> list[str]:
    found = core.case_numbers(text)
    for pattern in (
        r"\b\d{2,4}CR[A-Z]?\d{3,7}[A-Z]?\b",
        r"\bCR\d{4}-\d{3,7}\b",
        r"\bCR[AB]\d{6,8}\b",
        r"\bTRC\d{6,8}\b",
        r"\bCRA\d{6,8}\b",
    ):
        found.extend(match.group(0) for match in re.finditer(pattern, text, re.IGNORECASE))
    return core.unique(found)


def newworld_page_count(markup: str) -> int:
    text = BeautifulSoup(markup, "html.parser").get_text(" ")
    match = re.search(r"Showing\s+(\d+)\s+to\s+(\d+)\s+of\s+(\d+)", text, re.IGNORECASE)
    if not match:
        return 1
    first, last, total = (int(value) for value in match.groups())
    page_size = max(1, last - first + 1)
    return max(1, math.ceil(total / page_size))


def newworld_detail_links(markup: str, base_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(markup, "html.parser")
    output: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/inmate/detail/" not in href.casefold():
            continue
        name = core.normalize_space(anchor.get_text(" "))
        if not name or "," not in name:
            continue
        output[urljoin(base_url, href)] = name
    return list(output.items())


def first_booking_block(markup: str) -> list[str]:
    lines = core.text_lines(markup)
    starts = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r"Booking\s+\d{4}-\d+", line, re.IGNORECASE)
    ]
    if not starts:
        return []
    start = starts[0]
    end = starts[1] if len(starts) > 1 else len(lines)
    return lines[start:end]


def labeled_value(lines: list[str], label: str) -> str | None:
    folded = label.casefold()
    for index, line in enumerate(lines):
        current = line.casefold()
        if current.startswith(folded + " "):
            value = core.normalize_space(line[len(label) :])
            return value or None
        if current != folded or index + 1 >= len(lines):
            continue
        value = core.normalize_space(lines[index + 1])
        if value.casefold() in NEWORLD_LABELS:
            return None
        return value or None
    return None


def newworld_record(source: str, name: str, markup: str, detail_url: str, fetched_at: str) -> core.BookingRecord | None:
    spec = SOURCES[source]
    block = first_booking_block(markup)
    if not block:
        return None
    charges = core.violent_lines(block)
    if not charges:
        return None
    text = "\n".join(block)
    booking = re.match(r"Booking\s+(\d{4}-\d+)", block[0], re.IGNORECASE)
    return core.BookingRecord(
        source=source,
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=booking.group(1) if booking else None,
        booking_date=labeled_value(block, "Booking Date"),
        arresting_agency=labeled_value(block, "Booking Origin"),
        release_date=labeled_value(block, "Release Date"),
        case_numbers=newworld_case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


def mahoning_detail_links(markup: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(markup, "html.parser")
    output: list[str] = []
    for anchor in soup.find_all("a", href=True):
        url = urljoin(base_url, anchor["href"])
        query = parse_qs(urlparse(url).query)
        if query.get("bookingID") and query.get("inmateID"):
            output.append(url)
    return core.unique(output)


def mahoning_record(markup: str, detail_url: str, fetched_at: str) -> core.BookingRecord | None:
    spec = SOURCES["mahoning"]
    lines = core.text_lines(markup)
    text = "\n".join(lines)
    charges = core.violent_lines(lines)
    if not charges:
        return None
    name = re.search(r"Inmate Name:\s*([^\n]+)", text, re.IGNORECASE)
    booking = re.search(r"Booking Number:\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booking_date = re.search(r"Booking Date:\s*([^\n]+)", text, re.IGNORECASE)
    release_date = re.search(r"Release Date:\s*([^\n]+)", text, re.IGNORECASE)
    agency = re.search(r"Arresting Agency:\s*([^\n]+)", text, re.IGNORECASE)
    status = re.search(r"Status:\s*([^\n]+)", text, re.IGNORECASE)
    if not name:
        return None
    return core.BookingRecord(
        source="mahoning",
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=core.normalize_space(name.group(1)),
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=booking.group(1) if booking else None,
        booking_date=core.normalize_space(booking_date.group(1)) if booking_date else None,
        arresting_agency=core.normalize_space(agency.group(1)) if agency else None,
        status=core.normalize_space(status.group(1)) if status else None,
        release_date=core.normalize_space(release_date.group(1)) if release_date else None,
        case_numbers=newworld_case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


async def fetch(client: httpx.AsyncClient, url: str, *, params: dict[str, str | int] | None = None) -> httpx.Response:
    response = await client.get(url, params=params, follow_redirects=True)
    response.raise_for_status()
    return response


async def collect_newworld(source: str, client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = SOURCES[source]
    first = await fetch(client, spec["url"], params={"InCustody": "True", "Page": 1})
    page_count = newworld_page_count(first.text)
    pages = 1
    links: dict[str, str] = dict(newworld_detail_links(first.text, str(first.url)))

    async def load_page(page: int) -> list[tuple[str, str]]:
        response = await fetch(client, spec["url"], params={"InCustody": "True", "Page": page})
        return newworld_detail_links(response.text, str(response.url))

    page_tasks = [asyncio.create_task(load_page(page)) for page in range(2, page_count + 1)]
    for task in asyncio.as_completed(page_tasks):
        page_links = await task
        pages += 1
        for url, name in page_links:
            links[url] = name
        if len(links) >= max_records:
            for pending in page_tasks:
                if not pending.done():
                    pending.cancel()
            break
    await asyncio.gather(*page_tasks, return_exceptions=True)

    semaphore = asyncio.Semaphore(12)

    async def load_detail(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages
        url, name = item
        async with semaphore:
            response = await fetch(client, url)
            pages += 1
            return newworld_record(source, name, response.text, str(response.url), fetched_at)

    records: list[core.BookingRecord] = []
    tasks = [asyncio.create_task(load_detail(item)) for item in list(links.items())[:max_records]]
    for task in asyncio.as_completed(tasks):
        record = await task
        if record:
            records.append(record)
    return core.SourceResult(source, spec["locality"], spec["url"], fetched_at, records, pages, len(links))


async def collect_mahoning(client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = SOURCES["mahoning"]
    response = await fetch(client, spec["url"])
    links = mahoning_detail_links(response.text, str(response.url))[:max_records]
    pages = 1
    semaphore = asyncio.Semaphore(12)

    async def load_detail(url: str) -> core.BookingRecord | None:
        nonlocal pages
        async with semaphore:
            detail = await fetch(client, url)
            pages += 1
            return mahoning_record(detail.text, str(detail.url), fetched_at)

    records: list[core.BookingRecord] = []
    tasks = [asyncio.create_task(load_detail(url)) for url in links]
    for task in asyncio.as_completed(tasks):
        record = await task
        if record:
            records.append(record)
    return core.SourceResult("mahoning", spec["locality"], spec["url"], fetched_at, records, pages, len(links))


class HighYieldCollectorActor:
    def __init__(self, source: str, mailbox: asyncio.Queue[core.SourceResult], timeout: float, max_records: int):
        self.source = source
        self.mailbox = mailbox
        self.timeout = timeout
        self.max_records = max_records

    async def run(self) -> None:
        spec = SOURCES[self.source]
        fetched_at = core.utc_now()
        headers = {"User-Agent": core.USER_AGENT, "Accept": "text/html,*/*;q=0.8"}
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=12)
        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, limits=limits) as client:
                if spec["kind"] == "newworld":
                    result = await collect_newworld(self.source, client, fetched_at, self.max_records)
                else:
                    result = await collect_mahoning(client, fetched_at, self.max_records)
        except Exception as exc:
            result = core.SourceResult(
                source=self.source,
                locality=spec["locality"],
                source_url=spec["url"],
                fetched_at=fetched_at,
                error=f"{type(exc).__name__}: {exc}",
            )
        await self.mailbox.put(result)


async def collect_all(sources: list[str], timeout: float, max_records: int) -> list[core.SourceResult]:
    mailbox: asyncio.Queue[core.SourceResult] = asyncio.Queue()
    actors = [HighYieldCollectorActor(source, mailbox, timeout, max_records) for source in sources]
    tasks = [asyncio.create_task(actor.run(), name=f"high-yield:{actor.source}") for actor in actors]
    results = [await mailbox.get() for _ in actors]
    await asyncio.gather(*tasks)
    return sorted(results, key=lambda result: result.source)


def write_outputs(output: Path, results: list[core.SourceResult]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    records = core.dedupe_records(results)
    with (output / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "generated_at": core.utc_now(),
        "record_count": len(records),
        "sources": [
            {
                "source": result.source,
                "locality": result.locality,
                "source_url": result.source_url,
                "fetched_at": result.fetched_at,
                "records": len(result.records),
                "candidates_seen": result.candidates_seen,
                "pages_fetched": result.pages_fetched,
                "error": result.error,
            }
            for result in results
        ],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect high-yield Ohio inmate feeds with violent-charge matching")
    parser.add_argument("--source", action="append", choices=sorted(SOURCES), dest="sources")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--max-records-per-source", type=int, default=5000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = asyncio.run(collect_all(args.sources or list(SOURCES), args.timeout, args.max_records_per_source))
    write_outputs(args.output, results)
    for result in results:
        status = f"error={result.error}" if result.error else f"records={len(result.records)} candidates={result.candidates_seen} pages={result.pages_fetched}"
        print(f"{result.source}: {status}")
    return 2 if any(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
