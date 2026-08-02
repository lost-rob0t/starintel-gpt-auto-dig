# WEF–Columbus fiscal transactions — depth 9

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 9  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 13

## Smart Columbus payment chain

The official Columbus Auditor datasets resolve the 2025 Smart Columbus operational-support authorization into a completed fiscal chain:

`ORD 1663-2025 → PO525642 → invoice SC-2025-918 → APIN111456941 → $500,000 payment → check 676982`

The payee is recorded as **Columbus Partnership**, vendor account **045611**. The paid-check record lists **DBA Smart Columbus LLC**, `150 S Front St Ste 200, Columbus, OH 43215`.

`PO578849` records a separate **$300,000 open order** under ordinance `1850-2026`. The reviewed snapshot does not show a linked paid check for that order.

## Citywide membership transaction

The pass also resolves an explicit citywide-membership transaction:

`PO561654 → invoice 659020 → APIN111502025 → $6,425 payment → check 690797`

The payee is **National Institute of Governmental Purchasing Inc, DBA NIGP**, vendor account `009148`.

The accounting row records:

- department: Finance
- division: Financial Management
- fund: General Fund
- object class: Contractual Services
- program: Financial management
- subfund: General Fund Operating

Those named dimensions match the `0223-2026` Citywide Memberships authorization attachment. The public Accounting Distribution dataset omits the main-account field, so direct confirmation of account `63975` is unavailable. Literal `63975` search hits were unrelated invoice ID `R63975` and were rejected.

## WEF evidence boundary

The mapped pass parsed **1,315,900 rows** across eight official fiscal datasets. It found Smart Columbus, Columbus Partnership, and municipal membership transactions but no direct row naming the World Economic Forum, Global Shapers, Young Global Leaders, Davos, or the Centre/Center for Urban Transformation.

This is bounded non-discovery, not proof of absence. Fiscal tables do not include complete agreements, correspondence, travel records, or funded deliverables.

## Depth 10 targets

- `starintel:investigation-target:wef-depth-10-po525642-agreement-deliverables-and-wef-nexus`
- `starintel:investigation-target:wef-depth-10-citywide-membership-authorization-reconciliation`

## Validation

- 13 JSONL records parse successfully
- record IDs are unique
- normalized JSONL SHA-256: `7042d5ac8d3cf98f6ad251722d20df8094a2256488e1484b1db5671ef74cb6c1`

- deterministic gzip SHA-256: `673ba11297c156975bd3edeba4b58faac974bd1265a104990baa1986d328900b`
- base64 transport SHA-256: `e90da5eea5b9dfb146c48348c651f86f70ed9d28a3426a56a66aa3b1e38a42c1`
