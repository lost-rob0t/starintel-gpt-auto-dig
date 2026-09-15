#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any
from urllib.parse import urlsplit

MARKER_RE = re.compile(r"membership-list-url-sha256:([0-9a-f]{64})")
URL_LINE_RE = re.compile(r"^- \*\*URL:\*\*\s+(https?://\S+)", re.MULTILINE)
PROFILE_ROOTS = {
    "people", "experts", "members", "fellows", "staff", "team", "advisers",
    "advisors", "trustees", "participants", "profiles", "profile", "bios",
    "bio", "biographies", "biography",
}
LIST_ROOTS = {
    "people", "experts", "members", "membership", "fellows", "staff", "team",
    "advisers", "advisors", "trustees", "participants", "leadership", "board",
    "boards", "committee", "committees", "directory", "roster", "attendees",
    "delegates",
}
LIST_SLUG_RE = re.compile(
    r"(?:^|[-_])(?:members?|membership|participants?|attendees?|delegates?|experts?|"
    r"fellows?|leadership|staff|team|trustees?|boards?|committees?|directory|roster)"
    r"(?:$|[-_\d])",
    re.IGNORECASE,
)


def run_gh(arguments: list[str], *, capture: bool = True) -> str:
    completed = subprocess.run(
        ["gh", *arguments],
        check=True,
        text=True,
        capture_output=capture,
    )
    return completed.stdout.strip() if capture else ""


def issue_snapshot(repository: str, state: str, limit: int) -> list[dict[str, Any]]:
    output = run_gh(
        [
            "issue", "list", "--repo", repository, "--state", state,
            "--limit", str(limit), "--json", "number,title,body,url,state",
        ]
    )
    return json.loads(output or "[]")


def normalized_segments(url: str) -> list[str]:
    return [
        re.sub(r"\.(?:html?|php|aspx?)$", "", segment.lower())
        for segment in urlsplit(url).path.split("/")
        if segment
    ]


def invalid_generated_issue(issue: dict[str, Any]) -> bool:
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    if not title.startswith("Scrape membership list:"):
        return False
    if not MARKER_RE.search(body):
        return False
    match = URL_LINE_RE.search(body)
    if not match:
        return False

    segments = normalized_segments(match.group(1).rstrip(".,;:"))
    if not segments or segments == ["news"]:
        return True
    if len(segments) < 2:
        return False

    parent = segments[-2]
    leaf = segments[-1]
    if parent not in PROFILE_ROOTS:
        return False
    if leaf in LIST_ROOTS or LIST_SLUG_RE.search(leaf):
        return False
    return True


def drain_invalid_issues(
    repository: str,
    *,
    passes: int,
    stable_passes: int,
    batch_limit: int,
    sleep_seconds: float,
) -> list[int]:
    closed: list[int] = []
    stable = 0
    for pass_number in range(1, passes + 1):
        issues = issue_snapshot(repository, "open", batch_limit)
        invalid = [int(issue["number"]) for issue in issues if invalid_generated_issue(issue)]
        if not invalid:
            stable += 1
            print(json.dumps({"cleanup_pass": pass_number, "invalid": 0, "stable": stable}))
            if stable >= stable_passes:
                break
            time.sleep(sleep_seconds)
            continue

        stable = 0
        print(
            json.dumps(
                {
                    "cleanup_pass": pass_number,
                    "closing": len(invalid),
                    "first": min(invalid),
                    "last": max(invalid),
                }
            )
        )
        for number in invalid:
            run_gh(
                [
                    "issue", "close", str(number), "--repo", repository,
                    "--reason", "not planned",
                ],
                capture=False,
            )
        closed.extend(invalid)
        time.sleep(sleep_seconds)
    return closed


def load_candidates(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    candidates = value.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("candidate report must contain a candidates list")
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def marker_index(repository: str, limit: int) -> dict[str, dict[str, Any]]:
    markers: dict[str, dict[str, Any]] = {}
    for issue in issue_snapshot(repository, "all", limit):
        for digest in MARKER_RE.findall(str(issue.get("body") or "")):
            markers[digest] = issue
    return markers


def issue_body(candidate: dict[str, Any]) -> str:
    digest = str(candidate["digest"])
    organization = str(candidate.get("organization") or "unresolved")
    dataset = str(candidate.get("dataset") or "unresolved")
    label = str(candidate.get("label") or "unresolved")
    source = str(candidate.get("discovered_from") or "unknown")
    evidence = str(candidate.get("evidence") or "")[:1200]
    url = str(candidate["url"])
    return f"""<!-- membership-list-url-sha256:{digest} -->
## Membership-list scraper target

- **Organization:** {organization}
- **Dataset:** `{dataset}`
- **URL:** {url}
- **Page label:** {label}
- **Discovered from:** `{source}`

## Required parser work

- [ ] Verify this official public roster-list surface.
- [ ] Add or extend the organization-specific parser.
- [ ] Traverse pagination, year archives, regions, tabs, and linked roster pages.
- [ ] Preserve roles, affiliations, dates/years, regions, and source provenance.
- [ ] Record only contacts explicitly published by the organization.
- [ ] Import through the canonical StarIntel writer and validate the corpus.
- [ ] Add regression coverage for this URL.

```text
{evidence}
```
"""


def create_missing_issues(
    repository: str,
    candidates: list[dict[str, Any]],
    *,
    max_create: int,
    issue_scan_limit: int,
) -> list[dict[str, Any]]:
    if len(candidates) > max_create:
        raise RuntimeError(
            f"refusing unexpected issue fan-out: {len(candidates)} candidates exceeds {max_create}"
        )

    existing = marker_index(repository, issue_scan_limit)
    results: list[dict[str, Any]] = []
    for candidate in candidates:
        digest = str(candidate.get("digest") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid candidate digest: {digest!r}")
        if digest in existing:
            issue = existing[digest]
            results.append(
                {
                    **candidate,
                    "status": "existing",
                    "issue_number": issue.get("number"),
                    "issue_url": issue.get("url"),
                    "issue_state": issue.get("state"),
                }
            )
            continue

        organization = str(candidate.get("organization") or urlsplit(str(candidate["url"])).hostname or "unknown organization")
        label = str(candidate.get("label") or urlsplit(str(candidate["url"])).path.rstrip("/").split("/")[-1] or "membership list")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(issue_body(candidate))
            body_path = Path(handle.name)
        try:
            issue_url = run_gh(
                [
                    "issue", "create", "--repo", repository,
                    "--title", f"Scrape membership list: {organization} — {label}"[:240],
                    "--body-file", str(body_path),
                ]
            )
        finally:
            body_path.unlink(missing_ok=True)

        result = {**candidate, "status": "created", "issue_url": issue_url}
        results.append(result)
        existing[digest] = result
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean invalid generated tickets and synchronize one issue per roster-list URL."
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--cleanup-only", action="store_true")
    parser.add_argument("--cleanup-passes", type=int, default=20)
    parser.add_argument("--stable-passes", type=int, default=2)
    parser.add_argument("--batch-limit", type=int, default=1000)
    parser.add_argument("--issue-scan-limit", type=int, default=10000)
    parser.add_argument("--max-create", type=int, default=500)
    parser.add_argument("--sleep-seconds", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.repository:
        raise SystemExit("--repository or GITHUB_REPOSITORY is required")

    closed: list[int] = []
    if args.cleanup or args.cleanup_only:
        closed = drain_invalid_issues(
            args.repository,
            passes=args.cleanup_passes,
            stable_passes=args.stable_passes,
            batch_limit=args.batch_limit,
            sleep_seconds=args.sleep_seconds,
        )

    results: list[dict[str, Any]] = []
    if not args.cleanup_only:
        candidates = load_candidates(args.candidates)
        results = create_missing_issues(
            args.repository,
            candidates,
            max_create=args.max_create,
            issue_scan_limit=args.issue_scan_limit,
        )

    report = {
        "repository": args.repository,
        "closed_invalid_count": len(closed),
        "closed_invalid_issue_numbers": closed,
        "candidate_count": len(results),
        "created_count": sum(item.get("status") == "created" for item in results),
        "existing_count": sum(item.get("status") == "existing" for item in results),
        "results": results,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
