# StarIntel Auto-Dig Agent Instructions

## Mission

Publish durable public-record research as typed StarIntel documents, then generate an explorable Org-roam and web graph without duplicating canonical content.

## Canonical record

Each dated dig packet owns its non-overlapping `records/*.jsonl` shards. Together those shards are the canonical dataset. Generated Org and site output must never become a second manually maintained research corpus.

## Agent research

Agent-authored analysis is expected when it helps build a narrative. It must be a typed `analysis` document and include:

1. the question and method;
2. explicit definitions;
3. evidence supporting the assessment;
4. counterevidence and limits;
5. separation between structural resemblance, motive, legal liability, and moral equivalence;
6. confidence and verification status;
7. source links.

For ideological comparisons, use a visible feature matrix rather than label substitution. A few shared structures do not establish identity between systems.

## Generation

Run `python scripts/build.py`. The generator creates stable Org IDs, source links, computed exploration links, a dataset index, a combined JSONL export, evidence pages, and an interactive graph. GitHub Pages deploys only from `main`; pull requests build and validate without deployment.
