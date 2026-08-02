#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

BASE = "https://www.globalshapers.org"
DEFAULT_ROUTES = ["/shapers", "/hubs", "/members", "/"]
MEMBER_PATH_RE = re.compile(r"/(?:member-details|shapers|alumni)/[^\s\"'<>?#]+", re.I)
HUB_PATH_RE = re.compile(r"/community-details/[^\s\"'<>?#/]+", re.I)
SALESFORCE_ID_RE = re.compile(r"\b(?:a0e|003)[A-Za-z0-9]{12,15}\b")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
API_HINT_RE = re.compile(
    r"(?:api|graphql|salesforce|community|member|shaper|hub|search|directory|content|experience|aura)",
    re.I,
)


def canonical_url(value: str) -> str | None:
    parsed = urlparse(urljoin(BASE, value))
    if parsed.netloc.casefold() not in {"globalshapers.org", "www.globalshapers.org"}:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    if MEMBER_PATH_RE.fullmatch(path) or HUB_PATH_RE.fullmatch(path):
        return f"https://www.globalshapers.org{path}"
    return None


def extract_text_entities(text: str) -> dict[str, set[str]]:
    members: set[str] = set()
    hubs: set[str] = set()
    urls: set[str] = set()
    salesforce_ids = set(SALESFORCE_ID_RE.findall(text))
    for match in MEMBER_PATH_RE.findall(text):
        value = canonical_url(match)
        if value:
            members.add(value)
    for match in HUB_PATH_RE.findall(text):
        value = canonical_url(match)
        if value:
            hubs.add(value)
    for raw in URL_RE.findall(text):
        clean = raw.rstrip(".,);]}\\")
        urls.add(clean)
        value = canonical_url(clean)
        if value:
            if "/community-details/" in value:
                hubs.add(value)
            else:
                members.add(value)
    for identifier in salesforce_ids:
        if identifier.startswith("a0e"):
            hubs.add(f"{BASE}/community-details/{identifier}")
    return {
        "member_urls": members,
        "hub_urls": hubs,
        "salesforce_ids": salesforce_ids,
        "urls": urls,
    }


def merge_entities(target: dict[str, set[str]], source: dict[str, set[str]]) -> None:
    for key in target:
        target[key].update(source.get(key, set()))


def json_shape(value: Any, *, depth: int = 0, maximum_depth: int = 4) -> Any:
    if depth >= maximum_depth:
        return type(value).__name__
    if isinstance(value, dict):
        return {
            str(key): json_shape(item, depth=depth + 1, maximum_depth=maximum_depth)
            for key, item in list(value.items())[:80]
        }
    if isinstance(value, list):
        return [json_shape(item, depth=depth + 1, maximum_depth=maximum_depth) for item in value[:5]]
    if value is None:
        return None
    return type(value).__name__


def walk_json(value: Any, path: str = "$", depth: int = 0) -> Iterable[tuple[str, Any]]:
    if depth > 30:
        return
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk_json(item, f"{path}.{key}", depth + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_json(item, f"{path}[{index}]", depth + 1)


def summarize_json(value: Any) -> dict[str, Any]:
    key_counts: Counter[str] = Counter()
    string_samples: dict[str, list[str]] = defaultdict(list)
    ids: set[str] = set()
    names: set[str] = set()
    hubs: set[str] = set()
    record_candidates = 0
    for path, item in walk_json(value):
        if isinstance(item, dict):
            lowered = {str(key).casefold(): child for key, child in item.items()}
            for key in lowered:
                key_counts[key] += 1
            identifier = None
            for key in ("id", "recordid", "record_id", "salesforceid", "salesforce_id", "communityid", "memberid"):
                candidate = lowered.get(key)
                if isinstance(candidate, str) and SALESFORCE_ID_RE.fullmatch(candidate):
                    identifier = candidate
                    ids.add(candidate)
                    break
            for key in ("name", "fullname", "full_name", "displayname", "display_name", "title"):
                candidate = lowered.get(key)
                if isinstance(candidate, str) and 2 <= len(candidate.strip()) <= 160:
                    names.add(candidate.strip())
                    if identifier:
                        record_candidates += 1
                    break
            for key in ("hub", "hubname", "hub_name", "community", "communityname", "community_name"):
                candidate = lowered.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    hubs.add(candidate.strip())
        elif isinstance(item, str):
            for match in SALESFORCE_ID_RE.findall(item):
                ids.add(match)
            leaf = path.rsplit(".", 1)[-1].casefold()
            if len(string_samples[leaf]) < 5 and item.strip() and len(item) <= 240:
                string_samples[leaf].append(item.strip())
    return {
        "top_keys": key_counts.most_common(80),
        "salesforce_ids": sorted(ids),
        "names_sample": sorted(names)[:100],
        "hub_names_sample": sorted(hubs)[:100],
        "record_candidates": record_candidates,
        "string_samples": dict(sorted(string_samples.items())[:100]),
        "shape": json_shape(value),
    }


def expand_page(page: Any, max_clicks: int, scroll_rounds: int) -> dict[str, int]:
    clicks = 0
    scrolls = 0
    stable_rounds = 0
    previous_height = 0
    for _ in range(max(max_clicks, scroll_rounds)):
        clicked = False
        if clicks < max_clicks:
            for pattern in (r"show more", r"load more", r"view more", r"see more", r"next"):
                locator = page.get_by_text(re.compile(pattern, re.I))
                try:
                    count = locator.count()
                except Exception:
                    count = 0
                for index in range(min(count, 8) - 1, -1, -1):
                    try:
                        button = locator.nth(index)
                        if button.is_visible(timeout=100) and button.is_enabled(timeout=100):
                            button.click(timeout=1500)
                            page.wait_for_timeout(350)
                            clicks += 1
                            clicked = True
                            break
                    except Exception:
                        continue
                if clicked:
                    break
        if scrolls < scroll_rounds:
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(250)
                height = int(page.evaluate("document.body.scrollHeight"))
                scrolls += 1
                stable_rounds = stable_rounds + 1 if height == previous_height else 0
                previous_height = height
            except Exception:
                stable_rounds += 1
        if not clicked and stable_rounds >= 5:
            break
    return {"clicks": clicks, "scrolls": scrolls, "height": previous_height}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture public Global Shapers frontend state and network responses to discover actual hub/member data sources."
    )
    parser.add_argument("--route", action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("reports/global-shapers-frontend-data.json"))
    parser.add_argument("--hub-url-file", type=Path, default=Path("imports/global-shapers/frontend-hub-urls.txt"))
    parser.add_argument("--profile-url-file", type=Path, default=Path("imports/global-shapers/frontend-profile-urls.txt"))
    parser.add_argument("--max-clicks", type=int, default=700)
    parser.add_argument("--scroll-rounds", type=int, default=900)
    parser.add_argument("--timeout-ms", type=int, default=120_000)
    parser.add_argument("--body-limit", type=int, default=20_000_000)
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    routes = args.route or DEFAULT_ROUTES
    entities = {"member_urls": set(), "hub_urls": set(), "salesforce_ids": set(), "urls": set()}
    responses: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    response_seen: set[tuple[str, int]] = set()

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="StarIntel-AutoDig/0.9 public frontend-data discovery",
            viewport={"width": 1440, "height": 1200},
        )
        page = context.new_page()

        def capture_response(response: Any) -> None:
            key = (response.url, response.status)
            if key in response_seen:
                return
            response_seen.add(key)
            request = response.request
            content_type = response.headers.get("content-type", "")
            interesting = bool(API_HINT_RE.search(response.url) or "json" in content_type.casefold())
            entry: dict[str, Any] = {
                "url": response.url,
                "status": response.status,
                "method": request.method,
                "resource_type": request.resource_type,
                "content_type": content_type,
                "interesting": interesting,
            }
            if response.status >= 400:
                responses.append(entry)
                return
            try:
                body = response.body()
            except Exception as exc:
                entry["body_error"] = f"{type(exc).__name__}: {exc}"
                responses.append(entry)
                return
            entry["bytes"] = len(body)
            entry["sha256"] = hashlib.sha256(body).hexdigest()
            if len(body) > args.body_limit:
                entry["body_skipped"] = "over-limit"
                responses.append(entry)
                return
            text = body.decode("utf-8", errors="ignore")
            found = extract_text_entities(text)
            merge_entities(entities, found)
            entry["member_urls"] = len(found["member_urls"])
            entry["hub_urls"] = len(found["hub_urls"])
            entry["salesforce_ids"] = len(found["salesforce_ids"])
            if "json" in content_type.casefold() or text.lstrip().startswith(("{", "[")):
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    entry["json_error"] = str(exc)
                else:
                    entry["json_summary"] = summarize_json(payload)
            if interesting or entry["member_urls"] or entry["hub_urls"] or entry["salesforce_ids"]:
                entry["text_prefix"] = text[:1200]
            responses.append(entry)

        page.on("response", capture_response)

        for route in routes:
            url = urljoin(BASE, route)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=args.timeout_ms)
                page.wait_for_timeout(1500)
                expansion = expand_page(page, args.max_clicks, args.scroll_rounds)
                html = page.content()
                body_text = page.locator("body").inner_text(timeout=args.timeout_ms)
                html_found = extract_text_entities(html)
                text_found = extract_text_entities(body_text)
                merge_entities(entities, html_found)
                merge_entities(entities, text_found)
                inline_state: dict[str, Any] = {}
                for expression, label in (
                    ("window.__NEXT_DATA__ || null", "__NEXT_DATA__"),
                    ("window.__NUXT__ || null", "__NUXT__"),
                    ("window.__INITIAL_STATE__ || null", "__INITIAL_STATE__"),
                    ("window.__APOLLO_STATE__ || null", "__APOLLO_STATE__"),
                ):
                    try:
                        value = page.evaluate(expression)
                    except Exception as exc:
                        inline_state[label] = {"error": f"{type(exc).__name__}: {exc}"}
                    else:
                        if value is not None:
                            serialized = json.dumps(value, ensure_ascii=False)
                            merge_entities(entities, extract_text_entities(serialized))
                            inline_state[label] = summarize_json(value)
                resources = page.evaluate(
                    "performance.getEntriesByType('resource').map(e => ({name:e.name, initiatorType:e.initiatorType, transferSize:e.transferSize, decodedBodySize:e.decodedBodySize}))"
                )
                scripts = page.eval_on_selector_all("script[src]", "nodes => nodes.map(n => n.src)")
                anchors = page.eval_on_selector_all("a[href]", "nodes => nodes.map(n => n.href)")
                for value in anchors:
                    canonical = canonical_url(value)
                    if canonical:
                        if "/community-details/" in canonical:
                            entities["hub_urls"].add(canonical)
                        else:
                            entities["member_urls"].add(canonical)
                pages.append(
                    {
                        "route": route,
                        "url": page.url,
                        "title": page.title(),
                        "expansion": expansion,
                        "html_bytes": len(html.encode()),
                        "body_characters": len(body_text),
                        "html_member_urls": len(html_found["member_urls"]),
                        "html_hub_urls": len(html_found["hub_urls"]),
                        "body_member_urls": len(text_found["member_urls"]),
                        "body_hub_urls": len(text_found["hub_urls"]),
                        "inline_state": inline_state,
                        "scripts": scripts,
                        "resources": resources,
                        "anchor_count": len(anchors),
                    }
                )
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")

        context.close()
        browser.close()

    responses.sort(key=lambda row: (not bool(row.get("interesting")), row.get("resource_type", ""), row.get("url", "")))
    args.hub_url_file.parent.mkdir(parents=True, exist_ok=True)
    args.profile_url_file.parent.mkdir(parents=True, exist_ok=True)
    args.hub_url_file.write_text("".join(f"{url}\n" for url in sorted(entities["hub_urls"])), encoding="utf-8")
    args.profile_url_file.write_text("".join(f"{url}\n" for url in sorted(entities["member_urls"])), encoding="utf-8")
    report = {
        "base": BASE,
        "status": "complete" if entities["hub_urls"] or entities["member_urls"] else "incomplete",
        "routes": routes,
        "hub_url_count": len(entities["hub_urls"]),
        "member_url_count": len(entities["member_urls"]),
        "salesforce_id_count": len(entities["salesforce_ids"]),
        "all_url_count": len(entities["urls"]),
        "hub_urls": sorted(entities["hub_urls"]),
        "member_urls": sorted(entities["member_urls"]),
        "salesforce_ids": sorted(entities["salesforce_ids"]),
        "pages": pages,
        "responses": responses,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "hub_url_count": report["hub_url_count"],
        "member_url_count": report["member_url_count"],
        "salesforce_id_count": report["salesforce_id_count"],
        "responses": len(responses),
        "errors": len(errors),
    }, indent=2))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
