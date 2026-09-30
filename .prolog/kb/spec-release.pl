% Historical Auto-Dig release machinery and the Star-Lang authority handoff.

invariant(spec_release_authority_is_scripted,
    "Star-Lang is the sole StarIntel release and schema authority. Auto-Dig's
schema/starintel-schema.lock.json pins the exact commit. The local
scripts/schema-release.py is read-only; bump and mint fail closed.").

invariant(unified_line_has_no_expansion_registry,
    "The Star-Lang 0.10.1 release lock and compatibility registry are vendored
under schema/star-lang at their verified hashes. Repository-local schemas and
the 0.9 expansion registry are frozen legacy migration inputs, not authority.").

invariant(schema_version_migration_window,
    "The Star-Lang-derived binding accepts legacy 0.9.0 snake-case input only
at its migration boundary and emits lowerCamelCase 0.10.1. The local Auto-Dig
runtime remains a legacy corpus reader and must not emit canonical documents.").

method(mint_new_base_line,
    "Create and verify releases in Star-Lang, update each generated language
binding, then run scripts/sync-starintel-authority.py with the exact canonical
checkout and verify scripts/check-starintel-schema-lock.py. Auto-Dig never
mints a release.").

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
release time.").

%% Note: sorted() on version strings is wrong for 0.10.x ('0.10.1' < '0.9.0'
%% lexicographically); use spec.SCHEMA_VERSIONS_ENUM which is ordered
%% legacy-first by construction.
