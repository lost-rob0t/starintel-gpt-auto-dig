# Merged BHR corpus summary

The aggregate covers depths 1 through 11 of the BHR Partners investigation under the `hunter-biden` dataset.

## Totals

- 11 source packets
- 476 exact StarIntel v0.9.0 records
- 63 sources
- 93 entities: 59 organizations and 34 people
- 202 relations
- 118 investigation targets

## Design decision

The merge does not duplicate the 476 records in Git. Instead, `packet-index.json` and `build-merged-corpus.py` define and materialize one deterministic `starintel-documents.jsonl` export from the canonical packet files.

This preserves stable IDs, provenance, packet lineage, original line bytes, and source packet hashes while preventing duplicate corpus records from being interpreted as new documents.
