from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .constants import BASE_URL, DEFAULT_SITEMAP_URL, DEFAULT_USER_AGENT, MIN_REQUEST_DELAY
from .network import NetworkClient, discover_profile_urls, fetch_profiles, read_local_profiles
from .records import build_records
from .utils import canonicalize_url, clean, profile_kind, require_network_authorization

ROOT = Path(__file__).resolve().parents[2]


def write_jsonl(output: Path, records: Sequence[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    temp_path.replace(output)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import InfluenceWatch profiles into validated StarIntel JSONL. Network collection requires express written authorization.")
    parser.add_argument("--url", action="append", default=[], help="Authorized InfluenceWatch profile URL; repeatable")
    parser.add_argument("--url-file", type=Path, help="Text file containing one authorized profile URL per line")
    parser.add_argument("--crawl", action="store_true", help="Discover profile URLs through sitemap XML")
    parser.add_argument("--sitemap", action="append", default=[], help="Authorized sitemap URL; repeatable")
    parser.add_argument("--input", action="append", type=Path, default=[], help="Local HTML file with a canonical InfluenceWatch profile URL")
    parser.add_argument("--authorized", action="store_true", help="Acknowledge express written authorization for automated network collection")
    parser.add_argument("--respect-robots", action="store_true", help="Optionally enforce robots.txt despite the authorization")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of network profile URLs; 0 means unlimited")
    parser.add_argument("--delay", type=float, default=MIN_REQUEST_DELAY, help=f"Minimum seconds between requests; must be >= {MIN_REQUEST_DELAY}")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--import-db", action="store_true", help="Import generated JSONL through scripts/starintel.py")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.delay < MIN_REQUEST_DELAY:
        raise SystemExit(f"--delay must be at least {MIN_REQUEST_DELAY} seconds to honor the authorized one-request-per-second limit")
    requested_urls = [canonicalize_url(url) for url in args.url]
    if args.url_file:
        requested_urls.extend(canonicalize_url(line) for line in args.url_file.read_text(encoding="utf-8").splitlines() if clean(line) and not clean(line).startswith("#"))
    network_requested = bool(requested_urls or args.crawl or args.sitemap)
    if network_requested:
        require_network_authorization(authorized=args.authorized)
    profiles = read_local_profiles(args.input)
    if network_requested:
        client = NetworkClient(
            DEFAULT_USER_AGENT,
            args.delay,
            max(1.0, args.timeout),
            respect_robots=args.respect_robots,
        )
        if args.crawl or args.sitemap:
            default_sitemaps = client.sitemap_urls() or [
                urllib.parse.urljoin(BASE_URL, "wp-sitemap.xml"),
                DEFAULT_SITEMAP_URL,
                urllib.parse.urljoin(BASE_URL, "sitemap.xml"),
            ]
            requested_urls.extend(discover_profile_urls(client, args.sitemap or default_sitemaps, limit=max(0, args.limit)))
        requested_urls = list(dict.fromkeys(url for url in requested_urls if profile_kind(url) is not None))
        if args.limit:
            requested_urls = requested_urls[: args.limit]
        profiles.extend(fetch_profiles(client, requested_urls))
    if not profiles:
        raise SystemExit("No profiles supplied. Use --input, --url, --url-file, or --crawl.")
    records = build_records(list({profile.url: profile for profile in profiles}.values()), output=args.output)
    write_jsonl(args.output, records)
    if args.import_db:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "starintel.py"), "import", str(args.output)], check=True)
    counts = Counter(record["dtype"] for record in records)
    print(f"wrote {len(records)} records to {args.output}: {dict(sorted(counts.items()))}")
    return 0
