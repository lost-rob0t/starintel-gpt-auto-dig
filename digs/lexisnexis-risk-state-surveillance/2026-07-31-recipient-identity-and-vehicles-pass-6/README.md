# RELX / LexisNexis federal recipient and vehicle reconciliation — recursive pass 6

Follow-up to merged PR #104 and issue #106.

## Result

This pass separates the federal award identities used by the RELX/LexisNexis group:

- **RELX INC.** — UEI `LKAAJG8KK4U1`
- **LEXISNEXIS RISK SOLUTIONS INC** — UEI `UJJ2MWZC6SJ9`
- **LEXISNEXIS SPECIAL SERVICES INC** — UEI `H5AKPL6N4L96`
- **RELX PLC** — parent-recipient UEI `TUZXND87M5A1`

These identifiers are represented as distinct procurement identities. A shared parent recipient or overlapping LexisNexis branding does not rewrite the named recipient on an award.

## Ordering vehicles

- USCIS order `70SBUR25F00000065` is linked to Library of Congress FEDLINK parent IDV `03310323D0035`; LexisNexis identifies the corresponding contract as `LCFDL23D0035`.
- VA BPA `36C10X23A0001` is classified as **legal research subscription services**, not an investigative-database award.
- LNSSI orders `W912PL23F0024`, `HS002124F0006`, and `12319823F0019` are linked to GSA Federal Supply Schedule `GS00F178DA`.

## Service separation

The three LNSSI child orders preserve distinct stated purposes:

1. Accurint for Law Enforcement / background investigation.
2. ProMonitor alert service.
3. Address and death-match information retrieval for notices and due-process rights.

## Packet

- Canonical core records: **58**
- Recursive targets: **1**
- Total packet records: **59**
- Canonical transport: `starintel-documents.jsonl.gz.b64`
- Canonical JSONL SHA-256: `f1c41eb08fd28903fdd5860316749d048e520f0944667d7d14ba4956a2aa5968`
- Gzip SHA-256: `307bff57ce1aaca085d1ad358bfb40bb85c3b91a637fdba2a97ad002a14a8f18`
- Base64 transport SHA-256: `55c7e3b04450eb24a6a660ae5baf02752ca3e6e7cd84fe0cb14e0d4c4adfb2d8`

The next frontier maps product brands and service categories to exact legal recipients and business units, including Matthew Bender, Reed Tech, VitalChek, Risk Solutions, and Special Services.
