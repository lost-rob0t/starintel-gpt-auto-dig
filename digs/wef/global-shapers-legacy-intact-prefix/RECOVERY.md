# Global Shapers legacy transport recovery

This packet contains the verified intact prefix of the historical Global Shapers alumni transport:

- 2,736 person documents
- 5,472 `member_of` relations
- 1 Global Shapers organization
- 8,209 canonical StarIntel documents total
- canonical JSONL SHA-256: `0589735d353f868c5a97b82e9ad043aee14a8873c36d8318a6ce7572b4f09b17`

Repository history contains only two source snapshots. The compact snapshot is malformed base64 and corrupt during XZ decoding; the fallback snapshot is truncated after 10,000 encoded characters. No historical branch contains the previously claimed reproducible 4,062-person / 12,187-document packet.

The first 2,736 rows decode as complete JSON records and were imported through the canonical legacy importer. The remaining 1,326-person suffix is not guessed or synthesized. It remains queued for reconstruction from live and archived official Global Shapers sources.
