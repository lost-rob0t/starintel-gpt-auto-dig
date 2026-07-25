# StarIntel GPT Auto Dig

Evidence-first research packets and a Git-backed JSON database using the repository-local **`starintel_doc` v0.9.0 fork** as the only document specification.

## Canonical rule

`starintel_doc/` is the sole schema implementation. Scripts, skills, validation, migration, recursive target selection, imports, the static explorer, and generated JSON Schema all import it directly. Do not create a second schema, a prompt-only “style,” or undocumented top-level fields.

Every document uses the v0.9.0 envelope:

```text
_id, dataset, dtype, schema_version, version,
date_added, date_updated,
title, summary, description, status, language,
tags, labels, aliases, keywords, identifiers,
sources, evidence, temporal, provenance, assessment,
verification, handling, lineage, quality, workflow,
geospatial, attachments, related_ids, notes,
data, extensions
```

`data` is strictly selected by `dtype`. `extensions` is the declared, namespaced escape hatch for metadata that cannot yet be represented without data loss. Undeclared top-level fields and undeclared `data` fields fail validation.

## Repository layout

```text
starintel_doc/                 Canonical v0.9.0 schema fork and runtime
schemas/                       Generated JSON Schema
skills/                        Auto-dig operating skills
scripts/starintel.py           Unified CLI
scripts/validate-db.py         Strict corpus validator
scripts/migrate-starintel-v0.9.py
scripts/search-db.py
scripts/select-targets.py
db/<dtype>/<_id>.ndjson        One compact document per file
digs/<target>/<run>/starintel-documents.jsonl
manifests/                     Corpus and migration manifests
```

## CLI

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --output schemas/starintel-doc-v0.9.0.schema.json
python3 scripts/starintel.py create org \
  --dataset example \
  --id starintel:org:example \
  --title "Example Org" \
  --data '{"name":"Example Org","org_type":"company"}'
python3 scripts/starintel.py validate
python3 scripts/starintel.py search palantir --dtype org --with-location
python3 scripts/starintel.py select-targets \
  --query palantir \
  --limit 10 \
  --emit-documents \
  --output recursive-targets.jsonl
```

## Full migration

```bash
python3 scripts/migrate-starintel-v0.9.py --write
python3 scripts/validate-db.py
python3 -m unittest discover -s tests -v
```

The migration traverses every normalized DB record and every dig packet, converts old metadata into the v0.9.0 envelope, preserves unrecognized legacy values beneath `extensions.legacy.v0`, rewrites packets as plain canonical JSONL, removes old compressed transport fragments, and emits a migration manifest.

## Document creation

Creation must go through `Document.create`, `python -m starintel_doc create`, or `scripts/starintel.py create`. Direct JSON authored by an agent must still pass `validate_document` before publication.

```python
from starintel_doc import Document

record = Document.create(
    "relation",
    "example-dataset",
    doc_id="starintel:relation:alice-founded-example",
    data={
        "subject": "starintel:person:alice",
        "predicate": "founded",
        "object": "starintel:org:example",
        "confidence": 0.97,
    },
    sources=[{"kind": "filing", "url": "https://example.test", "credibility": 0.99}],
)
```

## Git flow

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit one coherent schema, tooling, or research transaction.
4. Validate Python, tests, the complete JSON corpus, generated schema, graph, and site.
5. Open a pull request into `main`.
6. Squash-merge after checks pass.

Do not publish research packets directly to `main`.
