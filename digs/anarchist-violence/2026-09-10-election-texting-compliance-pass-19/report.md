# Auto-Dig bounded pass 19 — political texting / messaging compliance infrastructure

Date: 2026-09-10
Dataset: `anarchist-violence`
Scope: public 2026 U.S. election communications ecosystem

## Result

This bounded breadth-first pass opens a new political-messaging infrastructure cluster centered on identity verification, A2P 10DLC registration, U.S. short-code administration, and public political SMS/MMS/RCS vendors.

Materialized packet records: **37 total**

- 12 `source`
- 8 `org`
- 4 `person`
- 12 `relation`
- 1 `investigation-target`
- 12 explicit relations; 0 inferred relations

## New graph surface

Organizations materialized:

- Campaign Verify
- The Campaign Registry
- CTIA
- GCH Technologies
- U.S. Short Code Registry
- Prompt.io
- RumbleUp
- Political Comms

Public people materialized:

- Phil Gordon — Prompt.io CEO & Co-Founder
- Thomas Peters — RumbleUp Founder & CEO
- Greg Pfundstein — RumbleUp President & COO
- Hunter Lamirande — Political Comms Founder & President

## Evidence-supported infrastructure edges

- Campaign Verify is listed by The Campaign Registry as a participating vetting partner.
- CTIA oversees/administers the U.S. Short Code Registry.
- CTIA selected GCH Technologies as its strategic partner for Common Short Code Registry services beginning January 1, 2026.
- GCH Technologies develops/operates the U.S. Short Code Registry and provides technical/customer support under the current registry policy.
- Prompt.io publicly describes Campaign Verify submission and The Campaign Registry approval as parts of its political 10DLC onboarding path.
- RumbleUp publicly describes 10DLC registration support involving The Campaign Registry.
- Political Comms states that political 10DLC brand registration goes through The Campaign Registry, with Campaign Verify review where applicable.

## Communications / distribution layer

The public materials describe election-related voter-contact use cases including GOTV, fundraising, volunteer recruitment/coordination, SMS, MMS, peer-to-peer texting, outsourced sending, RCS, campaign registration, and messaging-delivery/compliance workflows. This pass records only publicly supported organizational and infrastructure relationships; it does not infer undisclosed campaign customers or private carrier arrangements.

## Provenance and source strategy

Primary/current first-party sources were preferred. Source domains used in the packet include:

- `campaignverify.org`
- `campaignregistry.com`
- `ctia.org`
- `usshortcodes.com`
- `prompt.io`
- `rumbleup.com`
- `politicalcomms.com`

Every mature entity/relation in this packet retains a source reference, exact public URL, collection timestamp, run lineage, and confidence. No people were merged from name/handle similarity.

## Coverage / dedupe

The run deliberately moved away from already-covered fundraising/data, consulting, voter-protection, voting-system certification, election-administration coordination, election-law, polling/media, and ballot-mail clusters. Repository search also showed Scale to Win already represented in existing DNC research, so this pass did not create a potentially conflicting new canonical Scale to Win identity.

No identity collision was force-resolved in this pass. The packet contains no inferred relationship promoted to fact.

## Recursive frontier

The saved `political-messaging-carrier-infrastructure-frontier-2026-09-10` target carries the graph outward into:

- additional political SMS/MMS/RCS and calling platforms;
- Campaign Service Providers and Direct Connect Aggregators;
- publicly observable carrier, verification, registry, short-code, toll-free, and 10DLC paths;
- disclosed campaign/PAC/party/advocacy clients and vendor relationships;
- public leadership, product surfaces, APIs, documentation, webinars, newsletters, opt-in pages, and other communications surfaces;
- source-to-provider-to-registry/verification-to-aggregator/carrier-to-voter delivery paths where public evidence supports the edge.

## Canonical artifact

`starintel-documents.jsonl` is the machine-readable StarIntel v0.9 packet for this bounded pass. It was created on a fresh branch from the current canonical base and is subject to the repository's exact-head merge gate before landing.
