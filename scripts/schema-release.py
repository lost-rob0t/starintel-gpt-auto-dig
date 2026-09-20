#!/usr/bin/env python3
"""Resolve, validate, bump, and mint the StarIntel release/profile version.

The StarIntel wire/base schema version is deliberately independent from the
release/profile version. In the additive v0.9 line the immutable base schema
remained 0.9.0 while release/profile versions advanced (0.9.1, 0.9.2, ...).

The unified 0.10 line (0.10.1) reunifies the two: minting a new base line
through ``mint`` sets schema_version == release_version == profile_version and
retires the active expansion registry (the vocabulary lives in
``starintel_doc/spec.py`` and the generated schema; see
docs/schema-0.10.1-design.md).

Agents and humans must use this script instead of editing release version
fields by hand.

Line model:

- 0.9 line manifests carry ``expansion_registry_path`` and
  ``expansion_content_hash``; check() validates that registry.
- unified (0.10+) manifests carry no expansion registry; check() instead
  requires the manifest's ``base_schema_path`` to exist on disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("schemas/starintel-doc-v0.10.1.manifest.json")
# Legacy 0.9-line registry. Unified (0.10+) lines have no active expansion
# registry; mint renames this constant when a new base line is created.
LEGACY_EXPANSION = Path("schemas/starintel-doc-v0.9.0.expansion.json")
IMPLEMENTATIONS = Path("conformance/implementations.json")
CONFORMANCE_INIT = Path("conformance/__init__.py")
NIMBLE = Path("starintel_auto_dig.nimble")
OPERATION_TEST = Path("tests/test_operation_registry.py")
FIXTURES = Path("conformance/fixtures.py")
SELF = Path("scripts/schema-release.py")
# Files that pin the *current* generated schema filename as an authority.
SCHEMA_PIN_FILES = (
    Path("scripts/validate-for-merge.py"),
    Path("scripts/starintel_validate.nim"),
    Path(".github/workflows/sync-schema.yml"),
    Path(".github/workflows/conformance.yml"),
)
GENERATOR = Path("scripts/starintel.py")

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
UNIFIED_COMPATIBILITY = "additive-with-migration-v0.10"


def fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if not match:
        fail(f"expected semantic X.Y.Z release version, got {value!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def next_patch(value: str) -> str:
    major, minor, patch = parse_version(value)
    return f"{major}.{minor}.{patch + 1}"


def release_state(root: Path, manifest_rel: Path = MANIFEST) -> dict[str, str]:
    manifest = load_json(root, manifest_rel)
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


def check(root: Path, manifest_rel: Path = MANIFEST) -> dict[str, str]:
    state = release_state(root, manifest_rel)
    release = state["release_version"]
    profile = state["profile_version"]
    if release != profile:
        fail(f"manifest release/profile mismatch: {release} != {profile}")

    manifest = load_json(root, manifest_rel)
    expansion_rel = manifest.get("expansion_registry_path")
    if expansion_rel:
        expansion = load_json(root, Path(expansion_rel))
        if "release_version" in expansion:
            fail("expansion registry must not duplicate release_version; release authority belongs to the manifest")
        if expansion.get("profile_version") != profile:
            fail("expansion profile_version does not match manifest")
        if expansion.get("schema_version") != state["schema_version"]:
            fail("expansion schema_version does not match immutable base schema_version")
        if expansion.get("schema_revision") != state["schema_revision"]:
            fail("expansion schema_revision does not match manifest")
        if manifest.get("expansion_hash_algorithm") != "sha256-canonical-json":
            fail("unsupported expansion hash algorithm")
        if manifest.get("expansion_content_hash") != canonical_hash(expansion):
            fail("manifest expansion_content_hash does not match expansion registry")
    else:
        # Unified line: spec.py + the generated schema are the authority.
        base_schema = manifest.get("base_schema_path")
        if not base_schema:
            fail("unified-line manifest must declare base_schema_path")
        if not (root / base_schema).exists():
            fail(f"unified-line base schema is missing: {base_schema}")

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


def _current_expansion_rel(root: Path, manifest_rel: Path) -> Path | None:
    manifest = load_json(root, manifest_rel)
    expansion_rel = manifest.get("expansion_registry_path")
    return Path(expansion_rel) if expansion_rel else None


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

    expansion_rel = _current_expansion_rel(root, MANIFEST)
    planned = [
        *( [str(expansion_rel)] if expansion_rel else [] ),
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
    if expansion_rel:
        expansion = load_json(root, expansion_rel)
        expansion["profile_version"] = target
        write_json(root / expansion_rel, expansion)
        manifest["expansion_content_hash"] = canonical_hash(expansion)
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


def _load_package_spec(root: Path) -> Any:
    sys.path.insert(0, str(root))
    try:
        from starintel_doc import spec as doc_spec
    except ImportError as exc:  # pragma: no cover - environment guard
        fail(f"cannot import starintel_doc from {root}: {exc}")
    return doc_spec


def mint(root: Path, target: str, *, dry_run: bool) -> list[str]:
    """Create a new unified base line (e.g. 0.10.1) programmatically.

    Unlike bump (next patch of the current line), mint requires the spec
    source to already declare the new line: starintel_doc.spec.SCHEMA_VERSION
    must equal the target, and the generated schema is produced through the
    existing generator so the artifacts can never disagree with the package.
    """

    parse_version(target)
    state = check(root)
    if target == state["schema_version"]:
        fail(f"target {target} equals the current base schema version; use bump for patch releases")
    if parse_version(target) <= parse_version(state["schema_version"]):
        fail(
            f"refusing to mint {target}: it does not strictly advance the current "
            f"base schema version {state['schema_version']}"
        )

    doc_spec = _load_package_spec(root)
    if doc_spec.SCHEMA_VERSION != target:
        fail(
            f"starintel_doc.spec.SCHEMA_VERSION is {doc_spec.SCHEMA_VERSION!r}, not {target!r}; "
            "land the spec source change first; mint only plumbs release artifacts"
        )
    accepted = list(doc_spec.SCHEMA_VERSIONS_ENUM)
    if accepted != [state["schema_version"], target]:
        fail(
            "ACCEPTED_SCHEMA_VERSIONS must be exactly the legacy and target versions "
            f"during a mint; got {accepted}"
        )
    dtype_count = len(doc_spec.TYPE_FIELDS)

    legacy_base = state["schema_version"]
    legacy_release = state["release_version"]
    schema_rel = Path(f"schemas/starintel-doc-v{target}.schema.json")
    manifest_rel = Path(f"schemas/starintel-doc-v{target}.manifest.json")

    planned = [
        str(schema_rel),
        str(manifest_rel),
        str(IMPLEMENTATIONS),
        str(CONFORMANCE_INIT),
        str(NIMBLE),
        str(OPERATION_TEST),
        str(FIXTURES),
        str(SELF),
        *(str(path) for path in SCHEMA_PIN_FILES),
    ]
    if dry_run:
        return planned

    # 1. Regenerate the base schema through the existing generator.
    subprocess.run(
        [sys.executable, str(root / GENERATOR), "schema", "--output", str(root / schema_rel)],
        cwd=root,
        check=True,
    )

    # 2. Verify the generated artifact against the package authority.
    schema = load_json(root, schema_rel)
    if schema.get("properties", {}).get("dtype", {}).get("enum") != sorted(doc_spec.TYPE_FIELDS):
        fail("generated schema dtype enum does not match starintel_doc.TYPE_FIELDS")
    if schema.get("properties", {}).get("schema_version") != {"enum": accepted}:
        fail("generated schema schema_version is not the migration-window enum")
    if schema.get("title") != f"StarIntel Document v{target}":
        fail("generated schema title does not carry the minted version")

    # 3. Write the new manifest.
    write_json(
        root / manifest_rel,
        {
            "base_schema_path": str(schema_rel),
            "compatibility": UNIFIED_COMPATIBILITY,
            "dtype_count": dtype_count,
            "legacy": {
                "base_schema_path": f"schemas/starintel-doc-v{legacy_base}.schema.json",
                "expansion_registry_path": "schemas/starintel-doc-v0.9.0.expansion.json",
                "manifest_path": f"schemas/starintel-doc-v{legacy_base}.manifest.json",
                "network_capture_profile_manifest": "schemas/starintel-network-capture-v0.9.2.manifest.json",
                "release_version": legacy_release,
                "schema_version": legacy_base,
                "note": (
                    "Legacy 0.9-line artifacts remain on disk for consumers pinned to 0.9; "
                    "the 0.9.2 network-capture profile is superseded by this core release."
                ),
            },
            "materialization": (
                "Unified line: starintel_doc/spec.py and the generated schema are the single "
                "vocabulary authority; the 0.9 expansion registry is retired "
                "(docs/schema-0.10.1-design.md)."
            ),
            "migration": {
                "accepted_schema_versions": accepted,
                "emitted_schema_version": target,
                "note": (
                    "Validators accept legacy 0.9.0 envelopes during the migration window; "
                    "emitters write the current version; a future migrator upgrades legacy documents."
                ),
            },
            "profile": "starintel-core",
            "profile_version": target,
            "release_version": target,
            "schema_revision": doc_spec.SCHEMA_REVISION,
            "schema_version": target,
        },
    )

    # 4. Conformance inventory: authority fields only; per-binding release
    #    metadata stays with the binding repositories' own sync workflows.
    implementations = load_json(root, IMPLEMENTATIONS)
    implementations["spec_version"] = target
    implementations["release_version"] = target
    contract = implementations.setdefault("release_contract", {})
    contract["wire_spec_version"] = target
    contract["release_version"] = target
    contract["compatibility"] = UNIFIED_COMPATIBILITY
    implementations["migration"] = {
        "accepted_schema_versions": accepted,
        "note": (
            "Migration window: binding repositories repin through their own lock/sync "
            "workflows before claiming this release; supported_spec_versions and "
            "library_release are intentionally not rewritten by mint."
        ),
    }
    write_json(root / IMPLEMENTATIONS, implementations)

    # 5. Repoint this script's module constants at the minted line.
    replace_exact(
        root / SELF,
        f'MANIFEST = Path("schemas/starintel-doc-v{legacy_base}.manifest.json")',
        f'MANIFEST = Path("schemas/starintel-doc-v{target}.manifest.json")',
    )
    replace_exact(
        root / SELF,
        f'EXPANSION = Path("schemas/starintel-doc-v{legacy_base}.expansion.json")',
        f'LEGACY_EXPANSION = Path("schemas/starintel-doc-v{legacy_base}.expansion.json")',
    )

    # 6. Update the aligned metadata surfaces, mirroring bump().
    replace_exact(root / CONFORMANCE_INIT, f'SPEC_VERSION = "{legacy_base}"', f'SPEC_VERSION = "{target}"')
    replace_exact(root / CONFORMANCE_INIT, f'RELEASE_VERSION = "{legacy_release}"', f'RELEASE_VERSION = "{target}"')
    replace_exact(root / NIMBLE, f'version = "{legacy_release}"', f'version = "{target}"')
    replace_exact(
        root / OPERATION_TEST,
        f'"starintel-doc-v{legacy_base}.manifest.json"',
        f'"starintel-doc-v{target}.manifest.json"',
    )
    replace_exact(root / OPERATION_TEST, f'manifest["release_version"], "{legacy_release}"', f'manifest["release_version"], "{target}"')
    replace_exact(root / OPERATION_TEST, f'manifest["profile_version"], "{legacy_release}"', f'manifest["profile_version"], "{target}"')
    replace_exact(root / FIXTURES, f"the {legacy_release} operation control-plane contract", f"the {target} operation control-plane contract")

    # 7. Repoint current-schema filename pins to the minted schema file.
    legacy_schema_name = f"starintel-doc-v{legacy_base}.schema.json"
    minted_schema_name = f"starintel-doc-v{target}.schema.json"
    for pin in SCHEMA_PIN_FILES:
        replace_exact(root / pin, legacy_schema_name, minted_schema_name)

    minted = check(root, manifest_rel)
    if minted["release_version"] != target or minted["schema_version"] != target:
        fail("post-mint verification did not observe the requested base line")
    return planned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve/check/bump/mint StarIntel release versions without confusing them with the base schema version."
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

    mint_parser = sub.add_parser(
        "mint",
        help="create a new unified base line (schema == release == profile) with full artifacts",
    )
    mint_parser.add_argument("--to", required=True, dest="target")
    mint_parser.add_argument("--dry-run", action="store_true")
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

    if args.command == "mint":
        files = mint(root, args.target, dry_run=args.dry_run)
        verb = "would mint" if args.dry_run else "minted"
        print(f"{verb} StarIntel base line {args.target}:")
        for path in files:
            print(f"  {path}")
        if args.dry_run:
            print("No files changed.")
        return 0

    fail(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
