# Transport integrity correction

The pass-2 packet was originally committed with a malformed gzip trailer. Standard gzip decompression therefore fails its CRC check even though the deflate stream can be decoded.

The report recorded `5d22b16ee986db9906147090cf9b0f9ca965c58839054e939a969f2ff4a03626`, but the payload present in the introducing commit `a5968e43f996dc1bf3486f15fd942f8f6f6ac4d3` and on `main` decodes to SHA-256:

```text
44108c766289da56bbb95fde0394aadc3eb361f75d9f957f95cdafe6d6dae6fc
```

The repository transport reader may recover a CRC-failing gzip only when a sibling `starintel-documents.jsonl.sha256` file exists and exactly matches the raw decompressed payload. Missing or mismatched digests remain fatal. The mandatory merge gate then parses and validates every recovered JSONL record against the StarIntel v0.9.0 schema.

This correction does not claim that the stale digest described another valid packet; no matching historical blob was found in the repository history. The long-term canonical repair is to rewrite the verified payload as plain `starintel-documents.jsonl` through the repository migration tooling.
