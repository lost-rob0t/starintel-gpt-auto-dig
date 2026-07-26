# Validation

Completed locally against the generated packet:

- base64 decode
- deterministic gzip decompression
- 86 JSONL records parsed
- duplicate ID check
- required StarIntel v0.9.0 common-field check
- dtype-specific data-field allowlist check
- relation endpoint resolution check
- decoded SHA-256 check

Decoded packet SHA-256:

```text
95f16b1a8faa5881101d2faa4d658cba1165d0c3f62505eedcc3edd4c260d52b
```

The repository-wide merge gate was not run because the publication environment does not have a local GitHub checkout. Keep the pull request in draft until this passes:

```bash
python3 scripts/validate-for-merge.py --site
```
