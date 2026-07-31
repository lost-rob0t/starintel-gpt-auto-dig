#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

import run_membership_scraper_wave as base


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, text=True)


def discover_alumni(root: Path, targets_path: Path, suffix: str) -> Path:
    observations = root / "reports" / f"alumni-url-observations-{suffix}.jsonl"
    report = root / "reports" / f"alumni-coverage-{suffix}.json"
    run(
        [
            sys.executable,
            str(root / "scripts" / "expand_alumni_targets.py"),
            "--config",
            str(targets_path),
            "--observations",
            str(observations),
            "--report",
            str(report),
        ]
    )
    return observations


def extract_and_sync_issues(root: Path, targets_path: Path, suffix: str, alumni_observations: Path) -> None:
    observations = root / "reports" / f"membership-url-observations-{suffix}.jsonl"
    candidates = root / "reports" / f"membership-list-candidates-{suffix}.json"
    issue_report = root / "reports" / f"membership-list-issues-{suffix}.json"
    command = [
        sys.executable,
        str(root / "scripts" / "alumni_membership_list_surface_candidates.py"),
        "--input",
        str(targets_path),
    ]
    if observations.is_file():
        command.extend(["--input", str(observations)])
    if alumni_observations.is_file():
        command.extend(["--input", str(alumni_observations)])
    command.extend(
        [
            "--glob",
            "reports/dark-academia-membership-recursion*.json",
            "--report",
            str(candidates),
        ]
    )
    run(command)
    run(
        [
            sys.executable,
            str(root / "scripts" / "sync_alumni_membership_list_issues.py"),
            "--repository",
            os.environ["GITHUB_REPOSITORY"],
            "--cleanup",
            "--candidates",
            str(candidates),
            "--report",
            str(issue_report),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one complete current-and-alumni public roster scraper wave.")
    parser.add_argument("--wave", choices=sorted(base.WAVES), required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    config = base.WAVES[args.wave]
    if args.branch != config["branch"]:
        raise SystemExit(
            f"queue branch mismatch for {args.wave}: expected {config['branch']}, received {args.branch}"
        )

    run([sys.executable, str(root / "scripts" / "alumni_membership_list_surface_candidates.py"), "--self-test"])
    scraper_path, targets_path = base.restore(root, config)
    run([sys.executable, str(root / "scripts" / "patch_alumni_scraper.py"), str(scraper_path)])
    alumni_observations = discover_alumni(root, targets_path, config["report_suffix"])
    scrape_error = base.capture_and_scrape(root, scraper_path, config["report_suffix"])
    extract_and_sync_issues(root, targets_path, config["report_suffix"], alumni_observations)
    if scrape_error is not None:
        raise scrape_error
    base.validate_and_commit(root, config, args.branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
