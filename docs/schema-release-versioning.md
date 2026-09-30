# StarIntel schema release versioning

## Current authority

As of this document revision, Star-Lang is the canonical repository and this
Auto-Dig checkout is only a pinned consumer:

- current StarIntel **release/profile version**: `0.10.1`
- **base/wire schema version**: `0.10.1` (the unified 0.10 line reunifies
  release and base schema versions)
- next additive patch release: **`0.10.2`**
- legacy line: release `0.9.1` over immutable base `0.9.0`
  (`schemas/starintel-doc-v0.9.0.*` remain on disk for consumers pinned to
  0.9; repository-local schemas and `starintel_doc/spec.py` are legacy corpus
  compatibility inputs, never canonical authority)

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

Use Star-Lang's repository-owned release tooling and release lock. Do not run
Auto-Dig's resolver to create a release.

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

## Bumping or minting a release

Version changes happen only in Star-Lang through its repository-owned workflow.
Auto-Dig's `scripts/schema-release.py bump` and `mint` commands fail closed.
After a Star-Lang release, update the lock and synchronized snapshot with
`scripts/sync-starintel-authority.py`; never use `sed`, search/replace, or
hand-edited generated files.

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
- Auto-Dig is asked to bump or mint the contract;
- a consumer is about to edit copied schema files manually;
- an agent cannot establish which lock/manifest is authoritative.

Do not "pick the newest-looking number" from prose. Resolve the lock and run the
script.
