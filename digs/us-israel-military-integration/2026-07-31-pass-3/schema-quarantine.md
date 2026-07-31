# Pass-3 schema quarantine

The original pass-3 `starintel-documents.jsonl.gz.b64` transport was removed from the active corpus because the mandatory StarIntel v0.9.0 merge gate reported 39 schema violations across its 72 records.

The failures included:

- a target record missing `data.target`;
- undeclared `pass_number` and `judgment` fields;
- undeclared `organization_type`, `role`, `event_type`, and `classification` fields across organization, person, event, and claim records;
- source `published_at` values containing only `2026` rather than ISO-8601 date-times.

The narrative report and Quasar manifest remain as reconstruction inputs. They are not proof that the removed transport was schema-valid. Rebuild this packet through the canonical StarIntel constructors/import tooling, validate every record, regenerate the content hashes and manifest, and only then restore it to the active corpus.

The malformed transport remains recoverable from Git history at commit `36a519059c355ebf9bb79728865b32b7bc7004c3`.
