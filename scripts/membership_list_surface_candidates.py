#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

URL_RE = re.compile(r"https?://[^\s<>\]\[\)\(\"']+")
LIST_ROOTS = {
    "advisers", "advisors", "attendees", "board", "boards", "committee",
    "committees", "delegates", "directory", "experts", "fellows", "leadership",
    "members", "membership", "participants", "people", "roster", "staff", "team",
    "trustees",
}
LIST_SLUGS = {
    "board-of-directors", "board-of-trustees", "committee-members", "council-members",
    "expert-directory", "fellows-directory", "leadership-team", "member-directory",
    "our-experts", "our-fellows", "our-leadership", "our-members", "our-people",
    "our-staff", "our-team", "participant-list", "participants-list", "people-directory",
    "staff-directory", "team-members", "who-we-are",
}
LIST_TEXT = re.compile(
    r"\b(?:our people|people directory|people and leadership|member(?:ship)? (?:directory|list|roster)|"
    r"participants? (?:directory|list|roster)|experts? (?:directory|list|roster)|"
    r"fellows? (?:directory|list|roster)|staff (?:directory|list|roster)|"
    r"team (?:directory|list|members|roster)|leadership (?:directory|team|list|roster)|"
    r"board (?:of )?(?:directors|trustees|members)|committee members?|council members?|"
    r"attendees? (?:list|roster)|delegates? (?:list|roster)|who we are)\b",
    re.I,
)
META_KEYS = {
    "page_type", "role", "kind", "label", "heading", "title", "description",
    "parser", "mode", "section", "list_type", "roster_type",
}
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")
PAGE_RE = re.compile(r"^(?:page[-_]?\d+|\d+)$", re.I)


@dataclass(frozen=True)
class Candidate:
    digest: str
    url: str
    organization: str
    dataset: str
    label: str
    discovered_from: str
    evidence: str


def canonical_url(raw: str) -> str:
    parts = urlsplit(raw.strip().rstrip(".,;:"))
    scheme = parts.scheme.lower()
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


def segment_stem(segment: str) -> str:
    return re.sub(r"\.(?:html?|php|aspx?)$", "", segment.lower())


def is_list_path(url: str) -> bool:
    segments = [segment_stem(segment) for segment in urlsplit(url).path.split("/") if segment]
    if not segments:
        return False
    last = segments[-1]
    if last in LIST_ROOTS or last in LIST_SLUGS:
        return True
    if PAGE_RE.fullmatch(last) and len(segments) > 1:
        return segments[-2] in LIST_ROOTS or segments[-2] in LIST_SLUGS
    return False


def local_evidence(container: dict[str, Any], key: str) -> str:
    values = [key]
    for name in META_KEYS:
        value = container.get(name)
        if isinstance(value, str):
            values.append(value)
    return " ".join(values).replace("-", " ").replace("_", " ")


def qualifies(url: str, evidence: str) -> bool:
    return is_list_path(url) or bool(LIST_TEXT.search(evidence))


def host_label(url: str) -> str:
    host = (urlsplit(url).hostname or "unknown organization").lower()
    return host[4:] if host.startswith("www.") else host


def context(container: dict[str, Any], url: str) -> tuple[str, str, str]:
    def first(keys: tuple[str, ...], default: str = "") -> str:
        for key in keys:
            value = container.get(key)
            if isinstance(value, str) and value.strip() and not value.startswith("http"):
                return value.strip()
        return default

    return (
        first(("organization", "organization_name", "org", "target_name", "name"), host_label(url)),
        first(("dataset", "dataset_id", "slug", "key")),
        first(("label", "heading", "page_type", "role", "kind", "title")),
    )


def walk(value: Any, source: str) -> Iterable[Candidate]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                evidence = local_evidence(value, key)
                for raw in URL_RE.findall(item):
                    url = canonical_url(raw)
                    if not qualifies(url, evidence):
                        continue
                    organization, dataset, label = context(value, url)
                    yield Candidate(
                        hashlib.sha256(url.encode()).hexdigest(),
                        url,
                        organization,
                        dataset,
                        label,
                        source,
                        f"{key}: {item[:900]}",
                    )
            else:
                yield from walk(item, source)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item, source)


def read_path(path: Path) -> list[Candidate]:
    if not path.is_file():
        return []
    if path.suffix == ".jsonl":
        found: list[Candidate] = []
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    found.extend(walk(json.loads(line), f"{path}:{line_number}"))
                except json.JSONDecodeError:
                    for raw in URL_RE.findall(line):
                        url = canonical_url(raw)
                        if is_list_path(url):
                            found.append(Candidate(
                                hashlib.sha256(url.encode()).hexdigest(), url, host_label(url), "", "",
                                f"{path}:{line_number}", line[:900],
                            ))
        return found
    try:
        return list(walk(json.loads(path.read_text(encoding="utf-8")), str(path)))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = path.read_text(encoding="utf-8", errors="replace")
        return [
            Candidate(hashlib.sha256(url.encode()).hexdigest(), url, host_label(url), "", "", str(path), text[:900])
            for raw in URL_RE.findall(text)
            for url in [canonical_url(raw)]
            if is_list_path(url)
        ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract membership-list surfaces while excluding individual profile URLs.")
    parser.add_argument("--input", action="append", default=[], type=Path)
    parser.add_argument("--glob", action="append", default=[])
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    paths = list(args.input)
    for pattern in args.glob:
        paths.extend(Path(".").glob(pattern))
    paths = sorted({path.resolve() for path in paths if path.is_file()})

    candidates: dict[str, Candidate] = {}
    for path in paths:
        for candidate in read_path(path):
            candidates.setdefault(candidate.url, candidate)

    report = {
        "inputs": [str(path) for path in paths],
        "candidate_count": len(candidates),
        "candidates": [
            asdict(candidate)
            for candidate in sorted(candidates.values(), key=lambda item: (item.organization.lower(), item.url))
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
