#!/usr/bin/env python3
from __future__ import annotations

import argparse
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

ALLOWED = {
    "import_dnc_fec_administrative_fines.py",
    "import_dnc_fec_committee_transactions.py",
    "import_dnc_fec_democratic_candidates.py",
    "import_dnc_fec_democratic_committees.py",
    "import_dnc_fec_independent_expenditures.py",
    "import_dnc_fec_individual_contributions.py",
    "import_dnc_fec_oppexp.py",
}

REPLACEMENTS = (
    ('PARTY_CODES = {"DEM", "DFL"}', 'PARTY_CODES = {"REP"}'),
    ('C00010603', 'C00003418'),
    ('starintel:org:dnc', 'starintel:org:republican-national-committee'),
    ('democratic-party-fec-affiliation', 'republican-party-fec-affiliation'),
    ('DEMOCRATIC_PARTY_ID', 'REPUBLICAN_PARTY_ID'),
    ('DEM or DFL', 'REP'),
    ('DEM/DFL', 'REP'),
    ('"DEM"', '"REP"'),
    ("'DEM'", "'REP'"),
    ('DFL', 'REP'),
    ('DEMOCRATIC', 'REPUBLICAN'),
    ('Democratic', 'Republican'),
    ('democratic', 'republican'),
    ('DEMOCRAT', 'REPUBLICAN'),
    ('Democrat', 'Republican'),
    ('democrat', 'republican'),
    ('DNC', 'GOP'),
    ('dnc', 'gop'),
)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run an allow-listed DNC FEC importer as a deterministic GOP/RNC variant"
    )
    parser.add_argument("source", help="DNC FEC importer filename under scripts/")
    return parser.parse_known_args()


def transform(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    if 'DATASET = "dnc"' not in text:
        raise RuntimeError(f"{source_path.name} is no longer a DNC importer; review adapter")

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    required = (
        'DATASET = "gop"',
        'StarIntel-AutoDig/0.9',
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(f"GOP transform missing required markers: {missing}")

    forbidden = (
        'DATASET = "dnc"',
        'starintel:org:dnc',
        'PARTY_CODES = {"DEM", "DFL"}',
        'C00010603',
    )
    leaked = [marker for marker in forbidden if marker in text]
    if leaked:
        raise RuntimeError(f"GOP transform retained DNC-specific markers: {leaked}")

    if "PARTY_CODES" in text and 'PARTY_CODES = {"REP"}' not in text:
        raise RuntimeError("party-filtering importer did not resolve to REP-only")

    return text


def main() -> int:
    ns, forwarded = parse_args()
    source_path = SCRIPTS / Path(ns.source).name
    if source_path.name not in ALLOWED:
        raise RuntimeError(f"unsupported GOP variant source: {source_path.name}")
    if not source_path.is_file():
        raise RuntimeError(f"missing source importer: {source_path}")

    transformed = transform(source_path)
    old_argv = sys.argv[:]
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".py",
            prefix=".gop-variant-",
            dir=SCRIPTS,
            delete=False,
        ) as handle:
            handle.write(transformed)
            temp_path = Path(handle.name)

        sys.argv = [str(temp_path), *forwarded]
        runpy.run_path(str(temp_path), run_name="__main__")
    finally:
        sys.argv = old_argv
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
