#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

import scrape_violent_offender_localities as core

DEFAULT_OUTPUT = Path("artifacts/violent-offender-localities/expanded")

EXTRA_SOURCES = {
    "clermont": {
        "locality": "Batavia / Clermont County, Ohio",
        "kind": "clermont-html",
        "url": "https://www.clermontsheriff.org/jail-inmate-search",
        "publisher": "Clermont County Sheriff's Office",
    },
    "greene": {
        "locality": "Xenia / Greene County, Ohio",
        "kind": "ocv-detail",
        "url": "https://www.sheriff.greenecountyohio.gov/inmateSearch",
        "publisher": "Greene County Sheriff's Office",
        "detail_segment": "inmateSearch",
    },
    "pickaway": {
        "locality": "Circleville / Pickaway County, Ohio",
        "kind": "ocv-detail",
        "url": "https://www.pickawaysheriff.gov/activeInmates",
        "publisher": "Pickaway County Sheriff's Office",
        "detail_segment": "activeInmates",
    },
}


def extra_case_numbers(text: str) -> list[str]:
    found = core.case_numbers(text)
    for pattern in (
        r"\b\d{4}\s+CR(?:\s+[AB])?\s+\d{3,7}\b",
        r"\b\d{4}\s+TR(?:\s+[A-Z])?\s+\d{3,7}\b",
    ):
        found.extend(match.group(0) for match in re.finditer(pattern, text, re.IGNORECASE))
    return core.unique(found)


def clermont_blocks(markup: str) -> list[tuple[str, list[str]]]:
    lines = core.text_lines(markup)
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        name: str | None = None
        inline = re.fullmatch(r"(.+?,\s*.+?)\s*-\s*Details", line, re.IGNORECASE)
        if inline:
            name = core.normalize_space(inline.group(1))
        else:
            split = re.fullmatch(r"(.+?,\s*.+?)\s*-\s*", line, re.IGNORECASE)
            if split and index + 1 < len(lines) and lines[index + 1].casefold() == "details":
                name = core.normalize_space(split.group(1))
        if name and 4 <= len(name) <= 120:
            starts.append((index, name))

    blocks: list[tuple[str, list[str]]] = []
    for position, (start, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        blocks.append((name, lines[start:end]))
    return blocks


def clermont_booking(block: list[str]) -> tuple[str | None, str | None]:
    try:
        header = block.index("Booking Date")
    except ValueError:
        return None, None
    values = block[header + 1 : header + 5]
    if len(values) < 4:
        return None, None
    booking_id = values[2] if re.fullmatch(r"[0-9A-Za-z-]+", values[2]) else None
    booking_date = values[3] if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", values[3]) else None
    return booking_id, booking_date


def parse_clermont_html(markup: str, fetched_at: str) -> list[core.BookingRecord]:
    spec = EXTRA_SOURCES["clermont"]
    records: list[core.BookingRecord] = []
    for name, block in clermont_blocks(markup):
        try:
            marker = block.index("Charges")
            charge_lines = block[marker + 1 :]
        except ValueError:
            charge_lines = block
        charges = core.violent_lines(charge_lines)
        if not charges:
            continue
        booking_id, booking_date = clermont_booking(block)
        text = "\n".join(block)
        records.append(
            core.BookingRecord(
                source="clermont",
                locality=spec["locality"],
                publisher=spec["publisher"],
                name=name,
                source_url=spec["url"],
                booking_id=booking_id,
                booking_date=booking_date,
                case_numbers=extra_case_numbers(text),
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records


def ocv_detail_links(markup: str, base_url: str, segment: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(markup, "html.parser")
    by_url: dict[str, str] = {}
    path_re = re.compile(rf"/{re.escape(segment)}/\d+/?$", re.IGNORECASE)
    for anchor in soup.find_all("a", href=True):
        url = urljoin(base_url, anchor["href"])
        if not path_re.search(urlparse(url).path):
            continue
        name = core.normalize_space(anchor.get_text(" "))
        if not name or name.casefold() == "view charges":
            continue
        if "," not in name:
            continue
        by_url[url] = name
    return list(by_url.items())


def ocv_detail_record(source: str, name: str, markup: str, detail_url: str, fetched_at: str) -> core.BookingRecord | None:
    spec = EXTRA_SOURCES[source]
    lines = core.text_lines(markup)
    charges = core.violent_lines(lines)
    if not charges:
        return None
    text = "\n".join(lines)
    inmate_id = re.search(r"Inmate ID:\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booking_id = re.search(r"Booking (?:Number|#):\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booked = re.search(r"Booked Date:\s*([^\n]+)", text, re.IGNORECASE)
    booking_date = re.search(r"Booking Date:\s*([^\n]+)", text, re.IGNORECASE)
    status = re.search(r"Custody Status:\s*([^\n]+)", text, re.IGNORECASE)
    identity = booking_id or inmate_id
    date_match = booked or booking_date
    return core.BookingRecord(
        source=source,
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=identity.group(1) if identity else None,
        booking_date=core.normalize_space(date_match.group(1)) if date_match else None,
        status=core.normalize_space(status.group(1)) if status else None,
        case_numbers=extra_case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


async def fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    response = await client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response


async def collect_clermont(client: httpx.AsyncClient, fetched_at: str) -> core.SourceResult:
    spec = EXTRA_SOURCES["clermont"]
    response = await fetch(client, spec["url"])
    blocks = clermont_blocks(response.text)
    records = parse_clermont_html(response.text, fetched_at)
    return core.SourceResult("clermont", spec["locality"], spec["url"], fetched_at, records, 1, len(blocks))


async def collect_ocv(source: str, client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = EXTRA_SOURCES[source]
    response = await fetch(client, spec["url"])
    links = ocv_detail_links(response.text, str(response.url), spec["detail_segment"])
    semaphore = asyncio.Semaphore(8)
    pages = 1

    async def load(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages
        url, name = item
        async with semaphore:
            detail = await fetch(client, url)
            pages += 1
            return ocv_detail_record(source, name, detail.text, str(detail.url), fetched_at)

    records: list[core.BookingRecord] = []
    tasks = [asyncio.create_task(load(item)) for item in links[:max_records]]
    for task in asyncio.as_completed(tasks):
        record = await task
        if record:
            records.append(record)
    return core.SourceResult(source, spec["locality"], spec["url"], fetched_at, records, pages, len(links))


class ExtraCollectorActor:
    def __init__(self, source: str, mailbox: asyncio.Queue[core.SourceResult], timeout: float, max_records: int):
        self.source = source
        self.mailbox = mailbox
        self.timeout = timeout
        self.max_records = max_records

    async def run(self) -> None:
        spec = EXTRA_SOURCES[self.source]
        fetched_at = core.utc_now()
        headers = {"User-Agent": core.USER_AGENT, "Accept": "text/html,*/*;q=0.8"}
        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                if spec["kind"] == "clermont-html":
                    result = await collect_clermont(client, fetched_at)
                else:
                    result = await collect_ocv(self.source, client, fetched_at, self.max_records)
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
    actors = [ExtraCollectorActor(source, mailbox, timeout, max_records) for source in sources]
    tasks = [asyncio.create_task(actor.run(), name=f"extra-collector:{actor.source}") for actor in actors]
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
    parser = argparse.ArgumentParser(description="Collect additional Ohio locality jail feeds")
    parser.add_argument("--source", action="append", choices=sorted(EXTRA_SOURCES), dest="sources")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--max-records-per-source", type=int, default=5000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = asyncio.run(collect_all(args.sources or list(EXTRA_SOURCES), args.timeout, args.max_records_per_source))
    write_outputs(args.output, results)
    for result in results:
        status = f"error={result.error}" if result.error else f"records={len(result.records)} candidates={result.candidates_seen} pages={result.pages_fetched}"
        print(f"{result.source}: {status}")
    return 2 if any(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
