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

root_cause(backlog_actorless_target_failure, compatibility_route_requires_actor,
    "The legacy /new/target/:actor route requires an actor path component,
while canonical target documents may omit data.actor. Most remaining backlog
targets are actorless, so the importer cannot dispatch them through that
compatibility route.").

method(backlog_canonical_target_bulk,
    "Send target documents through /documents/bulk with the other canonical
documents. The server validates the full batch and authorizes each target as
targets:dispatch against its document resource before any publish side effect;
the full-corpus ingest credential must carry the required resource grants.").
