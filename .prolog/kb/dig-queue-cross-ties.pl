% Durable knowledge from dig-queue cross-ties passes (worker w2, 2026-09-19/20).
% Facts promoted from runs/run-3457a7dc713d4b09c373e2f5d80ff907bfa55dc7.pl.
:- multifile root_cause/3, invariant/2, method/2, tooling/3.

% --- validation / gate -------------------------------------------------
root_cause(gate_nimble_link_failure, 'nimble buildFast fails with cannot find -lssl/-lcrypto',
           'the Nim gate links openssl; LIBRARY_PATH must point at the nix openssl 3.6.3 lib dir').
invariant(merge_gate_needs_library_path,
          'run verify.py with LIBRARY_PATH=/nix/store/14cfdqp8w2iw188vhjfaz2wg8pzbghp3-openssl-3.6.3/lib or the nimble step fails before validation').
root_cause(new_doc_rejected_unsupported_spec_version,
           'bin/validate-for-merge rejects schema_version "0.10.1" on new records with unsupported_spec_version',
           'during the 0.10.1 migration window this repository Nim validator only accepts the 0.9.0 envelope; python import accepts 0.10.1, so python-green is not merge-green').
invariant(new_records_use_0_9_0_envelope,
          'until the validator is repinned, stage new db records with schema_version "0.9.0" to match corpus siblings and pass the Nim gate').
invariant(gate_is_slow,
          'bin/validate-for-merge --site over the 1.28M-document corpus takes 10-20 minutes; never kill it mid-run or stale validate/nimble children survive and can corrupt nimcache').
root_cause(import_not_file_transactional,
           'scripts/starintel.py import validates per-document and writes incrementally',
           'a batch with one invalid doc leaves earlier valid docs written and raises on the bad one; re-import with --replace after fixing the staged JSONL is safe').
method(verify_py_libpath,
       'LIBRARY_PATH=/nix/store/14cfdqp8w2iw188vhjfaz2wg8pzbghp3-openssl-3.6.3/lib python3 /home/unseen/.config/opencode/skills/starintel-auto-dig/scripts/verify.py --repo <worktree>').

% --- research conventions ---------------------------------------------
tooling(dark_academia_cross_ties, canonical_dataset_roots,
        'digs/dark-academia/ is the packet root; per-source datasets stay on the seed person (belfer-center, sipri, ...); org records may be reused cross-dataset by stable _id (e.g. starintel:org:goldman-sachs from wef)').
invariant(relation_id_shape,
          'cross-tie relations use starintel:relation:<dataset>:<person-slug>-affiliated_with-<org-slug> with qualifiers.published_role / source_page / coverage_status, predicate affiliated_with, inverse has_publicly_listed_person').
invariant(unresolved_leads_get_investigation_targets,
          'research-pass unresolved_target_ids must resolve to real db/investigation-target documents; create the investigation-target doc in the same batch').
tooling(disambiguation, common_name_persons,
        'anchor every affiliation of a common-name person to a unique work (e.g. the SIPRI monograph ISBN/LC record for Chris Smith 1955-), never to the bare name; record the authority name on the person doc').
tooling(source_ids, deterministic_ids,
        'sources[].source_id is a free-form string; "sha256:<hex of url>" matches house style and is deterministic without fetching page bytes').
