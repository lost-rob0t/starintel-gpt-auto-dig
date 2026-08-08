#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.schema_org import document_schema
from starintel_doc.store import packet_paths, read_transport, validate_repository

PAGES_CONTENT_BUDGET_BYTES = 9_000_000_000


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def validate_generated_schema() -> None:
    expected = ROOT / "schemas" / "starintel-doc-v0.9.0.schema.json"
    generated = json.dumps(document_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not expected.is_file():
        raise RuntimeError(f"missing generated schema: {expected.relative_to(ROOT)}")
    actual = expected.read_text(encoding="utf-8")
    if actual != generated:
        raise RuntimeError(
            "checked-in JSON Schema is stale; run: "
            "python3 scripts/starintel.py schema --output schemas/starintel-doc-v0.9.0.schema.json"
        )


def validate_packet_transports() -> None:
    for path in packet_paths(ROOT):
        try:
            payload = read_transport(path)
        except Exception as exc:
            raise RuntimeError(f"{path.relative_to(ROOT)}: transport decode failed: {exc}") from exc
        for number, raw in enumerate(payload.splitlines(), 1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                start = max(0, exc.pos - 120)
                end = min(len(raw), exc.pos + 120)
                excerpt = raw[start:end]
                raise RuntimeError(
                    f"{path.relative_to(ROOT)}:{number}: invalid JSON: {exc}; "
                    f"excerpt[{start}:{end}]={excerpt!r}"
                ) from exc
            if not isinstance(value, dict):
                raise RuntimeError(
                    f"{path.relative_to(ROOT)}:{number}: expected JSON object"
                )


def validate_corpus() -> None:
    validate_packet_transports()
    result = validate_repository(ROOT, require_v090=True)
    if result["ok"]:
        print(f"documents={result['documents']} schema=0.9.0 corpus=valid")
        return
    for error in result["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    raise RuntimeError(f"StarIntel corpus validation failed with {len(result['errors'])} error(s)")


def validate_javascript() -> None:
    modules = sorted((ROOT / "site-assets").glob("*.mjs"))
    scripts = [
        ROOT / "site-assets" / "people.js",
        ROOT / "site-assets" / "adar-shell.js",
        ROOT / "site-assets" / "corpus-dashboard.js",
    ]
    test = ROOT / "tests" / "test_graph_pathfinding.mjs"
    if not modules and not test.exists() and not any(path.exists() for path in scripts):
        return
    if shutil.which("node") is None:
        raise RuntimeError("node is required to validate graph and directory scripts")
    for module in modules:
        run(["node", "--check", str(module.relative_to(ROOT))])
    for script in scripts:
        if script.is_file():
            run(["node", "--check", str(script.relative_to(ROOT))])
    if test.is_file():
        run(["node", str(test.relative_to(ROOT))])


def validate_adar_surfaces(site: Path) -> None:
    index = site / "index.html"
    datasets = site / "datasets.html"
    dashboard_path = site / "dashboard-data.json"
    catalog_path = site / "dataset-catalog.json"
    shell = site / "assets" / "adar-shell.js"
    runtime = site / "assets" / "corpus-dashboard.js"

    index_markup = index.read_text(encoding="utf-8")
    datasets_markup = datasets.read_text(encoding="utf-8")
    shell_source = shell.read_text(encoding="utf-8")
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    if 'id="corpus-dashboard"' not in index_markup:
        raise RuntimeError("ADAR site validation failed; root dashboard container missing")
    if 'id="dataset-browser"' not in datasets_markup:
        raise RuntimeError("ADAR site validation failed; dataset browser container missing")
    if "https://auto-research.starintel.actor/" not in shell_source:
        raise RuntimeError("ADAR site validation failed; Research sibling-site link missing")
    if dashboard.get("version") != 1:
        raise RuntimeError("ADAR site validation failed; unsupported dashboard projection version")
    if any(row.get("label") == "relation" for row in dashboard.get("document_types", [])):
        raise RuntimeError("ADAR site validation failed; relation leaked into document-type chart")
    if not isinstance(dashboard.get("relation_types"), list):
        raise RuntimeError("ADAR site validation failed; relation-type projection missing")
    if any(row.get("kind") not in {"topic", "source"} for row in catalog):
        raise RuntimeError("ADAR site validation failed; invalid dataset catalog class")
    if not runtime.is_file() or runtime.stat().st_size == 0:
        raise RuntimeError("ADAR site validation failed; dashboard browser runtime missing")


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
            site / "datasets.html",
            site / "search-index.json",
            site / "dashboard-data.json",
            site / "dataset-catalog.json",
            site / "assets" / "graph-controller.mjs",
            site / "assets" / "graph-core.mjs",
            site / "assets" / "adar-shell.js",
            site / "assets" / "corpus-dashboard.js",
        ]
        missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError(f"site validation failed; missing generated artifacts: {missing}")
        validate_adar_surfaces(site)
        content_bytes = sum(path.stat().st_size for path in site.rglob("*") if path.is_file())
        if content_bytes >= PAGES_CONTENT_BUDGET_BYTES:
            raise RuntimeError(
                "site validation failed; generated content is too large for GitHub Pages "
                f"after archive overhead: {content_bytes:,} bytes"
            )


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
        validate_generated_schema()
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
