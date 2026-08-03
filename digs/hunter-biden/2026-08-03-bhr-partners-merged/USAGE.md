# Usage

Generate the merged export from the repository root:

```bash
python3 digs/hunter-biden/2026-08-03-bhr-partners-merged/build-merged-corpus.py
```

Validate without writing:

```bash
python3 digs/hunter-biden/2026-08-03-bhr-partners-merged/build-merged-corpus.py --dry-run
```

The generated JSONL is an export view over existing stable IDs. It is not a new research packet and should not be imported as an additive batch.
