# Auto-Dig Worker Fleet (Agent Zero scheduled actors)

Operators control this fleet through `config/auto-dig-control.json` (P0 gate,
see AGENTS.md). Every actor below fail-closes via
`python3 scripts/check-auto-dig-control.py` before doing any work.

## Actors

1. **auto-dig issue worker** (twice hourly, `:00` and `:30`)
   - Claims the oldest open `investigation-target` issue.
   - Runs a scripter/critic subagent loop until the pass completes.
   - Writes validated documents ONLY through `scripts/create-db-document.py`
     or `scripts/starintel.py import` into `db/` (never outboxes).
   - After completion, delegates ingestion to a dedicated subagent running
     `python3 scripts/import-starintel-documents.py --diff main`.
   - Closes the issue with a pass summary; opens a PR from a research branch.

2. **auto-dig pr gatekeeper** (twice hourly)
   - Lists open PRs, runs the merge gate
     (`nimble buildFast`, `bin/validate-for-merge --site`).
   - Merges PRs that pass all gates and required checks.
   - Fixes or annotates PRs that fail; never merges invalid documents.

3. **auto-dig target scout** (twice hourly)
   - Searches the local corpus (`scripts/starintel.py search`) and the
     StarIntel server for under-explored entities.
   - Emits `investigation-target` documents via the deterministic selector
     (`scripts/starintel.py select-targets --emit-documents`) and imports them
     through the canonical batch importer; files GitHub issues with the
     `investigation-target` label.

## Branch discipline

No actor commits to `main`. All work lands on `research/*` or `ops/*`
branches and reaches `main` through PRs that pass the merge gate.
