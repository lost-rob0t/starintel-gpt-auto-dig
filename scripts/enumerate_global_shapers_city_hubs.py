#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.globalshapers.org"
PUBLIC_PAGES = ["/", "/shapers", "/projects", "/impact", "/about", "/alumni"]
HUB_RE = re.compile(r"(?P<city>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.()\-/ ]{1,70}?)\s+Hub\b")
CURRENT_HUB_RE = re.compile(r"/community-details/[A-Za-z0-9_-]+", re.I)
PROFILE_RE = re.compile(r"/member-details/[^?#\s\"']+", re.I)
NOISE = {
    "global shapers", "local", "our", "the", "a", "an", "cross", "community",
    "founding curator and global shaper", "global shaper", "curator", "alumni",
}


def compact_space(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def clean_city(value: str) -> str | None:
    value = compact_space(value).strip(" ,;:–—-|/")
    value = re.sub(r"^(?:the\s+)", "", value, flags=re.I)
    value = re.sub(r"\s+[IVX]+$", "", value)
    if not value or len(value) < 2 or len(value) > 72:
        return None
    if value.casefold() in NOISE:
        return None
    if sum(ch.isalpha() for ch in value) < 2:
        return None
    if any(token in value.casefold() for token in ("project", "report", "community annual", "global shapers community")):
        return None
    return value


def ascii_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def slug_variants(city: str) -> list[str]:
    base = ascii_slug(city)
    variants = {base, f"{base}-hub"}
    variants.add(base.replace("-and-", "-"))
    variants.add(base.replace("-saint-", "-st-"))
    if base.startswith("saint-"):
        variants.add("st-" + base.removeprefix("saint-"))
    if base.startswith("st-"):
        variants.add("saint-" + base.removeprefix("st-"))
    return sorted(v for v in variants if v)


def extract_links(html: str, base_url: str) -> tuple[set[str], set[str]]:
    soup = BeautifulSoup(html, "lxml")
    hubs: set[str] = set()
    profiles: set[str] = set()
    for link in soup.select("a[href]"):
        href = urljoin(base_url, str(link.get("href", "")))
        parsed = urlparse(href)
        if parsed.netloc.casefold() not in {"globalshapers.org", "www.globalshapers.org"}:
            continue
        if CURRENT_HUB_RE.search(parsed.path):
            hubs.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
        elif PROFILE_RE.search(parsed.path):
            profiles.add(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
    return hubs, profiles


def extract_cities(text: str) -> set[str]:
    cities: set[str] = set()
    for match in HUB_RE.finditer(compact_space(text)):
        city = clean_city(match.group("city"))
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


def cities_from_corpus(root: Path) -> set[str]:
    cities: set[str] = set()
    candidates = list(root.glob("db/*/*.ndjson"))
    candidates += list(root.glob("digs/*/*/*.json"))
    candidates += list(root.glob("reports/*.json"))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        cities.update(extract_cities(text))
    return cities


def browser_discovery(max_clicks: int, timeout_ms: int) -> tuple[set[str], set[str], set[str], list[str]]:
    from playwright.sync_api import sync_playwright

    cities: set[str] = set()
    hubs: set[str] = set()
    profiles: set[str] = set()
    errors: list[str] = []
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(user_agent="StarIntel-AutoDig/0.9 public roster enumerator")
        page = context.new_page()
        for route in PUBLIC_PAGES:
            url = urljoin(BASE, route)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1000)
                for _ in range(max_clicks):
                    clicked = False
                    for pattern in (r"show more", r"load more", r"view more", r"see more"):
                        button = page.get_by_text(re.compile(pattern, re.I)).last
                        try:
                            if button.is_visible(timeout=250):
                                button.click(timeout=1000)
                                page.wait_for_timeout(450)
                                clicked = True
                                break
                        except Exception:
                            pass
                    if not clicked:
                        break
                html = page.content()
                text = page.locator("body").inner_text(timeout=timeout_ms)
                cities.update(extract_cities(text))
                found_hubs, found_profiles = extract_links(html, page.url)
                hubs.update(found_hubs)
                profiles.update(found_profiles)
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        context.close()
        browser.close()
    return cities, hubs, profiles, errors


def probe_legacy_city_urls(
    session: requests.Session,
    city: str,
    timeout: float,
) -> tuple[list[dict[str, object]], set[str], set[str]]:
    observations: list[dict[str, object]] = []
    hubs: set[str] = set()
    profiles: set[str] = set()
    for slug in slug_variants(city):
        url = f"{BASE}/hubs/{quote(slug)}"
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            found_hubs, found_profiles = extract_links(response.text, response.url)
            if CURRENT_HUB_RE.search(urlparse(response.url).path):
                found_hubs.add(response.url.split("?", 1)[0].split("#", 1)[0])
            body_text = BeautifulSoup(response.text, "lxml").get_text(" ", strip=True)
            expected = ascii_slug(city).replace("-", " ")
            valid_legacy = response.status_code == 200 and expected in ascii_slug(body_text).replace("-", " ") and "hub" in body_text.casefold()
            if valid_legacy and not found_hubs:
                found_hubs.add(response.url.split("?", 1)[0].split("#", 1)[0])
            hubs.update(found_hubs)
            profiles.update(found_profiles)
            observations.append({
                "city": city,
                "candidate": url,
                "status": response.status_code,
                "final_url": response.url,
                "hub_urls": sorted(found_hubs),
                "profile_urls": len(found_profiles),
                "valid": bool(found_hubs),
            })
        except requests.RequestException as exc:
            observations.append({"city": city, "candidate": url, "error": str(exc), "valid": False})
    return observations, hubs, profiles


def hydrate_hub_pages(session: requests.Session, hub_urls: Iterable[str], timeout: float) -> tuple[set[str], list[dict[str, object]]]:
    profiles: set[str] = set()
    observations: list[dict[str, object]] = []
    for url in sorted(set(hub_urls)):
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            found_hubs, found_profiles = extract_links(response.text, response.url)
            profiles.update(found_profiles)
            observations.append({
                "url": url,
                "status": response.status_code,
                "final_url": response.url,
                "linked_hubs": sorted(found_hubs),
                "profile_urls": len(found_profiles),
            })
        except requests.RequestException as exc:
            observations.append({"url": url, "error": str(exc)})
    return profiles, observations


def write_lines(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value}\n" for value in sorted(set(values))), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enumerate Global Shapers city names and resolve them into official hub URLs.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--city-file", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("reports/global-shapers-city-hubs.json"))
    parser.add_argument("--hub-url-file", type=Path, default=Path("imports/global-shapers/generated-hub-urls.txt"))
    parser.add_argument("--profile-url-file", type=Path, default=Path("imports/global-shapers/generated-member-profile-urls.txt"))
    parser.add_argument("--max-cities", type=int, default=2000)
    parser.add_argument("--max-clicks", type=int, default=350)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--browser-timeout-ms", type=int, default=60000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    source_counts: dict[str, int] = defaultdict(int)
    cities = read_city_files(args.city_file)
    source_counts["city_files"] = len(cities)
    corpus_cities = cities_from_corpus(root)
    cities.update(corpus_cities)
    source_counts["corpus"] = len(corpus_cities)

    browser_hubs: set[str] = set()
    browser_profiles: set[str] = set()
    browser_errors: list[str] = []
    if not args.no_browser:
        browser_cities, browser_hubs, browser_profiles, browser_errors = browser_discovery(args.max_clicks, args.browser_timeout_ms)
        cities.update(browser_cities)
        source_counts["browser"] = len(browser_cities)

    ordered_cities = sorted(cities, key=lambda value: (ascii_slug(value), value))[: args.max_cities]
    session = requests.Session()
    session.headers.update({"User-Agent": "StarIntel-AutoDig/0.9 (+https://starintel.actor; public roster enumeration)"})

    hub_urls = set(browser_hubs)
    profile_urls = set(browser_profiles)
    city_observations: list[dict[str, object]] = []
    resolved_by_city: dict[str, list[str]] = {}
    for city in ordered_cities:
        observations, found_hubs, found_profiles = probe_legacy_city_urls(session, city, args.timeout)
        city_observations.extend(observations)
        hub_urls.update(found_hubs)
        profile_urls.update(found_profiles)
        if found_hubs:
            resolved_by_city[city] = sorted(found_hubs)
        time.sleep(0.03)

    hydrated_profiles, hub_observations = hydrate_hub_pages(session, hub_urls, args.timeout)
    profile_urls.update(hydrated_profiles)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_lines(args.hub_url_file, hub_urls)
    write_lines(args.profile_url_file, profile_urls)
    report = {
        "base": BASE,
        "city_count": len(ordered_cities),
        "resolved_city_count": len(resolved_by_city),
        "unresolved_cities": sorted(set(ordered_cities) - set(resolved_by_city)),
        "hub_url_count": len(hub_urls),
        "profile_seed_url_count": len(profile_urls),
        "source_counts": dict(source_counts),
        "hub_urls": sorted(hub_urls),
        "profile_seed_urls": sorted(profile_urls),
        "resolved_by_city": resolved_by_city,
        "city_observations": city_observations,
        "hub_observations": hub_observations,
        "browser_errors": browser_errors,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("city_count", "resolved_city_count", "hub_url_count", "profile_seed_url_count")}, indent=2))
    return 0 if hub_urls else 2


if __name__ == "__main__":
    raise SystemExit(main())
