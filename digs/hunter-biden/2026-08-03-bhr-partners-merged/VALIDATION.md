# Validation contract

The merge builder performs these checks before writing any aggregate output:

1. all 11 packet manifests exist and identify `hunter-biden` / StarIntel `0.9.0`;
2. every declared JSONL file exists;
3. every available declared file SHA-256 matches;
4. every JSONL line is a non-empty JSON object;
5. every record has `_id`, `dtype`, the expected dataset, and the expected schema version;
6. per-file, per-packet, per-dtype, and global counts match;
7. every `_id` is unique across all packets;
8. the aggregate output is written atomically and receives its own SHA-256 manifest.

The repository merge gate remains authoritative:

```bash
python3 scripts/validate-for-merge.py --site
```
