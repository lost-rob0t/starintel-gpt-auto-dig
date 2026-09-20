% StarIntel spec release authority and 0.10.1 unified line.
% Verified 2026-09-19 on branch spec/0.10.1-unify (HEAD 40622e3f4).

invariant(spec_release_authority_is_scripted,
    "All StarIntel release/profile/base-schema version plumbing goes through
scripts/schema-release.py: bump advances the next patch of the current line;
mint creates a new unified base line and requires starintel_doc.spec.SCHEMA_VERSION
to already equal the target. Hand-editing version fields or schema filenames
breaks check() and the release-coupling tests.").

invariant(unified_line_has_no_expansion_registry,
    "Manifests without expansion_registry_path are unified lines: check()
instead requires their base_schema_path to exist. The 0.9 expansion registry
is frozen legacy; its vocabulary lives in starintel_doc/spec.py
(EXPANSION_ABSORBED_FIELDS merged at import, wire fields win on collision).").

invariant(schema_version_migration_window,
    "0.10.1 validators accept schema_version in {0.9.0, 0.10.1}; emitters write
0.10.1. The generated schema's schema_version is an enum, not a const. The
legacy spec_092 profile pins the 0.9.0 const and rejects 0.10.1 envelopes.").

method(mint_new_base_line,
    "Land the spec.py source change first (SCHEMA_VERSION, ACCEPTED_SCHEMA_VERSIONS
ordered legacy-first, SCHEMA_ID, new dtypes), commit, then run
`python3 scripts/schema-release.py mint --to X.Y.Z`. Mint regenerates the
schema via scripts/starintel.py, writes the manifest, and repoints conformance,
nimble, the operation-registry test, fixtures, and the schema filename pins
(scripts/validate-for-merge.py, scripts/starintel_validate.nim, workflows).
Release-coupling tests are red between the spec commit and the mint commit by
construction.").

root_cause(release_test_red_between_spec_and_mint, release_coupling_by_design,
    "tests/test_operation_registry.py and tests/test_spec_0101.py assert
agreement between runtime TYPE_FIELDS and the minted artifacts. Changing
spec.py alone makes them fail until mint lands; this is the designed
two-commit release train, not a regression.").

invariant(breach_reference_only_material,
    "breach documents never carry raw leaked material inline: no field is a
raw-bytes field, and validation.py rejects BREACH_FORBIDDEN_INLINE_FIELDS
names in breach data. leak_corpus_uri + leak_corpus_sha256 and leaked_file_ids
are the only corpus representations (0.9.2 artifact_reference_only precedent).").

invariant(db_corpus_untouched_by_spec_releases,
    "Spec releases must not write into db/. The dual schema_version acceptance
window exists precisely so legacy 0.9.0 corpus documents keep validating while
a future migrator upgrades them; validate-by-replacement is not required at
release time.")

%% Note: sorted() on version strings is wrong for 0.10.x ('0.10.1' < '0.9.0'
%% lexicographically); use spec.SCHEMA_VERSIONS_ENUM which is ordered
%% legacy-first by construction.
