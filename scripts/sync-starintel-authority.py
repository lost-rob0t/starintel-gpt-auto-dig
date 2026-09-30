#!/usr/bin/env python3
"""Synchronize the pinned Star-Lang contract into this consumer repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "schema/starintel-schema.lock.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def verify_source(canonical_root: Path, lock: dict[str, Any]) -> Path:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=canonical_root, text=True
    ).strip()
    if head != lock["canonical_commit"]:
        fail(f"Star-Lang HEAD {head} does not match {lock['canonical_commit']}")

    release_root = canonical_root / "specs/starintel" / lock["release_version"]
    release_lock = load(release_root / "release-lock.json")
    if release_lock["releaseVersion"] != lock["release_version"]:
        fail("Star-Lang release lock does not match the consumer lock")
    if release_lock["canonicalKeyStyle"] != "lowerCamelCase":
        fail("canonical StarIntel keys must be lowerCamelCase")

    for name, expected in release_lock["artifacts"].items():
        if digest(release_root / "generated" / name) != expected:
            fail(f"Star-Lang generated artifact hash mismatch: {name}")
    for name, expected in release_lock["sources"].items():
        if digest(release_root / name) != expected:
            fail(f"Star-Lang source artifact hash mismatch: {name}")
    return release_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    lock = load(LOCK_PATH)
    release_root = verify_source(args.canonical_root.resolve(), lock)
    destination = ROOT / lock["vendored_root"]
    files = {
        release_root / "release-lock.json": destination / "release-lock.json",
        release_root / "schema-lock-manifest.json": destination / "schema-lock-manifest.json",
        release_root / "compatibility.json": destination / "compatibility.json",
        release_root / "compatibility-fixtures.json": destination / "compatibility-fixtures.json",
        release_root / "generated/schema.json": destination / "schema.json",
        release_root / "generated/portable-manifest.json": destination / "portable-manifest.json",
        release_root / "generated/starintel_types.py": destination / "starintel_types.py",
    }

    if args.check:
        missing = [str(target.relative_to(ROOT)) for target in files.values() if not target.exists()]
        drifted = [
            str(target.relative_to(ROOT))
            for source, target in files.items()
            if target.exists() and source.read_bytes() != target.read_bytes()
        ]
        if missing or drifted:
            fail(f"Star-Lang snapshot drift: missing={missing}, drifted={drifted}")
        print(f"Star-Lang {lock['release_version']} snapshot is current")
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    for source, target in files.items():
        shutil.copy2(source, target)
    print(f"synchronized Star-Lang {lock['release_version']} from {lock['canonical_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
