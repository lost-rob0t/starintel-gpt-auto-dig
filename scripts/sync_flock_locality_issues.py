#!/usr/bin/env python3
"""Synchronize statewide Flock locality trackers into GitHub Issues.

The default strategy creates one state index issue and one county/borough issue
whose task list contains every official locality. Individual locality issues can
be materialized later for active investigations without creating 1,600+ issues
up front.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

NY_LOCALITY_SOURCE = (
    "https://data.ny.gov/api/v3/views/55k6-h6qq/query.json?accessType=DOWNLOAD"
)
STATE_MARKER = "starintel-locality-state"
COUNTY_MARKER = "starintel-locality-county"
LOCALITY_MARKER = "starintel-locality-id"


@dataclass(frozen=True)
class Locality:
    swis_code: str
    type_code: str
    locality_type: str
    county: str
    municipality: str
    county_code: str
    county_fips: str
    gnis_id: str
    website: str
    second_county: str

    @property
    def key(self) -> str:
        return f"ny:{self.swis_code}"

    @property
    def county_key(self) -> str:
        return f"ny:{self.county_code or slug(self.county)}"


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "starintel-locality-sync/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def locality_from_row(row: dict[str, Any]) -> Locality:
    website = row.get("website", "")
    if isinstance(website, dict):
        website = website.get("url", "")
    return Locality(
        swis_code=str(row.get("swis_code", "")).strip(),
        type_code=str(row.get("type_code", "")).strip(),
        locality_type=str(row.get("type", "Unknown")).strip(),
        county=str(row.get("county", "Unknown")).strip(),
        municipality=str(
            row.get("municipality")
            or row.get("city_name")
            or row.get("town_name")
            or row.get("village_name")
            or row.get("county")
            or "Unknown"
        ).strip(),
        county_code=str(row.get("county_code", "")).strip(),
        county_fips=str(row.get("county_fips", "")).strip(),
        gnis_id=str(row.get("gnis_id", "")).strip(),
        website=str(website or "").strip(),
        second_county=str(row.get("_2nd_county", "")).strip(),
    )


def load_localities(url: str) -> list[Locality]:
    rows = fetch_json(url)
    if not isinstance(rows, list):
        raise ValueError("locality source did not return a JSON array")
    localities = [locality_from_row(row) for row in rows if isinstance(row, dict)]
    localities = [item for item in localities if item.swis_code and item.municipality]
    return sorted(localities, key=lambda item: (item.county, item.locality_type, item.municipality, item.swis_code))


class GitHubClient:
    def __init__(self, repo: str, token: str, *, apply: bool, delay: float) -> None:
        self.repo = repo
        self.token = token
        self.apply = apply
        self.delay = delay
        self.api = "https://api.github.com"

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        if not self.token:
            raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required for GitHub writes")
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "starintel-locality-sync/1.0",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if self.delay:
                    time.sleep(self.delay)
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            raise RuntimeError(f"GitHub {method} {path} failed: {error.code} {body}") from error

    def list_issues(self) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.request(
                "GET", f"/repos/{self.repo}/issues?state=all&per_page=100&page={page}"
            )
            if not batch:
                break
            issues.extend(item for item in batch if "pull_request" not in item)
            if len(batch) < 100:
                break
            page += 1
        return issues

    def ensure_label(self, name: str, color: str, description: str) -> None:
        if not self.apply:
            return
        try:
            self.request(
                "POST",
                f"/repos/{self.repo}/labels",
                {"name": name, "color": color, "description": description},
            )
        except RuntimeError as error:
            if "422" not in str(error):
                raise

    def create_issue(self, title: str, body: str, labels: list[str]) -> dict[str, Any]:
        if not self.apply:
            print(f"CREATE {title}")
            return {"number": 0, "html_url": ""}
        return self.request(
            "POST", f"/repos/{self.repo}/issues", {"title": title, "body": body, "labels": labels}
        )

    def update_issue(self, number: int, title: str, body: str, labels: list[str]) -> dict[str, Any]:
        if not self.apply:
            print(f"UPDATE #{number} {title}")
            return {"number": number, "html_url": ""}
        return self.request(
            "PATCH",
            f"/repos/{self.repo}/issues/{number}",
            {"title": title, "body": body, "labels": labels},
        )


def marker(kind: str, value: str) -> str:
    return f"<!-- {kind}: {value} -->"


def marker_value(body: str, kind: str) -> str | None:
    match = re.search(rf"<!--\s*{re.escape(kind)}:\s*([^>]+?)\s*-->", body or "")
    return match.group(1).strip() if match else None


def checked_localities(body: str) -> set[str]:
    checked: set[str] = set()
    for line in (body or "").splitlines():
        if not re.match(r"\s*- \[[xX]\]", line):
            continue
        value = marker_value(line, LOCALITY_MARKER)
        if value:
            checked.add(value)
    return checked


def locality_task(item: Locality, checked: bool) -> str:
    box = "x" if checked else " "
    second = f"; also {item.second_county} County" if item.second_county else ""
    site = f" — {item.website}" if item.website else ""
    return (
        f"- [{box}] **{item.locality_type}: {item.municipality}** "
        f"(`SWIS {item.swis_code}`{second}){site} {marker(LOCALITY_MARKER, item.key)}"
    )


def county_body(
    county: str,
    county_code: str,
    county_fips: str,
    localities: list[Locality],
    checked: set[str],
    source_url: str,
) -> str:
    counts = Counter(item.locality_type for item in localities)
    count_text = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    tasks = "\n".join(locality_task(item, item.key in checked) for item in localities)
    return f"""{marker(COUNTY_MARKER, f'ny:{county_code or slug(county)}')}
# Flock locality tracker — {county} County, New York

This issue is the authoritative locality checklist for the county. A checked locality means its first bounded Flock/ALPR pass has produced evidence-backed StarIntel records or a documented no-deployment result.

## Inventory

- Official source: {source_url}
- County code: `{county_code or 'unknown'}`
- County FIPS: `{county_fips or 'unknown'}`
- Locality rows: **{len(localities)}**
- Breakdown: {count_text}

## Completion standard for every locality

- [ ] Determine status: `active`, `former`, `proposed`, `rejected`, `non-Flock ALPR`, or `no evidence found`
- [ ] Identify government, law-enforcement, campus, airport, hospital, retail, HOA, and other private network operators
- [ ] Recover contracts, quotes, procurement approvals, grants, renewals, and cancellation records
- [ ] Recover camera inventory, locations, model/version, installation and removal dates
- [ ] Recover inbound and outbound sharing edges as separate time-bounded permissions
- [ ] Recover Organization Audit, Network Audit, search IDs, purpose codes, case numbers, users, roles, and administrator events
- [ ] Recover retention, deletion, hotlist, alert, vendor-support, and misuse policies
- [ ] File or link FOIL requests and preserve productions with hashes and provenance
- [ ] Publish facts, claims, relations, conflicts, and unresolved leads as StarIntel v0.9 records

## Localities

{tasks}

## County-level leads

- [ ] County sheriff and county-wide task forces
- [ ] District attorney, probation, emergency management, transit, airport, SUNY/CUNY, and regional intelligence centers
- [ ] Private camera networks and law-enforcement integrations crossing municipal boundaries
- [ ] State, federal, and out-of-state access to locally generated data
"""


def locality_body(item: Locality, source_url: str, parent_issue: int | None) -> str:
    parent = f"- County tracker: #{parent_issue}\n" if parent_issue else ""
    return f"""{marker(LOCALITY_MARKER, item.key)}
# Flock locality pass — {item.municipality}, New York

{parent}- Official inventory source: {source_url}
- Locality type: `{item.locality_type}`
- County: `{item.county}`
- SWIS code: `{item.swis_code}`
- County FIPS: `{item.county_fips or 'unknown'}`
- GNIS ID: `{item.gnis_id or 'unknown'}`
- Official website: {item.website or 'not listed'}

## Research queue

- [ ] Deployment status and full vendor/product inventory
- [ ] Public and private camera owners/operators
- [ ] Contracts, funding, renewals, cancellations, litigation, and lobbying
- [ ] Camera count, locations, installation history, and technical configuration
- [ ] Directed sharing graph and historical permission changes
- [ ] Search/audit exports, purpose codes, case numbers, users, roles, administrators, and support events
- [ ] Retention, deletion, hotlist, alert, immigration, and misuse controls
- [ ] FOIL requests, responses, native files, hashes, and evidence lineage
- [ ] StarIntel records and recursive follow-up targets

## Evidence

Add source links, exact dates, quoted passages, hashes, and record identifiers. Separate confirmed facts, source claims, analytical inferences, and unresolved conflicts.
"""


def state_body(
    localities: list[Locality],
    county_issues: dict[str, dict[str, Any]],
    source_url: str,
) -> str:
    counts = Counter(item.locality_type for item in localities)
    counties = defaultdict(list)
    for item in localities:
        counties[item.county].append(item)
    lines: list[str] = []
    for county in sorted(counties):
        issue = county_issues.get(county)
        link = f"#{issue['number']}" if issue and issue.get("number") else "not materialized"
        lines.append(f"- [ ] **{county} County** — {len(counties[county])} rows — {link}")
    count_text = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
    return f"""{marker(STATE_MARKER, 'ny')}
# Flock locality tracker — New York State

This issue indexes the statewide locality program. The source currently returns **{len(localities)} official locality rows** across **{len(counties)} county/borough groups**.

## Source and identity

- Authoritative locality inventory: {source_url}
- Stable locality key: `ny:<SWIS code>`
- Breakdown: {count_text}
- County trackers preserve every locality as a task item.
- Individual locality issues are created only when work begins or evidence is found, avoiding an unmanageable 1,600-issue dump while retaining complete coverage.

## Required issue hierarchy

1. State index — this issue
2. County/borough tracker — one generated issue per county group
3. Locality investigation — materialized from a county task when active
4. Recursive target issues — agencies, private operators, contracts, sharing edges, users, audits, and named personnel

## Statewide workstreams

- [ ] Crosswalk all locality rows against the NYS DCJS criminal-justice-agency directory and personnel datasets
- [ ] Detect Flock, Axon, Genetec, Motorola/Avigilon, Rekor, Vigilant, and other ALPR deployments without conflating vendors
- [ ] Build directed sharing graphs with effective dates and revocation history
- [ ] Track private networks separately from government-owned networks
- [ ] Track FOIL requests and productions by stable locality key
- [ ] Track issue status back into StarIntel `investigation-target` and `research-pass` records

## County/borough trackers

{chr(10).join(lines)}
"""


def upsert_by_marker(
    client: GitHubClient,
    existing: dict[str, dict[str, Any]],
    marker_key: str,
    marker_id: str,
    title: str,
    body: str,
    labels: list[str],
) -> dict[str, Any]:
    issue = existing.get(marker_id)
    if issue:
        return client.update_issue(issue["number"], title, body, labels)
    created = client.create_issue(title, body, labels)
    existing[marker_id] = created
    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""))
    parser.add_argument("--source-url", default=NY_LOCALITY_SOURCE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--granularity", choices=("county", "locality"), default="county")
    parser.add_argument("--county", action="append", default=[])
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0, help="0 means all selected rows")
    parser.add_argument("--delay", type=float, default=0.15)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    localities = load_localities(args.source_url)
    if args.county:
        wanted = {value.casefold() for value in args.county}
        localities = [item for item in localities if item.county.casefold() in wanted]
    if args.offset:
        localities = localities[args.offset :]
    if args.limit:
        localities = localities[: args.limit]

    print(json.dumps({
        "locality_rows": len(localities),
        "county_groups": len({item.county for item in localities}),
        "types": Counter(item.locality_type for item in localities),
        "apply": args.apply,
        "granularity": args.granularity,
    }, default=dict, indent=2))

    if not args.repo:
        if args.apply:
            raise SystemExit("--repo or GITHUB_REPOSITORY is required with --apply")
        return 0

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    client = GitHubClient(args.repo, token, apply=args.apply, delay=args.delay)
    issues = client.list_issues() if token else []
    state_existing: dict[str, dict[str, Any]] = {}
    county_existing: dict[str, dict[str, Any]] = {}
    locality_existing: dict[str, dict[str, Any]] = {}
    for issue in issues:
        body = issue.get("body") or ""
        value = marker_value(body, STATE_MARKER)
        if value:
            state_existing[value] = issue
        value = marker_value(body, COUNTY_MARKER)
        if value:
            county_existing[value] = issue
        value = marker_value(body, LOCALITY_MARKER)
        if value:
            locality_existing[value] = issue

    labels = {
        "flock-locality": ("f4c430", "Flock/ALPR locality tracking"),
        "state:new-york": ("1d76db", "New York locality scope"),
        "locality-tracker": ("7e57c2", "Generated state or county tracker"),
        "investigation-target": ("d93f0b", "Recursive StarIntel investigation target"),
    }
    for name, (color, description) in labels.items():
        client.ensure_label(name, color, description)

    groups: dict[str, list[Locality]] = defaultdict(list)
    for item in localities:
        groups[item.county].append(item)

    county_results: dict[str, dict[str, Any]] = {}
    for county, items in sorted(groups.items()):
        key = items[0].county_key
        previous = county_existing.get(key, {})
        checked = checked_localities(previous.get("body", ""))
        body = county_body(
            county,
            items[0].county_code,
            items[0].county_fips,
            items,
            checked,
            args.source_url,
        )
        result = upsert_by_marker(
            client,
            county_existing,
            COUNTY_MARKER,
            key,
            f"[Flock locality][NY][County] {county}",
            body,
            ["flock-locality", "state:new-york", "locality-tracker"],
        )
        county_results[county] = result

        if args.granularity == "locality":
            parent_number = result.get("number") or None
            for item in items:
                upsert_by_marker(
                    client,
                    locality_existing,
                    LOCALITY_MARKER,
                    item.key,
                    f"[Flock locality][NY][{item.locality_type}] {item.municipality} — {item.county}",
                    locality_body(item, args.source_url, parent_number),
                    ["flock-locality", "state:new-york", "investigation-target"],
                )

    state_body_text = state_body(localities, county_results, args.source_url)
    upsert_by_marker(
        client,
        state_existing,
        STATE_MARKER,
        "ny",
        "[Flock locality][NY][State index] New York statewide tracker",
        state_body_text,
        ["flock-locality", "state:new-york", "locality-tracker"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
