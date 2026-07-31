from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import Any, Iterable

from .model import DOCUMENT_SUFFIXES, Collector, Observation, PageParser, TargetPlan, clean_url, keyword_hits, normalized_text, safe_name


class SiteCollector(Collector):
    name = "site"

    @staticmethod
    def _parse_sitemap(body: bytes) -> tuple[list[str], list[str]]:
        root = ET.fromstring(body)
        local = root.tag.rsplit("}", 1)[-1].casefold()
        locations = [normalized_text(node.text) for node in root.iter() if node.tag.rsplit("}", 1)[-1].casefold() == "loc" and node.text]
        return (locations, []) if local == "sitemapindex" else ([], locations)

    def _save_document(self, url: str, body: bytes) -> dict[str, Any]:
        digest = hashlib.sha256(body).hexdigest()
        result: dict[str, Any] = {"sha256": digest, "size": len(body)}
        if self.args.download_dir:
            output = Path(self.args.download_dir) / safe_name(f"{digest[:12]}-{Path(urllib.parse.urlsplit(url).path).name}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(body)
            result["path"] = str(output)
        return result

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        queue: deque[tuple[str, int]] = deque((clean_url(url), 0) for url in target.seed_urls)
        visited: set[str] = set()
        allowed_hosts = {urllib.parse.urlsplit(url).netloc.casefold() for url in target.seed_urls}
        while queue and len(visited) < self.args.max_pages:
            url, depth = queue.popleft()
            if url in visited or urllib.parse.urlsplit(url).netloc.casefold() not in allowed_hosts:
                continue
            visited.add(url)
            if not self.args.ignore_robots and not self.client.robots_allowed(url):
                continue
            try:
                body, headers, final_url = self.client.fetch(url, max_bytes=self.args.max_document_bytes)
            except (OSError, ValueError, urllib.error.URLError):
                continue
            final_url = clean_url(final_url)
            content_type = headers.get("Content-Type", "").casefold()
            suffix = Path(urllib.parse.urlsplit(final_url).path).suffix.casefold()
            if suffix in DOCUMENT_SUFFIXES or not ("html" in content_type or "xml" in content_type or not content_type):
                hits = keyword_hits((final_url, body[:250_000].decode("utf-8", errors="replace")), target.keywords)
                if hits:
                    payload = {"headers": dict(headers), **self._save_document(final_url, body)}
                    yield Observation(self.name, target.target_id, "document", final_url, payload, hits)
                continue
            if "xml" in content_type or body.lstrip().startswith(b"<?xml"):
                try:
                    child_sitemaps, page_urls = self._parse_sitemap(body)
                except ET.ParseError:
                    child_sitemaps, page_urls = [], []
                queue.extend((clean_url(child), depth) for child in child_sitemaps)
                queue.extend(
                    (clean_url(page_url), depth + 1)
                    for page_url in page_urls
                    if urllib.parse.urlsplit(page_url).netloc.casefold() in allowed_hosts
                )
                continue
            parser = PageParser(final_url)
            parser.feed(body.decode("utf-8", errors="replace"))
            page = {
                "title": parser.title,
                "description": parser.meta.get("description") or parser.meta.get("og:description"),
                "text": parser.text[:250_000],
                "links": [{"text": text, "url": href} for text, href in parser.links],
                "document_links": [
                    {"text": text, "url": href}
                    for text, href in parser.links
                    if Path(urllib.parse.urlsplit(href).path).suffix.casefold() in DOCUMENT_SUFFIXES
                ],
            }
            hits = keyword_hits(page, target.keywords)
            if hits:
                yield Observation(self.name, target.target_id, "web-page", final_url, page, hits)
            if depth >= self.args.max_depth:
                continue
            for anchor_text, href in parser.links:
                parsed = urllib.parse.urlsplit(href)
                if parsed.scheme not in {"http", "https"} or parsed.netloc.casefold() not in allowed_hosts:
                    continue
                if depth == 0 or keyword_hits((anchor_text, href), target.keywords):
                    queue.append((clean_url(href), depth + 1))
