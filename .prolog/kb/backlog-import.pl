% Full-corpus import recovery boundaries.

invariant(backlog_resume_preserves_canonical_source,
    "A resume restores its selected prior run ledger and checks out the
ledger's exact source commit before resolving the canonical corpus. The
highest confirmed offset for that commit determines the next batch.").

method(backlog_ambiguous_post_reconciliation,
    "If an accepted bulk POST loses status polling, inspect its failure ledger
and compare the exact canonical batch IDs and payloads to CouchDB. Resume at
the first missing offset only after proving that no later record is present;
do not blindly repeat the ambiguous POST.").
