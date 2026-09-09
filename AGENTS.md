# StarIntel GPT Auto-Dig Agent Instructions

## Non-negotiable authority

The repository-local `starintel_doc/` package and generated `schemas/starintel-doc-v0.9.0.schema.json` are the StarIntel document specification. Never create a parallel JSON shape, a prompt-only “StarIntel style,” a renderer-specific schema, or undocumented fields. The Nim runtime is an implementation of this contract, not an independent schema.

Before creating or changing a document, every agent must inspect the executable schema:

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype <dtype>
```

Strict rules:

1. choose an exact dtype from `starintel_doc.TYPE_FIELDS`;
2. place common metadata only in the v0.9.0 envelope;
3. place dtype-specific metadata only in `data`;
4. use a namespaced `extensions` entry only when the schema cannot represent a value without loss;
5. preserve exact sources, evidence, uncertainty, lineage, and migration provenance;
6. stop immediately when validation fails.

## Required scripted write path

Agents must not hand-write normalized DB records with an editor, heredoc, `cat`, `jq`, shell redirection, or ad hoc Python.

For one normalized record, use the transactional writer:

```bash
python3 scripts/create-db-document.py <dtype> \
  --dataset <dataset> \
  --id <stable-id> \
  --title '<title>' \
  --data @data.json \
  --metadata @metadata.json
```

This script validates the document before writing, writes only to the canonical DB path, validates the complete corpus after writing, and rolls back the write if any invariant fails.

For a batch, create validated JSONL outside `db/`, then import it:

```bash
python3 scripts/starintel.py import records.jsonl
```

Use `--replace` only for an intentional correction or newer version of an existing `_id`. Use `--migrate` only for legacy input that must be normalized first.

`scripts/starintel.py create` may be used to inspect or generate a draft document, but agents must not use `--output db/...`; normalized DB writes must go through `scripts/create-db-document.py` or `scripts/starintel.py import`.

## Database convention

Every normalized document must exist at exactly:

```text
db/<dtype>/<_id>.ndjson
```

The rules are absolute:

- the directory name equals the document's exact `dtype`;
- the filename equals the document's exact `_id` plus `.ndjson`;
- colons in `_id` remain literal;
- path separators are forbidden in `_id`;
- the file contains exactly one compact JSON object;
- the file ends with exactly one newline;
- duplicate normalized `_id` values are forbidden;
- relation endpoint IDs must resolve to normalized DB records, unless the endpoint is explicitly represented by the schema as unresolved.

A completed research pass updates at least one canonical machine-readable surface:

- `digs/<target>/<YYYY-MM-DD>-<slug>/starintel-documents.jsonl`; or
- `db/<dtype>/<_id>.ndjson`.

## Canonical dataset roots

Extend an existing dataset root. Do not create a second root because a company, project, product, alias, or spelling variant has another reasonable name.

Flock Safety research has exactly one canonical packet root:

```text
digs/flock/
```

All new Flock packets must be written beneath `digs/flock/<YYYY-MM-DD>-<slug>/`. Never create `digs/flock-safety/` or any other `digs/flock-*` sibling root. Before creating a new top-level directory under `digs/`, inspect existing roots and reuse the canonical subject root when one exists.

Directory canonicalization does not rename evidence identities. Stable StarIntel IDs such as `starintel:org:flock-safety`, dataset identifiers, source text, URLs, and historical migration provenance retain their evidence-backed values unless a separate identity migration explicitly requires a change.

## Email ingestion invariant

Every imported email artifact must produce the complete typed record set in the same research transaction:

1. a `source` document for the artifact and provenance;
2. an `email-message` document using the executable `email-message` dtype from `starintel_doc`;
3. `person` documents for the sender and every recipient;
4. `person` documents for explicit named people in the message body;
5. links from the email record to the source and person records through stable IDs.

When a displayed name cannot be resolved safely, create a source-scoped unresolved `person` document. Do not guess a legal identity, merge an ambiguous name into an existing person, or omit the person record. Statements in the message body remain attributed claims until independently corroborated.

An email import is not complete when it contains only an image, source record, generic `message`, summary, or investigation target.

## Social-content entity and relation invariant

Social, forum, chat, comment, feed, and other authored-content collection must preserve the graph represented by the source. Collecting content while leaving stable actors and directly observed relationships only as embedded strings is incomplete normalization.

For every collected artifact:

1. every stable observable account, handle, username, platform identifier, author identifier, or other source-backed actor identifier must be materialized as the canonical StarIntel entity/account/persona dtype that the executable schema provides;
2. every collected post, comment, reply, message, or equivalent authored object must link to its observed author entity through stable IDs;
3. every directly observed relationship supported by the source — including authorship, reply/parent relationships, mentions, links, membership/participation, source/community association, and dataset observation — must be materialized as canonical relation records when the executable schema provides a representation;
4. repeated observations of the same stable source identifier must resolve to the same canonical source-scoped entity rather than creating duplicate actors;
5. every entity and relation must preserve the exact source observation, collection provenance, timestamp/run lineage, and uncertainty needed to reproduce why the graph edge or node exists.

A collector must not keep `comment.author = "foo"` or an equivalent scalar while omitting the corresponding canonical entity and authorship relation when the schema supports them. Source-visible identifiers are observations; canonicalizing those observations into entity and relation records is part of ingestion, not a separate optional analysis step.

Entity creation does not by itself assert that two identifiers across different sources belong to the same real-world person. Cross-source candidate links must preserve evidence, confidence, contradictions, and alternate hypotheses, and ambiguous candidates must not be force-merged. When later enrichment confirms additional identity or entity relations, update the graph through the same canonical write/import and provenance path.

A social-content import is not complete when it contains only posts/comments/messages plus embedded usernames but omits the canonical actor/entity nodes or directly observed relations needed to reconstruct the source graph.

## Search and recursive target selection

Use the repository search engine rather than grepping individual records:

```bash
python3 scripts/starintel.py search '<terms>' \
  --dtype relation \
  --predicate founded \
  --with-location
```

After a pass, use the deterministic target selector:

```bash
python3 scripts/starintel.py select-targets \
  --query '<current subject>' \
  --limit 20 \
  --emit-documents \
  --output recursive-targets.jsonl
```

Any emitted target documents must still be imported through the canonical batch importer.

## Mandatory validation and merge gate

Performance-critical validation and site generation are Nim-first. CI checks out `lost-rob0t/starintel-doc.nim` at `.starintel-doc-nim`; local validation should use the same layout.

Before marking a pull request ready, approving it, or merging it, run:

```bash
nimble buildFast
bin/validate-for-merge --site
```

The gate verifies:

- strict v0.9.0 validation of every canonical DB and packet document using the generated repository schema;
- source-reference shape checks;
- creation of root-level `unverifed`, listing every document with an empty `sources` array;
- canonical packet discovery without treating generated partition shards as separate packets;
- JavaScript syntax checks when Node is available;
- full research-site generation through the Nim static-site engine;
- explicit topic minimums when supplied with `--topic-minimum TOPIC=COUNT`;
- the generated Pages content-size budget;
- `git diff --check` when a Git checkout is available.

Use `bin/starintel-validate --root . --require-sources` only when the current task explicitly requires every document to have at least one source. Empty-source records otherwise remain visible in `unverifed` without hiding them or silently dropping them.

## Never merge invalid documents

An agent must never merge, auto-merge, mark ready, or describe a document change as complete when any validation command or required GitHub check is failing, skipped, unavailable, or inconclusive.

If validation fails:

1. leave the pull request in draft state;
2. identify the exact invalid record or invariant;
3. fix or remove the invalid change;
4. rerun the complete merge gate;
5. merge only after the local gate and all required GitHub checks pass.

Do not merge invalid documents with a promise to repair them later. Do not bypass the validator, weaken the schema, add broad `additionalProperties`, or hide invalid values in `extensions` merely to make a check pass.

## Migration and update policy

Legacy records must be migrated with:

```bash
python3 scripts/migrate-starintel-v0.9.py --write
```

The migrator preserves unknown legacy values in `extensions.legacy.v0`; it does not silently discard them. After migration, run the Nim merge gate.

Existing IDs are stable:

- same `_id`, newer integer `version`: intentional replacement;
- same `_id`, same version, changed bytes: documented correction;
- different `_id`: new record;
- deletion: documented reason;
- schema change: migration plus full-corpus validation.

Keep contract ceilings, potential values, obligations, outlays, and recognized revenue as separate fields.

Generated `_site/`, `.generated/`, caches, and bytecode are never committed.
