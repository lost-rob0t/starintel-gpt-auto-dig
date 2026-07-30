# Hunter Biden — verified email corpus seed

**Dataset:** `hunter-biden`  
**Run:** `2026-07-30-liz-secundy-email-seed`  
**Schema:** StarIntel v0.9.0  
**Status:** queued for recursive AutoDig

## Seed artifact

The supplied artifact renders an email with this header:

```text
From: "Robert Biden" <rhbdbc@icloud.com>
To:   "Liz Secundy" <lizsecundy@aol.com>
Date: 2018-07-13 12:22
```

The source is recorded as verified. The screenshot does not show a cryptographic signature, but the absence of a visible signature is not evidence that the message is fake.

## Artifact identity

```text
media type: image/png
dimensions: 1643 × 1099
size:       855594 bytes
sha256:     a4096daeb377886c4a128fc3ad623bd72de942680d963a7b9e7b3583669993a4
```

## AutoDig scope

Depth 0 inventories the verified message, preserves provenance, resolves the sender, recipient, and named entities, and creates typed graph candidates.

Later depths expand through:

1. adjacent messages and mailbox metadata;
2. people, aliases, organizations, places, dates, and events;
3. business, legal, political, family, and social relations;
4. claim-level corroboration against primary records.

Claims inside the message remain attributed to the author until independently corroborated.

## Packet

- `starintel-documents.jsonl` — source, email-message, and investigation-target records
- `sources.md` — provenance and verification record
- `manifest.json` — packet counts and hashes
