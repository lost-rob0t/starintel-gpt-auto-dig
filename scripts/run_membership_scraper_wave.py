#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
from typing import Any

WAVES: dict[str, dict[str, Any]] = {
    "wave-2": {
        "branch": "agent/dark-academia-rand-bilderberg-wave-2",
        "import_dir": "imports/dark-academia-wave2",
        "transport": "gzip",
        "scraper": "scraper.py.gz",
        "scraper_sha256": "26dc09aa4077bc25f7187e1979002392da8ca183afeb0c7bb528b337560825c2",
        "targets": "targets.json.gz",
        "targets_sha256": "df8d6ecc5105d89b7e9a312e153c33a7388c730a48aef6ea0a2934a5a47057f2",
        "report_suffix": "wave-2",
        "commit_message": "Expand Dark Academia RAND and Bilderberg graph",
    },
    "wave-3": {
        "branch": "agent/dark-academia-institutions-foundations-wave-3",
        "import_dir": "imports/dark-academia-wave3",
        "transport": "chunked-base64-gzip",
        "scraper_glob": "scraper-*",
        "targets_glob": "targets-*",
        "report_suffix": "wave-3",
        "commit_message": "Expand Dark Academia institutions and foundations graph",
    },
}


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    return subprocess.run(command, check=check, text=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def restore_gzip(root: Path, config: dict[str, Any]) -> tuple[bytes, bytes]:
    import_dir = root / config["import_dir"]
    scraper_path = import_dir / config["scraper"]
    targets_path = import_dir / config["targets"]
    if sha256(scraper_path) != config["scraper_sha256"]:
        raise RuntimeError(f"scraper checksum mismatch: {scraper_path}")
    if sha256(targets_path) != config["targets_sha256"]:
        raise RuntimeError(f"target checksum mismatch: {targets_path}")
    with gzip.open(scraper_path, "rb") as handle:
        scraper = handle.read()
    with gzip.open(targets_path, "rb") as handle:
        targets = handle.read()
    return scraper, targets


def decode_chunked_gzip(import_dir: Path, pattern: str) -> bytes:
    parts = sorted(import_dir.glob(pattern))
    if not parts:
        raise FileNotFoundError(f"no transport chunks matched {import_dir / pattern}")
    encoded = "".join(part.read_text(encoding="utf-8") for part in parts)
    compact = "".join(encoded.split())
    compressed = base64.b64decode(compact, validate=True)
    return gzip.decompress(compressed)


def restore_chunked(root: Path, config: dict[str, Any]) -> tuple[bytes, bytes]:
    import_dir = root / config["import_dir"]
    return (
        decode_chunked_gzip(import_dir, config["scraper_glob"]),
        decode_chunked_gzip(import_dir, config["targets_glob"]),
    )


def restore(root: Path, config: dict[str, Any]) -> tuple[Path, Path]:
    if config["transport"] == "gzip":
        scraper_bytes, targets_bytes = restore_gzip(root, config)
    elif config["transport"] == "chunked-base64-gzip":
        scraper_bytes, targets_bytes = restore_chunked(root, config)
    else:
        raise ValueError(f"unsupported transport: {config['transport']}")

    scripts_dir = root / "scripts"
    config_dir = root / "config"
    reports_dir = root / "reports"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    scraper_path = scripts_dir / "scrape_dark_academia_memberships.py"
    targets_path = config_dir / "dark-academia-targets.json"
    scraper_path.write_bytes(scraper_bytes)
    targets_path.write_bytes(targets_bytes)

    source = scraper_path.read_text(encoding="utf-8")
    source = source.replace('"email_type"', '"type"').replace("'email_type'", "'type'")
    if "email_type" in source:
        raise RuntimeError("legacy email_type key remains after normalization")
    scraper_path.write_text(source, encoding="utf-8")

    py_compile.compile(str(scraper_path), doraise=True)
    json.loads(targets_path.read_text(encoding="utf-8"))
    return scraper_path, targets_path


def capture_and_scrape(root: Path, scraper_path: Path, suffix: str) -> BaseException | None:
    observation_path = root / "reports" / f"membership-url-observations-{suffix}.jsonl"
    command = [
        sys.executable,
        str(root / "scripts" / "run_with_membership_url_capture.py"),
        "--log",
        str(observation_path),
        "--",
        str(scraper_path),
        "--root",
        str(root),
    ]
    try:
        run(command)
    except BaseException as exc:  # preserve URL discovery even when extraction fails
        return exc
    return None


def extract_and_sync_issues(root: Path, targets_path: Path, suffix: str) -> None:
    observation_path = root / "reports" / f"membership-url-observations-{suffix}.jsonl"
    candidate_path = root / "reports" / f"membership-list-candidates-{suffix}.json"
    issue_path = root / "reports" / f"membership-list-issues-{suffix}.json"

    run(
        [
            sys.executable,
            str(root / "scripts" / "membership_list_surface_candidates.py"),
            "--input",
            str(targets_path),
            "--input",
            str(observation_path),
            "--glob",
            "reports/dark-academia-membership-recursion*.json",
            "--report",
            str(candidate_path),
        ]
    )
    run(
        [
            sys.executable,
            str(root / "scripts" / "sync_membership_list_issues.py"),
            "--repository",
            os.environ["GITHUB_REPOSITORY"],
            "--cleanup",
            "--candidates",
            str(candidate_path),
            "--report",
            str(issue_path),
        ]
    )


def validate_and_commit(root: Path, config: dict[str, Any], branch: str) -> None:
    import_dir = root / config["import_dir"]
    if import_dir.exists():
        shutil.rmtree(import_dir)
    imports_root = root / "imports"
    if imports_root.exists() and not any(imports_root.iterdir()):
        imports_root.rmdir()

    run([sys.executable, str(root / "scripts" / "starintel.py"), "validate", "--root", str(root)])
    run(["git", "add", "-A"])
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if staged.returncode == 0:
        print("Corpus already current", flush=True)
        return
    if staged.returncode != 1:
        raise RuntimeError(f"git diff --cached failed with {staged.returncode}")

    run(["git", "config", "user.name", "starintel-auto-dig-bot"])
    run(["git", "config", "user.email", "starintel-auto-dig-bot@users.noreply.github.com"])
    run(["git", "commit", "-m", config["commit_message"]])
    run(["git", "push", "origin", f"HEAD:{branch}"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one queued public membership-roster scraper wave.")
    parser.add_argument("--wave", choices=sorted(WAVES), required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    config = WAVES[args.wave]
    if args.branch != config["branch"]:
        raise SystemExit(
            f"queue branch mismatch for {args.wave}: expected {config['branch']}, received {args.branch}"
        )

    run([sys.executable, str(root / "scripts" / "membership_list_surface_candidates.py"), "--self-test"])
    scraper_path, targets_path = restore(root, config)
    scrape_error = capture_and_scrape(root, scraper_path, config["report_suffix"])
    extract_and_sync_issues(root, targets_path, config["report_suffix"])
    if scrape_error is not None:
        raise scrape_error
    validate_and_commit(root, config, args.branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
