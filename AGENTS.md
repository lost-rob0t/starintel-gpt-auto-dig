# StarIntel GPT Auto-Dig Agent Instructions

## Mission

Publish evidence-preserving StarIntel research as both machine-readable documents and a navigable Org-roam second brain.

## Required output

Every completed research pass must update both surfaces:

1. `db/<dtype>/<_id>.ndjson`
2. at least one relevant Org node beneath `roam/research/` or `roam/indexes/`

## Database rules

- Each NDJSON file contains exactly one compact JSON object plus a terminating newline.
- `dtype` must equal the directory name.
- `_id` must equal the filename without `.ndjson`.
- Preserve exact source URLs, source type, evidence, timestamps, confidence and analytical notes.
- Never collapse contract ceiling, potential value, current award amount, obligation, outlay and recognized revenue into one field.
- Never convert lobbying, prior government work, political relationships or vendor concentration into an allegation of illegality without evidence.
- Never fabricate sources, confidence, quotations, dates or relationships.
- Updating an existing `_id` requires an intentional correction or a newer document version.

## Org-roam rules

The repository is research-only. Do not create `roam/implement/`.

Every persistent Org file must:

- live beneath `roam/`
- have a stable file-level `ID`
- include `#+title` and `#+description`
- use durable `id:` links where practical
- link to its project index
- define non-obvious terms in a `Footnotes and Glossary` section
- remain readable without loading the entire repository

Use the canonical publication index:

```text
roam/indexes/second-brain/SECOND-BRAIN-000-org-roam-pages.org
```

## Validation

Run:

```bash
python3 scripts/validate-db.py
bash scripts/publish-pages
python3 scripts/check-pages-links.py _site
```

Generated state belongs under `.cache/` and `_site/`; never commit either directory.

## Publishing

- Pull requests validate but do not deploy.
- Pushes to `main` validate the database, build the Org-roam site and deploy through GitHub Pages.
- The user has authorized automatic merge or direct publication for assistant-generated research updates when checks are clean.
- Do not commit secrets, credentials, restricted evidence or personal data that is not intended to be published in this repository.
