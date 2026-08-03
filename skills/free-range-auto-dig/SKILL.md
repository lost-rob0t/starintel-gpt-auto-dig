---
name: free-range-auto-dig
description: Build a balanced multi-actor research frontier from queued and discoverable StarIntel targets without writing conclusions or mutating the canonical database.
---

# Free-Range Auto-Dig

## Command

```bash
python3 scripts/free-range.py \
  --limit 20 \
  --batch-size 5 \
  --max-per-dataset 3 \
  --max-per-type 5 \
  --format markdown \
  --output free-range-frontier.md
```

Optional controls:

- `--query`, `--dtype`, and `--dataset` scope the corpus before planning.
- `--queue-only` disables fresh candidate discovery.
- `--include-blocked` includes externally blocked targets with a penalty.
- `--strict-packets` aborts on unreadable packet transport; the default reports and skips it.
- `--db-only` or `--packets-only` selects a corpus surface.
- `--format jsonl` produces machine-readable mission cells.

## Actor cell

Each mission receives five independent roles:

1. `scout` — acquire the next primary-source surface.
2. `archivist` — preserve provenance, hashes, versions, and archives.
3. `verifier` — independently corroborate the strongest assertion.
4. `linker` — resolve canonical identities and exact predicates.
5. `skeptic` — seek counterevidence and falsify unsupported hypotheses.

## Procedure

1. Read `AGENTS.md`.
2. Generate the frontier.
3. Inspect target IDs, queue records, blockers, reasons, and dataset/type balance.
4. Select one batch.
5. Run actors independently before synthesis.
6. Normalize accepted evidence only through the canonical scripted write or import path.
7. Run deterministic target selection after the completed pass.
8. Run `python3 scripts/validate-for-merge.py --site` before publishing document changes.

The mission plan is not evidence and must never be imported as a factual record. Centrality, selection score, actor agreement, and recursion depth do not establish guilt, control, coordination, or truth.
