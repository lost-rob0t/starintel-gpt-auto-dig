#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

USER_AGENT = "StarIntel-AutoDig/0.9 (+https://starintel.actor; public-source WEF artifact research)"
WEF_HOSTS = {"weforum.org", "www.weforum.org", "www3.weforum.org", "initiatives.weforum.org"}
STAMP = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class LinkRecord:
    url: str
    kind: str
    text: str


def classify_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if "/publications/" in path:
        return "publication"
    if "/stories/" in path or "/agenda/" in path:
        return "story"
    if "/people/" in path:
        return "person"
    if parsed.netloc.lower() == "initiatives.weforum.org":
        return "initiative"
    return "page"


def normalize_url(base_url: str, href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    url = urllib.parse.urljoin(base_url, href).split("#", 1)[0]
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in WEF_HOSTS:
        return None
    return url


def extract_official_links(html: str, base_url: str) -> list[LinkRecord]:
    soup = BeautifulSoup(html, "lxml")
    records: dict[str, LinkRecord] = {}
    for anchor in soup.select("a[href]"):
        url = normalize_url(base_url, anchor.get("href", ""))
        if not url:
            continue
        text = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
        records[url] = LinkRecord(url=url, kind=classify_url(url), text=text)
    return [records[url] for url in sorted(records)]


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def extract_mentions(text: str, terms: Iterable[str]) -> list[str]:
    folded = text.casefold()
    return sorted({term for term in terms if term and term.casefold() in folded}, key=str.casefold)


def robots_allowed(session: requests.Session, url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = session.get(robots_url, timeout=20)
        if response.ok:
            parser.parse(response.text.splitlines())
            return parser.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        pass
    return True


def fetch(session: requests.Session, url: str, *, timeout: int = 45) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def maybe_extract_pdf_text(pdf_path: Path) -> tuple[str | None, str | None]:
    binary = shutil.which("pdftotext")
    if not binary:
        return None, "pdftotext unavailable"
    text_path = pdf_path.with_suffix(".txt")
    proc = subprocess.run(
        [binary, "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        return None, proc.stderr.strip() or f"pdftotext exited {proc.returncode}"
    return text_path.read_text(encoding="utf-8", errors="replace"), None


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "artifact"


def collect(urls: list[str], terms: list[str], output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
    pending = list(dict.fromkeys(urls))
    seen: set[str] = set()
    records: list[dict] = []

    while pending:
        url = pending.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if not robots_allowed(session, url):
            records.append({"url": url, "retrieved_at": STAMP, "status": "blocked_by_robots"})
            continue
        try:
            response = fetch(session, url)
        except RuntimeError as exc:
            records.append({"url": url, "retrieved_at": STAMP, "status": "fetch_error", "error": str(exc)})
            continue

        content_type = response.headers.get("content-type", "").lower()
        body = response.content
        base = {
            "url": url,
            "final_url": response.url,
            "retrieved_at": STAMP,
            "status": "ok",
            "http_status": response.status_code,
            "content_type": content_type,
            "sha256": sha256_bytes(body),
        }

        if "pdf" in content_type or response.url.lower().endswith(".pdf"):
            pdf_path = output_dir / f"{slug(Path(urllib.parse.urlparse(response.url).path).stem)}-{base['sha256'][:12]}.pdf"
            pdf_path.write_bytes(body)
            text, error = maybe_extract_pdf_text(pdf_path)
            base["artifact_path"] = str(pdf_path)
            base["mentions"] = extract_mentions(text or "", terms)
            if text is not None:
                text_path = pdf_path.with_suffix(".txt")
                base["text_path"] = str(text_path)
                base["text_sha256"] = sha256_bytes(text.encode("utf-8"))
            if error:
                base["text_extraction_error"] = error
            records.append(base)
            continue

        html = response.text
        text = clean_text(html)
        links = extract_official_links(html, response.url)
        base["title"] = BeautifulSoup(html, "lxml").title.get_text(" ", strip=True) if BeautifulSoup(html, "lxml").title else ""
        base["mentions"] = extract_mentions(text, terms)
        base["links"] = [{"url": item.url, "kind": item.kind, "text": item.text} for item in links]
        records.append(base)
        for item in links:
            if item.kind == "pdf" and item.url not in seen:
                pending.append(item.url)

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and hash public WEF council/profile/publication artifacts without writing canonical db records.")
    parser.add_argument("--url", action="append", required=True, help="Official WEF seed URL; repeatable")
    parser.add_argument("--term", action="append", default=[], help="Case-insensitive mention to record; repeatable")
    parser.add_argument("--output-dir", type=Path, required=True, help="Staging directory outside db/")
    args = parser.parse_args()

    if "db" in args.output_dir.parts:
        raise SystemExit("refusing to write scraper staging artifacts under db/")

    records = collect(args.url, args.term, args.output_dir)
    manifest = args.output_dir / "wef-council-artifacts.jsonl"
    manifest.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
