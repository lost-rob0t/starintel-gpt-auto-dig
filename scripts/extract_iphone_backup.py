#!/usr/bin/env python3

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decrypt an encrypted local iPhone backup while preserving domain and folder structure."
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        required=True,
        help="Encrypted iPhone backup directory containing Manifest.db and Manifest.plist.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for the decrypted manifest and extracted files.",
    )

    password = parser.add_mutually_exclusive_group()
    password.add_argument(
        "-p",
        "--password",
        help="Backup passphrase. This may be visible in shell history and process listings.",
    )
    password.add_argument(
        "--password-env",
        metavar="NAME",
        help="Read the backup passphrase from environment variable NAME.",
    )

    parser.add_argument(
        "--relative-path-like",
        default="%",
        help="Manifest relativePath SQL LIKE pattern. Default: %% (all files).",
    )
    parser.add_argument(
        "--domain-like",
        default="%",
        help="Manifest domain SQL LIKE pattern. Default: %% (all domains).",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Decrypt Manifest.db but do not extract the indexed files.",
    )
    parser.add_argument(
        "--skip-call-history",
        action="store_true",
        help="Do not create the friendly call_history.sqlite copy.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip existing extracted files whose backup modification time is not newer.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Extraction report path. Default: OUTPUT/extraction-report.json.",
    )
    return parser.parse_args(argv)


def resolve_passphrase(args: argparse.Namespace) -> str:
    if args.password is not None:
        return args.password

    if args.password_env is not None:
        value = os.environ.get(args.password_env)
        if value is None:
            raise ValueError(f"environment variable {args.password_env!r} is not set")
        return value

    return getpass.getpass("iPhone backup passphrase: ")


def validate_backup_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"backup directory does not exist: {resolved}")

    missing = [name for name in ("Manifest.db", "Manifest.plist") if not (resolved / name).is_file()]
    if missing:
        raise ValueError(f"backup directory is missing: {', '.join(missing)}")
    return resolved


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, object]:
    try:
        from iphone_backup_decrypt import EncryptedBackup, RelativePath
    except ImportError as exc:
        raise RuntimeError(
            "iphone_backup_decrypt is not installed; run: pip install iphone_backup_decrypt"
        ) from exc

    backup_directory = validate_backup_directory(args.directory)
    output_directory = args.output.expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = (args.report or (output_directory / "extraction-report.json")).expanduser().resolve()

    passphrase = resolve_passphrase(args)
    started_at = utc_now()
    backup = EncryptedBackup(backup_directory=str(backup_directory), passphrase=passphrase)

    report: dict[str, object] = {
        "started_at": started_at,
        "backup_directory": str(backup_directory),
        "output_directory": str(output_directory),
        "report_path": str(report_path),
        "relative_path_like": args.relative_path_like,
        "domain_like": args.domain_like,
        "incremental": bool(args.incremental),
        "manifest_only": bool(args.manifest_only),
        "call_history": "skipped" if args.skip_call_history else "pending",
        "extracted_files": 0,
    }

    backup.test_decryption()

    manifest_path = output_directory / "Manifest.db"
    backup.save_manifest_file(str(manifest_path))
    report["manifest_path"] = str(manifest_path)
    report["manifest_sha256"] = sha256_file(manifest_path)

    if not args.skip_call_history:
        call_history_path = output_directory / "call_history.sqlite"
        try:
            backup.extract_file(
                relative_path=RelativePath.CALL_HISTORY,
                output_filename=str(call_history_path),
            )
        except FileNotFoundError:
            report["call_history"] = "not-found"
        else:
            report["call_history"] = str(call_history_path)
            report["call_history_sha256"] = sha256_file(call_history_path)

    if not args.manifest_only:
        files_directory = output_directory / "files"
        extracted = backup.extract_files(
            relative_paths_like=args.relative_path_like,
            domain_like=args.domain_like,
            output_folder=str(files_directory),
            preserve_folders=True,
            domain_subfolders=True,
            incremental=args.incremental,
        )
        report["files_directory"] = str(files_directory)
        report["extracted_files"] = extracted

    report["completed_at"] = utc_now()
    write_report(report_path, report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Decrypted manifest: {report['manifest_path']}")
    if report["call_history"] == "not-found":
        print("Call history database was not present in the backup.")
    elif report["call_history"] != "skipped":
        print(f"Call history: {report['call_history']}")
    print(f"Extracted files: {report['extracted_files']}")
    print(f"Report: {report['report_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
