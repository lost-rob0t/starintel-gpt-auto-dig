from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import html
import json
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DOCUMENT_SUFFIXES = {".csv", ".doc", ".docx", ".json", ".pdf", ".rtf", ".xls", ".xlsx", ".xml", ".zip"}
DEPLOYMENT_MARKERS = (
    "ansible",
    "compose",
    "deploy",
    "docker",
    "environment",
    "helm",
    "k8s",
    "kubernetes",
    "operator",
    "production",
    "terraform",
    "workflow",
)
COLLECTORS = {"auditor", "github", "legistar", "site", "wayback"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalized_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(normalized_text(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return " ".join(normalized_text(item) for item in value)
    return re.sub(r"\s+", " ", str(value)).strip()


def keyword_hits(value: Any, keywords: Sequence[str]) -> tuple[str, ...]:
    text = normalized_text(value).casefold()
    tokenized_text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE).strip()
    hits: list[str] = []
    for keyword in keywords:
        folded = keyword.casefold()
        tokenized_keyword = re.sub(r"[\W_]+", " ", folded, flags=re.UNICODE).strip()
        if folded in text or (tokenized_keyword and tokenized_keyword in tokenized_text):
            hits.append(keyword)
    return tuple(hits)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def clean_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, ""))


def safe_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-.")
    return slug[:180] or "document"


@dataclasses.dataclass(frozen=True)
class TargetPlan:
    target_id: str
    title: str
    collectors: tuple[str, ...]
    keywords: tuple[str, ...]
    seed_urls: tuple[str, ...] = ()
    wayback_patterns: tuple[str, ...] = ()
    github_repositories: tuple[str, ...] = ()
    github_queries: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TargetPlan":
        target_id = str(value["target_id"])
        collectors = tuple(str(item) for item in value.get("collectors", ()))
        unknown = sorted(set(collectors) - COLLECTORS)
        if unknown:
            raise ValueError(f"{target_id}: unknown collectors: {', '.join(unknown)}")
        keywords = tuple(dict.fromkeys(str(item).strip() for item in value.get("keywords", ()) if str(item).strip()))
        if not collectors or not keywords:
            raise ValueError(f"{target_id}: collectors and keywords are required")
        return cls(
            target_id=target_id,
            title=str(value["title"]),
            collectors=collectors,
            keywords=keywords,
            seed_urls=tuple(str(item) for item in value.get("seed_urls", ())),
            wayback_patterns=tuple(str(item) for item in value.get("wayback_patterns", ())),
            github_repositories=tuple(str(item) for item in value.get("github_repositories", ())),
            github_queries=tuple(str(item) for item in value.get("github_queries", ())),
        )


@dataclasses.dataclass(frozen=True)
class Observation:
    collector: str
    target_id: str
    kind: str
    source_url: str
    payload: Any
    matched_keywords: tuple[str, ...] = ()
    retrieved_at: str = dataclasses.field(default_factory=utc_now)

    def as_dict(self) -> dict[str, Any]:
        payload_sha256 = content_hash(self.payload)
        identity = canonical_json([self.collector, self.target_id, self.source_url, payload_sha256])
        return {
            "collector": self.collector,
            "target_id": self.target_id,
            "kind": self.kind,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "matched_keywords": list(self.matched_keywords),
            "match_count": len(self.matched_keywords),
            "payload_sha256": payload_sha256,
            "observation_id": f"sha256:{hashlib.sha256(identity).hexdigest()}",
            "payload": self.payload,
        }


@dataclasses.dataclass(frozen=True)
class CollectJob:
    collector: str
    target: TargetPlan


@dataclasses.dataclass(frozen=True)
class Stop:
    pass


class PageParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.meta: dict[str, str] = {}
        self._in_title = False
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value or "" for name, value in attrs}
        tag = tag.casefold()
        if tag == "title":
            self._in_title = True
        elif tag == "a" and values.get("href"):
            self._anchor_href = urllib.parse.urljoin(self.base_url, values["href"])
            self._anchor_text = []
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key and values.get("content"):
                self.meta[key.casefold()] = values["content"]

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "title":
            self._in_title = False
        elif tag == "a" and self._anchor_href:
            self.links.append((normalized_text(self._anchor_text), clean_url(self._anchor_href)))
            self._anchor_href = None
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        text = normalized_text(html.unescape(data))
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._anchor_href:
            self._anchor_text.append(text)
        self.text_parts.append(text)

    @property
    def title(self) -> str:
        return normalized_text(self.title_parts)

    @property
    def text(self) -> str:
        return normalized_text(self.text_parts)


class Collector:
    name = "collector"

    def __init__(self, client: Any, args: Any, config: Mapping[str, Any]) -> None:
        self.client = client
        self.args = args
        self.config = config

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        raise NotImplementedError
