from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from typing import Any, Mapping

USER_AGENT = "StarIntel-WEFDepth7/1.0 (+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"


class HttpClient:
    def __init__(self, *, delay: float, timeout: float, user_agent: str = USER_AGENT, github_token: str | None = None) -> None:
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent
        self.github_token = github_token
        self._lock = threading.Lock()
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _throttle(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).netloc.casefold()
        with self._lock:
            now = time.monotonic()
            wait = self.delay - (now - self._last_request.get(host, 0.0))
            if wait > 0:
                time.sleep(wait)
            self._last_request[host] = time.monotonic()

    def fetch(self, url: str, *, accept: str = "*/*", max_bytes: int = 16_000_000) -> tuple[bytes, Mapping[str, str], str]:
        self._throttle(url)
        headers = {"Accept": accept, "User-Agent": self.user_agent}
        if self.github_token and urllib.parse.urlsplit(url).netloc.casefold() == "api.github.com":
            headers["Authorization"] = f"Bearer {self.github_token}"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError(f"response exceeds {max_bytes} bytes: {url}")
            return body, dict(response.headers.items()), response.geturl()

    def json(self, url: str, *, max_bytes: int = 32_000_000) -> Any:
        body, _, _ = self.fetch(url, accept="application/json", max_bytes=max_bytes)
        return json.loads(body.decode("utf-8"))

    def robots_allowed(self, url: str) -> bool:
        parsed = urllib.parse.urlsplit(url)
        key = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots.get(key)
        if parser is None:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(f"{key}/robots.txt")
            try:
                body, _, _ = self.fetch(parser.url, accept="text/plain", max_bytes=1_000_000)
                parser.parse(body.decode("utf-8", errors="replace").splitlines())
            except (OSError, ValueError, urllib.error.URLError):
                parser.parse([])
            self._robots[key] = parser
        return parser.can_fetch(self.user_agent, url)
