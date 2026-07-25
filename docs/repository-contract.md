# Repository contract

## Canonical schema

`starintel_doc/` is the sole schema implementation. `schemas/starintel-doc-v0.9.0.schema.json` is generated from it. Skills, scripts, validators, agents, and renderers may not duplicate the field registry or invent parallel document shapes.

Every producer must inspect the executable schema before creating a dtype:

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype <dtype>
```

Undeclared top-level fields and undeclared dtype-specific `data` fields are invalid.

## Canonical paths

```text
starintel_doc/
schemas/starintel-doc-v0.9.0.schema.json
digs/<target>/<YYYY-MM-DD>-<loop-slug>/starintel-documents.jsonl
db/<dtype>/<_id>.ndjson
manifests/<dataset>.json
reports/<dataset>.md
skills/<skill>/SKILL.md
```

## Required write tools

Normalized DB records may not be created through direct editing, shell redirection, heredocs, `cat`, `jq`, or ad hoc scripts.

Create one record with:

```bash
python3 scripts/create-db-document.py <dtype> \
  --dataset <dataset> \
  --id <stable-id> \
  --data @data.json \
  --metadata @metadata.json
```

The writer validates before the write, writes atomically to the canonical path, validates the complete corpus afterward, and rolls back on failure.

Import a batch with:

```bash
python3 scripts/starintel.py import records.jsonl
```

Use `--replace` only for an intentional correction or newer record version. `scripts/starintel.py create` may generate a draft, but it must not write directly into `db/`.

## Research transaction

A publication is one logical Git transaction containing the applicable combination of validated records, packet material, manifests, generated-schema changes, tests, and documentation. The Git commit is the durable transaction boundary.

## Filename and NDJSON policy

The literal StarIntel `_id` remains the normalized filename, including colons:

```text
db/org/starintel:org:palantir-technologies-inc.ndjson
```

Every normalized record must satisfy:

- directory name equals exact `dtype`;
- filename equals exact `_id` plus `.ndjson`;
- `_id` contains no `/` or `\` path separator;
- exactly one non-empty compact JSON line;
- exactly one terminating newline;
- no duplicate normalized `_id`;
- relation endpoint IDs resolve to normalized records unless the endpoint is explicitly represented by the schema as unresolved.

## Update policy

- same `_id`, newer integer `version`: intentional replacement;
- same `_id`, same version, changed bytes: documented correction;
- different `_id`: new record;
- deletion: documented reason;
- schema change: migration plus full-corpus validation.

## Packet policy

Plain `starintel-documents.jsonl` is canonical. Legacy gzip/base64 and `.parts` transports are migrated to plain JSONL and removed.

## Validation boundary

A record is publishable only when `starintel_doc.validate_document` accepts it. A corpus is publishable only when path consistency, one-record-per-file formatting, duplicate IDs, relation endpoints, tests, generated schema, graph, and site generation pass.

The mandatory merge gate is:

```bash
python3 scripts/validate-for-merge.py --site
```

## Absolute merge prohibition

Never mark a PR ready, approve it, enable auto-merge, or merge it when the merge gate or any required GitHub check is failing, pending, skipped, cancelled, unavailable, stale, or inconclusive.

If validation fails, keep the PR in draft, repair or remove the invalid change, rerun the complete gate, and confirm checks against the current head commit. Invalid documents must never be merged with a promise to fix them later.

Schema constraints may not be weakened, `additionalProperties` may not be broadened, and `extensions` may not be abused merely to make invalid records pass.
