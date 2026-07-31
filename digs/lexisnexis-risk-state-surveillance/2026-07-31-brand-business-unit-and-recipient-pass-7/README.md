# LexisNexis brand, business-unit, and legal-recipient attribution — recursive pass 7

Follow-up to merged PR #109 and issue #110.

## Result

This pass stops treating “LexisNexis” as a single entity and separates:

- **LexisNexis Legal & Professional** — a RELX division distinct from LexisNexis Risk Solutions.
- **Matthew Bender & Company Inc.** — federal recipient UEI `XM4JJJA593U4`, reported under parent recipient LexisNexis Special Services Inc. in the reviewed DOJ award.
- **Matthew Bender** — a currently marketed legal-publishing brand.
- **Reed Technology and Information Services / Reed Tech** — a LexisNexis Legal & Professional business unit and historical brand.
- **LexisNexis Life Sciences Solutions** — the current name replacing the Reed Tech life-sciences brand.
- **VitalChek** — a LexisNexis Risk Solutions company and vital-record ordering platform.

## Procurement edge

DOJ delivery order `15BNAS21FWNP10151` is attached to Matthew Bender & Company Inc., not generically to Risk Solutions. It is linked to parent IDV `15BNAS20D00000030` and preserved as a legal/information-technology award.

## Evidence discipline

A brand, product, division, business unit, affiliate, incorporated company, and federal award recipient are separate graph concepts. Marketing affiliation does not rewrite the named recipient on an award.

## Packet

- Canonical core records: **44**
- Recursive targets: **1**
- Total records: **45**
- Canonical JSONL SHA-256: `9cb376eb25d4e9f144a036148dce524d581e240959c6d460ad49323f3d691fe3`
- Gzip SHA-256: `518223ad1f40243b4b4d719a7dd241a1041befaa19557eda301290fcb6552ba3`
- Base64 transport SHA-256: `bbe94707f6259b7243f83d6cc50f594f86df8fa8c72af72ec64a90641bb03d8f`

Pass 8 is queued as a federal brand-to-recipient contract census.
