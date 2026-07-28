# Import

Decode the transport packet before importing it into Quasar:

```bash
base64 -d starintel-documents.jsonl.gz.b64 | gzip -d > starintel-documents.jsonl
```

Then select `starintel-documents.jsonl` together with `quasar-import-manifest.json` in Quasar's bulk import.

Expected decoded SHA-256:

```text
95f16b1a8faa5881101d2faa4d658cba1165d0c3f62505eedcc3edd4c260d52b
```

Expected record count: `86`.
