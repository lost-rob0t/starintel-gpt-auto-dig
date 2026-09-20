# StarIntel schema release versioning

## Current authority

As of this document revision (0.10.1, 2026-09-19):

- current StarIntel **release/profile version**: `0.10.1`
- **base/wire schema version**: `0.10.1` (the unified 0.10 line reunifies
  release and base schema versions)
- next additive patch release: **`0.10.2`**
- legacy line: release `0.9.1` over immutable base `0.9.0`
  (`schemas/starintel-doc-v0.9.0.*` remain on disk for consumers pinned to
  0.9; the 0.9 expansion registry is retired as an authority — the vocabulary
  lives in `starintel_doc/spec.py`; see `docs/schema-0.10.1-design.md`)

These numbers were intentionally allowed to differ throughout the 0.9 line.
The 0.10 line reunifies them. In neither case may a filename alone tell you
the current StarIntel release.

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
release=0.10.1 profile=0.10.1 base_schema=0.10.1 ... next=0.10.2
```

When someone asks "what is the current StarIntel spec/version?", report
`release_version` (`0.10.1` currently), not a schema filename.

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
python3 scripts/schema-release.py bump --to 0.10.2 --dry-run
python3 scripts/schema-release.py bump --to 0.10.2
python3 scripts/schema-release.py check
```

The bump command only accepts the next patch release. From `0.10.1`, the only
accepted additive bump is `0.10.2`.

## Minting a new base line

Creating a new base schema version (e.g. a future 0.11.0) requires an explicit
compatibility/migration decision and uses `mint`, not `bump`:

```bash
python3 scripts/schema-release.py mint --to <X.Y.Z> --dry-run
python3 scripts/schema-release.py mint --to <X.Y.Z>
python3 scripts/schema-release.py check
```

Mint refuses to run unless the target strictly advances the current base schema
version and `starintel_doc.spec.SCHEMA_VERSION` already equals the target (the
spec source lands first; mint only plumbs release artifacts: generated schema,
manifest, conformance inventory, package/version pins, and the current-schema
filename pins). See `docs/schema-0.10.1-design.md` for the 0.10.1 mint record.

The bump command, by contrast, preserves the base schema identity of the
current line. Do not obtain a new base line merely by renaming files.

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
