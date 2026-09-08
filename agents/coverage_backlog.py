#!/usr/bin/env python3
"""Durable deterministic coverage ledger for bounded Auto-Dig sweeps.

The ledger lives inside the existing Auto-Dig actor state under ``coverage``.
It is intentionally generic: callers provide the authoritative valid item set
for the current run; this module only shards, claims, completes, and retries
those validated items.  Invalid/non-authoritative candidates never enter the
ledger merely because they satisfy the shard arithmetic.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

STATE_SCHEMA = "auto-dig-prolog-state.v1"
LEDGER_SCHEMA = "auto-dig-coverage-ledger.v1"


def _canonical_items(items: Iterable[int]) -> list[int]:
    values = sorted({int(item) for item in items})
    if any(item < 0 for item in values):
        raise ValueError("coverage items must be non-negative integers")
    return values


def _ledger_key(corpus: str, seed_kind: str, shard: str) -> str:
    parts = [corpus.strip(), seed_kind.strip(), shard.strip()]
    if any(not part for part in parts):
        raise ValueError("corpus, seed_kind, and shard must be non-empty")
    return "/".join(parts)


def _coverage_map(state: dict[str, Any]) -> dict[str, Any]:
    coverage = state.setdefault("coverage", {})
    if not isinstance(coverage, dict):
        raise ValueError("state.coverage must be an object")
    return coverage


def ensure_ledger(
    state: dict[str, Any],
    *,
    corpus: str,
    seed_kind: str,
    authority: str,
    shard: str,
    shard_count: int,
    shard_index: int,
) -> tuple[str, dict[str, Any]]:
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError(f"state schema must be {STATE_SCHEMA!r}")
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must be in [0, shard_count)")

    key = _ledger_key(corpus, seed_kind, shard)
    coverage = _coverage_map(state)
    ledger = coverage.get(key)
    if ledger is None:
        ledger = {
            "schema": LEDGER_SCHEMA,
            "corpus": corpus,
            "seed_kind": seed_kind,
            "authority": authority,
            "shard": shard,
            "shard_count": shard_count,
            "shard_index": shard_index,
            "ordering": "numeric_ascending",
            "completed": [],
            "in_progress": [],
            "failed_retryable": [],
        }
        coverage[key] = ledger
    if not isinstance(ledger, dict) or ledger.get("schema") != LEDGER_SCHEMA:
        raise ValueError(f"coverage ledger {key!r} has an incompatible schema")
    immutable = {
        "corpus": corpus,
        "seed_kind": seed_kind,
        "authority": authority,
        "shard": shard,
        "shard_count": shard_count,
        "shard_index": shard_index,
    }
    for field, expected in immutable.items():
        if ledger.get(field) != expected:
            raise ValueError(
                f"coverage ledger {key!r} changed immutable {field}: "
                f"{ledger.get(field)!r} != {expected!r}"
            )
    for field in ("completed", "in_progress", "failed_retryable"):
        ledger[field] = _canonical_items(ledger.get(field, []))
    return key, ledger


def shard_items(valid_items: Iterable[int], shard_count: int, shard_index: int) -> list[int]:
    valid = _canonical_items(valid_items)
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid shard configuration")
    return [item for item in valid if item % shard_count == shard_index]


def unresolved_items(ledger: dict[str, Any], valid_items: Iterable[int]) -> list[int]:
    shard = shard_items(valid_items, int(ledger["shard_count"]), int(ledger["shard_index"]))
    completed = set(_canonical_items(ledger.get("completed", [])))
    in_progress = set(_canonical_items(ledger.get("in_progress", [])))
    return [item for item in shard if item not in completed and item not in in_progress]


def claim_batch(
    ledger: dict[str, Any], valid_items: Iterable[int], batch_size: int
) -> list[int]:
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    batch = unresolved_items(ledger, valid_items)[:batch_size]
    ledger["in_progress"] = _canonical_items([*ledger.get("in_progress", []), *batch])
    retry = set(_canonical_items(ledger.get("failed_retryable", [])))
    ledger["failed_retryable"] = sorted(retry.difference(batch))
    return batch


def complete_batch(ledger: dict[str, Any], items: Iterable[int]) -> None:
    done = set(_canonical_items(items))
    in_progress = set(_canonical_items(ledger.get("in_progress", [])))
    if not done.issubset(in_progress):
        missing = sorted(done.difference(in_progress))
        raise ValueError(f"cannot complete unclaimed coverage items: {missing}")
    completed = set(_canonical_items(ledger.get("completed", [])))
    ledger["completed"] = sorted(completed.union(done))
    ledger["in_progress"] = sorted(in_progress.difference(done))
    retry = set(_canonical_items(ledger.get("failed_retryable", [])))
    ledger["failed_retryable"] = sorted(retry.difference(done))


def fail_batch(ledger: dict[str, Any], items: Iterable[int]) -> None:
    failed = set(_canonical_items(items))
    in_progress = set(_canonical_items(ledger.get("in_progress", [])))
    if not failed.issubset(in_progress):
        missing = sorted(failed.difference(in_progress))
        raise ValueError(f"cannot fail unclaimed coverage items: {missing}")
    ledger["in_progress"] = sorted(in_progress.difference(failed))
    retry = set(_canonical_items(ledger.get("failed_retryable", [])))
    ledger["failed_retryable"] = sorted(retry.union(failed))


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--valid-items", required=True, type=Path)
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--seed-kind", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--shard", required=True)
    parser.add_argument("--shard-count", required=True, type=int)
    parser.add_argument("--shard-index", required=True, type=int)
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument("--action", choices=("next", "complete", "fail"), default="next")
    parser.add_argument("--items", default="", help="comma-separated claimed items for complete/fail")
    args = parser.parse_args(argv)

    state = _load_json(args.state)
    valid_items = _load_json(args.valid_items)
    if not isinstance(state, dict) or not isinstance(valid_items, list):
        raise ValueError("state must be an object and valid-items must be a JSON array")
    key, ledger = ensure_ledger(
        state,
        corpus=args.corpus,
        seed_kind=args.seed_kind,
        authority=args.authority,
        shard=args.shard,
        shard_count=args.shard_count,
        shard_index=args.shard_index,
    )
    if args.action == "next":
        batch = claim_batch(ledger, valid_items, args.batch_size)
    else:
        items = [int(item) for item in args.items.split(",") if item.strip()]
        if not items:
            raise ValueError("--items is required for complete/fail")
        if args.action == "complete":
            complete_batch(ledger, items)
        else:
            fail_batch(ledger, items)
        batch = items
    _atomic_write_json(args.state, state)
    print(json.dumps({"ledger": key, "action": args.action, "items": batch}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
