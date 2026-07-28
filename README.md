# StarIntel GPT Auto Dig

Evidence-first research packets and a Git-backed JSON database using the repository-local **`starintel_doc` v0.9.0 fork** as the only document specification.

## Canonical rule

`starintel_doc/` is the sole schema implementation. Scripts, skills, validation, migration, recursive target selection, imports, the static explorer, and generated JSON Schema all import it directly. Do not create a second schema, a prompt-only “style,” or undocumented fields.

Every document uses the v0.9.0 envelope:

```text
_id, dataset, dtype, schema_version, version,
date_added, date_updated,
title, summary, description, status, language,
tags, labels, aliases, keywords, identifiers,
sources, evidence, temporal, provenance, assessment,
verification, handling, lineage, quality, workflow,
geospatial, attachments, related_ids, notes,
schema_org, data, extensions
```

`schema_org` is the declared Schema.org JSON-LD metadata block. Constructors populate `@context`, `@type`, `@id`, and `additionalType`; explicit JSON-LD metadata may add identity links, identifiers, agents, places, dates, citations, licensing, media, actions, and structured `PropertyValue` records. Vocabulary not represented by a declared direct field belongs in `schema_org.additionalProperty` or `schema_org.properties`.

`data` is strictly selected by `dtype`. `extensions` is the declared, namespaced escape hatch for metadata that cannot yet be represented without data loss. Undeclared top-level fields, undeclared `schema_org` direct fields, and undeclared `data` fields fail validation.

## Repository layout

```text
starintel_doc/                    Canonical v0.9.0 schema fork and runtime
schemas/                          Generated JSON Schema
skills/                           Auto-dig operating skills
scripts/starintel.py              Unified CLI
scripts/create-db-document.py     Transactional canonical DB writer
scripts/validate-db.py            Strict corpus validator
scripts/validate-for-merge.py     Mandatory pre-merge gate
scripts/migrate-starintel-v0.9.py Full-corpus migration
scripts/search-db.py              JSON database search
scripts/select-targets.py         Recursive target selection
db/<dtype>/<_id>.ndjson           One compact document per file
digs/<target>/<run>/starintel-documents.jsonl
manifests/                        Corpus and migration manifests
```

## Required document creation

Agents and automation must not hand-write files under `db/`.

Create one normalized record with:

```bash
python3 scripts/create-db-document.py org \
  --dataset example \
  --id starintel:org:example \
  --title "Example Org" \
  --data '{"name":"Example Org","org_type":"company"}'
```

The script validates the schema before writing, writes only to `db/<dtype>/<_id>.ndjson`, validates the complete repository after writing, and rolls back on failure.

For a batch, create JSONL outside `db/` and import it:

```bash
python3 scripts/starintel.py import records.jsonl
```

Use `--replace` only for an intentional correction or newer version. Use `--migrate` only for legacy input.

`scripts/starintel.py create` may generate or inspect a draft document, but it must not be used to write directly into `db/`.

## Database convention

Every normalized document must exist at exactly:

```text
db/<dtype>/<_id>.ndjson
```

The directory must equal `dtype`; the literal `_id`, including colons, must equal the filename; path separators are forbidden in `_id`; each file contains exactly one compact JSON object and one terminating newline. Duplicate normalized IDs are invalid. Relation endpoint IDs must resolve to normalized records unless represented as explicitly unresolved schema endpoints.

## CLI

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype relation
python3 scripts/starintel.py schema --output schemas/starintel-doc-v0.9.0.schema.json
python3 scripts/starintel.py jsonld db/org/starintel:org:example.ndjson --pretty
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
python3 scripts/validate-for-merge.py --site
```

The migration traverses every normalized DB record and dig packet, converts old metadata into the v0.9.0 envelope, enriches existing v0.9 records with deterministic Schema.org defaults, preserves explicit JSON-LD metadata, preserves unrecognized legacy values beneath `extensions.legacy.v0`, rewrites packets as plain canonical JSONL, removes old compressed transport fragments, and emits a migration manifest.

## Mandatory merge gate

Before marking a pull request ready, approving it, enabling auto-merge, or merging it, run:

```bash
python3 scripts/validate-for-merge.py --site
```

The gate checks Python compilation, all unit tests, generated-schema reproducibility, strict validation of every DB and packet record, canonical paths, one-record-per-file formatting, duplicate IDs, relation endpoints, site generation, and `git diff --check`.

A document PR must not be merged unless the local gate and every required GitHub check pass against the current head commit. A failing, pending, skipped, cancelled, unavailable, stale, or inconclusive check is not success. Keep the PR in draft until fixed.

Never merge invalid documents with a promise to repair them later. Never weaken the schema, broaden `additionalProperties`, or misuse `extensions` merely to admit invalid data.

## Git flow

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit one coherent schema, tooling, or research transaction.
4. Run `python3 scripts/validate-for-merge.py --site`.
5. Open a draft pull request into `main`.
6. Mark ready only after the current head passes every check.
7. Squash-merge only when validation is fully green.

Do not publish research packets directly to `main`.
