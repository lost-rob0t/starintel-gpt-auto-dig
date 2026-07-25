---
name: create-starintel-documents
description: Create and update StarIntel auto-dig records exclusively through the repository-local starintel_doc v0.9.0 schema.
---

# Create StarIntel Documents

## Authority

`starintel_doc/` is authoritative. Never infer fields from examples, old packets, renderer code, or prose. Inspect the executable schema before generating a dtype:

```bash
python3 scripts/starintel.py schema --dtype <dtype>
```

## Procedure

1. Choose an exact dtype from `python3 scripts/starintel.py types`.
2. Create a stable `_id` or reuse the existing identity.
3. Put common metadata only in the canonical envelope.
4. Put dtype-specific values only in `data`.
5. Attach exact source and evidence records.
6. Separate observations, claims, analysis, and targets into their own documents.
7. Create explicit `relation` documents for graph edges.
8. Validate before writing.

Use the CLI:

```bash
python3 scripts/starintel.py create relation \
  --dataset <dataset> \
  --id <stable-id> \
  --title <title> \
  --data @relation-data.json \
  --metadata @common-metadata.json \
  --output /tmp/relation.ndjson
```

Or use Python:

```python
from starintel_doc import Document

record = Document.create(
    "org",
    dataset,
    doc_id=doc_id,
    title=title,
    data={"name": name, "org_type": org_type},
    sources=sources,
    evidence=evidence,
    assessment=assessment,
)
```

## Hard failures

Stop rather than publish when:

- a top-level key is not declared;
- a `data` key is not declared for the dtype;
- a relation lacks `subject`, `predicate`, or `object`;
- an exact source URL or retrieval record is missing for a sourced claim;
- a score is outside `0.0..1.0`;
- an update changes identity without creating a new `_id`;
- validation fails.

Use a namespaced `extensions` entry only when the schema cannot represent a value without loss. Do not use extensions as a substitute for selecting the correct dtype or field.
