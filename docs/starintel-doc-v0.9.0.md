# StarIntel Document Specification v0.9.0

## Status

This is the auto-dig fork of `starintel_doc` 0.8.2. It replaces multiple incompatible document shapes with one strict, metadata-rich envelope and a dtype registry.

## Design rules

- One implementation: `starintel_doc/`.
- One current schema version: `0.9.0`.
- No undeclared top-level keys.
- No undeclared dtype-specific keys inside `data`.
- Exact evidence and provenance survive migration.
- Unknown legacy values are retained beneath `extensions.legacy.v0`.
- Record identity and record revision are separate: `_id` is stable; `version` is an integer revision.
- All timestamps are ISO-8601 date-times.
- Confidence-like scores use `0.0..1.0`.

## Common envelope

| Field | Purpose |
|---|---|
| `_id`, `_rev` | Stable identity and optional CouchDB revision |
| `dataset`, `dtype`, `schema_version`, `version` | Dataset and schema identity |
| `date_added`, `date_updated` | Record lifecycle timestamps |
| `title`, `summary`, `description`, `status`, `language` | Human-readable identity and state |
| `tags`, `labels`, `aliases`, `keywords` | Discovery metadata |
| `identifiers` | Typed external identifiers |
| `sources` | Source provenance, retrieval, credibility, hashes, locators, licenses |
| `evidence` | Evidence excerpts, observations, custody, corroboration, contradiction |
| `temporal` | Observation, publication, validity, event, and first/last-seen time |
| `provenance` | Collector, agent, skill, tool, model, run, import, transform, original schema |
| `assessment` | Confidence, relevance, threat, impact, uncertainty, bias, gaps, alternatives |
| `verification` | Verification state, methods, reviewers, conflicts, unresolved checks |
| `handling` | Visibility, classification, compartments, retention, PII, redactions |
| `lineage` | Parents, children, derivation, supersession, merge/split, migration |
| `quality` | Completeness, consistency, timeliness, accuracy, coverage, validation |
| `workflow` | Queue, priority, assignment, recursion, selection score and reasons |
| `geospatial` | Coordinates, accuracy, address, jurisdiction, timezone |
| `attachments` | Media/file metadata and hashes |
| `related_ids`, `notes` | Explicit links and analyst notes |
| `data` | Strict dtype-specific object |
| `extensions` | Namespaced forward-compatibility and lossless legacy preservation |

## Canonical dtypes

The registry covers the original package types and the later auto-dig corpus:

- Core: `document`, `entity`, `person`, `org`, `relation`, `target`, `investigation-target`.
- Network/web: `domain`, `network`, `host`, `url`.
- Location/contact: `geo`, `address`, `location`, `phone`, `email`, `email-message`.
- Social: `user`, `message`, `social-media-post`.
- Research: `source`, `evidence-record`, `claim`, `observation`, `analysis`, `concept`, `research-pass`.
- Institutional/economic: `product`, `event`, `meeting`, `financial-observation`, `contract`, `procurement`, `grant`, `lobbying-filing`, `campaign-finance`, `legal-case`, `policy`, `education`, `employment`, `ownership`, `asset`.
- Operations: `actor-manifest`, `dataset-manifest`, `alert`, `task`, `media`, `file`, `breach`.

The executable registry in `starintel_doc/spec.py` is authoritative. The generated `schemas/starintel-doc-v0.9.0.schema.json` is derived from it and must not be edited independently.

## Relations

Relations use `data.subject`, `data.predicate`, and `data.object`. Endpoints may be StarIntel IDs or endpoint objects with `id`, `dtype`, `label`, `role`, and qualifiers. Relation metadata includes direction, inverse predicate, weight, confidence, validity, active state, and qualifiers.

## Recursive targets

`investigation-target` documents capture the selected target, target type, seed records, scope, research question, hypotheses, source preferences, recursion depth, maximum depth, selection score, reasons, queue state, and next-run metadata.

## Migration

The v0.9 migrator recognizes:

- the original 0.8.x package fields;
- ad hoc `source`, `time`, `analysis`, `opsec`, and `entity` objects;
- camelCase fields from `dataclasses-json`;
- later auto-dig dtypes absent from 0.8.2;
- compressed packet transport forms.

It normalizes timestamps and scores, moves dtype data into `data`, converts source/evidence records, preserves original schema/path in provenance and lineage, and retains unknown values in `extensions.legacy.v0`.
