#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
import urllib.robotparser
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

import alumni_membership_list_surface_candidates as alumni

STAMP = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://starintel.actor; official public alumni roster research)"
ALUMNI_TEXT = re.compile(
    r"\b(?:alumni|alumnae|alumnus|graduates?|former members?|past members?|"
    r"former fellows?|past fellows?|past participants?|cohort|class of|honorees?|awardees?|laureates?)\b",
    re.IGNORECASE,
)
YEAR_TEXT = re.compile(r"\b(?:19|20)\d{2}\b")
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")


def canonical_url(raw: str) -> str:
    parts = urlsplit(raw.strip())
    scheme = parts.scheme.lower() or "https"
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit((scheme, netloc, path, urlencode(sorted(query)), ""))


def same_host(left: str, right: str) -> bool:
    left_host = (urlsplit(left).hostname or "").lower().removeprefix("www.")
    right_host = (urlsplit(right).hostname or "").lower().removeprefix("www.")
    return bool(left_host and left_host == right_host)


def link_evidence(anchor: Any) -> str:
    values = [anchor.get_text(" ", strip=True), anchor.get("title", ""), anchor.get("aria-label", "")]
    parent = anchor.parent
    if parent is not None:
        values.append(parent.get_text(" ", strip=True)[:500])
    return " ".join(value for value in values if value)


class Discovery:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.observations: list[dict[str, Any]] = []
        self.fetch_cache: dict[str, tuple[str, int, str, str]] = {}

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self.robots:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(base + "/robots.txt")
            try:
                parser.read()
                self.robots[base] = parser
            except Exception:
                self.robots[base] = None
        parser = self.robots[base]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)

    def fetch(self, url: str, *, dataset: str, organization: str, kind: str) -> tuple[str, int, str, str]:
        url = canonical_url(url)
        if url in self.fetch_cache:
            return self.fetch_cache[url]
        if not self.allowed(url):
            result = ("", 999, url, "blocked_by_robots")
        else:
            try:
                response = self.session.get(url, timeout=35, allow_redirects=True)
                content_type = str(response.headers.get("content-type", ""))
                text = response.text if any(token in content_type.lower() for token in ("html", "text", "xml", "json")) or not content_type else ""
                result = (text, int(response.status_code), canonical_url(response.url), content_type)
            except requests.RequestException as exc:
                result = ("", 598, url, f"{type(exc).__name__}: {exc}")
        self.fetch_cache[url] = result
        self.observations.append(
            {
                "observed_at": STAMP,
                "dataset": dataset,
                "organization": organization,
                "kind": kind,
                "requested_url": url,
                "final_url": result[2],
                "status_code": result[1],
                "content_type": result[3],
            }
        )
        return result

    def sitemap_roots(self, target: dict[str, Any]) -> list[str]:
        homepage = canonical_url(str(target["homepage"]))
        parts = urlsplit(homepage)
        base = f"{parts.scheme}://{parts.netloc}"
        roots = list(target.get("sitemaps", []))
        robots, status, _, _ = self.fetch(
            base + "/robots.txt",
            dataset=str(target["dataset"]),
            organization=str(target["name"]),
            kind="robots",
        )
        if status == 200:
            roots.extend(re.findall(r"(?im)^\s*Sitemap:\s*(\S+)", robots))
        roots.extend([base + "/sitemap.xml", base + "/sitemap_index.xml", base + "/wp-sitemap.xml"])
        return list(dict.fromkeys(canonical_url(root) for root in roots))

    def sitemap_urls(self, target: dict[str, Any], *, max_maps: int = 100, max_urls: int = 200000) -> set[str]:
        pending = deque(self.sitemap_roots(target))
        seen: set[str] = set()
        urls: set[str] = set()
        while pending and len(seen) < max_maps and len(urls) < max_urls:
            sitemap = pending.popleft()
            if sitemap in seen:
                continue
            seen.add(sitemap)
            text, status, final, _ = self.fetch(
                sitemap,
                dataset=str(target["dataset"]),
                organization=str(target["name"]),
                kind="sitemap",
            )
            if status != 200 or "<loc" not in text:
                continue
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                continue
            locations = [
                canonical_url(element.text.strip())
                for element in root.iter()
                if element.tag.endswith("loc") and element.text
            ]
            if root.tag.endswith("sitemapindex"):
                pending.extend(location for location in locations if location not in seen)
            else:
                urls.update(location for location in locations if same_host(location, str(target["homepage"])))
        return urls

    def discover_target(self, target: dict[str, Any]) -> dict[str, Any]:
        dataset = str(target["dataset"])
        organization = str(target["name"])
        homepage = canonical_url(str(target["homepage"]))
        max_pages = int(target.get("max_alumni_pages", 2000))
        discovered: dict[str, dict[str, str]] = {}

        def add_candidate(url: str, label: str, source: str) -> bool:
            candidate = canonical_url(url)
            if not same_host(candidate, homepage):
                return False
            evidence = f"{label} alumni cohort former members past fellows archive roster"
            if not alumni.base.is_list_path(candidate) and not alumni.qualifies(candidate, evidence):
                return False
            if alumni.base.is_profile_path(candidate):
                return False
            discovered.setdefault(candidate, {"label": label[:300], "discovered_from": source})
            return True

        seeds = [homepage, *[canonical_url(str(url)) for url in target.get("seed_pages", [])[:40]]]
        for seed in target.get("seed_pages", []):
            label = str(target.get("seed_roles", {}).get(seed, "configured roster"))
            if ALUMNI_TEXT.search(label) or ALUMNI_TEXT.search(str(seed)):
                add_candidate(str(seed), label, "configured seed")

        for url in self.sitemap_urls(target):
            path_text = urlsplit(url).path.replace("-", " ").replace("_", " ")
            if ALUMNI_TEXT.search(path_text) or (YEAR_TEXT.search(path_text) and any(token in path_text.lower() for token in ("cohort", "class", "participant", "fellow"))):
                add_candidate(url, path_text, "official sitemap")
            if len(discovered) >= max_pages:
                break

        queue = deque(dict.fromkeys([*seeds, *discovered]))
        visited: set[str] = set()
        while queue and len(visited) < max_pages and len(discovered) < max_pages:
            page = canonical_url(queue.popleft())
            if page in visited or not same_host(page, homepage):
                continue
            visited.add(page)
            text, status, final, content_type = self.fetch(
                page,
                dataset=dataset,
                organization=organization,
                kind="alumni-discovery-page",
            )
            if status != 200 or not text or "html" not in content_type.lower() and "<html" not in text[:1000].lower():
                continue
            soup = BeautifulSoup(text, "lxml")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            heading = soup.select_one("h1")
            local_label = " ".join([title, heading.get_text(" ", strip=True) if heading else ""])
            if ALUMNI_TEXT.search(local_label):
                add_candidate(final, local_label, page)
            for anchor in soup.select("a[href]"):
                href = anchor.get("href", "").strip()
                if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                    continue
                candidate = canonical_url(urljoin(final, href))
                if not same_host(candidate, homepage) or alumni.base.is_profile_path(candidate):
                    continue
                evidence = link_evidence(anchor)
                path_text = urlsplit(candidate).path.replace("-", " ").replace("_", " ")
                historical = bool(ALUMNI_TEXT.search(f"{evidence} {path_text}"))
                archive = bool(YEAR_TEXT.search(f"{evidence} {path_text}")) and any(
                    token in f"{evidence} {path_text}".lower()
                    for token in ("class", "cohort", "participant", "fellow", "member", "alumni")
                )
                pagination = alumni.base.is_list_path(candidate) and any(
                    key.lower() in alumni.base.PAGE_QUERY_KEYS
                    for key, _ in parse_qsl(urlsplit(candidate).query, keep_blank_values=True)
                )
                if historical or archive or pagination:
                    if add_candidate(candidate, evidence or path_text, final) and candidate not in visited:
                        queue.append(candidate)

        existing = [canonical_url(str(url)) for url in target.get("seed_pages", [])]
        additions = [url for url in sorted(discovered) if url not in existing]
        target["seed_pages"] = [*existing, *additions]
        seed_roles = {canonical_url(str(key)): str(value) for key, value in target.get("seed_roles", {}).items()}
        for url in discovered:
            seed_roles[url] = "alumni"
        target["seed_roles"] = seed_roles
        target["alumni_coverage"] = {
            "discovered_list_pages": len(discovered),
            "newly_scheduled_list_pages": len(additions),
            "visited_discovery_pages": len(visited),
            "max_alumni_pages": max_pages,
            "truncated": len(discovered) >= max_pages or len(visited) >= max_pages,
            "generated_at": STAMP,
        }
        return {
            "dataset": dataset,
            "organization": organization,
            **target["alumni_coverage"],
            "list_pages": [
                {"url": url, **discovered[url]}
                for url in sorted(discovered)
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover every exposed official alumni, former-member, cohort, class, and historical roster surface.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    targets = config.get("targets")
    if not isinstance(targets, list):
        raise ValueError("target config must contain a targets list")

    discovery = Discovery()
    results: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict) or not target.get("homepage"):
            continue
        try:
            results.append(discovery.discover_target(target))
        except Exception as exc:
            results.append(
                {
                    "dataset": str(target.get("dataset") or "unresolved"),
                    "organization": str(target.get("name") or "unresolved"),
                    "error": f"{type(exc).__name__}: {exc}",
                    "coverage_status": "alumni_discovery_failed",
                }
            )

    args.config.write_text(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.observations.parent.mkdir(parents=True, exist_ok=True)
    args.observations.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in discovery.observations),
        encoding="utf-8",
    )
    report = {
        "generated_at": STAMP,
        "target_count": len(results),
        "total_discovered_list_pages": sum(int(item.get("discovered_list_pages", 0)) for item in results),
        "results": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
