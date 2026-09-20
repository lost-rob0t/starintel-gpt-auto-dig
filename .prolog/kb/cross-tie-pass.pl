% Durable discoveries from the w4 dig-queue cross-tie passes (2026-09-20).
% Load via .prolog/kb/index.pl.

% Concurrent nimble builds across dig-queue worktrees share ~/.cache/nim
% compile caches; overlapping runs raise transient [OSError] failures inside
% `nimble buildFast` (observed on scripts/starintel_ingest_core.nim).
root_cause(nimble_buildfast_transient_oserror, shared_nimcache_concurrency,
    "Two dig-queue workers ran `nimble buildFast` at the same time from
different worktrees. The shared per-module compile cache under ~/.cache/nim
was written concurrently and one link step failed with [OSError]. A lone
serial retry on an idle machine compiled all six binaries and the full
verify.py gate passed.").
invariant(never_run_concurrent_nimble_builds,
    "Before running `nimble buildFast` or verify.py, check pgrep for a live
nimble/nim process from any worktree. If a shell timeout detached a nimble
child, wait for its PID to exit before starting another build. A timed-out
verify.py leaves its nimble child running.").
method(recover_transient_nimble_oserror,
    "Wait for all nim processes to exit, then re-run
python3 <starintel-auto-dig-skill>/scripts/verify.py --repo <worktree>
serially; warm caches make the rebuild fast. Do not report gate status from
a run whose nimble exit code was lost to a shell timeout.").
invariant(verify_py_exit_requires_single_clean_run,
    "The merge gate claim must cite one verify.py invocation that exited 0
end-to-end; nimble and validate-for-merge succeeding in separate runs is
diagnostic only.").

% Cross-tie pass conventions verified against the wave-3 corpus.
invariant(source_id_is_sha256_of_url,
    "Wave-3 and later source_id values are 'sha256:' ++ hex(sha256(url))
with no trailing newline; reproduce with hashlib.sha256(url.encode()).").
invariant(cross_tie_relation_dataset_matches_pass,
    "Cross-tie relation records carry the dataset of the target that
spawned the pass (hoover-institution, sipri), while new org records get
their own subject dataset slug (nvidia, c3-ai, makena-capital, ...).").
invariant(relation_id_pattern,
    "Relation _id pattern: starintel:relation:<dataset>:<subject-slug>-
<predicate>-<object-slug>. Corrections keep the original _id and bump
version with a documented note; the wave-3 overseers 'fellow_of' mislabel
was corrected to member_of this way without renaming the _id.").
method(hoover_overseers_legend,
    "On https://www.hoover.org/about/who-we-are/overseers the roster markers
are: '* Executive Committee member' and '** Ex officio member'. Names in
the corpus published with a trailing ' *' (e.g. 'Michael G. McCaffery *')
encode Executive Committee membership, not a footnote or uncertainty.").
