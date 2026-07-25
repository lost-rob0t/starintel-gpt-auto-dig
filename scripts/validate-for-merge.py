#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc import SCHEMA_PROFILE, SCHEMA_PROFILE_VERSION, SCHEMA_REVISION, SCHEMA_VERSION
from starintel_doc.spec import SCHEMA_ID, TYPE_FIELDS, document_schema
from starintel_doc.store import validate_repository
from starintel_doc.v09_expansion import COMMON_DATA_FIELDS, EXPANSION_FIELD_NAMES


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def canonical_json_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_schema_bundle() -> None:
    base_path = ROOT / "schemas" / "starintel-doc-v0.9.0.schema.json"
    expansion_path = ROOT / "schemas" / "starintel-doc-v0.9.0.expansion.json"
    manifest_path = ROOT / "schemas" / "starintel-doc-v0.9.0.manifest.json"
    for path in (base_path, expansion_path, manifest_path):
        if not path.is_file():
            raise RuntimeError(f"missing schema bundle file: {path.relative_to(ROOT)}")

    base = json.loads(base_path.read_text(encoding="utf-8"))
    expansion = json.loads(expansion_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if base.get("$id") != SCHEMA_ID:
        raise RuntimeError("base schema ID does not match the executable v0.9 contract")
    if expansion.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("expansion registry schema_version mismatch")
    if expansion.get("schema_revision") != SCHEMA_REVISION:
        raise RuntimeError("expansion registry schema_revision mismatch")
    if expansion.get("profile") != SCHEMA_PROFILE or expansion.get("profile_version") != SCHEMA_PROFILE_VERSION:
        raise RuntimeError("expansion registry profile mismatch")

    expected_dtype_fields = {name: list(fields) for name, fields in sorted(EXPANSION_FIELD_NAMES.items())}
    if expansion.get("dtype_fields") != expected_dtype_fields:
        raise RuntimeError("checked-in expansion dtype registry is stale")
    if expansion.get("common_data_fields") != list(COMMON_DATA_FIELDS):
        raise RuntimeError("checked-in common data field registry is stale")
    if set(expansion["dtype_fields"]) != set(TYPE_FIELDS):
        raise RuntimeError("expansion registry does not cover every canonical dtype")

    expansion_hash = canonical_json_hash(expansion)
    if manifest.get("expansion_content_hash") != expansion_hash:
        raise RuntimeError("schema manifest expansion hash mismatch")
    if manifest.get("schema_revision") != SCHEMA_REVISION:
        raise RuntimeError("schema manifest revision mismatch")
    if manifest.get("dtype_count") != len(TYPE_FIELDS):
        raise RuntimeError("schema manifest dtype count mismatch")

    generated = document_schema()
    if generated.get("x-starintel-schema-revision") != SCHEMA_REVISION:
        raise RuntimeError("materialized schema revision mismatch")
    if generated.get("x-starintel-profile") != SCHEMA_PROFILE:
        raise RuntimeError("materialized schema profile mismatch")
    if "reference" not in generated.get("$defs", {}):
        raise RuntimeError("materialized schema is missing reusable definitions")

    for dtype, fields in TYPE_FIELDS.items():
        expected = set(COMMON_DATA_FIELDS) | set(EXPANSION_FIELD_NAMES[dtype])
        missing = sorted(expected - set(fields))
        if missing:
            raise RuntimeError(f"materialized {dtype} schema is missing fields: {missing}")

    # Ensure the complete materialized schema is serializable and deterministic.
    first = json.dumps(generated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    second = json.dumps(document_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if first != second:
        raise RuntimeError("materialized schema is nondeterministic")


def validate_corpus() -> None:
    result = validate_repository(ROOT, require_v090=True)
    if result["ok"]:
        print(f"documents={result['documents']} schema=0.9.0 corpus=valid")
        return
    for error in result["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    raise RuntimeError(f"StarIntel corpus validation failed with {len(result['errors'])} error(s)")


def validate_javascript() -> None:
    modules = sorted((ROOT / "site-assets").glob("*.mjs"))
    test = ROOT / "tests" / "test_graph_pathfinding.mjs"
    if not modules and not test.exists():
        return
    if shutil.which("node") is None:
        raise RuntimeError("node is required to validate graph modules")
    for module in modules:
        run(["node", "--check", str(module.relative_to(ROOT))])
    if test.is_file():
        run(["node", str(test.relative_to(ROOT))])


def validate_site() -> None:
    with tempfile.TemporaryDirectory(prefix="starintel-merge-") as directory:
        temporary = Path(directory)
        site = temporary / "site"
        org = temporary / "org"
        run(
            [
                sys.executable,
                "scripts/build_research_site.py",
                "--input",
                "digs",
                "--db",
                "db",
                "--output",
                str(site),
                "--org-output",
                str(org),
            ]
        )
        required = [
            site / "index.html",
            site / "search-index.json",
            site / "assets" / "graph-controller.mjs",
            site / "assets" / "graph-core.mjs",
        ]
        missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError(f"site validation failed; missing generated artifacts: {missing}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mandatory local and CI gate before merging StarIntel document changes"
    )
    parser.add_argument("--site", action="store_true", help="also build and validate the complete research site")
    parser.add_argument("--skip-git-diff-check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run([sys.executable, "-m", "compileall", "-q", "starintel_doc", "scripts"])
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
        validate_javascript()
        validate_schema_bundle()
        validate_corpus()
        if args.site:
            validate_site()
        if not args.skip_git_diff_check and (ROOT / ".git").exists():
            run(["git", "diff", "--check"])
        print("MERGE GATE: PASS")
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"MERGE GATE: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
