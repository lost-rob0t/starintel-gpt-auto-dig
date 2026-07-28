# StarIntel v0.9 Schema.org metadata

StarIntel v0.9 documents may carry a declared `schema_org` JSON-LD block alongside the canonical evidence and workflow envelope.

## Default JSON-LD identity

Constructors emit:

```json
{
  "schema_org": {
    "@context": "https://schema.org/",
    "@type": "Organization",
    "@id": "starintel:org:example",
    "additionalType": "https://starintel.dev/dtype/org"
  }
}
```

The `@type` value is selected deterministically from the canonical dtype. The mapping covers all 49 v0.9 dtypes and is guarded against schema drift.

## Declared metadata

The block supports identity, aliases, URLs, identifiers, agents, organizations, places, events, dates, citations, licensing, media, actions, and structured `PropertyValue` records. Vocabulary not yet promoted to a direct declared field belongs in `additionalProperty` or the namespaced `properties` object. The StarIntel top-level envelope and dtype-specific `data` objects remain strict.

## JSON-LD export

```bash
python3 scripts/starintel.py jsonld db/org/starintel:org:example.ndjson --pretty
```

`to_schema_org()` projects envelope fields, identifiers, related IDs, geospatial metadata, and dtype-specific names or URLs into a Schema.org JSON-LD object while preserving explicit `schema_org` overrides.

## Corpus migration

```bash
python3 scripts/migrate-starintel-v0.9.py --write
python3 scripts/validate-for-merge.py --site
```

The migration is idempotent. Existing v0.9 records are enriched with deterministic Schema.org defaults without replacing explicit JSON-LD metadata, changing `_id`, or altering evidence.
