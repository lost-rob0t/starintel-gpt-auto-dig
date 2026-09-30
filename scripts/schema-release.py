#!/usr/bin/env python3
"""Read-only StarIntel release resolver for the Auto-Dig consumer.

Star-Lang owns release creation. Auto-Dig pins and verifies a synchronized
snapshot; it cannot bump or mint the StarIntel contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
LOCK = Path("schema/starintel-schema.lock.json")


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def load(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def next_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        fail(f"invalid semantic version in Star-Lang lock: {version!r}")
    major, minor, patch = (int(part) for part in parts)
    return f"{major}.{minor}.{patch + 1}"


def release_state(root: Path) -> dict[str, str]:
    lock = load(root, LOCK)
    release = lock["release_version"]
    return {
        "release_version": release,
        "profile_version": release,
        "schema_version": lock["schema_version"],
        "schema_revision": lock["canonical_commit"],
        "canonical_repository": lock["canonical_repository"],
        "canonical_commit": lock["canonical_commit"],
        "canonical_key_style": lock["canonical_key_style"],
        "next_release_version": next_patch(release),
    }


def check(root: Path) -> dict[str, str]:
    state = release_state(root)
    if state["canonical_repository"] != "nsaspy/star-lang":
        fail("Star-Lang must be the canonical StarIntel repository")
    if state["canonical_key_style"] != "lowerCamelCase":
        fail("canonical StarIntel fields must use lowerCamelCase")
    if state["release_version"] != state["schema_version"]:
        fail("the 0.10 line requires release and schema versions to match")

    lock = load(root, LOCK)
    vendored = root / lock["vendored_root"]
    release_lock = json.loads((vendored / "release-lock.json").read_text(encoding="utf-8"))
    if release_lock["releaseVersion"] != state["release_version"]:
        fail("vendored Star-Lang release lock disagrees with the consumer lock")
    if release_lock["canonicalKeyStyle"] != "lowerCamelCase":
        fail("vendored Star-Lang release permits non-canonical key spelling")
    for name, expected in release_lock["artifacts"].items():
        candidate = vendored / name
        if candidate.exists() and digest(candidate) != expected:
            fail(f"vendored Star-Lang artifact hash mismatch: {name}")
    for name, expected in release_lock["sources"].items():
        candidate = vendored / name
        if candidate.exists() and digest(candidate) != expected:
            fail(f"vendored Star-Lang source hash mismatch: {name}")
    for required in ("schema.json", "portable-manifest.json", "starintel_types.py", "compatibility.json"):
        if not (vendored / required).is_file():
            fail(f"vendored Star-Lang artifact is missing: {required}")
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    current = subparsers.add_parser("current")
    current.add_argument("--json", action="store_true")
    subparsers.add_parser("check")
    subparsers.add_parser("next")
    for command in ("bump", "mint"):
        mutating = subparsers.add_parser(command)
        mutating.add_argument("--to", required=True)
        mutating.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()

    if args.command in {"bump", "mint"}:
        fail(
            f"{args.command} is disabled in Auto-Dig: Star-Lang owns StarIntel "
            "releases; update Star-Lang, then run sync-starintel-authority.py"
        )
    state = check(root)
    if args.command == "current":
        if args.json:
            print(json.dumps(state, sort_keys=True))
        else:
            print(
                f"release={state['release_version']} "
                f"profile={state['profile_version']} "
                f"base_schema={state['schema_version']} "
                f"authority={state['canonical_repository']}@{state['canonical_commit']} "
                f"next={state['next_release_version']}"
            )
    elif args.command == "check":
        print(
            f"StarIntel release {state['release_version']} is pinned to "
            f"{state['canonical_repository']}@{state['canonical_commit']}"
        )
    else:
        print(state["next_release_version"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
