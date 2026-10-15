#!/usr/bin/env python3
"""Sample random unresolved Auto-Dig targets and fan them out to workers.

Persisted queue builder for the dig-queue workflow. Unresolved means an
``investigation-target`` or ``target`` record whose canonical ``state`` or
legacy ``data.status`` is not ``completed``/``resolved``/``done``. Output is JSONL with one line per
sampled target, round-robin assigned to ``--assign`` workers.

Usage:
    python3 scripts/random-targets.py --count 10 --assign 4 \
        [--seed N] --output /tmp/opencode/dig-queue-<date>/queue.jsonl
"""
import argparse
import json
import random
import sys
from pathlib import Path

RESOLVED_STATUSES = {"completed", "resolved", "done"}
UNRESOLVED_DTYPES = ("investigation-target", "target")


def iter_unresolved(root: Path):
    for dtype in UNRESOLVED_DTYPES:
        ddir = root / "db" / dtype
        if not ddir.is_dir():
            continue
        for path in sorted(ddir.glob("*.ndjson")):
            try:
                doc = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                print(f"warn: skipping unreadable {path}: {exc}", file=sys.stderr)
                continue
            if not isinstance(doc, dict):
                print(f"warn: skipping non-object {path}", file=sys.stderr)
                continue
            canonical = "id" in doc or "schemaVersion" in doc
            identity = doc.get("id" if canonical else "_id")
            data = doc if canonical else doc.get("data", {})
            if (not isinstance(identity, str) or not identity.strip()
                    or not isinstance(data, dict)
                    or doc.get("dtype", dtype) != dtype):
                print(f"warn: skipping malformed target {path}", file=sys.stderr)
                continue
            status = data.get("state", data.get("status")) if canonical else data.get("status")
            if str(status).strip().lower() in RESOLVED_STATUSES:
                continue
            question = data.get("researchQuestion" if canonical else "research_question") or data.get("query")
            yield {
                # Queue compatibility: _id is the source identity, including flat id.
                "_id": identity,
                "dtype": dtype,
                "status": status,
                "title": doc.get("title") or data.get("target") or question or identity,
                "research_question": question,
                "target": data.get("target"),
                "target_id": data.get("targetId" if canonical else "target_id"),
                "target_type": data.get("targetType" if canonical else "target_type"),
                "dataset": doc.get("dataset"),
                "priority": data.get("priority"),
            }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=10, help="number of targets to sample")
    ap.add_argument("--assign", type=int, default=4, help="number of workers")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    ap.add_argument("--output", required=True, help="queue JSONL output path")
    ap.add_argument("--root", default=None, help="repository root (default: parent of this script)")
    args = ap.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    if args.count < 1 or args.assign < 1:
        ap.error("--count and --assign must be >= 1")

    pool = list(iter_unresolved(root))
    if not pool:
        print("error: no unresolved targets found", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    sample = rng.sample(pool, min(args.count, len(pool)))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    per_worker = {w: 0 for w in range(1, args.assign + 1)}
    with out.open("w") as fh:
        for i, rec in enumerate(sample):
            worker = (i % args.assign) + 1
            rec["worker"] = worker
            per_worker[worker] += 1
            fh.write(json.dumps(rec, sort_keys=True) + "\n")

    summary = {
        "unresolved_pool": len(pool),
        "sampled": len(sample),
        "seed": args.seed,
        "workers": args.assign,
        "per_worker": per_worker,
        "remaining_after": len(pool) - len(sample),
        "output": str(out),
    }
    (out.parent / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
