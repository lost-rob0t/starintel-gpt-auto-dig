from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Sequence

from starintel_doc.model import utc_now

from .constants import BLOCK_TAGS, FIELD_LABELS, VOID_TAGS
from .utils import canonicalize_url, clean, content_digest, first, iter_json_ld_nodes, normalize_datetime, normalize_resource_url, profile_kind


class ProfileHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.canonical = ""
        self.meta_description = ""
        self.lines: list[str] = []
        self.paragraphs: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.json_ld: list[Any] = []
        self._ignored_depth = 0
        self._capture_json_ld = False
        self._json_ld_buffer: list[str] = []
        self._title_buffer: list[str] = []
        self._h1_buffer: list[str] = []
        self._block_buffers: list[list[str]] = []
        self._paragraph_buffers: list[list[str]] = []
        self._anchor_href = ""
        self._anchor_buffer: list[str] = []
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            if tag == "script" and attrs_map.get("type", "").lower() == "application/ld+json":
                self._capture_json_ld = True
                self._json_ld_buffer = []
            else:
                self._ignored_depth += 1
            self._tag_stack.append(tag)
            return
        if self._ignored_depth:
            if tag not in VOID_TAGS:
                self._tag_stack.append(tag)
            return
        if tag not in VOID_TAGS:
            self._tag_stack.append(tag)
        if tag == "link" and "canonical" in attrs_map.get("rel", "").lower().split():
            self.canonical = attrs_map.get("href", "")
        elif tag == "meta":
            if attrs_map.get("name", "").lower() == "description" or attrs_map.get("property", "").lower() == "og:description":
                self.meta_description = self.meta_description or clean(attrs_map.get("content"))
        elif tag == "a":
            self._anchor_href = attrs_map.get("href", "")
            self._anchor_buffer = []
        if tag in BLOCK_TAGS:
            self._block_buffers.append([])
        if tag == "p":
            self._paragraph_buffers.append([])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self._capture_json_ld:
            self._capture_json_ld = False
            raw = "".join(self._json_ld_buffer).strip()
            if raw:
                try:
                    self.json_ld.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
            self._json_ld_buffer = []
            if self._tag_stack:
                self._tag_stack.pop()
            return
        if tag in {"script", "style", "noscript", "svg"}:
            if self._ignored_depth:
                self._ignored_depth -= 1
            if self._tag_stack:
                self._tag_stack.pop()
            return
        if self._ignored_depth:
            return
        if tag == "a" and self._anchor_href:
            self.links.append((clean(" ".join(self._anchor_buffer)), self._anchor_href))
            self._anchor_href = ""
            self._anchor_buffer = []
        if tag == "title":
            self.title = clean(" ".join(self._title_buffer))
            self._title_buffer = []
        if tag == "h1":
            self.h1 = clean(" ".join(self._h1_buffer))
            self._h1_buffer = []
        if tag == "p" and self._paragraph_buffers:
            value = clean(" ".join(self._paragraph_buffers.pop()))
            if value:
                self.paragraphs.append(value)
        if tag in BLOCK_TAGS and self._block_buffers:
            value = clean(" ".join(self._block_buffers.pop()))
            if value:
                self.lines.append(value)
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_ld_buffer.append(data)
            return
        if self._ignored_depth:
            return
        value = clean(data)
        if not value:
            return
        current = self._tag_stack[-1] if self._tag_stack else ""
        if current == "title":
            self._title_buffer.append(value)
        if current == "h1":
            self._h1_buffer.append(value)
        if self._block_buffers:
            self._block_buffers[-1].append(value)
        if self._paragraph_buffers:
            self._paragraph_buffers[-1].append(value)
        if self._anchor_href:
            self._anchor_buffer.append(value)


@dataclass(slots=True)
class Profile:
    url: str
    dtype: str
    profile_type: str
    title: str
    summary: str
    text: str
    fields: dict[str, str]
    links: list[tuple[str, str]]
    content_hash: str
    collected_at: str
    published_at: str | None = None
    modified_at: str | None = None
    image_url: str = ""


def extract_fields(lines: Sequence[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    normalized = [clean(line) for line in lines if clean(line)]
    index = 0
    while index < len(normalized):
        line = normalized[index]
        match = re.match(r"^([^:]{1,48}):\s*(.*)$", line)
        if match:
            key, value = clean(match.group(1)).lower(), clean(match.group(2))
            if key in FIELD_LABELS:
                if not value and index + 1 < len(normalized):
                    index += 1
                    value = normalized[index]
                if value:
                    fields.setdefault(key, value)
        elif line.lower().rstrip(":") in FIELD_LABELS and index + 1 < len(normalized):
            fields.setdefault(line.lower().rstrip(":"), normalized[index + 1])
            index += 1
        index += 1
    return fields


def parse_profile(payload: bytes, source_url: str, *, collected_at: str | None = None) -> Profile:
    parser = ProfileHTMLParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    canonical = canonicalize_url(parser.canonical or source_url, base=source_url)
    kind = profile_kind(canonical)
    if kind is None:
        raise ValueError(f"not an InfluenceWatch profile URL: {canonical}")
    profile_type, dtype = kind
    ld_nodes = [node for item in parser.json_ld for node in iter_json_ld_nodes(item)]
    ld_title = first(next((node.get("headline") or node.get("name") for node in ld_nodes if node.get("headline") or node.get("name")), ""))
    ld_description = first(next((node.get("description") for node in ld_nodes if node.get("description")), ""))
    published_at = normalize_datetime(next((node.get("datePublished") for node in ld_nodes if node.get("datePublished")), ""))
    modified_at = normalize_datetime(next((node.get("dateModified") for node in ld_nodes if node.get("dateModified")), ""))
    image_url = first(next((node.get("image") for node in ld_nodes if node.get("image")), ""))
    title = clean(parser.h1 or ld_title or parser.title.removesuffix(" - Influence Watch"))
    if not title:
        raise ValueError(f"profile has no title: {canonical}")
    paragraphs = [value for value in parser.paragraphs if value not in {title, "Read More"}]
    summary = clean(parser.meta_description or ld_description or (paragraphs[0] if paragraphs else ""))
    text_lines = list(dict.fromkeys(clean(line) for line in parser.lines if clean(line)))
    links: list[tuple[str, str]] = []
    seen_links: set[str] = set()
    for label, href in parser.links:
        absolute = canonicalize_url(href, base=canonical)
        if absolute == canonical or profile_kind(absolute) is None or absolute in seen_links:
            continue
        seen_links.add(absolute)
        links.append((clean(label), absolute))
    return Profile(
        url=canonical,
        dtype=dtype,
        profile_type=profile_type,
        title=title,
        summary=summary,
        text="\n\n".join(text_lines),
        fields=extract_fields(text_lines),
        links=links,
        content_hash=content_digest(payload),
        collected_at=collected_at or utc_now(),
        published_at=published_at,
        modified_at=modified_at,
        image_url=normalize_resource_url(image_url, base=canonical) if image_url else "",
    )
