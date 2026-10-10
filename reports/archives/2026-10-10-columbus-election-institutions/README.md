# Archival input, not canonical wire records

`original-unpublished-packet.jsonl.txt` is the byte-exact 13-record draft received
for schema repair. It was created against an unsupported unpublished 90-dtype
schema, even though its records say `schemaVersion: 0.10.1`. That version string
does not make it valid under the maintained published release.

Do not import or publish this archive as canonical StarIntel data. It preserves
every original field, including the complete `research-pass` receipt and exact
fractional retrieval timestamps. No archive record has been edited or dropped.

SHA-256: `6811aa5d3f0f171f9a7d8493571a7363cccad21e0761eb7115c74249823b9b48`.

The supported canonical projection, reproducible CLI generator, field mapping
receipt, and scope notes are under
[`digs/anarchist-violence/2026-10-10-columbus-election-institutions/`](../../../digs/anarchist-violence/2026-10-10-columbus-election-institutions/).

The historical dataset name does not imply violence or wrongdoing by the public
institutions described. This archive introduces no new collection or claims.
