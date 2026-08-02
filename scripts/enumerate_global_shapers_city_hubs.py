#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import threading
import time
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.globalshapers.org"
PUBLIC_PAGES = ["/", "/shapers", "/projects", "/impact", "/about", "/alumni", "/hubs"]
HUB_RE = re.compile(r"(?P<city>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.()\-–—/ ]{1,80}?)\s+Hub\b")
CURRENT_HUB_RE = re.compile(r"/community-details/[A-Za-z0-9_-]+", re.I)
PROFILE_RE = re.compile(r"/member-details/[^?#\s\"']+", re.I)
LEGACY_HUB_RE = re.compile(r"/hubs/(?P<slug>[a-z0-9][a-z0-9-]{1,90})", re.I)
NOISE = {
    "global shapers",
    "local",
    "our",
    "the",
    "a",
    "an",
    "cross",
    "community",
    "founding curator and global shaper",
    "global shaper",
    "curator",
    "alumni",
}
SKIP_DIRS = {
    ".git",
    ".generated",
    ".venv",
    "node_modules",
    "_site",
    "__pycache__",
}
TEXT_SUFFIXES = {".json", ".jsonl", ".ndjson", ".md", ".txt", ".csv", ".tsv"}
THREAD_LOCAL = threading.local()


def compact_space(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def clean_city(value: str) -> str | None:
    value = compact_space(value).strip(" ,;:–—-|/")
    value = re.sub(r"^(?:the\s+)", "", value, flags=re.I)
    value = re.sub(r"\s+[IVX]+$", "", value)
    if not value or len(value) < 2 or len(value) > 82:
        return None
    folded = value.casefold()
    if folded in NOISE:
        return None
    if sum(ch.isalpha() for ch in value) < 2:
        return None
    if any(
        token in folded
        for token in (
            "project",
            "report",
            "community annual",
            "global shapers community",
            "world economic forum",
            "young global leaders",
        )
    ):
        return None
    return value


def ascii_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def title_from_slug(slug: str) -> str:
    words = [word for word in slug.replace("-hub", "").split("-") if word]
    return " ".join(word.capitalize() for word in words)


def slug_variants(city: str) -> list[str]:
    base = ascii_slug(city)
    variants = {base, f"{base}-hub"}
    variants.add(base.replace("-and-", "-"))
    variants.add(base.replace("-saint-", "-st-"))
    variants.add(base.replace("-st-", "-saint-"))
    variants.add(base.replace("-city", ""))
    variants.add(base.replace("-metropolitan-area", ""))
    if base.startswith("saint-"):
        variants.add("st-" + base.removeprefix("saint-"))
    if base.startswith("st-"):
        variants.add("saint-" + base.removeprefix("st-"))
    return sorted(v for v in variants if v and len(v) <= 96)


def canonical_public_url(url: str) -> str:
    parsed = urlparse(url)
    return f"https://www.globalshapers.org{parsed.path}".rstrip("/")


def extract_links(html: str, base_url: str) -> tuple[set[str], set[str], set[str]]:
    soup = BeautifulSoup(html, "lxml")
    hubs: set[str] = set()
    profiles: set[str] = set()
    legacy_slugs: set[str] = set()
    for link in soup.select("a[href]"):
        href = urljoin(base_url, str(link.get("href", "")))
        parsed = urlparse(href)
        if parsed.netloc.casefold() not in {"globalshapers.org", "www.globalshapers.org"}:
            continue
        if CURRENT_HUB_RE.search(parsed.path):
            hubs.add(canonical_public_url(href))
        elif PROFILE_RE.search(parsed.path):
            profiles.add(canonical_public_url(href))
        match = LEGACY_HUB_RE.search(parsed.path)
        if match:
            legacy_slugs.add(match.group("slug").casefold())
    return hubs, profiles, legacy_slugs


def extract_cities(text: str) -> set[str]:
    cities: set[str] = set()
    normalized = compact_space(text)
    for match in HUB_RE.finditer(normalized):
        city = clean_city(match.group("city"))
        if city:
            cities.add(city)
    for match in LEGACY_HUB_RE.finditer(text):
        city = clean_city(title_from_slug(match.group("slug")))
        if city:
            cities.add(city)
    return cities


def read_city_files(paths: Iterable[Path]) -> set[str]:
    cities: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            city = clean_city(line.split("\t", 1)[0].split(",", 1)[0])
            if city:
                cities.add(city)
    return cities


def candidate_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > 25_000_000:
                continue
        except OSError:
            continue
        yield path


def cities_from_corpus(root: Path) -> set[str]:
    cities: set[str] = set()
    for path in candidate_text_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        cities.update(extract_cities(text))
    return cities


def cities_from_geonames(limit: int, min_population: int) -> set[str]:
    if limit <= 0:
        return set()
    try:
        import geonamescache
    except ImportError:
        return set()
    cache = geonamescache.GeonamesCache()
    records = list(cache.get_cities().values())
    records.sort(key=lambda row: int(row.get("population") or 0), reverse=True)
    cities: set[str] = set()
    for record in records:
        population = int(record.get("population") or 0)
        if population < min_population:
            continue
        for key in ("name", "alternatenames"):
            value = record.get(key)
            values = value if isinstance(value, list) else [value]
            for raw in values:
                if not isinstance(raw, str):
                    continue
                city = clean_city(raw)
                if city:
                    cities.add(city)
        if len(cities) >= limit:
            break
    return cities


def browser_discovery(max_clicks: int, timeout_ms: int) -> tuple[set[str], set[str], set[str], set[str], list[str]]:
    from playwright.sync_api import sync_playwright

    cities: set[str] = set()
    hubs: set[str] = set()
    profiles: set[str] = set()
    legacy_slugs: set[str] = set()
    errors: list[str] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(user_agent="StarIntel-AutoDig/0.9 public roster enumerator")
        page = context.new_page()
        for route in PUBLIC_PAGES:
            url = urljoin(BASE, route)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(800)
                for _ in range(max_clicks):
                    clicked = False
                    for pattern in (r"show more", r"load more", r"view more", r"see more"):
                        button = page.get_by_text(re.compile(pattern, re.I)).last
                        try:
                            if button.is_visible(timeout=250):
                                button.click(timeout=1200)
                                page.wait_for_timeout(350)
                                clicked = True
                                break
                        except Exception:
                            pass
                    if not clicked:
                        break
                html = page.content()
                text = page.locator("body").inner_text(timeout=timeout_ms)
                cities.update(extract_cities(text))
                found_hubs, found_profiles, found_slugs = extract_links(html, page.url)
                hubs.update(found_hubs)
                profiles.update(found_profiles)
                legacy_slugs.update(found_slugs)
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        context.close()
        browser.close()
    return cities, hubs, profiles, legacy_slugs, errors


def thread_session() -> requests.Session:
    session = getattr(THREAD_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "StarIntel-AutoDig/0.9 (+https://starintel.actor; public roster enumeration)",
                "Accept": "text/html,application/xhtml+xml",
            }
        )
        THREAD_LOCAL.session = session
    return session


def normalize_for_match(value: str) -> str:
    return " ".join(ascii_slug(value).split("-"))


def probe_candidate(city: str, slug: str, timeout: float) -> dict[str, Any]:
    url = f"{BASE}/hubs/{quote(slug)}"
    session = thread_session()
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        found_hubs, found_profiles, found_slugs = extract_links(response.text, response.url)
        final_path = urlparse(response.url).path
        if CURRENT_HUB_RE.search(final_path):
            found_hubs.add(canonical_public_url(response.url))
        body_text = BeautifulSoup(response.text, "lxml").get_text(" ", strip=True)
        normalized_body = normalize_for_match(body_text[:250_000])
        expected = normalize_for_match(city)
        specific_city_page = (
            response.status_code == 200
            and expected
            and expected in normalized_body
            and "hub" in body_text.casefold()
            and "global shaper" in body_text.casefold()
        )
        if specific_city_page and not found_hubs:
            found_hubs.add(canonical_public_url(response.url))
        return {
            "city": city,
            "candidate": url,
            "status": response.status_code,
            "final_url": response.url,
            "hub_urls": sorted(found_hubs),
            "profile_urls": sorted(found_profiles),
            "legacy_slugs": sorted(found_slugs),
            "valid": bool(found_hubs),
        }
    except requests.RequestException as exc:
        return {
            "city": city,
            "candidate": url,
            "error": f"{type(exc).__name__}: {exc}",
            "valid": False,
            "hub_urls": [],
            "profile_urls": [],
            "legacy_slugs": [],
        }


def probe_city_urls(
    cities: Iterable[str],
    timeout: float,
    workers: int,
) -> tuple[list[dict[str, Any]], set[str], set[str], dict[str, set[str]]]:
    tasks = [(city, slug) for city in cities for slug in slug_variants(city)]
    observations: list[dict[str, Any]] = []
    hubs: set[str] = set()
    profiles: set[str] = set()
    resolved: dict[str, set[str]] = defaultdict(set)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        future_map = {
            pool.submit(probe_candidate, city, slug, timeout): (city, slug)
            for city, slug in tasks
        }
        for future in as_completed(future_map):
            observation = future.result()
            observations.append(observation)
            city = str(observation["city"])
            found_hubs = set(observation.get("hub_urls") or [])
            found_profiles = set(observation.get("profile_urls") or [])
            hubs.update(found_hubs)
            profiles.update(found_profiles)
            resolved[city].update(found_hubs)
    observations.sort(key=lambda row: (str(row.get("city", "")), str(row.get("candidate", ""))))
    return observations, hubs, profiles, resolved


def hydrate_hub(url: str, timeout: float) -> dict[str, Any]:
    session = thread_session()
    candidates = {
        url,
        f"{url}?tab=members",
        f"{url}?tab=alumni",
        f"{url}/members",
        f"{url}/alumni",
    }
    profiles: set[str] = set()
    linked_hubs: set[str] = set()
    attempts: list[dict[str, Any]] = []
    for candidate in sorted(candidates):
        try:
            response = session.get(candidate, timeout=timeout, allow_redirects=True)
            found_hubs, found_profiles, _ = extract_links(response.text, response.url)
            profiles.update(found_profiles)
            linked_hubs.update(found_hubs)
            attempts.append(
                {
                    "candidate": candidate,
                    "status": response.status_code,
                    "final_url": response.url,
                    "profiles": len(found_profiles),
                }
            )
        except requests.RequestException as exc:
            attempts.append({"candidate": candidate, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "url": url,
        "linked_hubs": sorted(linked_hubs),
        "profile_urls": sorted(profiles),
        "attempts": attempts,
    }


def hydrate_hub_pages(
    hub_urls: Iterable[str],
    timeout: float,
    workers: int,
) -> tuple[set[str], list[dict[str, Any]]]:
    profiles: set[str] = set()
    observations: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(hydrate_hub, url, timeout) for url in sorted(set(hub_urls))]
        for future in as_completed(futures):
            observation = future.result()
            observations.append(observation)
            profiles.update(observation.get("profile_urls") or [])
    observations.sort(key=lambda row: str(row.get("url", "")))
    return profiles, observations


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in sorted(set(values))), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enumerate Global Shapers city names and resolve them into official hub URLs."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--city-file", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("reports/global-shapers-city-hubs.json"))
    parser.add_argument(
        "--hub-url-file",
        type=Path,
        default=Path("imports/global-shapers/generated-hub-urls.txt"),
    )
    parser.add_argument(
        "--profile-url-file",
        type=Path,
        default=Path("imports/global-shapers/generated-member-profile-urls.txt"),
    )
    parser.add_argument("--max-cities", type=int, default=7000)
    parser.add_argument("--geonames-limit", type=int, default=6000)
    parser.add_argument("--min-population", type=int, default=50_000)
    parser.add_argument("--minimum-hubs", type=int, default=1)
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--max-clicks", type=int, default=350)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--browser-timeout-ms", type=int, default=60_000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    source_counts: dict[str, int] = defaultdict(int)

    file_cities = read_city_files(args.city_file)
    source_counts["city_files"] = len(file_cities)

    corpus_cities = cities_from_corpus(root)
    source_counts["corpus"] = len(corpus_cities)

    geonames_cities = cities_from_geonames(args.geonames_limit, args.min_population)
    source_counts["geonames"] = len(geonames_cities)

    cities = set(file_cities) | set(corpus_cities) | set(geonames_cities)
    browser_hubs: set[str] = set()
    browser_profiles: set[str] = set()
    browser_slugs: set[str] = set()
    browser_errors: list[str] = []
    if not args.no_browser:
        (
            browser_cities,
            browser_hubs,
            browser_profiles,
            browser_slugs,
            browser_errors,
        ) = browser_discovery(args.max_clicks, args.browser_timeout_ms)
        cities.update(browser_cities)
        source_counts["browser"] = len(browser_cities)

    for slug in browser_slugs:
        city = clean_city(title_from_slug(slug))
        if city:
            cities.add(city)

    priority = set(file_cities) | set(corpus_cities)
    ordered_cities = sorted(
        cities,
        key=lambda value: (
            0 if value in priority else 1,
            ascii_slug(value),
            value,
        ),
    )[: args.max_cities]

    started = time.time()
    city_observations, probed_hubs, probed_profiles, resolved_by_city_raw = probe_city_urls(
        ordered_cities,
        args.timeout,
        args.workers,
    )
    hub_urls = set(browser_hubs) | set(probed_hubs)
    profile_urls = set(browser_profiles) | set(probed_profiles)
    resolved_by_city = {
        city: sorted(urls)
        for city, urls in sorted(resolved_by_city_raw.items())
        if urls
    }

    hydrated_profiles, hub_observations = hydrate_hub_pages(
        hub_urls,
        args.timeout,
        args.workers,
    )
    profile_urls.update(hydrated_profiles)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_lines(args.hub_url_file, hub_urls)
    write_lines(args.profile_url_file, profile_urls)
    report = {
        "base": BASE,
        "status": "complete" if len(hub_urls) >= args.minimum_hubs else "incomplete",
        "minimum_hubs": args.minimum_hubs,
        "city_count": len(ordered_cities),
        "resolved_city_count": len(resolved_by_city),
        "unresolved_cities": sorted(set(ordered_cities) - set(resolved_by_city)),
        "hub_url_count": len(hub_urls),
        "profile_seed_url_count": len(profile_urls),
        "probe_count": len(city_observations),
        "elapsed_seconds": round(time.time() - started, 3),
        "source_counts": dict(source_counts),
        "hub_urls": sorted(hub_urls),
        "profile_seed_urls": sorted(profile_urls),
        "resolved_by_city": resolved_by_city,
        "city_observations": city_observations,
        "hub_observations": hub_observations,
        "browser_errors": browser_errors,
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "city_count",
                    "resolved_city_count",
                    "hub_url_count",
                    "profile_seed_url_count",
                    "probe_count",
                    "elapsed_seconds",
                )
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
