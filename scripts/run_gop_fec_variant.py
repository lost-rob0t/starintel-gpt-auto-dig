#!/usr/bin/env python3
from __future__ import annotations

import argparse
import runpy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GENERATED_AT = "2026-08-08T21:55:00Z"

ALLOWED = {
    "import_dnc_fec_administrative_fines.py",
    "import_dnc_fec_committee_transactions.py",
    "import_dnc_fec_democratic_candidates.py",
    "import_dnc_fec_democratic_committees.py",
    "import_dnc_fec_independent_expenditures.py",
    "import_dnc_fec_oppexp.py",
}

REPLACEMENTS = (
    ('2026-07-31', '2026-08-08'),
    ('    if party_code == "DFL":\n        base += 0.01\n', ''),
    ('PARTY_CODES = {"DEM", "DFL"}', 'PARTY_CODES = {"REP"}'),
    ('DEM|DFL', 'REP'),
    ('`DEM` or `DFL`', '`REP`'),
    ('DEM and DFL', 'REP'),
    ('DEM or DFL', 'REP'),
    ('DEM/DFL', 'REP'),
    ('MAX_MATCHING_ROWS = 50_000', 'MAX_MATCHING_ROWS = 250_000'),
    ('C00010603', 'C00003418'),
    ('starintel:org:dnc', 'starintel:org:republican-national-committee'),
    ('democratic-party-fec-affiliation', 'republican-party-fec-affiliation'),
    ('DEMOCRATIC_PARTY_ID', 'REPUBLICAN_PARTY_ID'),
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


def transformed_script_name(source_name: str) -> str:
    name = source_name.replace("dnc", "gop")
    name = name.replace("democratic", "republican")
    return name


def normalize_generated_at(text: str) -> str:
    lines = text.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith("GENERATED_AT = "):
            lines[index] = f'GENERATED_AT = "{GENERATED_AT}"'
            replaced = True
    if not replaced:
        raise RuntimeError("source importer no longer declares GENERATED_AT")
    return "\n".join(lines) + "\n"


def transform(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    if 'DATASET = "dnc"' not in text:
        raise RuntimeError(f"{source_path.name} is no longer a DNC importer; review adapter")

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = normalize_generated_at(text)

    generated_name = transformed_script_name(source_path.name)
    text = text.replace(
        f"python3 scripts/{generated_name}",
        f"python3 scripts/run_gop_fec_variant.py {source_path.name}",
    )

    required = (
        'DATASET = "gop"',
        f'GENERATED_AT = "{GENERATED_AT}"',
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
        'DEM|DFL',
        'DEM and DFL',
        'DEM or DFL',
        'DFL',
    )
    leaked = [marker for marker in forbidden if marker in text]
    if leaked:
        raise RuntimeError(f"GOP transform retained DNC-specific markers: {leaked}")

    if "PARTY_CODES" in text and 'PARTY_CODES = {"REP"}' not in text:
        raise RuntimeError("party-filtering importer did not resolve to REP-only")
    if source_path.name == "import_dnc_fec_oppexp.py" and 'COMMITTEE_ID = "C00003418"' not in text:
        raise RuntimeError("RNC-scoped importer did not resolve to C00003418")
    if 'party_code == "REP"' in text and 'base += 0.01' in text:
        raise RuntimeError("DFL-specific committee-priority bonus leaked into REP transform")

    return text


def main() -> int:
    ns, forwarded = parse_args()
    source_path = SCRIPTS / Path(ns.source).name
    if source_path.name == "import_dnc_fec_individual_contributions.py":
        raise RuntimeError(
            "identity-bearing individual-contribution import is disabled for GOP; "
            "use scripts/import_gop_fec_deidentified_receipts.py"
        )
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
