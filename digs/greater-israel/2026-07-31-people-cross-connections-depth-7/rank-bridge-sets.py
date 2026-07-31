#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any


def load_memberships(path: Path) -> dict[str, set[str]]:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("membership file must be an object")

    out: dict[str, set[str]] = {}
    for person, labels in raw.items():
        if not isinstance(person, str) or not isinstance(labels, list):
            raise ValueError("expected person -> list[str]")
        clean = {label for label in labels if isinstance(label, str) and label}
        if clean:
            out[person] = clean
    return out


def rank(memberships: dict[str, set[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for person, labels in memberships.items():
        ordered = sorted(labels)
        pairs = [list(pair) for pair in combinations(ordered, 2)]
        rows.append(
            {
                "person": person,
                "membership_count": len(ordered),
                "pairwise_intersection_count": len(pairs),
                "memberships": ordered,
                "intersections": pairs,
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            -row["pairwise_intersection_count"],
            -row["membership_count"],
            row["person"],
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank people by independently sourced cluster-set intersections."
    )
    parser.add_argument("memberships", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    rows = rank(load_memberships(args.memberships))
    indent = 2 if args.pretty else None
    print(json.dumps(rows, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
