# StarIntel v0.9 field expansion and synchronization plan

## Decision

StarIntel v0.9 remains the active compatibility family while StarLang is not usable as the schema compiler. The source of truth is currently:

1. the executable Python registry;
2. the immutable v0.9 base JSON Schema;
3. the portable expansion registry;
4. the revision manifest and canonical-JSON hash;
5. shared conformance vectors.

Other runtimes materialize the expanded schema from the same bundle. StarLang can later replace the Python registry as the compiler without becoming a runtime dependency.

This change is additive:

- existing valid v0.9 documents remain valid;
- newly created documents include an exact `schema_revision`;
- every registered dtype receives shared identity, linkage, provenance, lifecycle, and facet fields;
- every registered dtype receives an explicit dtype-specific expansion;
- strict rejection of undeclared fields remains in force;
- the complete corpus does not need a mass rewrite merely to adopt this revision.

## Current-state findings

The original v0.9 work fixed the largest structural problem: incompatible top-level document shapes. It established one strict envelope, one dtype registry, lossless legacy migration, and a validated repository writer.

The remaining problems were inside the dtype layer:

1. The registry contains 49 dtypes, but only eight have required `data` fields. Most objects can validate with semantically thin `data`.
2. Many complex fields are unrestricted JSON maps or arrays of unrestricted objects, including services, DNS records, HTTP exchanges, reactions, contract modifications, docket entries, findings, actor configuration, and manifest files.
3. Several dtypes shared field dictionaries even though their semantics differ. Meetings, procurements, grants, location variants, and both manifest types require distinct fields.
4. `_id` identifies a record, but the exact schema contract used to emit it was not recorded.
5. Provenance did not fully distinguish the collected entity, the generating activity, and the responsible agent.
6. Relations lacked predicate namespace, endpoint dtype and role, asserting agent, explicit evidence links, negation, and statement identity.
7. Cross-runtime synchronization depended on a mutable schema URL rather than an immutable compatibility base plus a revisioned, hashed expansion.
8. Structural validation existed, but semantic checks such as endpoint existence, temporal ordering, identifier normalization, amount basis, and percentage basis remain incomplete.

## Compatibility version and revision

`schema_version` identifies the compatibility family:

```text
0.9.0
```

`schema_revision` identifies the exact additive contract:

```text
0.9.0+fields.20260725.1
```

The synchronized bundle is:

```text
schemas/starintel-doc-v0.9.0.schema.json
schemas/starintel-doc-v0.9.0.expansion.json
schemas/starintel-doc-v0.9.0.manifest.json
```

The base schema is the immutable v0.9 compatibility contract. The expansion registry records common fields, explicit fields for all 49 dtypes, field-kind metadata, and additions to provenance, lineage, verification, and the top-level envelope. The manifest records version, revision, profile, dtype count, and the canonical-JSON SHA-256 of the expansion registry.

A runtime must reject a bundle whose version, revision, profile, dtype count, or hash does not reconcile. A runtime may accept a v0.9 record without `schema_revision` for backward compatibility, but every newly emitted record must include it.

## Shared typed records

The expansion introduces reusable records for:

- document and external references;
- money and measurements;
- status changes;
- role assignments;
- facets;
- collection or processing actions;
- network interfaces and services;
- certificates and DNS records;
- HTTP exchanges;
- message reactions;
- contract modifications;
- docket entries;
- research findings;
- manifest files;
- executable query specifications.

Legacy unrestricted fields remain valid. New typed companion fields create a migration path without invalidating the corpus.

## Universal data fields

Every dtype supports:

- `canonical_key` and `display_label`;
- status history and validity intervals;
- explicit source-record and evidence-record references;
- external references;
- role assignments;
- object markings;
- typed facets;
- supersession links;
- namespaced attributes.

This is not an unrestricted universal object. Dtype-specific fields remain authoritative, and undeclared fields remain invalid.

## Facets

A facet is a typed, versioned subobject with its own source, evidence, and confidence links. Facets let specialized datasets extend a record without adding every experimental field to the core schema.

Promote a facet field into the core registry only when it is stable, broadly interoperable, and query-critical.

## Provenance

The provenance object gains:

- `activity_id`;
- `agent_ids`;
- `used_ids`;
- `generated_by`;
- derivation and attribution links;
- association links;
- `plan_id`;
- typed action records.

This keeps the source entity, extraction or transformation activity, and performing actor independently addressable.

## Relationship statements

Relations gain:

- statement identity;
- predicate identifier and namespace;
- subject and object dtype;
- subject and object role;
- asserting agents;
- supporting and contradicting evidence;
- negation, symmetry, and transitivity flags;
- typed qualifier records.

The preferred canonical form remains one subject, one predicate, and one object per relation document. Array-valued legacy endpoints remain valid for compatibility, but new writers should emit separate relations unless a true hyperedge is represented through a facet.

## Dtype expansion matrix

| Family | Added coverage |
|---|---|
| Core identity | canonical identity, duplicate resolution, status history, roles, external references, facets |
| Person and organization | offices, memberships, ownership, governance, filings, contracts, grants, lobbying, campaign finance, financial observations |
| Relations and targets | predicate vocabularies, endpoint typing, assertion and evidence, query plans, dependencies, completion and stop conditions |
| Network and web | typed interfaces, services, certificates, DNS records, HTTP exchanges, capture and archive links |
| Location and contact | normalized contact values, geometry, accuracy, containment, providers, accounts, validity |
| Messaging and social | actor and recipient references, conversations, quotes and replies, reactions, attachments, captures, engagement observations |
| Research | propositions, measurements, findings, actions, query plans, outputs, uncertainty, reviews |
| Finance and institutions | typed money, amount basis, transactions, awards, modifications, line items, party roles, legal dockets, policy versions |
| Operations | actor dependencies and routing, dataset version manifests, alert lifecycle, task dependencies and attempts |
| Files and evidence | multiple hashes, derivation, capture and custody actions, exact and normalized content, storage and quarantine state |

## Validation layers

### JSON Schema validation

The materialized schema enforces:

- declared top-level and dtype-specific fields;
- reusable nested record shapes;
- required primitive fields inside typed records;
- score bounds;
- date-time formats;
- exact schema revision when present.

### Repository semantic validation

The repository validator should add, incrementally:

1. relation endpoint existence and dtype agreement;
2. start/end and valid-from/valid-to ordering;
3. deterministic identity collisions and duplicate identity keys;
4. currency, country, jurisdiction, and identifier-scheme vocabularies;
5. percentages with an explicit basis and valid range;
6. contract amount reconciliation by basis rather than silent summation;
7. document references constrained to expected dtype families;
8. revoked, deleted, and tombstone lifecycle invariants;
9. manifest count, version, revision, and hash reconciliation;
10. source, evidence, and content-hash reconciliation.

### Cross-runtime conformance

Every maintained runtime should execute the same vectors:

- minimal valid document for every dtype;
- expanded valid document for every dtype;
- undeclared-field rejection;
- invalid score and timestamp rejection;
- relation endpoint variants;
- old v0.9 document without `schema_revision`;
- new v0.9 document with the current revision;
- expansion hash match and mismatch;
- deterministic identity vectors;
- migration fixtures from v0.8 and earlier JavaScript shapes.

## Runtime synchronization contract

### Canonical Python package

The Python package owns the executable dtype registry, expansion materialization, migrations, repository validation, and canonical conformance fixtures. The portable JSON registry must be tested against the executable registry.

### JavaScript package

`starintel_doc.js` now:

- loads the immutable base schema, expansion registry, and manifest;
- verifies the canonical expansion hash;
- materializes the expanded schema locally;
- preserves the strict Schema.org JSON-LD layer;
- exports version, revision, profile, hash, dtypes, and dtype field names;
- stamps new documents with revision and profile metadata;
- supports deterministic identity inputs with random fallback;
- separates raw validation from normalization;
- verifies its local bundle without a network request during package installation.

### Common Lisp, Nim, and server runtimes

Until StarLang generates bindings, these runtimes should consume the same three-file bundle. Hand-maintained classes are convenience APIs, not independent schema authorities.

Each runtime must expose:

- schema version;
- schema revision;
- schema hash;
- supported dtypes;
- dtype field inventory;
- raw validation;
- normalization;
- deterministic identity construction;
- conformance-vector execution.

## StarLang handoff

StarLang should eventually compile the registry, facets, semantic constraints, and migration mappings into JSON Schema and language bindings. It should not become mandatory for reading or validating StarIntel records.

The stable handoff boundary is:

1. v0.9 base schema plus revisioned expansion and manifest remain the interchange contract;
2. conformance vectors define runtime behavior;
3. StarLang later replaces the Python registry as compiler input;
4. generated artifacts and public runtime APIs remain compatible.

## Rollout

1. Merge the additive canonical expansion bundle.
2. Merge the JavaScript v0.9 runtime after it passes bundle and dtype conformance.
3. Publish shared conformance fixtures from the canonical repository.
4. Port bundle materialization to Common Lisp, Nim, and the server.
5. Add semantic validators in corpus-safe increments.
6. Convert the old standalone v0.8 Python package into a compatibility shim or deprecate it.
7. Freeze the v0.9 compatibility family after every maintained runtime reports the same revision and expansion hash.

## External design references

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- OASIS STIX 2.1: https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html
- OASIS TAXII 2.1: https://docs.oasis-open.org/cti/taxii/v2.1/taxii-v2.1.html
- CASE/UCO: https://caseontology.org/ and https://unifiedcyberontology.org/
