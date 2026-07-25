# StarIntel GPT Auto-Dig Agent Instructions

## Mission

Publish evidence-preserving StarIntel research as machine-readable documents, readable research material, and Python-generated exploration pages.

## Required output

Every completed research pass must update at least one canonical machine-readable surface:

1. a packet beneath `digs/<target>/<date>-<slug>/`; or
2. normalized records beneath `db/<dtype>/<_id>.ndjson` with the required manifest and report material.

Optional Org research notes may be stored beneath `roam/research/` or `roam/indexes/`, but they are source material rather than the deployment engine.

## Database rules

- Each normalized NDJSON file contains exactly one compact JSON object plus a terminating newline.
- `dtype` must equal the directory name.
- `_id` must equal the filename without `.ndjson`.
- Preserve exact source URLs, source type, evidence, timestamps, confidence, and analytical notes.
- Never collapse contract ceiling, potential value, current award amount, obligation, outlay, and recognized revenue into one field.
- Never convert lobbying, prior government work, political relationships, or vendor concentration into an allegation of illegality without evidence.
- Never fabricate sources, confidence, quotations, dates, relationships, tests, commits, or workflow status.
- Updating an existing `_id` requires an intentional correction or a newer document version.

## Research-note rules

The repository is research-only. Do not create `roam/implement/`.

Every persistent Org file must:

- live beneath `roam/`
- have a stable file-level `ID`
- include `#+title` and `#+description`
- use durable `id:` links where practical
- link to its project index
- define non-obvious terms where needed
- remain readable without loading the entire repository

## Validation

For packet-oriented research, run:

```bash
python -m compileall -q scripts
python3 scripts/build_research_site.py \
  --input digs \
  --output _site \
  --org-output .generated/org
```

For normalized database records, also run:

```bash
python3 scripts/validate-db.py
```

Generated state belongs under `_site/`, `.generated/`, and cache directories; never commit it.

## Publishing

- The Python research-site generator is the canonical publisher.
- Pull requests validate but do not deploy.
- Pushes to `main` build the Python-generated site and deploy it through GitHub Pages.
- Do not add an Emacs-based Pages workflow.
- The user has authorized automatic merge or direct publication for assistant-generated research updates when checks are clean.
- Do not commit secrets, credentials, restricted evidence, or personal data that is not intended to be published in this repository.
