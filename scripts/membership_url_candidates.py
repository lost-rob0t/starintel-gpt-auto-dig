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
PATH_WORDS = {
    "advisers", "advisors", "attendees", "board", "boards", "committee",
    "committees", "delegates", "directory", "experts", "fellows", "leadership",
    "members", "membership", "participants", "people", "roster", "staff", "team",
    "trustees",
}
TEXT_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"\bmembers(?:hip)?\b", r"\bparticipants?\b", r"\bexperts?\b",
        r"\bfellows?\b", r"\bleadership\b", r"\bstaff\b", r"\bteam\b",
        r"\btrustees?\b", r"\bboard\s+(?:of\s+)?(?:directors|trustees|members)?\b",
        r"\bcommittee\s+members?\b", r"\bcouncil\s+members?\b", r"\bdirectory\b",
        r"\broster\b", r"\battendees?\b", r"\bdelegates?\b", r"\bwho\s+we\s+are\b",
    )
]
META_KEYS = {
    "page_type", "role", "kind", "label", "heading", "title", "description",
    "parser", "mode", "section", "list_type", "roster_type",
}
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")


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
        (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit((scheme, netloc, path, urlencode(sorted(query)), ""))


def host_label(url: str) -> str:
    host = (urlsplit(url).hostname or "unknown organization").lower()
    return host[4:] if host.startswith("www.") else host


def local_evidence(container: dict[str, Any], key: str, item: str) -> str:
    values = [key, item]
    for name in META_KEYS:
        value = container.get(name)
        if isinstance(value, str):
            values.append(value)
    return " ".join(values)


def is_membership_list(url: str, evidence: str) -> bool:
    parts = urlsplit(url)
    segments = {segment.lower() for segment in parts.path.split("/") if segment}
    if segments & PATH_WORDS:
        return True
    text = f"{parts.query} {evidence}".replace("-", " ").replace("_", " ")
    return any(pattern.search(text) for pattern in TEXT_PATTERNS)


def infer_context(container: dict[str, Any], url: str) -> tuple[str, str, str]:
    organization = next((str(container[key]).strip() for key in (
        "organization", "organization_name", "org", "target_name", "name"
    ) if isinstance(container.get(key), str) and not str(container[key]).startswith("http")), host_label(url))
    dataset = next((str(container[key]).strip() for key in (
        "dataset", "dataset_id", "slug", "key"
    ) if isinstance(container.get(key), str) and not str(container[key]).startswith("http")), "")
    label = next((str(container[key]).strip() for key in (
        "label", "heading", "page_type", "role", "kind", "title"
    ) if isinstance(container.get(key), str) and not str(container[key]).startswith("http")), "")
    return organization, dataset, label


def walk(value: Any, source: str) -> Iterable[Candidate]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                evidence = local_evidence(value, key, item)
                for raw in URL_RE.findall(item):
                    url = canonical_url(raw)
                    if not is_membership_list(url, evidence):
                        continue
                    organization, dataset, label = infer_context(value, url)
                    digest = hashlib.sha256(url.encode()).hexdigest()
                    yield Candidate(digest, url, organization, dataset, label, source, f"{key}: {item[:900]}")
            else:
                yield from walk(item, source)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item, source)


def read_candidates(path: Path) -> list[Candidate]:
    if not path.is_file():
        return []
    found: list[Candidate] = []
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    found.extend(walk(json.loads(line), f"{path}:{line_number}"))
                except json.JSONDecodeError:
                    for raw in URL_RE.findall(line):
                        url = canonical_url(raw)
                        if is_membership_list(url, line):
                            found.append(Candidate(
                                hashlib.sha256(url.encode()).hexdigest(), url, host_label(url), "", "",
                                f"{path}:{line_number}", line[:900],
                            ))
        return found
    try:
        return list(walk(json.loads(path.read_text(encoding="utf-8")), str(path)))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in URL_RE.findall(text):
            url = canonical_url(raw)
            if is_membership_list(url, text):
                found.append(Candidate(
                    hashlib.sha256(url.encode()).hexdigest(), url, host_label(url), "", "", str(path), text[:900],
                ))
        return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract canonical membership-list URL candidates without network access.")
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
        for candidate in read_candidates(path):
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
