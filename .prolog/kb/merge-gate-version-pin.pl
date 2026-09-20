% Merge-gate schema-version pin (verified 2026-09-20, HEAD 3457a7dc7,
% branch dig/queue-2026-09-19-w1, run dig-queue-2026-09-19-w1).
%
% The Python emitters (scripts/starintel.py create/import/select-targets and
% scripts/create-db-document.py) stamp schema_version "0.10.1" on new
% documents, but the Nim merge gate used by the Auto-Dig verify helper
% (bin/validate-for-merge, built from .starintel-doc-nim) validates with
% SpecVersion "0.9.0" only and rejects 0.10.1 envelopes with
% `unsupported_spec_version: $.schema_version: unsupported version`.

invariant(new_docs_must_match_nim_gate_version,
    "Before importing newly emitted documents into db/, set their
schema_version (and provenance.software_version) to the version the pinned
Nim gate accepts. On the 2026-09 worktree pin that is 0.9.0 even though
scripts/schema-release.py current reports release 0.10.1; release_version
describes the spec release line, not what the pinned Nim validator accepts.

Corollary: 0.9.0 target data has no result_ids field (0.10.1-only); put
result references in related_ids/workflow.notes instead.").

root_cause(emitter_gate_version_skew, pinned_nim_runtime_lags_python_spec,
    ".starintel-doc-nim is a symlink to a shared checkout pinned at a commit
whose starintel_doc SpecVersion is 0.9.0 while the repository's Python
starintel_doc package already emits 0.10.1. The AGENTS.md migration-window
sentence (both envelopes validate) is true only for validators built from a
newer Nim pin; the local merge gate fails closed on 0.10.1.

Fix options: repin .starintel-doc-nim to the 0.10.1-capable revision (a
shared-state operation across worktrees), or downstage new documents to
0.9.0 as this run did. Do not hand-edit existing corpus documents.").

method(patch_emitted_batch_to_gate_version,
    "Import the emitted batch, then rewrite the staged JSONL outside db/
(replace \"schema_version\":\"0.10.1\" with 0.9.0, likewise
provenance.software_version) and re-import with --replace; the same _id at
version 1 with corrected bytes is a documented correction. Rerun the merge
gate after the corrective import — imports mutate db/.").
