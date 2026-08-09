#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
from dataclasses import asdict
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

import scrape_violent_offender_high_yield as high
import scrape_violent_offender_localities as core

DEFAULT_OUTPUT = Path("artifacts/violent-offender-localities/batch2")

SOURCES = {
    "lorain": {
        "locality": "Elyria / Lorain County, Ohio",
        "kind": "newworld",
        "url": "https://loraincooh-wii.publicsafety.tylerapp.com/Default/",
        "publisher": "Lorain County Sheriff's Office",
    },
    "summit": {
        "locality": "Akron / Summit County, Ohio",
        "kind": "summit-roster",
        "url": "https://sheriff.summitoh.net/files/Current-Inmate-Roster.html",
        "publisher": "Summit County Sheriff's Office",
    },
}

SUMMIT_INMATE_RE = re.compile(
    r"(?m)^\s*(\d{3,})\s+(\S+)\s+([A-Z][A-Z .,'’-]+?)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+([A-Z])\s+([MF])\s*$"
)
SUMMIT_ARREST_RE = re.compile(
    r"(?m)^\s*(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+([A-Z0-9-]+)\s+.*$"
)


def response_text(content: bytes, content_type: str) -> str:
    if content.startswith(b"%PDF") or "application/pdf" in content_type.casefold():
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return BeautifulSoup(content, "html.parser").get_text("\n")


def summit_records(text: str, fetched_at: str) -> list[core.BookingRecord]:
    spec = SOURCES["summit"]
    matches = list(SUMMIT_INMATE_RE.finditer(text))
    records: list[core.BookingRecord] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        charges = core.violent_lines(block.splitlines())
        if not charges:
            continue
        arrest = SUMMIT_ARREST_RE.search(block)
        arrest_date = None
        agency = None
        if arrest:
            arrest_date = core.normalize_space(f"{arrest.group(1)} {arrest.group(2)}")
            agency = arrest.group(3)
        records.append(
            core.BookingRecord(
                source="summit",
                locality=spec["locality"],
                publisher=spec["publisher"],
                name=core.normalize_space(match.group(3)),
                source_url=spec["url"],
                booking_id=match.group(1),
                arrest_date=arrest_date,
                arresting_agency=agency,
                status="current",
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records


def lorain_record(name: str, markup: str, detail_url: str, fetched_at: str) -> core.BookingRecord | None:
    spec = SOURCES["lorain"]
    block = high.first_booking_block(markup)
    if not block:
        return None
    charges = core.violent_lines(block)
    if not charges:
        return None
    text = "\n".join(block)
    booking = re.match(r"Booking\s+(\d{4}-\d+)", block[0], re.IGNORECASE)
    return core.BookingRecord(
        source="lorain",
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=booking.group(1) if booking else None,
        booking_date=high.labeled_value(block, "Booking Date"),
        arresting_agency=high.labeled_value(block, "Booking Origin"),
        release_date=high.labeled_value(block, "Release Date"),
        case_numbers=high.newworld_case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


async def fetch(client: httpx.AsyncClient, url: str, *, params: dict[str, str | int] | None = None) -> httpx.Response:
    response = await client.get(url, params=params, follow_redirects=True)
    response.raise_for_status()
    return response


async def collect_lorain(client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = SOURCES["lorain"]
    first = await fetch(client, spec["url"], params={"InCustody": "True", "Page": 1})
    page_count = high.newworld_page_count(first.text)
    pages = 1
    links: dict[str, str] = dict(high.newworld_detail_links(first.text, str(first.url)))

    async def load_page(page: int) -> list[tuple[str, str]]:
        response = await fetch(client, spec["url"], params={"InCustody": "True", "Page": page})
        return high.newworld_detail_links(response.text, str(response.url))

    page_tasks = [asyncio.create_task(load_page(page)) for page in range(2, page_count + 1)]
    for task in asyncio.as_completed(page_tasks):
        for url, name in await task:
            links[url] = name
        pages += 1
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
            return lorain_record(name, response.text, str(response.url), fetched_at)

    records: list[core.BookingRecord] = []
    tasks = [asyncio.create_task(load_detail(item)) for item in list(links.items())[:max_records]]
    for task in asyncio.as_completed(tasks):
        record = await task
        if record:
            records.append(record)
    return core.SourceResult("lorain", spec["locality"], spec["url"], fetched_at, records, pages, len(links))


async def collect_summit(client: httpx.AsyncClient, fetched_at: str) -> core.SourceResult:
    spec = SOURCES["summit"]
    response = await fetch(client, spec["url"])
    text = await asyncio.to_thread(response_text, response.content, response.headers.get("content-type", ""))
    all_inmates = list(SUMMIT_INMATE_RE.finditer(text))
    records = summit_records(text, fetched_at)
    return core.SourceResult("summit", spec["locality"], spec["url"], fetched_at, records, 1, len(all_inmates))


class Batch2CollectorActor:
    def __init__(self, source: str, mailbox: asyncio.Queue[core.SourceResult], timeout: float, max_records: int):
        self.source = source
        self.mailbox = mailbox
        self.timeout = timeout
        self.max_records = max_records

    async def run(self) -> None:
        spec = SOURCES[self.source]
        fetched_at = core.utc_now()
        headers = {"User-Agent": core.USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8"}
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=12)
        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, limits=limits) as client:
                if spec["kind"] == "newworld":
                    result = await collect_lorain(client, fetched_at, self.max_records)
                else:
                    result = await collect_summit(client, fetched_at)
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
    actors = [Batch2CollectorActor(source, mailbox, timeout, max_records) for source in sources]
    tasks = [asyncio.create_task(actor.run(), name=f"batch2:{actor.source}") for actor in actors]
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
    parser = argparse.ArgumentParser(description="Collect Lorain and Summit violent-charge jail records")
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
