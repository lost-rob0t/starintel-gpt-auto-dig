# BHR Partners merged Hunter corpus — depths 1–11

This directory merges the prior BHR Partners research packets in the `hunter-biden` dataset into one reproducible corpus view.

The source packets remain canonical and unchanged. The merge is **virtual**: `build-merged-corpus.py` reads the validated JSONL records from depths 1 through 11, verifies their manifests, resolves only explicitly documented historical revisions, and materializes one aggregate file on demand. This avoids committing a second copy of every `_id` and prevents the repository from treating an aggregate projection as new research records.

## Aggregate scope

The 11 packet manifests contain 476 rows. One investigation target was intentionally refined under its stable ID in depth 10, so the merged corpus contains 475 unique records.

| Type | Packet rows | Unique merged records |
|---|---:|---:|
| source | 63 | 63 |
| org | 59 | 59 |
| person | 34 | 34 |
| relation | 202 | 202 |
| investigation-target | 118 | 117 |
| **Total** | **476** | **475** |

The packet index covers:

- `2026-07-31-bhr-partners-depth-1` through `depth-5`;
- `2026-08-01-bhr-partners-depth-6` through `depth-11`.

## Documented revision

`starintel:investigation-target:bhr-obtain-beijing-arbitration-award` appears in depths 7 and 10 with the same stable ID and version but different content. The depth-10 record is the documented correction because it:

- narrows the request to the December 25, 2025 award;
- adds the Beijing Arbitration Commission seed;
- uses the newer official arbitration notice;
- has a later `date_updated`.

`packet-index.json` explicitly names the preferred and superseded files and records the reason. Any other non-identical duplicate remains fatal. Byte-identical repeats may be coalesced with provenance recorded in the generated manifest.

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
- a file, packet, dtype, raw aggregate, or unique aggregate count differs from its manifest/index;
- a record has the wrong dataset or schema version;
- a non-identical repeated `_id` lacks an exact documented resolution;
- a declared preferred or superseded source does not match the actual collision set.

Ordering is deterministic: depth order, then each packet manifest's `document_files` order, then original line order, with superseded revisions omitted.

## Provenance

`packet-index.json` records every packet path, expected total, available combined packet hash, and explicit revision resolution. Depth 4 predates complete packet-level hashing, so its aggregate entry records that limitation; every available per-file hash and all declared record counts are still checked.

The generated aggregate is a read/export surface. Do not import it into the canonical database as a new additive batch.
