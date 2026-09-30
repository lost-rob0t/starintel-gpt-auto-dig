#!/usr/bin/env python3
"""Verify Auto-Dig's Star-Lang consumer lock and vendored snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--python-binding-root", type=Path)
    parser.add_argument("--binding-root", type=Path, action="append", default=[])
    args = parser.parse_args()

    lock = load(ROOT / "schema/starintel-schema.lock.json")
    if lock.get("canonical_repository") != "nsaspy/star-lang":
        fail("Star-Lang must be the canonical StarIntel repository")
    if lock.get("release_version") != "0.10.1" or lock.get("schema_version") != "0.10.1":
        fail("Auto-Dig requires StarIntel 0.10.1")
    if lock.get("canonical_key_style") != "lowerCamelCase":
        fail("canonical StarIntel keys must be lowerCamelCase")

    vendored = ROOT / lock["vendored_root"]
    release_lock = load(vendored / "release-lock.json")
    if release_lock["releaseVersion"] != lock["release_version"]:
        fail("vendored release lock disagrees with consumer lock")
    if release_lock["canonicalKeyStyle"] != "lowerCamelCase":
        fail("vendored release lock permits a non-canonical key style")
    artifact_map = {
        "schema.json": vendored / "schema.json",
        "portable-manifest.json": vendored / "portable-manifest.json",
        "starintel_types.py": vendored / "starintel_types.py",
    }
    for name, path in artifact_map.items():
        if digest(path) != release_lock["artifacts"][name]:
            fail(f"vendored Star-Lang artifact hash mismatch: {name}")
    for name in ("compatibility.json", "compatibility-fixtures.json", "schema-lock-manifest.json"):
        if digest(vendored / name) != release_lock["sources"][name]:
            fail(f"vendored Star-Lang source hash mismatch: {name}")

    schema = load(vendored / "schema.json")
    definitions = schema.get("$defs", {})
    required = {name.replace("-", "").lower() for name in lock["required_dtypes"]}
    available = {name.replace("_", "").replace("-", "").lower() for name in definitions}
    if not required <= available:
        fail(f"vendored schema is missing required types: {sorted(required - available)}")

    if args.canonical_root:
        canonical_root = args.canonical_root.resolve()
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=canonical_root, text=True
        ).strip()
        if head != lock["canonical_commit"]:
            fail("canonical Star-Lang checkout does not match the lock")
        canonical_release = canonical_root / "specs/starintel" / lock["release_version"]
        for source, target in (
            (canonical_release / "release-lock.json", vendored / "release-lock.json"),
            (canonical_release / "generated/schema.json", vendored / "schema.json"),
            (canonical_release / "compatibility.json", vendored / "compatibility.json"),
        ):
            if source.read_bytes() != target.read_bytes():
                fail(f"vendored artifact differs from Star-Lang: {target.name}")

    binding_roots = list(args.binding_root)
    if args.python_binding_root:
        binding_roots.append(args.python_binding_root)
    for binding_root in binding_roots:
        binding_lock = load(binding_root.resolve() / "schema/starintel-schema.lock.json")
        for field in ("release_version", "schema_version", "canonical_repository", "canonical_commit"):
            if binding_lock.get(field) != lock[field]:
                fail(f"binding lock at {binding_root} disagrees on {field}")

    print(
        f"verified Auto-Dig consumer at StarIntel {lock['release_version']} "
        f"from {lock['canonical_repository']}@{lock['canonical_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
