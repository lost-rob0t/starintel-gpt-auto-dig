# WEF-Columbus public records - depth 7

**Dataset:** `wef`  
**Date:** 2026-08-01  
**Recursion depth:** 7  
**Schema:** StarIntel v0.9.0  
**Records:** 16  
**Resolved target:** `starintel:investigation-target:wef-depth-7-wef-columbus-public-records`

## Core finding

This pass found a concrete identity and accounting gap below the existing WEF-Columbus graph.

- Ohio attachments identify **Smart Columbus, LLC** as active entity `4212222`, formed July 23, 2018.
- City ordinances describe the counterparty as **Columbus Partnership dba Smart Columbus LLC**.
- The City used contract-compliance/vendor identifier `040255` in 2023 and vendor account `045611` in 2025-2026.
- Funding authority moved from Development / General Fund in 2023 to Technology / Information Services in 2025-2026.
- The reviewed packets authorize expenditure ceilings, but do not include the executed contracts, invoices, payment ledger, vendor-master linkage, or accepted deliverables.
- None of the reviewed attachments names WEF or attributes these City funds to WEF activity.

## Authorized ceilings

| Year | Ordinance | Ceiling | Department / fund | Vendor ID |
|---|---|---:|---|---|
| 2023 | 1462-2023 | $500,000 | Development / General Fund | 040255 |
| 2025 | 1663-2025 | $500,000 | Technology / Information Services Operating Fund | 045611 |
| 2026 | 1850-2026 | $300,000 | Technology / Information Services Operating Fund | 045611 |

These are authorized ceilings, not confirmed outlays.

## Next recursive targets

- `starintel:investigation-target:wef-depth-8-smart-columbus-vendor-ledger-and-contracts`
- `starintel:investigation-target:wef-depth-8-columbus-correspondence-travel-and-profile-authorization`

Depth 8 should obtain vendor-master history, executed contracts, purchase orders, invoices, payment warrants, WEF correspondence, travel records, profile authorization, participant agreements, and task-force deliverables.

## Transport

The packet is stored as deterministic gzip content encoded with base64 in `starintel-documents.jsonl.gz.b64`. Decode with:

```bash
base64 -d starintel-documents.jsonl.gz.b64 | gzip -dc > starintel-documents.jsonl
```

The manifest records decoded, gzip, and transport SHA-256 hashes.
