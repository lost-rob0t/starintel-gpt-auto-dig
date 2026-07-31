from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .constants import BASE_URL, MAX_RESPONSE_BYTES
from .parser import Profile, parse_profile
from .utils import canonicalize_url, clean, normalize_resource_url, profile_kind


def parse_sitemap(payload: bytes, source_url: str) -> tuple[list[str], list[str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError(f"invalid sitemap XML at {source_url}: {exc}") from exc
    name = root.tag.rsplit("}", 1)[-1].lower()
    locations = [clean(node.text) for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "loc" and clean(node.text)]
    if name == "sitemapindex":
        return [normalize_resource_url(location, base=source_url) for location in locations], []
    if name == "urlset":
        urls = [canonicalize_url(location, base=source_url) for location in locations]
        return [], [url for url in urls if profile_kind(url) is not None]
    raise ValueError(f"unsupported sitemap root {name!r} at {source_url}")


@dataclass(slots=True)
class NetworkClient:
    user_agent: str
    delay: float
    timeout: float
    max_bytes: int = MAX_RESPONSE_BYTES
    _last_request_at: float = field(default=0.0, init=False)
    _robots: urllib.robotparser.RobotFileParser | None = field(default=None, init=False)
    _sitemap_urls: list[str] = field(default_factory=list, init=False)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def fetch(self, url: str, *, accept: str) -> bytes:
        self._throttle()
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent, "Accept": accept})
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = response.read(self.max_bytes + 1)
                    if len(payload) > self.max_bytes:
                        raise ValueError(f"response exceeds {self.max_bytes} bytes: {url}")
                    self._last_request_at = time.monotonic()
                    return payload
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
                time.sleep(max(self.delay, 2**attempt))
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == 2:
                    raise
                time.sleep(max(self.delay, 2**attempt))
        assert last_error is not None
        raise last_error

    def load_robots(self) -> None:
        robots_url = urllib.parse.urljoin(BASE_URL, "robots.txt")
        lines = self.fetch(robots_url, accept="text/plain").decode("utf-8", errors="replace").splitlines()
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(lines)
        self._robots = parser
        self._sitemap_urls = [
            normalize_resource_url(line.split(":", 1)[1].strip(), base=robots_url)
            for line in lines
            if line.lower().startswith("sitemap:") and clean(line.split(":", 1)[1])
        ]

    def sitemap_urls(self) -> list[str]:
        if self._robots is None:
            self.load_robots()
        return list(self._sitemap_urls)

    def fetch_allowed(self, url: str, *, accept: str) -> bytes:
        if self._robots is None:
            self.load_robots()
        assert self._robots is not None
        if not self._robots.can_fetch(self.user_agent, url):
            raise PermissionError(f"robots.txt disallows {url} for {self.user_agent}")
        return self.fetch(url, accept=accept)


def discover_profile_urls(client: NetworkClient, sitemap_urls: Sequence[str], *, limit: int = 0) -> list[str]:
    pending = list(dict.fromkeys(normalize_resource_url(url) for url in sitemap_urls))
    seen_sitemaps: set[str] = set()
    profiles: list[str] = []
    seen_profiles: set[str] = set()
    while pending:
        sitemap_url = pending.pop(0)
        if sitemap_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap_url)
        try:
            payload = client.fetch_allowed(sitemap_url, accept="application/xml,text/xml")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        children, urls = parse_sitemap(payload, sitemap_url)
        pending.extend(child for child in children if child not in seen_sitemaps)
        for url in urls:
            if url in seen_profiles:
                continue
            seen_profiles.add(url)
            profiles.append(url)
            if limit and len(profiles) >= limit:
                return profiles
    return profiles


def read_local_profiles(paths: Sequence[Path]) -> list[Profile]:
    return [parse_profile(path.read_bytes(), path.as_uri()) for path in paths]


def fetch_profiles(client: NetworkClient, urls: Sequence[str]) -> list[Profile]:
    return [parse_profile(client.fetch_allowed(url, accept="text/html,application/xhtml+xml"), url) for url in urls]
