#!/usr/bin/env python3
"""Collect the US government-branches corpus through the pro-actors web crawler.

Replays the evidence-first enumeration as one repeatable transaction:

1. fail closed unless the Auto-Dig control plane is enabled and running;
2. run the ``us-gov-branches`` site adapter seeds through ``starintel-web``
   into a dated canonical packet under ``digs/fed/``;
3. optionally import every emitted document through the canonical batch
   importer (``scripts/starintel.py import``).

Examples:

    python3 scripts/collect-gov-branches.py
    python3 scripts/collect-gov-branches.py --import
    STARINTEL_WEB_BIN=/path/to/starintel-web python3 scripts/collect-gov-branches.py --import
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_FILE = REPO_ROOT / "config" / "auto-dig-control.json"
PACKET_ROOT = REPO_ROOT / "digs" / "fed"
SITE = "us-gov-branches"
SEEDS = (
    "https://en.wikipedia.org/wiki/List_of_United_States_state_legislatures",
    "https://www.visitthecapitol.gov/explore/about-congress",
    "https://ballotpedia.org/Official_names_of_state_legislatures",
)


def fail_closed_on_control_plane() -> None:
    try:
        control = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read Auto-Dig control file {CONTROL_FILE}: {exc}")
    if not control.get("enabled") or control.get("state") != "running":
        raise SystemExit(
            "Auto-Dig control plane is not enabled/running "
            f"(enabled={control.get('enabled')!r}, state={control.get('state')!r}); refusing to collect"
        )


def find_starintel_web(override: str | None) -> str:
    candidate = override or os.environ.get("STARINTEL_WEB_BIN") or "starintel-web"
    if "/" not in candidate:
        resolved = shutil.which(candidate)
        if not resolved:
            raise SystemExit(
                f"{candidate} not found on PATH; install starintel-pro-actors "
                "or pass --starintel-web-bin / set STARINTEL_WEB_BIN"
            )
        return resolved
    if not Path(candidate).exists():
        raise SystemExit(f"starintel-web binary not found: {candidate}")
    return candidate


def run_crawl(binary: str, output: Path, max_pages: int) -> dict:
    command = [
        binary,
        "scrape",
        *SEEDS,
        "--site",
        SITE,
        "--max-depth",
        "0",
        "--max-pages",
        str(max_pages),
        "--output",
        str(output),
    ]
    print("+", " ".join(command), file=sys.stderr)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        sys.stderr.write(completed.stdout)
        raise SystemExit(f"starintel-web scrape failed with exit {completed.returncode}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"cannot parse starintel-web report: {exc}") from exc


def import_packet(output: Path) -> None:
    command = [sys.executable, str(REPO_ROOT / "scripts" / "starintel.py"), "import", str(output)]
    print("+", " ".join(command), file=sys.stderr)
    completed = subprocess.run(command, check=False, capture_output=True, text=True, cwd=REPO_ROOT)
    sys.stderr.write(completed.stderr)
    sys.stderr.write(completed.stdout)
    if completed.returncode != 0:
        raise SystemExit(f"canonical import failed with exit {completed.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Packet directory (default: digs/fed/<today>-us-gov-branches-web-crawl)",
    )
    parser.add_argument(
        "--import",
        dest="do_import",
        action="store_true",
        help="Import the emitted JSONL through scripts/starintel.py import",
    )
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--starintel-web-bin", default=None)
    args = parser.parse_args()

    fail_closed_on_control_plane()
    packet_dir = args.output_dir or PACKET_ROOT / f"{date.today().isoformat()}-us-gov-branches-web-crawl"
    packet_dir.mkdir(parents=True, exist_ok=True)
    output = packet_dir / "starintel-documents.jsonl"

    binary = find_starintel_web(args.starintel_web_bin)
    report = run_crawl(binary, output, args.max_pages)
    documents = report.get("documents", 0)
    counts = report.get("counts_by_dtype", {})
    warnings = report.get("warnings", [])
    print(f"packet: {output}")
    print(f"documents: {documents} {counts}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if documents == 0:
        raise SystemExit("crawl emitted no documents; refusing to continue")

    if args.do_import:
        import_packet(output)
        print(
            "imported; before merging run: nimble buildFast && "
            "bin/validate-for-merge --site"
        )


if __name__ == "__main__":
    main()
