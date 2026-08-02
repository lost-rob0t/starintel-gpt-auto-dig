#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
GENERATED_AT = "2026-07-31T22:02:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-official-press-archive")
ARCHIVE_URL = "https://democrats.org/news-type/press-release/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
MAX_PAGES = 1_500
MAX_RECORDS = 20_000
REQUEST_DELAY = 0.12
DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
)
PAGE_RE = re.compile(r"/news-type/press-release/page/(\d+)/?$")
SKIP_PATH_PREFIXES = (
    "/about/",
    "/act/",
    "/careers/",
    "/contact/",
    "/donate/",
    "/leadership/",
    "/news-type/",
    "/privacy-policy/",
    "/shop/",
    "/submission-terms/",
    "/terms-of-service/",
    "/trainings/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the official DNC press-release archive")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES)
    parser.add_argument("--offline-dir", type=Path)
    return parser.parse_args()


def request_text(url: str, *, retries: int = 6) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = response.read(20_000_001)
                if len(body) > 20_000_000:
                    raise RuntimeError(f"response exceeds 20 MB: {url}")
                content_type = response.headers.get_content_charset() or "utf-8"
                return body.decode(content_type, errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise
            time.sleep(min(30.0, (2**attempt) + random.random()))
    raise RuntimeError(f"failed after {retries} attempts: {url}") from last_error


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(base: str, href: str) -> str | None:
    value = urllib.parse.urljoin(base, href.strip())
    parsed = urllib.parse.urlparse(value)
    host = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme not in {"http", "https"} or host != "democrats.org":
        return None
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path == "/" or path.startswith(SKIP_PATH_PREFIXES):
        return None
    if PAGE_RE.search(path):
        return None
    return urllib.parse.urlunparse(("https", "democrats.org", path.rstrip("/") + "/", "", "", ""))


def parse_date(text: str) -> str | None:
    match = DATE_RE.search(text)
    if not match:
        return None
    return datetime.strptime(match.group(0), "%B %d, %Y").date().isoformat()


def nearby_card_text(heading: Any) -> str:
    candidates: list[str] = []
    node = heading
    for _ in range(7):
        node = getattr(node, "parent", None)
        if node is None:
            break
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) <= 4_000:
            candidates.append(text)
        if parse_date(text) and "Press Release" in text:
            return text
    return min(candidates, key=len) if candidates else ""


def nearby_date(heading: Any, card_text: str) -> str | None:
    date = parse_date(card_text)
    if date:
        return date
    count = 0
    for previous in heading.find_all_previous(string=True):
        text = clean_text(str(previous))
        if not text:
            continue
        count += 1
        date = parse_date(text)
        if date:
            return date
        if count >= 20:
            break
    return None


def parse_archive_page(html_text: str, page_url: str, page_number: int) -> tuple[list[dict[str, Any]], int]:
    soup = BeautifulSoup(html_text, "html.parser")
    pages = {1, page_number}
    for anchor in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(page_url, str(anchor.get("href") or ""))
        match = PAGE_RE.search(urllib.parse.urlparse(href).path)
        if match:
            pages.add(int(match.group(1)))

    records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for heading in soup.find_all(["h2", "h3", "h4"]):
        anchor = heading.find("a", href=True)
        if anchor is None:
            continue
        url = canonical_url(page_url, str(anchor.get("href") or ""))
        if not url or url in seen_urls:
            continue
        title = clean_text(anchor.get_text(" ", strip=True))
        if len(title) < 8 or title.lower() in {"read now", "read more", "press release"}:
            continue
        card_text = nearby_card_text(heading)
        published_date = nearby_date(heading, card_text)
        if not published_date:
            continue
        if "Press Release" not in card_text:
            sibling_text = " ".join(
                clean_text(str(value))
                for value in heading.find_all_next(string=True, limit=8)
                if clean_text(str(value))
            )
            if "Press Release" not in sibling_text:
                continue
        slug = urllib.parse.urlparse(url).path.strip("/").split("/")[-1]
        records.append(
            {
                "archive_page": page_number,
                "link": url,
                "published_date": published_date,
                "slug": slug,
                "title": title,
            }
        )
        seen_urls.add(url)
    return records, max(pages)


def page_url(page: int) -> str:
    return ARCHIVE_URL if page == 1 else f"{ARCHIVE_URL}page/{page}/"


def crawl(delay: float, max_pages: int, offline_dir: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if max_pages < 1 or max_pages > MAX_PAGES:
        raise RuntimeError(f"max-pages must be between 1 and {MAX_PAGES}")

    def load(page: int) -> str:
        if offline_dir:
            path = offline_dir / f"page-{page:04d}.html"
            if not path.exists():
                raise RuntimeError(f"missing offline archive page: {path}")
            return path.read_text(encoding="utf-8")
        return request_text(page_url(page))

    first_html = load(1)
    first_records, declared_pages = parse_archive_page(first_html, page_url(1), 1)
    if not first_records:
        raise RuntimeError("first archive page yielded no press-release records")
    if declared_pages > max_pages:
        raise RuntimeError(f"archive declares {declared_pages} pages, exceeding cap {max_pages}")

    records_by_url: dict[str, dict[str, Any]] = {record["link"]: record for record in first_records}
    page_counts = {1: len(first_records)}
    for page in range(2, declared_pages + 1):
        html_text = load(page)
        page_records, observed_pages = parse_archive_page(html_text, page_url(page), page)
        if observed_pages > declared_pages:
            declared_pages = min(observed_pages, max_pages)
        if not page_records:
            raise RuntimeError(f"archive page {page} yielded no press-release records")
        page_counts[page] = len(page_records)
        for record in page_records:
            existing = records_by_url.get(record["link"])
            if existing and existing != record:
                earlier_page = min(int(existing["archive_page"]), int(record["archive_page"]))
                existing["archive_page"] = earlier_page
                continue
            records_by_url[record["link"]] = record
        if len(records_by_url) > MAX_RECORDS:
            raise RuntimeError(f"archive record count exceeds safety cap: {len(records_by_url)}")
        if not offline_dir:
            time.sleep(max(0.0, delay))

    records = sorted(
        records_by_url.values(),
        key=lambda item: (item["published_date"], item["link"]),
    )
    return records, {
        "archive_pages": declared_pages,
        "page_counts": page_counts,
        "unique_records": len(records),
    }


def iso_midnight(date_value: str) -> str:
    return f"{date_value}T00:00:00Z"


def source_id(record: dict[str, Any]) -> str:
    digest = hashlib.sha256(record["link"].encode("utf-8")).hexdigest()
    return f"starintel:source:dnc-press-release-{digest[:32]}"


def relation_id(object_id: str) -> str:
    raw = f"{DNC_ID}\x1fpublished\x1f{object_id}".encode("utf-8")
    return "starintel:relation:" + hashlib.sha256(raw).hexdigest()


def source_doc(record: dict[str, Any], when: str) -> dict[str, Any]:
    document_id = source_id(record)
    published_at = iso_midnight(record["published_date"])
    url_digest = hashlib.sha256(record["link"].encode("utf-8")).hexdigest()
    return {
        "_id": document_id,
        "data": {
            "accessed_at": when,
            "archive_page": record["archive_page"],
            "credibility": 0.99,
            "kind": "official_press_release_archive_record",
            "language": "en",
            "published_at": published_at,
            "publisher": "Democratic National Committee",
            "uri": record["link"],
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "identifiers": [
            {
                "canonical": True,
                "issuer": "Democratic National Committee",
                "scheme": "canonical_url_sha256",
                "value": url_digest,
            },
            {
                "canonical": False,
                "issuer": "Democratic National Committee",
                "scheme": "press_release_slug",
                "value": record["slug"],
            },
        ],
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": f"Official DNC press-release archive entry dated {record['published_date']}.",
        "tags": ["dnc", "press-release", "official-source", "archive-index"],
        "temporal": {"published_at": published_at},
        "title": record["title"],
        "verification": {
            "last_reviewed_at": when,
            "status": "official-archive-record",
            "verified": True,
        },
        "version": 1,
    }


def publication_relation(record: dict[str, Any], object_id: str, when: str) -> dict[str, Any]:
    published_at = iso_midnight(record["published_date"])
    return {
        "_id": relation_id(object_id),
        "data": {
            "confidence": 0.99,
            "directed": True,
            "object": object_id,
            "predicate": "published",
            "qualifiers": {
                "archive_page": record["archive_page"],
                "published_at": published_at,
                "press_release_slug": record["slug"],
            },
            "subject": DNC_ID,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {
            "handling": "public-source-only",
            "pii": False,
            "sensitive": False,
            "visibility": "public",
        },
        "schema_version": "0.9.0",
        "sources": [{"source_id": object_id}],
        "status": "recorded",
        "summary": "The Democratic National Committee lists this item in its official press-release archive.",
        "tags": ["dnc", "press-release", "publication", "relation", "archive-index"],
        "title": f"DNC published: {record['title']}",
        "verification": {
            "last_reviewed_at": when,
            "status": "official-archive-record",
            "verified": True,
        },
        "version": 1,
    }


def build(records: list[dict[str, Any]], when: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        source = source_doc(record, when)
        relation = publication_relation(record, source["_id"], when)
        for document in (source, relation):
            validate_document(document)
            if document["_id"] in seen:
                raise RuntimeError(f"duplicate generated ID: {document['_id']}")
            seen.add(document["_id"])
            documents.append(document)
    return sorted(documents, key=lambda document: document["_id"])


def write(
    output: Path,
    records: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    metadata: dict[str, Any],
    when: str,
) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    inventory = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    ).encode("utf-8")
    (output / "source/archive-records.jsonl").write_bytes(inventory)
    jsonl = "".join(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
        for document in documents
    ).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(jsonl)
    counts = Counter(document["dtype"] for document in documents)
    dates = [record["published_date"] for record in records]
    manifest = {
        "archive_url": ARCHIVE_URL,
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "first_published_date": min(dates),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory).hexdigest(),
        "last_published_date": max(dates),
        "schema_version": "0.9.0",
        "total_documents": len(documents),
        "total_press_releases": len(records),
        "crawl": metadata,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        f"""# Official DNC press-release archive

Archive-page crawl of the DNC's public press-release index.

- archive pages: {metadata['archive_pages']:,}
- unique press releases: {len(records):,}
- StarIntel documents: {len(documents):,}
- source records: {counts.get('source', 0):,}
- publication relations: {counts.get('relation', 0):,}
- date range: {min(dates)} through {max(dates)}

The importer follows the official archive's pagination, extracts each listed title, canonical URL, publication date, slug, and source page, deduplicates canonical URLs, validates every StarIntel v0.9.0 document, and stores a compact source inventory. It indexes archive metadata rather than copying article bodies.

```bash
python3 -m pip install 'beautifulsoup4>=4.12,<5'
python3 scripts/import_dnc_press_archive.py
python3 scripts/validate-for-merge.py --site
```
""",
        encoding="utf-8",
    )


def main() -> int:
    ns = parse_args()
    if ns.delay < 0:
        raise RuntimeError("delay cannot be negative")
    records, metadata = crawl(ns.delay, ns.max_pages, ns.offline_dir)
    documents = build(records, ns.generated_at)
    write(ns.output, records, documents, metadata, ns.generated_at)
    print(
        json.dumps(
            {
                "archive_pages": metadata["archive_pages"],
                "documents": len(documents),
                "output": str(ns.output),
                "press_releases": len(records),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
