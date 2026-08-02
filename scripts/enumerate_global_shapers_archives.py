#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse, urlunparse

import requests

WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
COMMON_CRAWL_INDEXES = "https://index.commoncrawl.org/collinfo.json"
PROFILE_PATHS = ("/member-details/*", "/shapers/*", "/alumni/*")
ALLOWED_HOSTS = {"globalshapers.org", "www.globalshapers.org"}
PROFILE_RE = re.compile(r"^/(?:member-details|shapers|alumni)/[^/?#]+/?$", re.I)


@dataclass(frozen=True)
class Discovery:
    source: str
    query: str
    status: str
    urls: int
    error: str = ""


def session() -> requests.Session:
    client = requests.Session()
    client.headers.update({
        "User-Agent": "StarIntel-AutoDig/0.9 (+https://starintel.actor; public archive enumeration)",
        "Accept": "application/json,text/plain,*/*",
    })
    return client


def canonical_profile_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value if value.startswith(("http://", "https://")) else "https://www.globalshapers.org/" + value.lstrip("/"))
    host = parsed.netloc.casefold().split(":", 1)[0]
    if host not in ALLOWED_HOSTS:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    if not PROFILE_RE.match(path):
        return None
    return urlunparse(("https", "www.globalshapers.org", path, "", "", ""))


def request_json(
    client: requests.Session,
    url: str,
    *,
    params: list[tuple[str, str]] | dict[str, Any] | None = None,
    timeout: float = 60.0,
    attempts: int = 4,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"request failed after {attempts} attempts: {url}: {last_error}")


def wayback_query(client: requests.Session, wildcard: str, timeout: float) -> tuple[set[str], Discovery]:
    params = [
        ("url", wildcard),
        ("output", "json"),
        ("filter", "statuscode:200"),
        ("filter", "mimetype:text/html"),
        ("collapse", "urlkey"),
        ("fl", "original"),
        ("from", "2010"),
        ("limit", "100000"),
    ]
    try:
        payload = request_json(client, WAYBACK_CDX, params=params, timeout=timeout)
        urls: set[str] = set()
        rows = payload[1:] if isinstance(payload, list) and payload and isinstance(payload[0], list) else payload
        if isinstance(rows, list):
            for row in rows:
                raw = row[0] if isinstance(row, list) and row else row
                if isinstance(raw, str):
                    canonical = canonical_profile_url(raw)
                    if canonical:
                        urls.add(canonical)
        return urls, Discovery("wayback-cdx", wildcard, "complete", len(urls))
    except Exception as exc:
        return set(), Discovery("wayback-cdx", wildcard, "failed", 0, f"{type(exc).__name__}: {exc}")


def common_crawl_indexes(client: requests.Session, timeout: float, count: int) -> list[dict[str, Any]]:
    payload = request_json(client, COMMON_CRAWL_INDEXES, timeout=timeout)
    if not isinstance(payload, list):
        return []
    indexes = [row for row in payload if isinstance(row, dict) and row.get("cdx-api")]
    return indexes[:count]


def common_crawl_query(
    client: requests.Session,
    index: dict[str, Any],
    wildcard: str,
    timeout: float,
) -> tuple[set[str], Discovery]:
    api = str(index["cdx-api"])
    label = str(index.get("id") or api)
    params = [
        ("url", wildcard),
        ("output", "json"),
        ("filter", "status:200"),
        ("filter", "mime:text/html"),
        ("collapse", "urlkey"),
        ("fl", "url"),
    ]
    try:
        response = client.get(api, params=params, timeout=timeout)
        response.raise_for_status()
        urls: set[str] = set()
        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            raw: Any = value
            if isinstance(value, dict):
                raw = value.get("url") or value.get("original")
            elif isinstance(value, list) and value:
                raw = value[0]
            if isinstance(raw, str):
                canonical = canonical_profile_url(raw)
                if canonical:
                    urls.add(canonical)
        return urls, Discovery(f"common-crawl:{label}", wildcard, "complete", len(urls))
    except Exception as exc:
        return set(), Discovery(f"common-crawl:{label}", wildcard, "failed", 0, f"{type(exc).__name__}: {exc}")


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in sorted(set(values))), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enumerate archived official Global Shapers profile URLs from Wayback CDX and Common Crawl."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("imports/global-shapers/generated-archive-profile-urls.txt"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/global-shapers-archive-urls.json"),
    )
    parser.add_argument("--common-crawl-indexes", type=int, default=12)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--minimum-urls", type=int, default=1)
    args = parser.parse_args()

    tasks: list[tuple[str, Any]] = []
    for host in sorted(ALLOWED_HOSTS):
        for path in PROFILE_PATHS:
            tasks.append(("wayback", f"{host}{path}"))

    indexes: list[dict[str, Any]] = []
    index_error = ""
    try:
        indexes = common_crawl_indexes(session(), args.timeout, args.common_crawl_indexes)
    except Exception as exc:
        index_error = f"{type(exc).__name__}: {exc}"
    for index in indexes:
        for host in sorted(ALLOWED_HOSTS):
            for path in PROFILE_PATHS:
                tasks.append(("common-crawl", (index, f"{host}{path}")))

    urls: set[str] = set()
    discoveries: list[Discovery] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {}
        for kind, payload in tasks:
            if kind == "wayback":
                futures[pool.submit(wayback_query, session(), payload, args.timeout)] = (kind, payload)
            else:
                index, wildcard = payload
                futures[pool.submit(common_crawl_query, session(), index, wildcard, args.timeout)] = (kind, wildcard)
        for future in as_completed(futures):
            found, discovery = future.result()
            urls.update(found)
            discoveries.append(discovery)

    write_lines(args.output, urls)
    report = {
        "status": "complete" if len(urls) >= args.minimum_urls else "incomplete",
        "minimum_urls": args.minimum_urls,
        "profile_url_count": len(urls),
        "wayback_queries": sum(item.source == "wayback-cdx" for item in discoveries),
        "common_crawl_indexes_requested": args.common_crawl_indexes,
        "common_crawl_indexes_loaded": len(indexes),
        "common_crawl_index_error": index_error,
        "discoveries": [asdict(item) for item in sorted(discoveries, key=lambda item: (item.source, item.query))],
        "profile_urls": sorted(urls),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        key: report[key]
        for key in ("status", "profile_url_count", "common_crawl_indexes_loaded")
    }, indent=2))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
