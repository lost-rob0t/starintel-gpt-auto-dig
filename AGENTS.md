# StarIntel GPT Auto-Dig Agent Instructions

## Canonical implementation

The repository-local `starintel_doc/` package is the only StarIntel document specification. Never create a parallel JSON shape, “StarIntel style,” prompt-only schema, validator-specific schema, or renderer-specific schema.

All agents must:

1. select a dtype from `starintel_doc.TYPE_FIELDS`;
2. place common metadata in the v0.9.0 envelope;
3. place dtype-specific metadata in `data`;
4. place unavoidable noncanonical metadata in a namespaced `extensions` entry;
5. validate before writing;
6. preserve exact sources, evidence, uncertainty, lineage, and migration provenance.

## Required output

Every completed research pass updates at least one canonical machine-readable surface:

- `digs/<target>/<date>-<slug>/starintel-documents.jsonl`; or
- `db/<dtype>/<_id>.ndjson`.

A normalized NDJSON file contains exactly one compact JSON object and one terminating newline. `dtype` must equal its directory and `_id` must equal its filename without `.ndjson`.

## Document creation

Use:

```bash
python3 scripts/starintel.py create <dtype> --dataset <dataset> --data '<json>'
```

or import `starintel_doc.Document`. Do not manually invent fields. Query the schema first when uncertain:

```bash
python3 scripts/starintel.py schema --dtype <dtype>
```

## Search

Use the repository search engine instead of grepping individual files when selecting evidence:

```bash
python3 scripts/starintel.py search '<terms>' --dtype relation --predicate founded --with-location
```

Search results are JSONL and may be piped into other tools.

## Recursive target selection

Use the deterministic selector after a pass:

```bash
python3 scripts/starintel.py select-targets \
  --query '<current subject>' \
  --limit 20 \
  --emit-documents \
  --output recursive-targets.jsonl
```

The selector scores referenced entities, graph degree, source/evidence coverage, analytical metadata, and unresolved gaps. It emits schema-valid `investigation-target` documents with selection provenance and recursion depth.

## Validation

Run all checks before publication:

```bash
python3 -m compileall -q starintel_doc scripts
python3 -m unittest discover -s tests -v
python3 scripts/starintel.py schema --output schemas/starintel-doc-v0.9.0.schema.json
python3 scripts/validate-db.py
python3 scripts/build_research_site.py --input digs --db db --output _site --org-output .generated/org
```

Generated `_site/`, `.generated/`, caches, and bytecode are never committed.

## Migration and updates

Legacy records must be migrated with `scripts/migrate-starintel-v0.9.py --write`. The migrator preserves unknown legacy values in `extensions.legacy.v0`; it does not silently discard them.

Existing IDs are stable. Replace an existing `_id` only for an intentional correction or newer record version. Keep contract ceilings, potential value, obligations, outlays, and recognized revenue as separate fields.
