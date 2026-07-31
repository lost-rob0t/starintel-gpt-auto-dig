#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

URL_RE = re.compile(r"https?://[^\s<>\]\[\)\(\"']+")
MARKER_RE = re.compile(r"membership-list-url-sha256:([0-9a-f]{64})")
KEYWORDS = {
    "advisers", "advisors", "attendees", "board", "committee", "council",
    "delegates", "directory", "experts", "fellows", "governance",
    "leadership", "members", "membership", "participants", "people",
    "roster", "staff", "team", "trustees", "who we are",
}
PATH_SEGMENTS = {
    "advisers", "advisors", "attendees", "board", "boards", "committee",
    "committees", "council", "delegates", "directory", "experts", "fellows",
    "leadership", "members", "membership", "participants", "people", "roster",
    "staff", "team", "trustees",
}
PROFILE_HINTS = {"profile", "biography", "bio"}
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")


@dataclass(frozen=True)
class Candidate:
    url: str
    organization: str
    dataset: str
    label: str
    discovered_from: str
    evidence: str

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()


def canonical_url(raw: str) -> str:
    raw = raw.strip().rstrip(".,;:")
    parts = urlsplit(raw)
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


def human_host(url: str) -> str:
    host = (urlsplit(url).hostname or "unknown organization").lower()
    return host[4:] if host.startswith("www.") else host


def compact(value: Any, limit: int = 800) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(compact(item, 120) for item in value[:12])[:limit]
    if isinstance(value, dict):
        return " ".join(f"{key} {compact(item, 120)}" for key, item in list(value.items())[:20])[:limit]
    return str(value)[:limit]


def looks_like_membership_list(url: str, evidence: str) -> bool:
    parts = urlsplit(url)
    segments = {segment.lower() for segment in parts.path.split("/") if segment}
    haystack = f"{parts.path} {parts.query} {evidence}".lower().replace("-", " ").replace("_", " ")
    keyword_hit = any(re.search(rf"\b{re.escape(word)}\b", haystack) for word in KEYWORDS)
    path_hit = bool(segments & PATH_SEGMENTS)
    profile_only = bool(segments & PROFILE_HINTS) and not path_hit and not keyword_hit
    return (path_hit or keyword_hit) and not profile_only


def infer_context(container: dict[str, Any], fallback_url: str) -> tuple[str, str, str]:
    organization = ""
    for key in ("organization", "organization_name", "org", "name", "title", "target_name"):
        value = container.get(key)
        if isinstance(value, str) and value.strip() and not value.startswith("http"):
            organization = value.strip()
            break
    dataset = ""
    for key in ("dataset", "dataset_id", "slug", "key"):
        value = container.get(key)
        if isinstance(value, str) and value.strip() and not value.startswith("http"):
            dataset = value.strip()
            break
    label = ""
    for key in ("label", "title", "heading", "page_type", "role", "kind", "name"):
        value = container.get(key)
        if isinstance(value, str) and value.strip() and not value.startswith("http"):
            label = value.strip()
            break
    return organization or human_host(fallback_url), dataset, label


def walk_json(value: Any, source: str, ancestors: tuple[dict[str, Any], ...] = ()) -> Iterable[Candidate]:
    if isinstance(value, dict):
        chain = (*ancestors, value)
        evidence = " ".join(compact(item, 500) for item in chain[-3:])
        for key, item in value.items():
            if isinstance(item, str):
                for raw_url in URL_RE.findall(item):
                    url = canonical_url(raw_url)
                    if looks_like_membership_list(url, f"{key} {evidence}"):
                        organization, dataset, label = infer_context(value, url)
                        yield Candidate(url, organization, dataset, label, source, f"{key}: {compact(item)}")
            else:
                yield from walk_json(item, source, chain)
    elif isinstance(value, list):
        for item in value:
            yield from walk_json(item, source, ancestors)


def read_candidates(path: Path) -> list[Candidate]:
    if not path.exists() or not path.is_file():
        return []
    if path.suffix == ".jsonl":
        found: list[Candidate] = []
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    for raw_url in URL_RE.findall(line):
                        url = canonical_url(raw_url)
                        if looks_like_membership_list(url, line):
                            found.append(Candidate(url, human_host(url), "", "", f"{path}:{line_number}", line[:500]))
                    continue
                found.extend(walk_json(value, f"{path}:{line_number}"))
        return found
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = path.read_text(encoding="utf-8", errors="replace")
        found = []
        for raw_url in URL_RE.findall(text):
            url = canonical_url(raw_url)
            if looks_like_membership_list(url, text):
                found.append(Candidate(url, human_host(url), "", "", str(path), text[:500]))
        return found
    return list(walk_json(value, str(path)))


def github_json(method: str, url: str, token: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "starintel-membership-url-issue-queue",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {exc.code} {detail}") from exc


def existing_markers(repository: str, token: str) -> dict[str, int]:
    markers: dict[str, int] = {}
    page = 1
    while True:
        items = github_json("GET", f"https://api.github.com/repos/{repository}/issues?state=all&per_page=100&page={page}", token)
        if not items:
            break
        for item in items:
            for digest in MARKER_RE.findall(str(item.get("body") or "")):
                markers[digest] = int(item["number"])
        if len(items) < 100:
            break
        page += 1
    return markers


def issue_title(candidate: Candidate) -> str:
    org = re.sub(r"\s+", " ", candidate.organization).strip()[:80]
    label = re.sub(r"\s+", " ", candidate.label).strip()[:70]
    suffix = label or urlsplit(candidate.url).path.strip("/").split("/")[-1] or "membership list"
    return f"Scrape membership list: {org} — {suffix}"[:240]


def issue_body(candidate: Candidate) -> str:
    marker = f"<!-- membership-list-url-sha256:{candidate.digest} -->"
    dataset = candidate.dataset or "unresolved"
    label = candidate.label or "unresolved"
    return f"""{marker}
## Membership-list scraper target

- **Organization:** {candidate.organization}
- **Dataset:** `{dataset}`
- **URL:** {candidate.url}
- **Page label:** {label}
- **Discovered from:** `{candidate.discovered_from}`

## Required parser work

- [ ] Verify this is an official public membership, leadership, board, fellow, expert, participant, staff, or comparable roster surface.
- [ ] Add or extend the organization-specific scraper instead of relying on generic card extraction alone.
- [ ] Traverse pagination, year archives, regional tabs, and linked roster pages.
- [ ] Preserve published roles, affiliations, dates/years, regions, and source-page provenance.
- [ ] Record only contact details explicitly published by the organization.
- [ ] Import through the canonical StarIntel writer and validate the complete corpus.
- [ ] Add regression coverage so the URL remains supported.

## Discovery evidence

```text
{candidate.evidence[:1200]}
```
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open one deduplicated GitHub issue per discovered membership-list URL.")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--input", action="append", default=[], type=Path)
    parser.add_argument("--glob", action="append", default=[])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--max-create", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository:
        raise SystemExit("--repository or GITHUB_REPOSITORY is required")
    if not args.dry_run and not args.token:
        raise SystemExit("--token or GITHUB_TOKEN is required")

    paths = list(args.input)
    for pattern in args.glob:
        paths.extend(Path(".").glob(pattern))
    paths = sorted({path.resolve() for path in paths if path.exists() and path.is_file()})

    merged: dict[str, Candidate] = {}
    for path in paths:
        for candidate in read_candidates(path):
            merged.setdefault(candidate.url, candidate)

    existing = {} if args.dry_run else existing_markers(args.repository, args.token)
    created: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    for candidate in sorted(merged.values(), key=lambda item: (item.organization.lower(), item.url)):
        if candidate.digest in existing:
            retained.append({**asdict(candidate), "issue_number": existing[candidate.digest]})
            continue
        if len(created) >= args.max_create:
            raise RuntimeError(f"refusing to create more than {args.max_create} issues in one run")
        if args.dry_run:
            created.append({**asdict(candidate), "issue_number": None, "dry_run": True})
            continue
        issue = github_json(
            "POST",
            f"https://api.github.com/repos/{args.repository}/issues",
            args.token,
            {"title": issue_title(candidate), "body": issue_body(candidate)},
        )
        created.append({**asdict(candidate), "issue_number": int(issue["number"]), "html_url": issue.get("html_url")})

    report = {
        "repository": args.repository,
        "inputs": [str(path) for path in paths],
        "candidate_count": len(merged),
        "created_count": len(created),
        "existing_count": len(retained),
        "created": created,
        "existing": retained,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
