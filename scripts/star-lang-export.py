#!/usr/bin/env python3
"""Regenerate the Star-Lang spec-library export for the current release.

Writes spec/star/starintel-core-<SCHEMA_VERSION>.star plus a SHA256SUMS entry
in spec/star/. Deterministic: committing the artifact lets consumers vendor
byte-identical copies and pin them by digest.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from starintel_doc.spec import SCHEMA_VERSION  # noqa: E402
from starintel_doc.star_lang import write_library  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "spec" / "star")
    args = parser.parse_args()

    target = args.out / f"starintel-core-{SCHEMA_VERSION}.star"
    digest = write_library(target)

    sums = args.out / "SHA256SUMS"
    entries: dict[str, str] = {}
    if sums.exists():
        for line in sums.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value, name = line.split(maxsplit=1)
                entries[name.strip()] = value
    entries[target.name] = digest.removeprefix("sha256:")
    sums.write_text(
        "".join(f"{v}  {n}\n" for n, v in sorted(entries.items())),
        encoding="utf-8", newline="\n")

    print(f"wrote {target}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
