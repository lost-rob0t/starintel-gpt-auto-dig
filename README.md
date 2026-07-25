# StarIntel GPT Auto Dig

Git-backed StarIntel research database and Org-roam publication corpus produced by GPT-assisted auto-research.

## Storage contract

Every machine-readable record lives at:

```text
db/<dtype>/<_id>.ndjson
```

Each file contains exactly one compact JSON object plus one terminating newline. Its directory and filename must match the document's `dtype` and `_id` exactly.

## Repository layout

- `db/` — StarIntel NDJSON records grouped by document type
- `manifests/` — dataset manifests and integrity metadata
- `reports/` — readable research reports
- `roam/research/` — Org-roam research nodes
- `roam/indexes/` — publication and investigation indexes
- `lisp/starintel/`, `pages/`, `scripts/` — reproducible Org-roam Pages exporter

There is deliberately no `roam/implement/` workflow. This repository publishes research and indexes; it does not select software implementations.

See [`README.org`](README.org), [`AGENTS.md`](AGENTS.md), and [`docs/repository-contract.md`](docs/repository-contract.md) for the full contract and publication workflow.
