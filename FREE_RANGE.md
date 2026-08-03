# Free-Range Auto-Dig

Free-Range turns the existing StarIntel corpus into a deterministic research mission board. It does not generate conclusions. It selects the next evidence work, balances the frontier, and assigns independent actor roles so one hypothesis does not consume the whole run.

## Run it

```bash
python3 scripts/free-range.py \
  --limit 20 \
  --batch-size 5 \
  --max-per-dataset 3 \
  --max-per-type 5 \
  --format markdown \
  --output free-range-frontier.md
```

Scope the frontier when needed:

```bash
python3 scripts/free-range.py \
  --query "FBI TSC AI" \
  --dataset fed \
  --limit 10 \
  --format jsonl \
  --output free-range-frontier.jsonl
```

Use `--queue-only` to plan only from existing `target` and `investigation-target` records. Without it, the planner also asks the canonical recursive selector for high-value entities not already in the queue.

Unreadable compressed research packets are reported and skipped by default so one broken transport cannot blind the entire planner. Use `--strict-packets` when packet corruption must abort the run.

Blocked work is excluded by default. Use `--include-blocked` to place it at the end of the actionable frontier with an explicit score penalty and blocker list.

## Five-actor mission cell

Every selected target receives the same adversarial evidence cell:

1. **Scout** — locates the next primary-source surface and enumerates concrete people, organizations, records, identifiers, and dates.
2. **Archivist** — captures URLs, retrieval times, hashes, versions, archives, and lineage before interpretation.
3. **Verifier** — independently corroborates the strongest material assertion and preserves conflicts and search limits.
4. **Linker** — resolves canonical IDs and exact predicates without duplicating entities or inventing generic edges.
5. **Skeptic** — tries to falsify the leading hypothesis and downgrades unsupported proximity, capability, employment, and allegation chains.

This is an actor workflow, not five votes on truth. Outputs remain research instructions until the underlying evidence is collected and normalized through the canonical StarIntel write path.

## Frontier behavior

The planner:

- prefers actionable queued targets over newly discovered candidates;
- excludes completed, closed, cancelled, rejected, and superseded work;
- deduplicates by canonical target ID;
- balances datasets and target types with configurable caps;
- preserves queue document IDs, seed IDs, blockers, and selection reasons;
- creates stable mission IDs from target IDs;
- emits deterministic Markdown or JSONL;
- never writes normalized records into `db/`.

## GitHub Action

Run **Free-Range Frontier** from the Actions tab. The workflow tests the planner, generates Markdown and JSONL mission packs, writes a compact job summary, and uploads both plans as an artifact. It is manual by design: the planner proposes work but does not silently mutate the database or launch uncontrolled collection.

## Evidence boundary

Every mission carries these rules:

- prefer primary sources and preserve exact provenance, dates, hashes, and versions;
- keep facts, attributed claims, inference, counterevidence, and unresolved gaps separate;
- do not convert proximity, capability, employment, or allegations into control or culpability without a direct evidence edge;
- reuse canonical StarIntel identities and exact predicates; never create a parallel schema.
