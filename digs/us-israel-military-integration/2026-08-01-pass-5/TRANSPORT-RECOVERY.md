# Canonical transport recovery required

The original `starintel-documents.jsonl.gz.b64` committed for this packet was malformed and could not be decoded as base64. The first Git commit containing the payload was already corrupt, and no plain JSONL copy was committed, so the missing bytes cannot be reconstructed safely from repository history.

The unusable transport has been removed. The report, source notes, merge utility, and Quasar manifests are retained for provenance, but the reported 252 pass-5 records are **not currently importable from this directory**.

Regeneration from the original source rows or a retained local canonical packet is tracked in issue #1947. The regenerated packet must pass JSONL validation, reference checks, decoded SHA-256 verification, and repository CI before the transport is restored.
