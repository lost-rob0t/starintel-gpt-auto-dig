#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os

import scrape_violent_offender_recovery_fixups as fixups


def set_current_status(form, payload: dict[str, str]) -> None:
    """Select a current-inmate status whether the form uses select, radio, or checkbox controls."""
    original = fixups.core.form_field(form, ("status",), ("select",))
    select = form.find("select", attrs={"name": original}) if original else None
    if select:
        for option in select.find_all("option"):
            text = fixups.core.normalize_space(option.get_text(" "))
            if "current" in text.casefold():
                payload[original] = option.get("value", text)
                return

    for tag in form.find_all("input"):
        name = tag.get("name")
        if not name:
            continue
        input_type = (tag.get("type") or "text").casefold()
        if input_type not in {"radio", "checkbox"}:
            continue
        value = str(tag.get("value") or "")
        control_id = str(tag.get("id") or "")
        label = form.find("label", attrs={"for": control_id}) if control_id else None
        label_text = fixups.core.normalize_space(label.get_text(" ")) if label else ""
        parent_text = fixups.core.normalize_space(tag.parent.get_text(" ")) if tag.parent else ""
        haystack = " ".join((name, control_id, value, label_text, parent_text)).casefold()
        if "current" not in haystack:
            continue
        if not ("status" in haystack or label_text.casefold() == "current" or value.casefold() == "current"):
            continue
        payload[name] = value or "Current"
        return


def franklin_prefixes() -> list[str]:
    focused = os.environ.get("FRANKLIN_PREFIXES", "").strip()
    if focused:
        return [part.strip().upper() for part in focused.split(",") if part.strip()]
    return ["", *"ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


async def collect_franklin(client, fetched_at: str, max_records: int):
    spec = fixups.recovery.RECOVERY_SOURCES["franklin"]
    first = await fixups.recovery.fetch(client, spec["url"])
    pages = 1
    prefixes = franklin_prefixes()
    search_semaphore = asyncio.Semaphore(min(6, max(1, len(prefixes))))

    async def search(prefix: str):
        async with search_semaphore:
            try:
                response = await fixups.core.submit_form_search(client, first.text, str(first.url), prefix)
                return response
            except Exception as exc:
                return exc

    search_results = await asyncio.gather(*(search(prefix) for prefix in prefixes))
    direct: dict[str, str] = {}
    postbacks: list[tuple[str, str, str, str]] = []
    postback_seen: set[tuple[str, str, str]] = set()
    search_errors = 0
    for result in search_results:
        if isinstance(result, Exception):
            search_errors += 1
            continue
        pages += 1
        for url in fixups.recovery.direct_detail_links(result.text, str(result.url)):
            direct[url] = url
        for target, argument in fixups.recovery.postback_targets(result.text):
            key = (str(result.url), target, argument)
            if key in postback_seen:
                continue
            postback_seen.add(key)
            postbacks.append((result.text, str(result.url), target, argument))

    candidate_total = len(direct) + len(postbacks)
    if candidate_total == 0:
        error = (
            "ParserDrift: Franklin Current-status searches returned no detail links/postbacks "
            f"({search_errors}/{len(prefixes)} searches failed; prefixes={','.join(prefixes) or '<blank>'})"
        )
        return fixups.core.SourceResult(
            "franklin", spec["locality"], spec["url"], fetched_at, [], pages, 0, error
        )

    detail_semaphore = asyncio.Semaphore(12)

    async def load_direct(url: str):
        nonlocal pages
        async with detail_semaphore:
            try:
                detail = await fixups.recovery.fetch(client, url)
                pages += 1
                return fixups.core.detail_record("franklin", detail.text, str(detail.url), fetched_at)
            except Exception:
                return None

    async def load_postback(item: tuple[str, str, str, str]):
        nonlocal pages
        markup, page_url, target, argument = item
        async with detail_semaphore:
            try:
                detail = await fixups.recovery.follow_postback(client, markup, page_url, target, argument)
                pages += 1
                return fixups.core.detail_record("franklin", detail.text, str(detail.url), fetched_at)
            except Exception:
                return None

    direct_items = list(direct)[:max_records]
    remaining = max(0, max_records - len(direct_items))
    work = [load_direct(url) for url in direct_items]
    work.extend(load_postback(item) for item in postbacks[:remaining])
    records = [record for record in await asyncio.gather(*work) if record is not None]
    followed = len(direct_items) + min(len(postbacks), remaining)
    return fixups.core.SourceResult(
        "franklin", spec["locality"], spec["url"], fetched_at, records, pages, followed, None
    )


fixups.core.set_current_status = set_current_status
fixups.recovery.collect_franklin = collect_franklin

fixups.recovery.RECOVERY_SOURCES["summit"]["url"] = (
    "https://sheriff.summitoh.net/files/31565/file/activeoffenderreport.pdf"
)

if __name__ == "__main__":
    raise SystemExit(fixups.recovery.main())
