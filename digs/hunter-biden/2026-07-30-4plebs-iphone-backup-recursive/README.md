# Hunter Biden 4plebs iPhone-backup recursive AutoDig

This packet expands the two archived July 2022 `/pol/` threads into a typed StarIntel source graph and a five-target recursive queue.

## Result

The pass identifies and links:

- the original archived thread, `385931719`;
- the follow-up backup-general thread, `386015453`;
- contemporaneous reporting by The Verge, VICE Motherboard, and NBC News;
- the commercial iPhone Backup Extractor documentation;
- the open-source `iphone_backup_decrypt` implementation;
- Apple iCloud security documentation;
- an independent forensic-methodology reference for separating cryptographically verified records from an unverified remainder.

The output contains **9 source documents** and **5 investigation-target documents**.

## Evidence model

This dig does **not** label the archive fabricated because an original checksum is unavailable.

The evidence is split into four independent layers:

1. **Event and source provenance** — the archived threads, reporting, screenshots, and tool references existed.
2. **Byte-level integrity** — whether two surviving copies are identical, measured with file and tree hashes.
3. **Message or artifact authenticity** — whether a specific email, database row, photo, or attachment can be authenticated.
4. **Claim corroboration** — whether a statement inside an authentic artifact is independently supported.

The Verge and VICE provide contemporaneous corroboration of the event, extraction workflow, screenshots, and novel posted media. Their July 2022 reports did not claim a complete forensic authentication of every file. This is recorded as a verification-scope distinction rather than a “fake” classification.

## Key technical finding

The screenshots and reporting identify **iPhone Backup Extractor**. The open-source `iphone_backup_decrypt` library independently documents the expected local encrypted-backup components: `Manifest.db`, relative paths, domains, `EncryptedBackup`, and file extraction.

Current Reincubate documentation says direct iCloud-backup retrieval became unavailable as of May 2020. That creates a concrete recursive question: was the 2022 material a local encrypted backup, a converted iCloud backup, live iCloud data, or another exported container?

## Recursive queue

### Depth 0

Preserve both threads as root nodes, capture complete thread JSON and media metadata, remove credentials from retained material, hash the captures, and enumerate every outbound public URL.

### Depth 1

- Reconstruct the exact extraction path and historical tool versions.
- Locate surviving archive copies and cluster them by normalized tree hash.
- Build a contemporaneous-source statement matrix.
- Recover original filenames, media hashes, backup dates, device identifiers, and `Manifest.db` metadata.

### Depth 2

Import recovered communications under the repository’s permanent email-ingestion invariant:

1. source document;
2. canonical `email-message`;
3. sender and recipient `person` documents;
4. source-scoped `person` documents for explicit body mentions;
5. stable links among all records.

Then corroborate individual claims with adjacent messages, cryptographic signatures where available, and independent primary records.

## Integrity capture requirements

For every surviving lawful copy, record:

- acquisition URL and timestamp;
- packaging format and byte size;
- SHA-256 and BLAKE3;
- normalized file count and directory-tree hash;
- per-file hashes;
- `Manifest.db` and `Manifest.plist` hashes;
- transformations, extraction-tool version, and error report.

No password, account credential, authentication token, or explicit private media is included in this packet.

## Files

- `sources.md` — source ledger and recursive leads.
- `manifest.json` — document inventory and validation state.
- `db/source/` — nine canonical source records.
- `db/investigation-target/` — depth-0, depth-1, and depth-2 recursive queue records.
