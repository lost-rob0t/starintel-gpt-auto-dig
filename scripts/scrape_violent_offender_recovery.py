#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

import scrape_violent_offender_batch2 as batch2
import scrape_violent_offender_high_yield as high
import scrape_violent_offender_localities as core
import scrape_violent_offender_localities_extra as extra

DEFAULT_OUTPUT = Path("artifacts/violent-offender-localities/recovered")

RECOVERY_SOURCES = {
    "franklin": core.SOURCE_SPECS["franklin"],
    "madison": core.SOURCE_SPECS["madison"],
    "lucas": core.SOURCE_SPECS["lucas"],
    "allen": high.SOURCES["allen"],
    "hancock": high.SOURCES["hancock"],
    "muskingum": high.SOURCES["muskingum"],
    "mahoning": high.SOURCES["mahoning"],
    "lorain": batch2.SOURCES["lorain"],
    "summit": batch2.SOURCES["summit"],
}

BOOKING_HEADER_RE = re.compile(r"\bBooking\s+(\d{4}-\d+)\b", re.IGNORECASE)
POSTBACK_RE = re.compile(r"__doPostBack\('([^']*)','([^']*)'\)", re.IGNORECASE)


async def fetch(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str = "GET",
    params: dict[str, str | int] | None = None,
    data: dict[str, str] | None = None,
    attempts: int = 3,
) -> httpx.Response:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            response = await client.request(method, url, params=params, data=data, follow_redirects=True)
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            last = exc
            retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code >= 500
            if not retryable or attempt + 1 >= attempts:
                raise
            await asyncio.sleep(0.6 * (2**attempt))
    assert last is not None
    raise last


def booking_blocks(markup: str) -> list[list[str]]:
    lines = core.text_lines(markup)
    starts = [index for index, line in enumerate(lines) if BOOKING_HEADER_RE.search(line)]
    return [
        lines[start : starts[position + 1] if position + 1 < len(starts) else len(lines)]
        for position, start in enumerate(starts)
    ]


def booking_id(block: list[str]) -> str | None:
    if not block:
        return None
    match = BOOKING_HEADER_RE.search(block[0])
    return match.group(1) if match else None


def booking_sort_key(block: list[str]) -> tuple[int, ...]:
    value = booking_id(block) or ""
    return tuple(int(piece) for piece in re.findall(r"\d+", value))


def has_blank_release_date(block: list[str]) -> bool:
    for index, line in enumerate(block):
        folded = line.casefold()
        if folded.startswith("release date "):
            return False
        if folded != "release date":
            continue
        if index + 1 >= len(block):
            return True
        next_line = block[index + 1].casefold()
        if next_line in high.NEWORLD_LABELS or next_line.startswith("scheduled release date"):
            return True
        return False
    return False


def current_booking_block(markup: str) -> list[str]:
    blocks = booking_blocks(markup)
    if not blocks:
        return []
    active = [block for block in blocks if has_blank_release_date(block)]
    pool = active or blocks
    return max(pool, key=booking_sort_key)


def recovered_newworld_record(
    source: str,
    name: str,
    markup: str,
    detail_url: str,
    fetched_at: str,
) -> core.BookingRecord | None:
    spec = RECOVERY_SOURCES[source]
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


async def collect_newworld(
    source: str,
    client: httpx.AsyncClient,
    fetched_at: str,
    max_records: int,
) -> core.SourceResult:
    spec = RECOVERY_SOURCES[source]
    first = await fetch(client, spec["url"], params={"InCustody": "True", "Page": 1})
    page_count = high.newworld_page_count(first.text)
    pages = 1
    links: dict[str, str] = dict(high.newworld_detail_links(first.text, str(first.url)))

    async def load_page(page: int) -> list[tuple[str, str]]:
        response = await fetch(client, spec["url"], params={"InCustody": "True", "Page": page})
        return high.newworld_detail_links(response.text, str(response.url))

    page_tasks = [asyncio.create_task(load_page(page)) for page in range(2, page_count + 1)]
    for task in asyncio.as_completed(page_tasks):
        try:
            for url, name in await task:
                links[url] = name
        except Exception:
            pass
        pages += 1
        if len(links) >= max_records:
            break
    await asyncio.gather(*page_tasks, return_exceptions=True)

    semaphore = asyncio.Semaphore(5)
    detail_failures = 0

    async def load_detail(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages, detail_failures
        url, name = item
        async with semaphore:
            try:
                response = await fetch(client, url)
                pages += 1
                return recovered_newworld_record(source, name, response.text, str(response.url), fetched_at)
            except Exception:
                detail_failures += 1
                return None

    tasks = [asyncio.create_task(load_detail(item)) for item in list(links.items())[:max_records]]
    records = [record for record in await asyncio.gather(*tasks) if record is not None]
    error = None
    if links and detail_failures == min(len(links), max_records):
        error = f"DetailFetchError: all {detail_failures} detail requests failed"
    return core.SourceResult(source, spec["locality"], spec["url"], fetched_at, records, pages, len(links), error)


def ocv_detail_links(markup: str, base_url: str, segment: str) -> list[tuple[str, str]]:
    return extra.ocv_detail_links(markup, base_url, segment)


def madison_record(name: str, markup: str, detail_url: str, fetched_at: str) -> core.BookingRecord | None:
    spec = RECOVERY_SOURCES["madison"]
    lines = core.text_lines(markup)
    charges = core.violent_lines(lines)
    if not charges:
        return None
    text = "\n".join(lines)
    inmate_id = re.search(r"Inmate ID\s*:?\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booking_id_match = re.search(r"Booking (?:Number|#)\s*:?\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booked = re.search(r"(?:Booked Date|Booking Date)\s*:?\s*([^\n]+)", text, re.IGNORECASE)
    agency = re.search(r"(?:Arresting )?Agency\s*:?\s*([^\n]+)", text, re.IGNORECASE)
    status = re.search(r"Custody Status\s*:?\s*([^\n]+)", text, re.IGNORECASE)
    identity = booking_id_match or inmate_id
    return core.BookingRecord(
        source="madison",
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=identity.group(1) if identity else None,
        booking_date=core.normalize_space(booked.group(1)) if booked else None,
        arresting_agency=core.normalize_space(agency.group(1)) if agency else None,
        status=core.normalize_space(status.group(1)) if status else None,
        case_numbers=core.case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


async def collect_madison(client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = RECOVERY_SOURCES["madison"]
    response = await fetch(client, spec["url"])
    links = ocv_detail_links(response.text, str(response.url), "inmateSearch")[:max_records]
    pages = 1
    semaphore = asyncio.Semaphore(5)

    async def load(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages
        url, name = item
        async with semaphore:
            detail = await fetch(client, url)
            pages += 1
            return madison_record(name, detail.text, str(detail.url), fetched_at)

    records = [record for record in await asyncio.gather(*(load(item) for item in links), return_exceptions=False) if record]
    error = None if links else "ParserDrift: Madison roster exposed no inmate detail links"
    return core.SourceResult("madison", spec["locality"], spec["url"], fetched_at, records, pages, len(links), error)


def mahoning_entries(markup: str, base_url: str) -> list[tuple[str, str]]:
    lines = core.text_lines(markup)
    output: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        if "," not in line or not re.fullmatch(r"[A-Z0-9 .,'’\-]+", line):
            continue
        block = "\n".join(lines[index : index + 9])
        inmate = re.search(r"Inmate ID:\s*([0-9A-Za-z-]+)", block, re.IGNORECASE)
        booking = re.search(r"Booking #:\s*([0-9A-Za-z-]+)", block, re.IGNORECASE)
        if not inmate or not booking:
            continue
        query = urlencode({"bookingID": booking.group(1), "inmateID": inmate.group(1)})
        output.append((urljoin(base_url, "?") + query, core.normalize_space(line)))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for url, name in output:
        if url in seen:
            continue
        seen.add(url)
        deduped.append((url, name))
    return deduped


async def collect_mahoning(client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = RECOVERY_SOURCES["mahoning"]
    response = await fetch(client, spec["url"])
    entries = mahoning_entries(response.text, str(response.url))[:max_records]
    pages = 1
    semaphore = asyncio.Semaphore(5)
    failures = 0

    async def load(item: tuple[str, str]) -> core.BookingRecord | None:
        nonlocal pages, failures
        url, _ = item
        async with semaphore:
            try:
                detail = await fetch(client, url)
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


def direct_detail_links(markup: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(markup, "html.parser")
    output: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        folded = href.casefold()
        if folded.startswith("javascript:"):
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        query = {key.casefold(): value for key, value in parse_qs(parsed.query).items()}
        path = parsed.path.casefold()
        looks_detail = (
            "bookingdetail" in path
            or "booking-detail" in path
            or "inmate-detail" in path
            or "inmatedetail" in path
            or (("booking" in path or "inmate" in path) and any(key in query for key in ("id", "bookingid", "inmateid")))
        )
        if looks_detail and "find" not in path and "search" not in path:
            output.append(url)
    return core.unique(output)


def postback_targets(markup: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(markup, "html.parser")
    output: list[tuple[str, str]] = []
    for tag in soup.find_all(True):
        for attribute in ("href", "onclick"):
            value = tag.get(attribute)
            if not value or "__doPostBack" not in value:
                continue
            match = POSTBACK_RE.search(value)
            if not match:
                continue
            target, argument = match.groups()
            folded = f"{target} {argument} {core.normalize_space(tag.get_text(' '))}".casefold()
            if any(token in folded for token in ("select", "detail", "booking", "inmate")):
                output.append((target, argument))
    return list(dict.fromkeys(output))


async def follow_postback(client: httpx.AsyncClient, markup: str, page_url: str, target: str, argument: str) -> httpx.Response:
    soup = BeautifulSoup(markup, "html.parser")
    form = soup.find("form")
    if not form:
        raise RuntimeError("postback page has no form")
    payload: dict[str, str] = {}
    for tag in form.find_all("input"):
        name = tag.get("name")
        if name and (tag.get("type") or "text").casefold() == "hidden":
            payload[name] = tag.get("value", "")
    payload["__EVENTTARGET"] = target
    payload["__EVENTARGUMENT"] = argument
    action = urljoin(page_url, form.get("action") or page_url)
    return await fetch(client, action, method="POST", data=payload)


async def collect_franklin(client: httpx.AsyncClient, fetched_at: str, max_records: int) -> core.SourceResult:
    spec = RECOVERY_SOURCES["franklin"]
    first = await fetch(client, spec["url"])
    pages = 1
    direct: dict[str, str] = {}
    postbacks: list[tuple[str, str, str, str]] = []
    postback_seen: set[tuple[str, str, str]] = set()

    prefixes = [""] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for prefix in prefixes:
        response = await core.submit_form_search(client, first.text, str(first.url), prefix)
        pages += 1
        for url in direct_detail_links(response.text, str(response.url)):
            direct[url] = url
        for target, argument in postback_targets(response.text):
            key = (str(response.url), target, argument)
            if key in postback_seen:
                continue
            postback_seen.add(key)
            postbacks.append((response.text, str(response.url), target, argument))
        if len(direct) + len(postbacks) >= max_records:
            break

    semaphore = asyncio.Semaphore(4)

    async def load_direct(url: str) -> core.BookingRecord | None:
        nonlocal pages
        async with semaphore:
            detail = await fetch(client, url)
            pages += 1
            return core.detail_record("franklin", detail.text, str(detail.url), fetched_at)

    async def load_postback(item: tuple[str, str, str, str]) -> core.BookingRecord | None:
        nonlocal pages
        markup, page_url, target, argument = item
        async with semaphore:
            detail = await follow_postback(client, markup, page_url, target, argument)
            pages += 1
            return core.detail_record("franklin", detail.text, str(detail.url), fetched_at)

    direct_items = list(direct)[:max_records]
    remaining = max(0, max_records - len(direct_items))
    tasks = [load_direct(url) for url in direct_items] + [load_postback(item) for item in postbacks[:remaining]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    records = [result for result in results if isinstance(result, core.BookingRecord)]
    candidates = len(direct_items) + min(len(postbacks), remaining)
    error = None if candidates else "ParserDrift: Franklin searches returned no direct detail links or ASP.NET detail postbacks"
    return core.SourceResult("franklin", spec["locality"], spec["url"], fetched_at, records, pages, candidates, error)


def lucas_candidates(text: str) -> list[tuple[str, str, str]]:
    lines = [core.normalize_space(line) for line in text.splitlines() if core.normalize_space(line)]
    output: list[tuple[str, str, str]] = []
    for index, line in enumerate(lines):
        match = re.search(r"^(.*?)\s+Book(?:ing)?\s+Dttm:\s*([0-9/]+(?:\s+[0-9:APM ]+)?)$", line, re.IGNORECASE)
        if match:
            output.append((match.group(1).strip(), match.group(2).strip(), "\n".join(lines[index:])))
            continue
        if re.fullmatch(r"Book(?:ing)?\s+Dttm:\s*[0-9/]+(?:\s+[0-9:APM ]+)?", line, re.IGNORECASE) and index:
            date = line.split(":", 1)[1].strip()
            output.append((lines[index - 1], date, "\n".join(lines[index - 1 :])))
    return output


def recovered_lucas_records(text: str, fetched_at: str) -> tuple[list[core.BookingRecord], int]:
    existing = core.parse_lucas_text(text, fetched_at)
    candidates = lucas_candidates(text)
    if existing:
        return existing, max(len(existing), len(candidates))
    records: list[core.BookingRecord] = []
    for position, (name, booking_date, _) in enumerate(candidates):
        start = text.find(name)
        next_start = text.find(candidates[position + 1][0], start + len(name)) if position + 1 < len(candidates) else -1
        block = text[start : next_start if next_start >= 0 else len(text)]
        charges = core.violent_lines(block.splitlines())
        if not charges:
            continue
        agency = re.search(r"Arresting Agency:\s*(.+?)(?:\s+Arrest Dttm:|\n)", block, re.IGNORECASE)
        arrest = re.search(r"Arrest Dttm:\s*([0-9/]+(?:\s+[0-9:APM ]+)?)", block, re.IGNORECASE)
        status = re.search(r"Current Status:\s*([^\n]+)", block, re.IGNORECASE)
        records.append(
            core.BookingRecord(
                source="lucas",
                locality=RECOVERY_SOURCES["lucas"]["locality"],
                publisher=RECOVERY_SOURCES["lucas"]["publisher"],
                name=core.normalize_space(name),
                source_url=RECOVERY_SOURCES["lucas"]["url"],
                booking_date=booking_date,
                arrest_date=core.normalize_space(arrest.group(1)) if arrest else None,
                arresting_agency=core.normalize_space(agency.group(1)) if agency else None,
                status=core.normalize_space(status.group(1)) if status else None,
                case_numbers=core.case_numbers(block),
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records, len(candidates)


async def collect_lucas(client: httpx.AsyncClient, fetched_at: str) -> core.SourceResult:
    spec = RECOVERY_SOURCES["lucas"]
    try:
        response = await fetch(client, spec["url"])
    except httpx.HTTPStatusError as exc:
        return core.SourceResult("lucas", spec["locality"], spec["url"], fetched_at, error=f"HTTPStatusError: {exc.response.status_code}")
    content_type = response.headers.get("content-type", "")
    if response.content.startswith(b"%PDF") or "application/pdf" in content_type.casefold():
        reader = PdfReader(io.BytesIO(response.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = BeautifulSoup(response.content, "html.parser").get_text("\n")
    records, candidates = recovered_lucas_records(text, fetched_at)
    error = None if candidates else "ParserDrift: Lucas response contained no booking markers"
    return core.SourceResult("lucas", spec["locality"], spec["url"], fetched_at, records, 1, candidates, error)


def summit_table_records(markup: str, fetched_at: str) -> tuple[list[core.BookingRecord], int]:
    soup = BeautifulSoup(markup, "html.parser")
    rows = [[core.normalize_space(cell.get_text(" ")) for cell in row.find_all(["th", "td"])] for row in soup.find_all("tr")]
    starts: list[int] = []
    for index, cells in enumerate(rows):
        if not cells or not re.fullmatch(r"\d{3,}", cells[0]):
            continue
        if any(re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", cell) for cell in cells) and any("," in cell for cell in cells):
            starts.append(index)
    records: list[core.BookingRecord] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(rows)
        header = rows[start]
        block_rows = rows[start:end]
        lines = [" ".join(row) for row in block_rows if row]
        charges = core.violent_lines(lines)
        if not charges:
            continue
        name = next((cell for cell in header if "," in cell), "")
        arrest_match = next((re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+([A-Z0-9-]+)", line) for line in lines if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", line)), None)
        records.append(
            core.BookingRecord(
                source="summit",
                locality=RECOVERY_SOURCES["summit"]["locality"],
                publisher=RECOVERY_SOURCES["summit"]["publisher"],
                name=core.normalize_space(name),
                source_url=RECOVERY_SOURCES["summit"]["url"],
                booking_id=header[0],
                arrest_date=core.normalize_space(f"{arrest_match.group(1)} {arrest_match.group(2)}") if arrest_match else None,
                arresting_agency=arrest_match.group(3) if arrest_match else None,
                status="current",
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records, len(starts)


async def collect_summit(client: httpx.AsyncClient, fetched_at: str) -> core.SourceResult:
    spec = RECOVERY_SOURCES["summit"]
    response = await fetch(client, spec["url"])
    pages = 1
    content = response.content
    content_type = response.headers.get("content-type", "")
    if not content.startswith(b"%PDF") and "application/pdf" not in content_type.casefold():
        soup = BeautifulSoup(content, "html.parser")
        pdf_ref = None
        for tag, attribute in (("iframe", "src"), ("embed", "src"), ("object", "data"), ("a", "href")):
            for node in soup.find_all(tag):
                value = node.get(attribute)
                if value and ".pdf" in value.casefold():
                    pdf_ref = urljoin(str(response.url), value)
                    break
            if pdf_ref:
                break
        if pdf_ref:
            pdf_response = await fetch(client, pdf_ref)
            pages += 1
            content = pdf_response.content
            content_type = pdf_response.headers.get("content-type", "")
    if content.startswith(b"%PDF") or "application/pdf" in content_type.casefold():
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        records = batch2.summit_records(text, fetched_at)
        candidates = len(list(batch2.SUMMIT_INMATE_RE.finditer(text)))
    else:
        markup = content.decode(response.encoding or "utf-8", errors="replace")
        text = BeautifulSoup(markup, "html.parser").get_text("\n")
        records = batch2.summit_records(text, fetched_at)
        candidates = len(list(batch2.SUMMIT_INMATE_RE.finditer(text)))
        if not candidates:
            records, candidates = summit_table_records(markup, fetched_at)
    error = None if candidates else "ParserDrift: Summit roster contained no recognizable inmate rows"
    return core.SourceResult("summit", spec["locality"], spec["url"], fetched_at, records, pages, candidates, error)


class RecoveryActor:
    def __init__(self, source: str, mailbox: asyncio.Queue[core.SourceResult], timeout: float, max_records: int):
        self.source = source
        self.mailbox = mailbox
        self.timeout = timeout
        self.max_records = max_records

    async def run(self) -> None:
        spec = RECOVERY_SOURCES[self.source]
        fetched_at = core.utc_now()
        headers = {"User-Agent": core.USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8"}
        limits = httpx.Limits(max_connections=12, max_keepalive_connections=6)
        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, limits=limits) as client:
                if self.source in {"allen", "hancock", "muskingum", "lorain"}:
                    result = await collect_newworld(self.source, client, fetched_at, self.max_records)
                elif self.source == "mahoning":
                    result = await collect_mahoning(client, fetched_at, self.max_records)
                elif self.source == "madison":
                    result = await collect_madison(client, fetched_at, self.max_records)
                elif self.source == "franklin":
                    result = await collect_franklin(client, fetched_at, self.max_records)
                elif self.source == "lucas":
                    result = await collect_lucas(client, fetched_at)
                elif self.source == "summit":
                    result = await collect_summit(client, fetched_at)
                else:
                    raise RuntimeError(f"unsupported recovery source: {self.source}")
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
    actors = [RecoveryActor(source, mailbox, timeout, max_records) for source in sources]
    tasks = [asyncio.create_task(actor.run(), name=f"recovery:{actor.source}") for actor in actors]
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
    parser = argparse.ArgumentParser(description="Recover violent-offender sources that previously produced false zeroes")
    parser.add_argument("--source", action="append", choices=sorted(RECOVERY_SOURCES), dest="sources")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=35.0)
    parser.add_argument("--max-records-per-source", type=int, default=10000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = asyncio.run(collect_all(args.sources or list(RECOVERY_SOURCES), args.timeout, args.max_records_per_source))
    write_outputs(args.output, results)
    for result in results:
        status = f"error={result.error}" if result.error else f"records={len(result.records)} candidates={result.candidates_seen} pages={result.pages_fetched}"
        print(f"{result.source}: {status}")
    return 2 if all(result.error for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
