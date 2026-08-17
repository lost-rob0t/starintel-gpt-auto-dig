# StarIntel GPT Auto Dig

Evidence-first research packets and a Git-backed JSON database using the repository-local **`starintel_doc` v0.9.0 schema** as the document specification, with Nim as the performance-critical validation and static-site runtime.

## Canonical rule

`starintel_doc/` and `schemas/starintel-doc-v0.9.0.schema.json` define the document contract. The Nim validator loads that generated schema through the canonical `starintel-doc.nim` runtime. Do not create a second JSON shape, a prompt-only “style,” or undocumented fields.

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
starintel_doc/                    Canonical v0.9.0 schema source
schemas/                          Generated JSON Schema
skills/                           Auto-dig operating skills
scripts/starintel.py              Legacy/admin schema CLI
scripts/create-db-document.py     Transactional canonical DB writer
scripts/starintel_transport.nim   Streaming packet transport reader
scripts/starintel_validate.nim    Fast schema + source audit validator
scripts/validate-for-merge.nim    Canonical Nim merge gate
scripts/starintel_site.nim        High-throughput static site generator
scripts/import_gop_fec_deidentified_receipts.nim
                                  Streaming RNC FEC receipt importer
starintel_auto_dig.nimble         Nim build/validate/site tasks
db/<dtype>/<_id>.ndjson           One compact document per file
digs/<target>/<run>/starintel-documents.jsonl
manifests/                        Corpus and migration manifests
```

## Canonical dataset roots

Each research subject or dataset has exactly one top-level `digs/<target>/` root. **Dataset siblings and alias roots are not allowed.** Existing roots are extended rather than split by geography, product, subsidiary, project phase, spelling variant, company alias, or later naming preference.

Before adding a new top-level directory under `digs/`, check the existing roots. If the work belongs to an existing subject, place the packet under that root as `digs/<canonical>/<YYYY-MM-DD>-<slug>/`. A new top-level root is reserved for a genuinely distinct subject, not a narrower slice of one already present.

CI enforces the structural rule repo-wide: if `digs/foo/` exists, a hyphen-qualified sibling such as `digs/foo-bar/` is invalid. Retired aliases are also recorded in `config/dataset-root-aliases.json` and may not reappear.

Current canonicalizations include:

```text
digs/flock/    # includes all Flock Safety research
digs/wef/      # includes WEF Columbus research
```

The former `digs/flock-safety/` and `digs/wef-columbus/` roots are retired. Stable StarIntel `_id` values, record-level dataset identifiers, source text, URLs, and historical migration provenance are evidence identities and are not renamed merely because packet directories were canonicalized.

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

## Nim fast path

The checked-in Nimble file builds the performance-critical pipeline. The canonical Nim runtime is checked out by CI at `.starintel-doc-nim`; local development can use the same layout.

```bash
git clone https://github.com/lost-rob0t/starintel-doc.nim .starintel-doc-nim
nimble buildFast
```

Then use:

```bash
nimble validate
nimble validateSite
nimble site
```

`nimble validate` always creates or replaces the root-level **`unverifed`** report. The file lists every canonical document whose `sources` array is empty, including packet path, line number, `_id`, dtype, dataset, and title. Malformed non-empty source references are validation errors. Use `bin/starintel-validate --root . --require-sources` when source-less records must be treated as a hard failure.

The site generator keeps raw canonical JSON plus small index fields in memory. Parsed JSON trees are discarded after indexing and recreated only for the capped graph/node-page subset. Bulk campaign-finance observations stay in JSONL/download surfaces instead of producing hundreds of thousands of tiny HTML/Org files.

## Administrative CLI

The existing Python CLI remains for schema inspection, migration, normalized DB writes, search, and recursive target tooling that has not yet moved into the Nim runtime:

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype relation
python3 scripts/starintel.py schema --output schemas/starintel-doc-v0.9.0.schema.json
python3 scripts/starintel.py jsonld db/org/starintel:org:example.ndjson --pretty
python3 scripts/starintel.py search palantir --dtype org --with-location
python3 scripts/starintel.py select-targets \
  --query palantir \
  --limit 10 \
  --emit-documents \
  --output recursive-targets.jsonl
```

## Full migration

Legacy v0.9 migration still uses the compatibility migrator, then the resulting corpus is validated by the Nim gate:

```bash
python3 scripts/migrate-starintel-v0.9.py --write
nimble validateSite
```

The migration traverses every normalized DB record and dig packet, converts old metadata into the v0.9.0 envelope, enriches existing v0.9 records with deterministic Schema.org defaults, preserves explicit JSON-LD metadata, preserves unrecognized legacy values beneath `extensions.legacy.v0`, rewrites packets as plain canonical JSONL, removes old compressed transport fragments, and emits a migration manifest.

## Mandatory merge gate

Before marking a pull request ready, approving it, enabling auto-merge, or merging it, run:

```bash
nimble buildFast
bin/validate-for-merge --site
```

For dataset-size gates, add explicit topical minimums:

```bash
bin/validate-for-merge --site --topic-minimum gop=100000
```

The Nim gate performs strict v0.9 schema validation over canonical DB and packet transports, emits `unverifed`, validates source-reference shapes, checks JavaScript syntax when Node is available, builds the static site when requested, enforces topic minimums and the Pages content budget, and runs `git diff --check` when a Git checkout is available.

A document PR must not be merged unless the local gate and every required GitHub check pass against the current head commit. A failing, pending, skipped, cancelled, unavailable, stale, or inconclusive check is not success. Keep the PR in draft until fixed.

Never merge invalid documents with a promise to repair them later. Never weaken the schema, broaden `additionalProperties`, or misuse `extensions` merely to admit invalid data.

## Git flow

1. Start from `main`.
2. Create `agent/<description>`.
3. Commit one coherent schema, tooling, or research transaction.
4. Run `nimble buildFast && bin/validate-for-merge --site`.
5. Open a draft pull request into `main`.
6. Mark ready only after the current head passes every check.
7. Squash-merge only when validation is fully green.

Do not publish research packets directly to `main`.
