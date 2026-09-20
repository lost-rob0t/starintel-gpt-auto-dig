% Durable knowledge from the dig-queue w3 cross-ties passes (2026-09-19/20).

method(cross_ties_person_pass, 
    "Bounded person cross-tie pass: read target+seeds, fetch the seed org's official bio page, run Brave exact-name discovery with board/fellow/advisor/director qualifiers, write only officially corroborated relations, keep exact-name identity-unconfirmed listings as research-pass findings/unresolved leads (never merge onto the target person), then replace the target at version+1 with status completed and result_ids pointing at the research-pass and relations.").

method(js_app_official_pages_via_brave,
    "RUSI people pages (Gatsby) fail direct fetch with parse error '8: ) not found'; Brave-rendered snippets of the same URL carry the biography text. Prefer Brave discovery for JS-rendered official directories and record the canonical URL as source.").

invariant(db_schema_version_090_only_in_this_checkout,
    "The Nim merge gate in this checkout (bin/starintel-validate via .starintel-doc-nim) rejects schema_version 0.10.1 envelopes with unsupported_spec_version even though scripts/schema-release.py reports 0.10.1; every canonical DB document must still use schema_version 0.9.0 until the Nim runtime is repinned. Do not hand-migrate existing 0.9.0 records.").

root_cause(nimble_buildfast_ssl_link_failure, missing_library_path,
    "nimble buildFast fails linking bin/starintel-ingest-core with 'cannot find -lcrypto/-lssl' unless LIBRARY_PATH points at the nix openssl 3.6.3 lib dir (/nix/store/14cfdqp8w2iw188vhjfaz2wg8pzbghp3-openssl-3.6.3/lib).").

root_cause(nimble_exit_sigterm_15, shared_nimcache_concurrency,
    "Multiple dig-queue worker worktrees share ~/.cache/nim and the nimble wrapper; a build started while another worker's nimble/site-generation is running can die with exit status -15. Poll for running nimble/starintel-site/validate-for-merge processes and only then run the gate.").

invariant(one_nimble_build_at_a_time,
    "Across all worktrees on one host, at most one nimble buildFast may run concurrently; check ps for nimble/starintel-site/validate-for-merge before invoking the merge gate.").

invariant(import_is_incremental_not_transactional,
    "scripts/starintel.py import validates and writes each JSONL line immediately; a mid-batch validation error leaves earlier lines written. Fix the offending document and re-run the same batch with --replace (idempotent: identical bytes become unchanged).").

root_cause(provenance_closed_vocabulary, schema_rejects_custom_keys,
    "provenance is additionalProperties:false; free-form completion markers like completed_by fail validation. Use the declared updated_by/run_id/notes keys.").
