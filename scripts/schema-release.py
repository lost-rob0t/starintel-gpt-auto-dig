#!/usr/bin/env python3
"""Resolve, validate, and bump the StarIntel release/profile version.

The StarIntel wire/base schema version is deliberately independent from the
release/profile version.  In the current additive v0.9 line the immutable base
schema remains 0.9.0 while release/profile versions advance (0.9.1, 0.9.2, ...).

Agents and humans must use this script instead of editing release version fields
by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("schemas/starintel-doc-v0.9.0.manifest.json")
IMPLEMENTATIONS = Path("conformance/implementations.json")
CONFORMANCE_INIT = Path("conformance/__init__.py")
NIMBLE = Path("starintel_auto_dig.nimble")
OPERATION_TEST = Path("tests/test_operation_registry.py")
FIXTURES = Path("conformance/fixtures.py")

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if not match:
        fail(f"expected semantic X.Y.Z release version, got {value!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def next_patch(value: str) -> str:
    major, minor, patch = parse_version(value)
    return f"{major}.{minor}.{patch + 1}"


def release_state(root: Path) -> dict[str, str]:
    manifest = load_json(root, MANIFEST)
    release = manifest.get("release_version")
    profile = manifest.get("profile_version")
    schema = manifest.get("schema_version")
    revision = manifest.get("schema_revision")
    if not all(isinstance(value, str) and value for value in (release, profile, schema, revision)):
        fail("schema manifest is missing release/profile/schema/revision metadata")
    return {
        "release_version": release,
        "profile_version": profile,
        "schema_version": schema,
        "schema_revision": revision,
        "next_release_version": next_patch(release),
    }


def require_text(root: Path, relative: Path, needle: str, label: str) -> str:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"{label} is not aligned with expected value {needle!r}: {relative}")
    return text


def check(root: Path) -> dict[str, str]:
    state = release_state(root)
    release = state["release_version"]
    profile = state["profile_version"]
    if release != profile:
        fail(f"manifest release/profile mismatch: {release} != {profile}")

    implementations = load_json(root, IMPLEMENTATIONS)
    if implementations.get("release_version") != release:
        fail("conformance inventory release_version does not match manifest")
    if implementations.get("release_contract", {}).get("release_version") != release:
        fail("conformance release_contract.release_version does not match manifest")
    if implementations.get("spec_version") != state["schema_version"]:
        fail("conformance spec_version does not match immutable base schema_version")
    if implementations.get("release_contract", {}).get("wire_spec_version") != state["schema_version"]:
        fail("conformance wire_spec_version does not match immutable base schema_version")

    require_text(root, CONFORMANCE_INIT, f'RELEASE_VERSION = "{release}"', "conformance RELEASE_VERSION")
    require_text(root, NIMBLE, f'version = "{release}"', "Auto-Dig package version")
    require_text(root, OPERATION_TEST, f'manifest["release_version"], "{release}"', "operation registry release assertion")
    require_text(root, OPERATION_TEST, f'manifest["profile_version"], "{profile}"', "operation registry profile assertion")

    return state


def replace_exact(path: Path, old: str, new: str, *, expected_at_least: int = 1) -> bool:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < expected_at_least:
        fail(f"expected {old!r} in {path}, found {count} occurrences")
    updated = text.replace(old, new)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def bump(root: Path, target: str, *, dry_run: bool) -> list[str]:
    state = check(root)
    current = state["release_version"]
    expected = state["next_release_version"]
    parse_version(target)
    if target != expected:
        fail(
            f"refusing non-next patch bump {current} -> {target}; "
            f"the next additive release is {expected}"
        )

    planned = [
        str(MANIFEST),
        str(IMPLEMENTATIONS),
        str(CONFORMANCE_INIT),
        str(NIMBLE),
        str(OPERATION_TEST),
        str(FIXTURES),
    ]
    if dry_run:
        return planned

    manifest = load_json(root, MANIFEST)
    manifest["release_version"] = target
    manifest["profile_version"] = target
    write_json(root / MANIFEST, manifest)

    implementations = load_json(root, IMPLEMENTATIONS)
    implementations["release_version"] = target
    implementations.setdefault("release_contract", {})["release_version"] = target
    # Per-language library_release values describe actually released bindings.
    # They are intentionally NOT rewritten here; binding repositories bump them
    # through their own release/sync workflows.
    write_json(root / IMPLEMENTATIONS, implementations)

    replace_exact(root / CONFORMANCE_INIT, f'RELEASE_VERSION = "{current}"', f'RELEASE_VERSION = "{target}"')
    replace_exact(root / NIMBLE, f'version = "{current}"', f'version = "{target}"')
    replace_exact(root / OPERATION_TEST, f'manifest["release_version"], "{current}"', f'manifest["release_version"], "{target}"')
    replace_exact(root / OPERATION_TEST, f'manifest["profile_version"], "{current}"', f'manifest["profile_version"], "{target}"')
    replace_exact(root / FIXTURES, f"the {current} operation control-plane contract", f"the {target} operation control-plane contract")

    bumped = check(root)
    if bumped["release_version"] != target:
        fail("post-bump verification did not observe the requested release")
    return planned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve/check/bump StarIntel release version without confusing it with the immutable base schema version."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="canonical starintel-gpt-auto-dig checkout")
    sub = parser.add_subparsers(dest="command", required=True)

    current = sub.add_parser("current", help="print current release/profile/base-schema state")
    current.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    sub.add_parser("check", help="fail unless all canonical release metadata agrees")
    sub.add_parser("next", help="print the required next additive patch release")

    bump_parser = sub.add_parser("bump", help="bump the canonical release/profile metadata")
    bump_parser.add_argument("--to", required=True, dest="target")
    bump_parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()

    if args.command == "current":
        state = check(root)
        if args.json:
            print(json.dumps(state, sort_keys=True))
        else:
            print(
                f"release={state['release_version']} "
                f"profile={state['profile_version']} "
                f"base_schema={state['schema_version']} "
                f"schema_revision={state['schema_revision']} "
                f"next={state['next_release_version']}"
            )
        return 0

    if args.command == "check":
        state = check(root)
        print(f"StarIntel release {state['release_version']} metadata is consistent")
        return 0

    if args.command == "next":
        print(check(root)["next_release_version"])
        return 0

    if args.command == "bump":
        files = bump(root, args.target, dry_run=args.dry_run)
        verb = "would update" if args.dry_run else "updated"
        print(f"{verb} StarIntel release to {args.target}:")
        for path in files:
            print(f"  {path}")
        if args.dry_run:
            print("No files changed.")
        return 0

    fail(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
