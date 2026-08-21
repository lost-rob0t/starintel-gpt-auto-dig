#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import re
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

import scrape_violent_offender_high_yield as high
import scrape_violent_offender_localities as core
import scrape_violent_offender_recovery as recovery

BOOKING_COMBINED_RE = re.compile(r"^Booking\s+(\d{4}-\d+)$", re.IGNORECASE)
BOOKING_ID_RE = re.compile(r"^\d{4}-\d+$")


def booking_starts(lines: list[str]) -> list[tuple[int, str, int]]:
    """Return (line-index, booking-id, consumed-lines) for combined or split NewWorld headers."""
    starts: list[tuple[int, str, int]] = []
    for index, line in enumerate(lines):
        match = BOOKING_COMBINED_RE.fullmatch(line)
        if match:
            starts.append((index, match.group(1), 1))
            continue
        if line.casefold() == "booking" and index + 1 < len(lines) and BOOKING_ID_RE.fullmatch(lines[index + 1]):
            starts.append((index, lines[index + 1], 2))
            continue
        # Some Tyler renderings expose only the booking number as the heading text.
        if BOOKING_ID_RE.fullmatch(line):
            previous = lines[index - 1].casefold() if index else ""
            if previous in {"booking", "booking history"}:
                starts.append((index, line, 1))
    deduped: list[tuple[int, str, int]] = []
    seen: set[tuple[int, str]] = set()
    for item in starts:
        key = (item[0], item[1])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def booking_blocks(markup: str) -> list[list[str]]:
    lines = core.text_lines(markup)
    starts = booking_starts(lines)
    blocks: list[list[str]] = []
    for position, (start, booking_id, consumed) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        body_start = start + consumed
        block = [f"Booking {booking_id}", *lines[body_start:end]]
        blocks.append(block)
    return blocks


def booking_id(block: list[str]) -> str | None:
    if not block:
        return None
    match = BOOKING_COMBINED_RE.fullmatch(block[0])
    return match.group(1) if match else None


def current_booking_block(markup: str) -> list[str]:
    blocks = booking_blocks(markup)
    if not blocks:
        return []
    active = [block for block in blocks if recovery.has_blank_release_date(block)]
    pool = active or blocks
    return max(pool, key=lambda block: tuple(int(piece) for piece in re.findall(r"\d+", booking_id(block) or "")))


def recovered_newworld_record(
    source: str,
    name: str,
    markup: str,
    detail_url: str,
    fetched_at: str,
) -> core.BookingRecord | None:
    spec = recovery.RECOVERY_SOURCES[source]
    block = current_booking_block(markup)
    if not block:
        return None
    charges = core.violent_lines(block)
    if not charges:
        return None
    text = "\n".join(block)
    return core.BookingRecord(
        source=source,
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=booking_id(block),
        booking_date=high.labeled_value(block, "Booking Date"),
        arresting_agency=high.labeled_value(block, "Booking Origin"),
        release_date=high.labeled_value(block, "Release Date"),
        case_numbers=high.newworld_case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


def ocv_detail_links(markup: str, base_url: str, segment: str) -> list[tuple[str, str]]:
    """Accept numeric IDs and modern hexadecimal OCV detail tokens."""
    soup = BeautifulSoup(markup, "html.parser")
    output: list[tuple[str, str]] = []
    segment_folded = f"/{segment.casefold()}/"
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        absolute = urljoin(base_url, href)
        path = absolute.split("?", 1)[0].rstrip("/")
        folded = path.casefold()
        if segment_folded not in folded:
            continue
        tail = path.rsplit("/", 1)[-1]
        if not re.fullmatch(r"[0-9A-Fa-f]{16,}|\d+", tail):
            continue
        name = core.normalize_space(anchor.get_text(" "))
        if name:
            output.append((absolute, name))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for url, name in output:
        if url not in seen:
            seen.add(url)
            deduped.append((url, name))
    return deduped


def mahoning_entries(markup: str, base_url: str) -> list[tuple[str, str]]:
    lines = core.text_lines(markup)
    output: list[tuple[str, str]] = []
    root = base_url.split("?", 1)[0]
    if not root.endswith("/"):
        root += "/"
    for index, line in enumerate(lines):
        if "," not in line or not re.fullmatch(r"[A-Z0-9 .,'’\-]+", line):
            continue
        block = "\n".join(lines[index : index + 12])
        inmate = re.search(r"Inmate ID:\s*([0-9A-Za-z-]+)", block, re.IGNORECASE)
        booking = re.search(r"Booking #:\s*([0-9A-Za-z-]+)", block, re.IGNORECASE)
        if not inmate or not booking:
            continue
        query = urlencode({"bookingID": booking.group(1), "inmateID": inmate.group(1)})
        output.append((f"{root}?{query}", core.normalize_space(line)))
    seen: set[str] = set()
    return [(url, name) for url, name in output if not (url in seen or seen.add(url))]


async def collect_madison(client, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = recovery.RECOVERY_SOURCES["madison"]
    response = await recovery.fetch(client, spec["url"])
    links = ocv_detail_links(response.text, str(response.url), "inmateSearch")[:max_records]
    pages = 1
    semaphore = asyncio.Semaphore(5)
    failures = 0

    async def load(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages, failures
        url, name = item
        async with semaphore:
            try:
                detail = await recovery.fetch(client, url)
                pages += 1
                return recovery.madison_record(name, detail.text, str(detail.url), fetched_at)
            except Exception:
                failures += 1
                return None

    records = [record for record in await asyncio.gather(*(load(item) for item in links)) if record]
    error = None
    if not links:
        error = "ParserDrift: Madison roster exposed no inmate detail links"
    elif failures == len(links):
        error = f"DetailFetchError: all {failures} Madison detail requests failed"
    return core.SourceResult("madison", spec["locality"], spec["url"], fetched_at, records, pages, len(links), error)


async def collect_mahoning(client, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = recovery.RECOVERY_SOURCES["mahoning"]
    response = await recovery.fetch(client, spec["url"])
    entries = mahoning_entries(response.text, str(response.url))[:max_records]
    pages = 1
    semaphore = asyncio.Semaphore(4)
    failures = 0

    async def load(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages, failures
        url, _ = item
        async with semaphore:
            try:
                detail = await recovery.fetch(client, url)
                pages += 1
                return high.mahoning_record(detail.text, str(detail.url), fetched_at)
            except Exception:
                failures += 1
                return None

    records = [record for record in await asyncio.gather(*(load(item) for item in entries)) if record]
    error = None
    if not entries:
        error = "ParserDrift: Mahoning active roster yielded no booking/inmate identifiers"
    elif failures == len(entries):
        error = f"DetailFetchError: all {failures} Mahoning detail requests failed"
    return core.SourceResult("mahoning", spec["locality"], spec["url"], fetched_at, records, pages, len(entries), error)


def install() -> None:
    recovery.booking_blocks = booking_blocks
    recovery.booking_id = booking_id
    recovery.current_booking_block = current_booking_block
    recovery.recovered_newworld_record = recovered_newworld_record
    recovery.ocv_detail_links = ocv_detail_links
    recovery.collect_madison = collect_madison
    recovery.mahoning_entries = mahoning_entries
    recovery.collect_mahoning = collect_mahoning


install()

if __name__ == "__main__":
    raise SystemExit(recovery.main())
