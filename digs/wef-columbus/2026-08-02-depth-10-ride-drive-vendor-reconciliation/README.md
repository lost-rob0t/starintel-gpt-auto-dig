# WEF–Columbus Ride & Drive vendor reconciliation — depth 10

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 10  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 7

## Directly confirmed transaction

Ordinance `2840-2024` authorized up to **$250,000** for Smart Columbus to implement the Ride & Drive Program.

The fiscal chain directly identifies:

`2840-2024 → PO507489 → invoice 2026-115 → APIN111447010 → APPY141902977 → check 673476`

- invoice description: `(25) Ride & Drive Program Task 3`
- amount: **$110,000**
- check status: **Paid**
- check cleared: **January 30, 2026**
- check payee: Columbus Partnership
- check address field: `DBA Smart Columbus LLC`

## Candidate sibling-invoice cluster

Two additional same-vendor invoices appear in the same period:

- `SC-2025-602`: **$36,000**
- `SC-2025-603`: **$85,000**

They were combined into a **$121,000** payment and reissued warrant:

- payment voucher `APPY141896444`
- paid check `672135`
- canceled check `676951`
- void reason: `Stop Pay/Reissue - Vendor Request`

Together with Task 3, the cluster totals **$231,000**, or 92.4% of the authorization. However, the reviewed public rows do not describe `SC-2025-602` or `SC-2025-603`, so those two invoices are **not attributed to Ride & Drive** without invoice images or a contract task schedule.

## Vendor-account discrepancy

- ordinance vendor account: `033348`
- fiscal PO and payment vendor account: `045611`

The accounts are not treated as interchangeable. Vendor-master history, W-9 records, and contract setup records are required to explain the change.

## WEF boundary

No reviewed ordinance or transaction row names the World Economic Forum, Global Shapers, Young Global Leaders, Davos, or the Centre/Center for Urban Transformation.

This is bounded non-discovery, not proof of absence outside the reviewed fiscal fields.

## Depth 11 target

`starintel:investigation-target:wef-depth-11-ride-drive-invoice-images-vendor-master-and-deliverables`

The target seeks the executed contract, SOW, invoice images, vendor-account crosswalk, stop-payment/reissue records, task deliverables, event records, sponsor allocation, and CFI grant cost allocation.

## Validation

- 7 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `42dd21e5920457edb77cbea1d56771dd3f5a34f9c631210150adc6dd497a82c0`
- deterministic gzip SHA-256: `9ef46ca703064558cb0dfca0e95528184ed389bd20ce70c76bff408c3c919791`
- base64 transport SHA-256: `8b494924e89a4095f70d69e447b2f31667072b9af9b3b1e60442039c13aa25b3`
