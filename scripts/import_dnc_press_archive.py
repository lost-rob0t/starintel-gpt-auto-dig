#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
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
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.validation import validate_document

DATASET = "dnc"
DNC_ID = "starintel:org:dnc"
GENERATED_AT = "2026-07-31T07:10:00Z"
OUTPUT = Path("digs/dnc/2026-07-31-official-press-archive")
API_ROOT = "https://democrats.org/wp-json/"
TERMS_ENDPOINT = "https://democrats.org/wp-json/wp/v2/dnc_news_type"
POSTS_ENDPOINT = "https://democrats.org/wp-json/wp/v2/posts"
ARCHIVE_URL = "https://democrats.org/news-type/press-release/"
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
PER_PAGE = 100
MAX_PAGES = 250
MAX_POSTS = 25_000
REQUEST_DELAY = 0.25
FIELDS = "id,date_gmt,modified_gmt,slug,link,title,type,status,dnc_news_type,lang"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the official DNC press-release archive")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY)
    parser.add_argument("--offline-jsonl", type=Path)
    return parser.parse_args()


def request_json(url: str, *, retries: int = 5, delay: float = REQUEST_DELAY) -> tuple[Any, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = response.read(50_000_001)
                if len(body) > 50_000_000:
                    raise RuntimeError(f"response exceeds 50 MB: {url}")
                headers = {key.lower(): value for key, value in response.headers.items()}
                return json.loads(body.decode("utf-8")), headers
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                raise
            time.sleep(min(20.0, (2 ** attempt) + random.random()))
    raise RuntimeError(f"failed after {retries} attempts: {url}") from last_error


def press_release_term(delay: float) -> tuple[int, dict[str, Any]]:
    query = urllib.parse.urlencode({"per_page": 100, "_fields": "id,name,slug,count,taxonomy"})
    terms, _ = request_json(f"{TERMS_ENDPOINT}?{query}", delay=delay)
    if not isinstance(terms, list):
        raise RuntimeError("unexpected dnc_news_type response")
    matches = [term for term in terms if str(term.get("slug", "")).lower() == "press-release"]
    if len(matches) != 1:
        raise RuntimeError(f"expected one press-release taxonomy term, found {len(matches)}")
    return int(matches[0]["id"]), matches[0]


def normalize_post(post: dict[str, Any]) -> dict[str, Any]:
    post_id = int(post["id"])
    title_raw = post.get("title")
    title_rendered = title_raw.get("rendered") if isinstance(title_raw, dict) else title_raw
    title = re.sub(r"\s+", " ", html.unescape(str(title_rendered or ""))).strip()
    link = str(post.get("link") or "").strip()
    date_gmt = str(post.get("date_gmt") or "").strip()
    modified_gmt = str(post.get("modified_gmt") or "").strip()
    slug = str(post.get("slug") or "").strip()
    if not title or not link or not date_gmt or not slug:
        raise RuntimeError(f"press-release post {post_id} is missing title, link, date, or slug")
    if urllib.parse.urlparse(link).netloc.lower() not in {"democrats.org", "www.democrats.org"}:
        raise RuntimeError(f"post {post_id} has unexpected host: {link}")
    return {
        "id": post_id,
        "date_gmt": date_gmt,
        "modified_gmt": modified_gmt,
        "slug": slug,
        "link": link,
        "title": title,
        "type": str(post.get("type") or "post"),
        "status": str(post.get("status") or "publish"),
        "dnc_news_type": [int(value) for value in post.get("dnc_news_type", [])],
        "lang": str(post.get("lang") or "en"),
    }


def fetch_posts(term_id: int, delay: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    total_expected: int | None = None
    total_pages: int | None = None
    for page in range(1, MAX_PAGES + 1):
        query = urllib.parse.urlencode(
            {
                "context": "view",
                "dnc_news_type": term_id,
                "order": "asc",
                "orderby": "id",
                "page": page,
                "per_page": PER_PAGE,
                "status": "publish",
                "_fields": FIELDS,
            }
        )
        result, headers = request_json(f"{POSTS_ENDPOINT}?{query}", delay=delay)
        if not isinstance(result, list):
            raise RuntimeError(f"unexpected posts response on page {page}")
        if page == 1:
            total_expected = int(headers.get("x-wp-total", len(result)))
            total_pages = int(headers.get("x-wp-totalpages", 1))
            if total_expected > MAX_POSTS:
                raise RuntimeError(f"press-release total exceeds safety cap: {total_expected}")
            if total_pages > MAX_PAGES:
                raise RuntimeError(f"press-release pages exceed safety cap: {total_pages}")
        for raw_post in result:
            post = normalize_post(raw_post)
            if term_id not in post["dnc_news_type"]:
                raise RuntimeError(f"post {post['id']} lacks requested press-release taxonomy term")
            if post["id"] in seen_ids:
                raise RuntimeError(f"duplicate WordPress post ID: {post['id']}")
            seen_ids.add(post["id"])
            records.append(post)
        if total_pages is not None and page >= total_pages:
            break
        if not result:
            raise RuntimeError(f"empty page {page} before declared final page {total_pages}")
        time.sleep(max(0.0, delay))
    if total_expected is None or total_pages is None:
        raise RuntimeError("missing WordPress pagination headers")
    if len(records) != total_expected:
        raise RuntimeError(f"expected {total_expected} posts, received {len(records)}")
    return records, {"total": total_expected, "total_pages": total_pages, "term_id": term_id}


def read_offline(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = [normalize_post(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("offline archive contains duplicate post IDs")
    if not records:
        raise RuntimeError("offline archive is empty")
    return sorted(records, key=lambda item: item["id"]), {"total": len(records), "total_pages": None, "term_id": None}


def dt(value: str) -> str:
    value = value.strip()
    if not value:
        raise RuntimeError("empty WordPress date")
    return value + "Z" if not value.endswith("Z") and "+" not in value[-6:] else value


def relation_id(source_id: str) -> str:
    raw = f"{DNC_ID}\x1fpublished\x1f{source_id}".encode("utf-8")
    return "starintel:relation:" + hashlib.sha256(raw).hexdigest()


def source_doc(post: dict[str, Any], when: str) -> dict[str, Any]:
    source_id = f"starintel:source:dnc-press-release-wp-{post['id']}"
    return {
        "_id": source_id,
        "data": {
            "accessed_at": when,
            "credibility": 0.99,
            "kind": "official_press_release",
            "language": post["lang"],
            "published_at": dt(post["date_gmt"]),
            "publisher": "Democratic National Committee",
            "uri": post["link"],
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "source",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "identifiers": [
            {"canonical": True, "issuer": "Democratic National Committee", "scheme": "wordpress_post_id", "value": str(post["id"])},
            {"canonical": False, "issuer": "Democratic National Committee", "scheme": "wordpress_slug", "value": post["slug"]},
        ],
        "schema_version": "0.9.0",
        "sources": [],
        "status": "recorded",
        "summary": f"Official DNC press release published {post['date_gmt'][:10]}.",
        "tags": ["dnc", "press-release", "official-source"],
        "temporal": {"modified_at": dt(post["modified_gmt"]) if post["modified_gmt"] else None, "published_at": dt(post["date_gmt"])},
        "title": post["title"],
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }


def publication_relation(post: dict[str, Any], source_id: str, when: str) -> dict[str, Any]:
    return {
        "_id": relation_id(source_id),
        "data": {
            "confidence": 0.99,
            "directed": True,
            "object": source_id,
            "predicate": "published",
            "qualifiers": {
                "language": post["lang"],
                "published_at": dt(post["date_gmt"]),
                "wordpress_post_id": post["id"],
                "wordpress_slug": post["slug"],
            },
            "subject": DNC_ID,
        },
        "dataset": DATASET,
        "date_added": when,
        "date_updated": when,
        "dtype": "relation",
        "evidence": [],
        "handling": {"handling": "public-source-only", "pii": False, "sensitive": False, "visibility": "public"},
        "schema_version": "0.9.0",
        "sources": [{"source_id": source_id}],
        "status": "recorded",
        "summary": "The Democratic National Committee published this official press release.",
        "tags": ["dnc", "press-release", "publication", "relation"],
        "title": f"DNC published: {post['title']}",
        "verification": {"last_reviewed_at": when, "status": "official-source-record", "verified": True},
        "version": 1,
    }


def build(posts: list[dict[str, Any]], when: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for post in posts:
        source = source_doc(post, when)
        relation = publication_relation(post, source["_id"], when)
        for document in (source, relation):
            validate_document(document)
            if document["_id"] in seen:
                raise RuntimeError(f"duplicate generated ID: {document['_id']}")
            seen.add(document["_id"])
            documents.append(document)
    return sorted(documents, key=lambda document: document["_id"])


def write(output: Path, posts: list[dict[str, Any]], documents: list[dict[str, Any]], metadata: dict[str, Any], when: str) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "source").mkdir(parents=True)
    inventory = "".join(json.dumps(post, ensure_ascii=False, separators=(",", ":")) + "\n" for post in posts).encode("utf-8")
    (output / "source/wordpress-posts.jsonl").write_bytes(inventory)
    jsonl = "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n" for document in documents).encode("utf-8")
    (output / "starintel-documents.jsonl").write_bytes(jsonl)
    counts = Counter(document["dtype"] for document in documents)
    manifest = {
        "api_root": API_ROOT,
        "archive_url": ARCHIVE_URL,
        "counts": dict(sorted(counts.items())),
        "dataset": DATASET,
        "document_sha256": hashlib.sha256(jsonl).hexdigest(),
        "generated_at": when,
        "inventory_sha256": hashlib.sha256(inventory).hexdigest(),
        "schema_version": "0.9.0",
        "total_documents": len(documents),
        "total_press_releases": len(posts),
        "wordpress": metadata,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        f"""# Official DNC press-release archive

API-first import from the DNC's public WordPress REST API, filtered by the official `press-release` term in the `dnc_news_type` taxonomy.

- press releases: {len(posts):,}
- StarIntel documents: {len(documents):,}
- source records: {counts.get('source', 0):,}
- publication relations: {counts.get('relation', 0):,}

The importer requests 100 records per page, follows WordPress pagination headers, validates the declared total, retries transient failures, rate-limits requests, and stores a compact source inventory. It records titles, canonical links, publication and modification dates, WordPress IDs, slugs, and language; it does not duplicate article bodies.

```bash
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
    if ns.offline_jsonl:
        posts, metadata = read_offline(ns.offline_jsonl)
    else:
        term_id, term = press_release_term(ns.delay)
        posts, metadata = fetch_posts(term_id, ns.delay)
        metadata["term"] = term
    documents = build(posts, ns.generated_at)
    write(ns.output, posts, documents, metadata, ns.generated_at)
    print(json.dumps({"documents": len(documents), "output": str(ns.output), "press_releases": len(posts)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
