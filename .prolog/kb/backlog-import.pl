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

root_cause(backlog_legacy_source_http_422, unnormalized_source_file_format,
    "The backlog importer sends selected source documents without the local
validator's legacy normalization. A source data.file_format field is valid
only after conversion to data.medium and migration provenance; the ingest
server strictly rejects the undeclared legacy field before submitting bulk
work.").

method(backlog_legacy_source_correction,
    "Materialize corrected source documents through scripts/starintel.py
import, which validates and records the existing file_format-to-medium
migration. Preserve stable IDs and sorted order, check the prior confirmed
prefix is unchanged, then resume at the cleanly rejected offset on the new
source commit. Keep prior ledgers for the cross-commit audit trail.").
