#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from starintel_site.builder import build_site


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Org-roam and a static StarIntel research site.")
    parser.add_argument("--input", type=Path, default=Path("digs"))
    parser.add_argument("--output", type=Path, default=Path("_site"))
    parser.add_argument("--org-output", type=Path, default=Path(".generated/org"))
    parser.add_argument("--config", type=Path, default=Path("site-config.json"))
    parser.add_argument("--assets", type=Path, default=Path("site-assets"))
    args = parser.parse_args()
    try:
        build_site(args.input, args.output, args.org_output, args.config, args.assets)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Built site at {args.output} and Org corpus at {args.org_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
