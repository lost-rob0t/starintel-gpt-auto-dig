# StarIntel v0.9 field expansion and synchronization plan

## Decision

StarIntel v0.9 remains the active compatibility family while StarLang is not usable as the schema compiler. The immediate source of truth is executable Python plus generated JSON Schema Draft 2020-12. Every other runtime consumes the generated schema, its manifest, and shared conformance fixtures.

This change is additive:

- existing valid v0.9 documents remain valid;
- newly created documents include an exact `schema_revision`;
- every registered dtype receives shared identity, linkage, provenance, lifecycle, and facet fields;
- every registered dtype receives an explicit dtype-specific expansion;
- strict rejection of undeclared fields remains in force;
- the complete corpus does not need to be rewritten merely to adopt this revision.

## Current-state findings

The original v0.9 work fixed the largest structural problem: incompatible top-level document shapes. It established one strict envelope, one dtype registry, a generated schema, lossless legacy migration, and a validated repository writer.

The remaining issues are inside the dtype layer:

1. The registry contains 49 dtypes, but only eight have required `data` fields. Most objects can therefore validate with semantically empty `data`.
2. Many complex fields are unrestricted JSON maps or arrays of unrestricted objects. Examples include network services, DNS records, HTTP forms, message reactions, contract modifications, legal docket entries, research findings, actor configuration, and manifest files.
3. Several dtypes share a field dictionary even though their semantics differ. `event` and `meeting`, `contract` and `procurement`, location variants, and the two manifest types need distinct fields.
4. Object identity is stable at `_id`, but the exact schema contract used to create or validate a record is not recorded.
5. Provenance is a flat metadata object. It does not fully distinguish the collected entity, the activity that generated it, and the agent that performed the activity.
6. Relationship documents are expressive but underspecified. Predicate namespace, endpoint dtype, assertion agent, evidence links, negation, and statement identity are absent.
7. Cross-runtime synchronization relies on a mutable branch URL rather than a content fingerprint and conformance vectors.
8. The schema is structurally strict but lacks many semantic checks: temporal ordering, currency and country-code vocabularies, endpoint existence, identifier normalization, percentage basis, and amount basis.

## Architecture

### 1. Compatibility version and immutable revision

`schema_version` identifies the compatibility family: `0.9.0`.

`schema_revision` identifies the exact additive contract: `0.9.0+fields.20260725.1`.

The generated manifest records:

- schema version and revision;
- profile and profile version;
- SHA-256 of the generated schema;
- source commit;
- dtype list;
- field count for each dtype.

A runtime must reject a configured expected hash that does not match the materialized schema. A runtime may accept a v0.9 document without `schema_revision` for backward compatibility, but every newly emitted document must include it.

### 2. Shared typed records

The expansion introduces reusable records for:

- document references;
- external references;
- money and measurement values;
- status changes;
- role assignments;
- facets;
- collection or processing actions;
- network services and interfaces;
- certificates and DNS records;
- HTTP exchanges;
- message reactions;
- contract modifications;
- docket entries;
- research findings;
- manifest files;
- executable query specifications.

Legacy unrestricted fields remain accepted. New typed companion fields provide a migration path without invalidating the corpus.

### 3. Universal data fields

Every dtype now supports:

- `canonical_key` and `display_label`;
- status history and validity interval;
- explicit references to source and evidence records;
- external references;
- role assignments;
- object markings;
- typed facets;
- supersession links;
- namespaced attributes.

This does not turn all objects into one universal bag. Dtype-specific fields remain authoritative, and undeclared fields remain invalid.

### 4. Facets instead of unbounded dtype growth

A facet is a typed, versioned subobject with its own source and evidence links. Facets allow specialized communities or future StarLang profiles to extend a record without adding every possible field to the core object.

Core fields should be added when they are broadly interoperable and query-critical. Specialized fields should be expressed as a named facet until they are stable enough to promote into the core registry.

### 5. Provenance as entity, activity, and agent

The provenance object gains:

- `activity_id`;
- `agent_ids`;
- `used_ids`;
- `generated_by`;
- derivation and attribution links;
- association links;
- `plan_id`;
- typed action records.

This permits a source record, an extraction activity, and the actor or tool that performed it to remain independently addressable.

### 6. Relationship statements

Relations gain:

- statement identity;
- predicate identifier and namespace;
- source and target dtype;
- source and target role;
- asserting agents;
- supporting and contradicting evidence;
- negation, symmetry, and transitivity flags;
- typed qualifier records.

The preferred canonical form remains one subject, one predicate, and one object per relation document. Existing array-valued objects remain valid for compatibility, but new writers should emit separate relation documents unless the relation is explicitly modeled as a hyperedge facet.

### 7. Distinct semantic objects

The expansion separates previously shared shapes:

- meetings receive chair, attendee-role, agenda, minutes, decision, and action-item fields;
- procurements receive stage, notice, competition-exception, evaluation, and source-system fields;
- grants receive recipient, program, assistance-listing, matching, performance, objective, and reporting fields;
- actor manifests receive implementation, routing, dependency, capability, configuration, and health fields;
- dataset manifests receive versioned document references, file records, schema revision, profile, sync cursor, and validation state.

## Dtype expansion matrix

| Family | Added coverage |
|---|---|
| Core identity | canonical identity, duplicate resolution, status history, roles, external references, facets |
| Person and organization | offices, memberships, ownership, governance, filings, contracts, grants, lobbying, campaign finance, financial observations |
| Relations and targets | predicate vocabularies, endpoint typing, assertion/evidence, query plans, dependencies, completion and stop conditions |
| Network and web | typed interfaces, services, certificates, DNS records, HTTP exchanges, capture and archive links |
| Location and contact | normalized contact values, geometry, accuracy, containment, providers, account links, validity |
| Messaging and social | actor/recipient references, conversations, quotes/replies, reactions, attachments, capture and engagement observations |
| Research | structured propositions, measurements, findings, actions, query plans, outputs, uncertainty, reviews |
| Finance and institutions | typed money, amount basis, transactions, awards, modifications, line items, party roles, legal dockets and policy versions |
| Operations | actor dependencies and routing, dataset version manifests, alert lifecycle, task dependencies and attempts |
| Files and evidence | multiple hashes, derivation, capture actions, custody actions, exact and normalized content, storage and quarantine state |

## Validation layers

### JSON Schema validation

The generated schema enforces:

- declared top-level and dtype-specific fields;
- reusable nested record shapes;
- required primitive fields for typed nested objects;
- score bounds;
- date-time formats;
- exact schema revision when present.

### Repository semantic validation

The repository validator should incrementally add checks that are awkward or impossible in JSON Schema:

1. relation endpoint existence and endpoint dtype agreement;
2. start/end and valid-from/valid-to ordering;
3. unique identifiers and deterministic identity-key collisions;
4. currency, country, jurisdiction, and identifier-scheme vocabularies;
5. percentages with an explicit basis and permitted range;
6. contract amount reconciliation by basis rather than silent summation;
7. document references constrained to expected dtype families;
8. revoked, deleted, and tombstone lifecycle invariants;
9. manifest record count, per-dtype count, version, and content-hash reconciliation;
10. source/evidence references and content hashes.

### Cross-runtime conformance

All maintained runtimes should execute the same vectors:

- minimal valid document for every dtype;
- expanded valid document for every dtype;
- undeclared-field rejection;
- invalid score and timestamp rejection;
- relation endpoint variants;
- old v0.9 document without `schema_revision`;
- new v0.9 document with the current revision;
- manifest hash match and mismatch;
- migration fixtures from v0.8 and earlier JavaScript shapes.

## Runtime synchronization contract

### Canonical Python package

The Python package owns:

- dtype and field registry;
- generated JSON Schema;
- schema manifest and hash;
- migration logic;
- corpus and semantic validation;
- conformance vectors.

### JavaScript package

`starintel_doc.js` should:

- materialize both schema and manifest;
- verify SHA-256 before replacing its local schema;
- export schema version, revision, profile, dtypes, and field names;
- stamp new documents with the revision and profile;
- use deterministic IDs when identity inputs are supplied;
- retain random IDs only as an explicit fallback;
- validate strict raw documents separately from normalization;
- run the shared conformance vectors;
- avoid a mandatory network fetch during ordinary package installation.

### Common Lisp, Nim, and server runtimes

Until StarLang can generate bindings, these runtimes should consume the same schema artifact and manifest. Hand-maintained model classes should be treated as convenience APIs, not independent schema authorities.

Each runtime must expose at least:

- `schema-version`;
- `schema-revision`;
- `schema-hash`;
- `supported-dtypes`;
- raw validation;
- normalization;
- deterministic identity construction;
- conformance-vector execution.

## StarLang handoff

StarLang should eventually compile the registry, facets, semantic constraints, and migration mappings into JSON Schema and language bindings. It should not become a required runtime dependency for document validation.

The handoff boundary is therefore stable:

1. v0.9 JSON Schema and manifest remain the interchange contract;
2. conformance vectors define behavior;
3. StarLang later replaces the Python registry as the compiler input;
4. generated artifacts and runtime APIs remain compatible.

## Rollout

1. Merge the additive canonical expansion and generated schema manifest.
2. Update the open JavaScript v0.9 PR to verify and expose the manifest revision.
3. Add shared conformance vectors and make Python and JavaScript pass them.
4. Port the artifact/manifest contract to Common Lisp, Nim, and the server.
5. Add repository semantic validators in small, corpus-safe increments.
6. Deprecate the old standalone v0.8 Python package or turn it into a compatibility shim that imports the canonical v0.9 implementation.
7. Freeze the v0.9 compatibility family after all maintained runtimes report the same schema hash.

## External design references

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- OASIS STIX 2.1: https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html
- OASIS TAXII 2.1: https://docs.oasis-open.org/cti/taxii/v2.1/taxii-v2.1.html
- CASE/UCO: https://caseontology.org/ and https://unifiedcyberontology.org/
