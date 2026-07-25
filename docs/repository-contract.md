# Repository contract

## Canonical schema

`starintel_doc/` is the sole schema implementation. `schemas/starintel-doc-v0.9.0.schema.json` is generated from it. Skills and scripts may not duplicate the field registry.

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

## Research transaction

A publication is one logical Git transaction containing the applicable combination of validated records, a packet README/report, manifests, generated-schema changes, and tests. The Git commit is the durable transaction boundary.

## Filename policy

The literal StarIntel `_id` remains the normalized filename, including colons:

```text
db/org/starintel:org:palantir-technologies-inc.ndjson
```

## Update policy

- same `_id`, newer integer `version`: intentional replacement;
- same `_id`, same version, changed bytes: documented correction;
- different `_id`: new record;
- deletion: documented reason;
- schema change: migration plus full-corpus validation.

## Packet policy

Plain `starintel-documents.jsonl` is canonical. Legacy gzip/base64 and `.parts` transports are migrated to plain JSONL and removed.

## Validation boundary

A record is publishable only when `starintel_doc.validate_document` accepts it. A corpus is publishable only when path consistency, duplicate IDs, relation endpoints, tests, generated schema, graph, and site generation pass.
