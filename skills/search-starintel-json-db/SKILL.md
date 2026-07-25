---
name: search-starintel-json-db
description: Search normalized StarIntel NDJSON and dig packet JSONL using the canonical v0.9.0 corpus reader.
---

# Search the StarIntel JSON DB

## Command

```bash
python3 scripts/starintel.py search '<terms>' \
  --dtype <dtype> \
  --dataset <dataset-fragment> \
  --predicate <predicate-fragment> \
  --source <source-fragment> \
  --min-confidence 0.8 \
  --with-location
```

The search traverses both:

- `db/<dtype>/<_id>.ndjson`; and
- `digs/<target>/<run>/starintel-documents.jsonl`.

Results are emitted as JSONL. `--with-location` wraps each record with its path, line, and surface.

## Search strategy

1. Start with the exact entity, predicate, identifier, source URL, or research question.
2. Narrow by dtype when the requested record class is known.
3. Search relations by predicate instead of matching prose.
4. Use `--id` for exact or partial StarIntel IDs.
5. Use `--source` to find all records derived from one filing, article, award, or dataset.
6. Use `--min-confidence` only when the task requires a confidence floor; do not hide lower-confidence contrary records by default.
7. Preserve record paths and IDs in the answer or downstream pass.

## Programmatic API

```python
from pathlib import Path
from starintel_doc import iter_corpus, search_documents

results = search_documents(
    iter_corpus(Path(".")),
    query="palantir lobbying",
    dtypes={"org", "relation", "lobbying-filing"},
)
```

Do not grep compressed legacy packet fragments. The migration converts them to canonical JSONL, and the corpus reader handles any remaining transport during transition.
