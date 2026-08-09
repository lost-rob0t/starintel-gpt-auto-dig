#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

USER_AGENT = "StarIntel-AutoDig/0.9 locality-scraper (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
DEFAULT_OUTPUT = Path("artifacts/violent-offender-localities")

VIOLENT_PATTERNS = (
    r"\baggravated murder\b",
    r"\bmurder\b",
    r"\bmanslaughter\b",
    r"\bfelonious assault\b",
    r"\baggravated assault\b",
    r"\bassault\b",
    r"\bdomestic violence\b",
    r"\bstrang(?:ulation|ling|le)\b",
    r"\bsuffocat(?:ion|e|ing)\b",
    r"\bkidnapp(?:ing|ed)?\b",
    r"\babduction\b",
    r"\baggravated robbery\b",
    r"\brobbery\b",
    r"\baggravated burglary\b",
    r"\bburglary\b",
    r"\baggravated arson\b",
    r"\barson\b",
    r"\brape\b",
    r"\bsexual battery\b",
    r"\bgross sexual imposition\b",
    r"\bsexual imposition\b",
    r"\bmenacing by stalking\b",
    r"\baggravated menacing\b",
    r"\bmenacing\b",
    r"\bviolation of (?:a )?protection order\b",
    r"\bchild abuse\b",
    r"\bendangering children\b",
    r"\bphysical harm\b",
    r"\bserious physical harm\b",
    r"\bthreat(?:en|ens|ened|ening)? to inflict\b",
    r"\buse or threaten(?:ed|ing)? the immediate use of force\b",
    r"\bfighting\b",
)
VIOLENT_RE = re.compile("|".join(f"(?:{pattern})" for pattern in VIOLENT_PATTERNS), re.IGNORECASE)

SOURCE_SPECS = {
    "franklin": {
        "locality": "Columbus / Franklin County, Ohio",
        "kind": "webform",
        "url": "https://fcsojmsweb.franklincountyohio.gov/Publicview/BookingFind.aspx",
        "publisher": "Franklin County Sheriff's Office",
    },
    "licking": {
        "locality": "Newark / Licking County, Ohio",
        "kind": "licking-html",
        "url": "https://apps.lickingcounty.gov/sheriff/InmateList/",
        "publisher": "Licking County Sheriff's Office",
    },
    "madison": {
        "locality": "London / Madison County, Ohio",
        "kind": "madison-html",
        "url": "https://www.madisonsheriff.org/inmateSearch",
        "publisher": "Madison County Sheriff's Office",
    },
    "lucas": {
        "locality": "Toledo / Lucas County, Ohio",
        "kind": "lucas-pdf",
        "url": "https://lucapps.co.lucas.oh.us/ftproot/noris/upload/lcsheriff/data/lccc-bookingsummary.pdf",
        "publisher": "Lucas County Sheriff's Office",
    },
    "hamilton": {
        "locality": "Cincinnati / Hamilton County, Ohio",
        "kind": "html-form",
        "url": "https://www.hcso.org/justice-center-services/inmate-search/",
        "publisher": "Hamilton County Sheriff's Office",
    },
}


@dataclass(slots=True)
class BookingRecord:
    source: str
    locality: str
    publisher: str
    name: str
    source_url: str
    detail_url: str | None = None
    booking_id: str | None = None
    booking_date: str | None = None
    arrest_date: str | None = None
    arresting_agency: str | None = None
    status: str | None = None
    release_date: str | None = None
    case_numbers: list[str] = field(default_factory=list)
    violent_charge_matches: list[str] = field(default_factory=list)
    fetched_at: str = ""

    def dedupe_key(self) -> str:
        raw = "\x1f".join(
            (
                self.source,
                self.booking_id or "",
                self.booking_date or "",
                normalize_space(self.name).casefold(),
            )
        )
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(slots=True)
class SourceResult:
    source: str
    locality: str
    source_url: str
    fetched_at: str
    records: list[BookingRecord] = field(default_factory=list)
    pages_fetched: int = 0
    candidates_seen: int = 0
    error: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        value = normalize_space(value)
        key = value.casefold()
        if not value or key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def text_lines(markup: str) -> list[str]:
    soup = BeautifulSoup(markup, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return [normalize_space(line) for line in soup.get_text("\n").splitlines() if normalize_space(line)]


def violent_lines(lines: Iterable[str]) -> list[str]:
    return unique(line for line in lines if VIOLENT_RE.search(line))


def case_numbers(text: str) -> list[str]:
    patterns = (
        r"\b\d{2}CR[A-Z]?\d{2,7}\b",
        r"\b\d{4}CR[A-Z]?\d{2,7}\b",
        r"\b\d{2}TR[A-Z]?\d{2,7}\b",
        r"\b\d{4}TR[A-Z]?\d{2,7}\b",
        r"\bB\s?\d{6,8}\b",
    )
    found: list[str] = []
    for pattern in patterns:
        found.extend(match.group(0) for match in re.finditer(pattern, text, re.IGNORECASE))
    return unique(found)


def parse_licking_html(markup: str, fetched_at: str) -> list[BookingRecord]:
    spec = SOURCE_SPECS["licking"]
    lines = text_lines(markup)
    starts: list[int] = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"[A-Z][A-Z .,'’-]+,\s*[A-Z][A-Z .,'’-]*(?:,\s*Jr|,\s*Sr)?", line):
            continue
        if "Booking#" in " ".join(lines[index + 1 : index + 7]):
            starts.append(index)

    records: list[BookingRecord] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = lines[start:end]
        charges = violent_lines(block)
        if not charges:
            continue
        text = "\n".join(block)
        booking = re.search(r"Booking#\s*([0-9-]+)", text, re.IGNORECASE)
        in_date = re.search(r"In Date\s*([0-9/]+)", text, re.IGNORECASE)
        agency = re.search(r"Arresting Agency\s*([^\n]+)", text, re.IGNORECASE)
        release = re.search(r"Release Date\s*-\s*([^\n]+)", text, re.IGNORECASE)
        records.append(
            BookingRecord(
                source="licking",
                locality=spec["locality"],
                publisher=spec["publisher"],
                name=lines[start],
                source_url=spec["url"],
                booking_id=booking.group(1) if booking else None,
                booking_date=in_date.group(1) if in_date else None,
                arresting_agency=normalize_space(agency.group(1)) if agency else None,
                release_date=normalize_space(release.group(1)) if release else None,
                case_numbers=case_numbers(text),
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records


def parse_madison_html(markup: str, fetched_at: str) -> list[BookingRecord]:
    spec = SOURCE_SPECS["madison"]
    lines = text_lines(markup)
    starts: list[int] = []
    for index, line in enumerate(lines):
        if not re.fullmatch(r"[A-Z][A-Z .,'’-]+,\s*[A-Z][A-Z .,'’-]+", line):
            continue
        lookahead = " ".join(lines[index + 1 : index + 12])
        if "Inmate Details:" in lookahead and "Booking Details:" in lookahead:
            starts.append(index)

    records: list[BookingRecord] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = lines[start:end]
        text = "\n".join(block)
        marker = next((i for i, line in enumerate(block) if line.casefold() == "charge(s):"), None)
        charges = violent_lines(block[marker + 1 :] if marker is not None else block)
        if not charges:
            continue
        booking_date = re.search(r"Booking Date:\s*([0-9/]+)", text, re.IGNORECASE)
        booking_number = re.search(r"Booking Number:\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
        agency = re.search(r"Agency:\s*([^\n]+)", text, re.IGNORECASE)
        records.append(
            BookingRecord(
                source="madison",
                locality=spec["locality"],
                publisher=spec["publisher"],
                name=lines[start],
                source_url=spec["url"],
                booking_id=booking_number.group(1) if booking_number else None,
                booking_date=booking_date.group(1) if booking_date else None,
                arresting_agency=normalize_space(agency.group(1)) if agency else None,
                case_numbers=case_numbers(text),
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records


def parse_lucas_text(text: str, fetched_at: str) -> list[BookingRecord]:
    spec = SOURCE_SPECS["lucas"]
    booking_re = re.compile(
        r"(?m)^\s*([A-Z][A-Za-zÀ-ÖØ-öø-ÿ .,'’-]{2,80})\s+Book Dttm:\s*([0-9/]+(?:\s+[0-9:]+)?)\s*$"
    )
    starts = list(booking_re.finditer(text))
    records: list[BookingRecord] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.start() : end]
        charges = violent_lines(block.splitlines())
        if not charges:
            continue
        agency = re.search(r"Arresting Agency:\s*(.+?)(?:\s+Arrest Dttm:|\n)", block, re.IGNORECASE)
        arrest = re.search(r"Arrest Dttm:\s*([0-9/]+(?:\s+[0-9:]+)?)", block, re.IGNORECASE)
        status = re.search(r"Current Status:\s*([^\n]+)", block, re.IGNORECASE)
        released = re.search(r"Released On\s*\n?\s*([0-9/]+(?:\s+[0-9:]+)?)", block, re.IGNORECASE)
        records.append(
            BookingRecord(
                source="lucas",
                locality=spec["locality"],
                publisher=spec["publisher"],
                name=normalize_space(match.group(1)),
                source_url=spec["url"],
                booking_date=normalize_space(match.group(2)),
                arrest_date=normalize_space(arrest.group(1)) if arrest else None,
                arresting_agency=normalize_space(agency.group(1)) if agency else None,
                status=normalize_space(status.group(1)) if status else None,
                release_date=normalize_space(released.group(1)) if released else None,
                case_numbers=case_numbers(block),
                violent_charge_matches=charges,
                fetched_at=fetched_at,
            )
        )
    return records


def pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def form_field(form, tokens: tuple[str, ...], tag_names: tuple[str, ...] = ("input", "select")) -> str | None:
    for tag in form.find_all(tag_names):
        name = tag.get("name")
        if not name:
            continue
        haystack = " ".join((name, tag.get("id", ""), tag.get("placeholder", ""))).casefold()
        if all(token in haystack for token in tokens):
            return name
    for label in form.find_all("label"):
        if not all(token in normalize_space(label.get_text(" ")).casefold() for token in tokens):
            continue
        target = label.get("for")
        tag = form.find(id=target) if target else None
        if tag and tag.get("name"):
            return tag["name"]
    return None


def form_payload(form) -> dict[str, str]:
    payload: dict[str, str] = {}
    for tag in form.find_all("input"):
        name = tag.get("name")
        if not name:
            continue
        if (tag.get("type") or "text").casefold() in {"hidden", "submit"}:
            payload[name] = tag.get("value", "")
    return payload


def set_current_status(form, payload: dict[str, str]) -> None:
    name = form_field(form, ("status",), ("select",))
    select = form.find("select", attrs={"name": name}) if name else None
    if not select:
        return
    for option in select.find_all("option"):
        text = normalize_space(option.get_text(" "))
        if "current" in text.casefold():
            payload[name] = option.get("value", text)
            return


def search_detail_links(markup: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(markup, "html.parser")
    output: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        folded = href.casefold()
        if not any(token in folded for token in ("bookingdetail", "booking-detail", "inmate-detail", "inmatedetail")):
            continue
        if "find" not in folded:
            output.append(urljoin(base_url, href))
    return unique(output)


def detail_name(markup: str) -> str | None:
    soup = BeautifulSoup(markup, "html.parser")
    match = re.search(r"\bInmate:\s*([^\n]+)", soup.get_text("\n"), re.IGNORECASE)
    if match:
        return normalize_space(match.group(1)).strip(" ,") or None
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        candidate = normalize_space(tag.get_text(" "))
        if "," in candidate and 3 <= len(candidate) <= 120:
            return candidate
    return None


def detail_record(source: str, markup: str, detail_url: str, fetched_at: str) -> BookingRecord | None:
    spec = SOURCE_SPECS[source]
    lines = text_lines(markup)
    charges = violent_lines(lines)
    if not charges:
        return None
    text = "\n".join(lines)
    name = detail_name(markup)
    if not name:
        return None
    booking = re.search(r"(?:Booking Number|Booking#|JMS Number|Inmate Number)\s*:?\s*([0-9A-Za-z-]+)", text, re.IGNORECASE)
    booking_date = re.search(r"(?:Booking Date|Admitted Date)\s*:?\s*([0-9/]+(?:\s+[0-9:APM ]+)?)", text, re.IGNORECASE)
    status = re.search(r"Current Status\s*:?\s*([^\n]+)", text, re.IGNORECASE)
    return BookingRecord(
        source=source,
        locality=spec["locality"],
        publisher=spec["publisher"],
        name=name,
        source_url=spec["url"],
        detail_url=detail_url,
        booking_id=booking.group(1) if booking else None,
        booking_date=normalize_space(booking_date.group(1)) if booking_date else None,
        status=normalize_space(status.group(1)) if status else None,
        case_numbers=case_numbers(text),
        violent_charge_matches=charges,
        fetched_at=fetched_at,
    )


async def fetch(client: httpx.AsyncClient, url: str, *, method: str = "GET", data: dict[str, str] | None = None) -> httpx.Response:
    response = await client.request(method, url, data=data, follow_redirects=True)
    response.raise_for_status()
    return response


async def collect_static_html(source: str, client: httpx.AsyncClient, fetched_at: str) -> SourceResult:
    spec = SOURCE_SPECS[source]
    response = await fetch(client, spec["url"])
    parser = parse_licking_html if source == "licking" else parse_madison_html
    records = parser(response.text, fetched_at)
    return SourceResult(source, spec["locality"], spec["url"], fetched_at, records, 1, len(records))


async def collect_lucas(client: httpx.AsyncClient, fetched_at: str) -> SourceResult:
    spec = SOURCE_SPECS["lucas"]
    response = await fetch(client, spec["url"])
    records = parse_lucas_text(await asyncio.to_thread(pdf_text, response.content), fetched_at)
    return SourceResult("lucas", spec["locality"], spec["url"], fetched_at, records, 1, len(records))


async def submit_form_search(client: httpx.AsyncClient, markup: str, page_url: str, prefix: str) -> httpx.Response:
    soup = BeautifulSoup(markup, "html.parser")
    form = soup.find("form")
    if not form:
        raise RuntimeError("search page has no form")
    payload = form_payload(form)
    set_current_status(form, payload)
    last_name = form_field(form, ("last",))
    first_name = form_field(form, ("first",))
    if last_name:
        payload[last_name] = prefix
    if first_name:
        payload[first_name] = ""
    submit = form.find("input", attrs={"type": re.compile(r"submit", re.I)})
    if submit and submit.get("name"):
        payload[submit["name"]] = submit.get("value", "Search")
    action = urljoin(page_url, form.get("action") or page_url)
    if (form.get("method") or "get").casefold() == "post":
        return await fetch(client, action, method="POST", data=payload)
    response = await client.get(action, params=payload, follow_redirects=True)
    response.raise_for_status()
    return response


async def collect_search_form(source: str, client: httpx.AsyncClient, fetched_at: str, max_records: int) -> SourceResult:
    spec = SOURCE_SPECS[source]
    first = await fetch(client, spec["url"])
    pages = 1
    seen: set[str] = set()
    links: list[str] = []

    async def search(prefix: str) -> None:
        nonlocal pages
        response = await submit_form_search(client, first.text, str(first.url), prefix)
        pages += 1
        for link in search_detail_links(response.text, str(response.url)):
            if link not in seen:
                seen.add(link)
                links.append(link)

    await search("")
    if not links:
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            await search(letter)
            if len(links) >= max_records:
                break

    semaphore = asyncio.Semaphore(8)

    async def load_detail(url: str) -> BookingRecord | None:
        nonlocal pages
        async with semaphore:
            response = await fetch(client, url)
            pages += 1
            return detail_record(source, response.text, str(response.url), fetched_at)

    records: list[BookingRecord] = []
    tasks = [asyncio.create_task(load_detail(url)) for url in links[:max_records]]
    for task in asyncio.as_completed(tasks):
        record = await task
        if record:
            records.append(record)
    return SourceResult(source, spec["locality"], spec["url"], fetched_at, records, pages, len(links))


class CollectorActor:
    def __init__(self, source: str, mailbox: asyncio.Queue[SourceResult], timeout: float, max_records: int):
        self.source = source
        self.mailbox = mailbox
        self.timeout = timeout
        self.max_records = max_records

    async def run(self) -> None:
        spec = SOURCE_SPECS[self.source]
        fetched_at = utc_now()
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8"}
        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                if spec["kind"] in {"licking-html", "madison-html"}:
                    result = await collect_static_html(self.source, client, fetched_at)
                elif spec["kind"] == "lucas-pdf":
                    result = await collect_lucas(client, fetched_at)
                else:
                    result = await collect_search_form(self.source, client, fetched_at, self.max_records)
        except Exception as exc:
            result = SourceResult(
                source=self.source,
                locality=spec["locality"],
                source_url=spec["url"],
                fetched_at=fetched_at,
                error=f"{type(exc).__name__}: {exc}",
            )
        await self.mailbox.put(result)


async def collect_all(sources: list[str], timeout: float, max_records: int) -> list[SourceResult]:
    mailbox: asyncio.Queue[SourceResult] = asyncio.Queue()
    actors = [CollectorActor(source, mailbox, timeout, max_records) for source in sources]
    tasks = [asyncio.create_task(actor.run(), name=f"collector:{actor.source}") for actor in actors]
    results = [await mailbox.get() for _ in actors]
    await asyncio.gather(*tasks)
    return sorted(results, key=lambda result: result.source)


def dedupe_records(results: list[SourceResult]) -> list[BookingRecord]:
    seen: set[str] = set()
    records: list[BookingRecord] = []
    for result in results:
        for record in result.records:
            key = record.dedupe_key()
            if key in seen:
                continue
            seen.add(key)
            records.append(record)
    return sorted(records, key=lambda record: (record.locality, record.name.casefold(), record.booking_date or ""))


def write_outputs(output: Path, results: list[SourceResult]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    records = dedupe_records(results)
    with (output / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "generated_at": utc_now(),
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
    (output / "sources.json").write_text(
        json.dumps({source: SOURCE_SPECS[source] for source in sorted(SOURCE_SPECS)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Ohio jail/custody records matching violent-charge terms")
    parser.add_argument("--source", action="append", choices=sorted(SOURCE_SPECS), dest="sources")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--max-records-per-source", type=int, default=5000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = asyncio.run(collect_all(args.sources or list(SOURCE_SPECS), args.timeout, args.max_records_per_source))
    write_outputs(args.output, results)
    for result in results:
        status = f"error={result.error}" if result.error else f"records={len(result.records)} candidates={result.candidates_seen} pages={result.pages_fetched}"
        print(f"{result.source}: {status}")
    failed = [result.source for result in results if result.error]
    if failed:
        print(f"failed sources: {', '.join(failed)}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
