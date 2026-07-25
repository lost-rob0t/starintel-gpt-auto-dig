---
name: create-starintel-documents
description: Create and update StarIntel records only through the repository scripts and the strict starintel_doc v0.9.0 schema.
---

# Create StarIntel Documents

## Authority

`starintel_doc/` is authoritative. Never infer fields from examples, old packets, renderer code, prose, or model memory.

Inspect the executable schema before creating a record:

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype <dtype>
```

## Required single-record workflow

Prepare dtype-specific data and common metadata as JSON objects, then use the transactional DB writer:

```bash
python3 scripts/create-db-document.py relation \
  --dataset <dataset> \
  --id starintel:relation:<stable-slug> \
  --title '<title>' \
  --data @relation-data.json \
  --metadata @common-metadata.json
```

The script:

1. creates the document through `Document.create`;
2. validates it against the executable v0.9.0 schema;
3. writes it only to `db/<dtype>/<_id>.ndjson`;
4. uses compact one-line JSON plus a terminating newline;
5. validates the complete repository after the write;
6. rolls the write back if schema, path, duplicate-ID, or relation-endpoint validation fails.

Never bypass this script with direct file editing, heredocs, `cat`, `jq`, shell redirection, or ad hoc Python.

## Required batch workflow

For multiple documents, create a temporary JSONL file outside `db/`, validate each record, and import it through:

```bash
python3 scripts/starintel.py import records.jsonl
```

Use:

```bash
python3 scripts/starintel.py import records.jsonl --replace
```

only for an intentional correction or newer version. Use `--migrate` only for legacy input.

`scripts/starintel.py create` is a draft-generation and inspection tool. Do not use it to write directly into `db/`. Canonical DB writes go through `scripts/create-db-document.py` or `scripts/starintel.py import`.

## Database convention

Every normalized record must satisfy all of these rules:

```text
db/<dtype>/<_id>.ndjson
```

- directory equals exact `dtype`;
- filename equals exact `_id` plus `.ndjson`;
- colons remain literal;
- `_id` contains no path separators;
- exactly one non-empty JSON line;
- exactly one terminating newline;
- no duplicate normalized `_id`;
- relation endpoint IDs resolve to normalized records unless represented as explicitly unresolved schema objects.

## Schema procedure

1. Choose an exact dtype from `python3 scripts/starintel.py types`.
2. Inspect `python3 scripts/starintel.py schema --dtype <dtype>`.
3. Reuse a stable `_id` only for an intentional update.
4. Put common metadata only in the canonical envelope.
5. Put dtype-specific values only in `data`.
6. Attach exact source and evidence records.
7. Separate observations, claims, analysis, events, and investigation targets into their own documents.
8. Create explicit `relation` documents for graph edges.
9. Use namespaced `extensions` only when the schema cannot represent a value without loss.
10. Run the mandatory merge gate.

## Mandatory merge gate

Before a document change can be marked ready or merged:

```bash
python3 scripts/validate-for-merge.py --site
```

All required GitHub checks must also pass.

## Hard failures

Stop rather than write, publish, mark ready, or merge when:

- a top-level key is undeclared;
- a `data` key is undeclared for the dtype;
- a relation lacks `subject`, `predicate`, or `object`;
- a relation endpoint ID does not resolve;
- an exact source URL or retrieval record is missing for a sourced claim;
- a score is outside `0.0..1.0`;
- an update changes identity without a new `_id`;
- the DB path differs from `db/<dtype>/<_id>.ndjson`;
- the file is not one compact JSON line plus one newline;
- any local validation or GitHub check fails, is skipped, is unavailable, or is inconclusive.

Never merge invalid documents with a plan to repair them later. Never weaken the schema, broaden `additionalProperties`, or misuse `extensions` merely to pass validation.
