# StarIntel schema release versioning

## Current authority

As of this document revision:

- current StarIntel **release/profile version**: `0.9.1`
- immutable v0.9 **base/wire schema version**: `0.9.0`
- next additive release for schema/profile changes: **`0.9.2`**

These numbers are intentionally allowed to differ. The file name
`schemas/starintel-doc-v0.9.0.schema.json` identifies the immutable base schema
family; it does **not** tell you the current StarIntel release.

## The rule agents must follow

Never infer the current StarIntel release from:

- a schema filename;
- `schema_version` alone;
- an issue title/body;
- an old research note;
- a README sentence;
- a remembered version number.

The current release is the canonical bundle's `release_version`, and consumer
repositories must resolve it from their schema lock.

### In the canonical schema repository

Run:

```bash
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
```

`current` reports all distinct version dimensions, for example:

```text
release=0.9.1 profile=0.9.1 base_schema=0.9.0 ... next=0.9.2
```

When someone asks "what is the current StarIntel spec/version?", report
`release_version` (`0.9.1` currently), not the base schema filename/version.

### In a consumer repository

Read `schema/starintel-schema.lock.json` first. The lock is an immutable pointer
containing at least:

```text
release_version
schema_version
canonical_repository
canonical_commit
schema_path
expansion_path
manifest_path
```

Then verify the manifest at `canonical_repository@canonical_commit` and require:

```text
manifest.release_version == lock.release_version
manifest.schema_version  == lock.schema_version
```

If the repository has a lock checker/sync command, use it. Do not replace that
workflow with hand-edited copies of schema files.

## Bumping an additive release

Version changes are scripted. Do not use `sed`, search/replace, or hand-edit the
release/profile fields.

For the next approved additive release:

```bash
python3 scripts/schema-release.py bump --to 0.9.2 --dry-run
python3 scripts/schema-release.py bump --to 0.9.2
python3 scripts/schema-release.py check
```

The bump command only accepts the next patch release. From `0.9.1`, the only
accepted additive bump is `0.9.2`.

The script updates release/profile metadata while deliberately leaving the
immutable v0.9.0 base-schema identity alone. A new base schema version requires
a separate explicit compatibility/migration decision; do not get one merely by
renaming files.

After the canonical release is merged and green:

1. record the exact canonical commit;
2. repin each consumer's `schema/starintel-schema.lock.json` through that
   repository's existing schema sync/lock workflow;
3. run each binding repository's existing release/sync script rather than
   hand-editing copied schema bundles or package versions;
4. run cross-language conformance;
5. only then describe consumers as supporting the new release.

## Binding and consumer rule

A binding's package version and the canonical release version are related but
not interchangeable. `conformance/implementations.json` records the actual
released binding versions. The canonical schema bump script does not fabricate
new binding releases.

## Failure policy

Fail closed when:

- the lock is missing;
- `release_version` is missing;
- lock and canonical manifest disagree;
- the canonical commit cannot be resolved;
- a proposed bump skips the required next patch;
- a consumer is about to edit copied schema files manually;
- an agent cannot establish which lock/manifest is authoritative.

Do not "pick the newest-looking number" from prose. Resolve the lock and run the
script.
