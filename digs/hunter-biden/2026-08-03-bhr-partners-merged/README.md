# BHR Partners merged Hunter corpus — depths 1–11

This directory merges the prior BHR Partners research packets in the `hunter-biden` dataset into one reproducible corpus view.

The source packets remain canonical and unchanged. The merge is **virtual**: `build-merged-corpus.py` reads the exact validated JSONL records from depths 1 through 11, verifies their manifests, and materializes one aggregate file on demand. This avoids committing a second copy of every `_id` and prevents the repository from treating an aggregate projection as new research records.

## Aggregate scope

| Type | Records |
|---|---:|
| source | 63 |
| org | 59 |
| person | 34 |
| relation | 202 |
| investigation-target | 118 |
| **Total** | **476** |

The packet index covers:

- `2026-07-31-bhr-partners-depth-1` through `depth-5`;
- `2026-08-01-bhr-partners-depth-6` through `depth-11`.

## Build the merged corpus

From the repository root:

```bash
python3 digs/hunter-biden/2026-08-03-bhr-partners-merged/build-merged-corpus.py
```

This produces local generated files:

```text
digs/hunter-biden/2026-08-03-bhr-partners-merged/starintel-documents.jsonl
digs/hunter-biden/2026-08-03-bhr-partners-merged/merged-manifest.json
```

Run a validation-only pass without writing:

```bash
python3 digs/hunter-biden/2026-08-03-bhr-partners-merged/build-merged-corpus.py --dry-run
```

## Merge invariants

The builder fails before writing when any invariant is violated:

- a packet manifest or declared JSONL file is missing;
- a declared per-file SHA-256 does not match;
- JSONL contains malformed JSON or blank records;
- a file, packet, dtype, or aggregate count differs from its manifest/index;
- a record has the wrong dataset or schema version;
- any `_id` appears more than once across the 11 packets.

Ordering is deterministic: depth order, then each packet manifest's `document_files` order, then original line order.

## Provenance

`packet-index.json` records every packet path, expected total, and available combined packet hash. Depth 4 predates complete packet-level hashing, so its aggregate entry explicitly records that limitation; every available per-file hash and all declared record counts are still checked.

The generated aggregate is a read/export surface. Do not import it into the canonical database as a new batch unless the operation is explicitly intended to replace or migrate existing stable IDs.
