#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.spec import document_schema
from starintel_doc.store import validate_repository


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


def validate_corpus() -> None:
    result = validate_repository(ROOT, require_v090=True)
    if result["ok"]:
        print(f"documents={result['documents']} schema=0.9.0 corpus=valid")
        return
    for error in result["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    raise RuntimeError(f"StarIntel corpus validation failed with {len(result['errors'])} error(s)")


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
        required = [site / "index.html", site / "search-index.json"]
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
