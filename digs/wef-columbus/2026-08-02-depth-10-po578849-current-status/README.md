# WEF–Columbus PO578849 current status — depth 10

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 10  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 6

## Current status

- ordinance `1850-2026` authorized up to **$300,000**
- purchase order `PO578849`
- PO record `5639382635`
- source-document header `5642393098`
- source-document line `5657827605`
- vendor account `045611`
- accounting date: **July 28, 2026**
- status: **Open Order**
- matching invoice found: **no**
- matching paid check found: **no**

The source-backed status is **authorized and encumbered, not confirmed paid**.

## Funding continuity

The same vendor account links:

- `1663-2025 → PO525642 → $500,000 paid → check 676982`
- `1850-2026 → PO578849 → $300,000 open order`

Combined authorized ceiling: **$800,000**. Confirmed paid: **$500,000**. Open order: **$300,000**.

## WEF boundary

No reviewed ordinance or fiscal row for `PO578849` names the World Economic Forum, Global Shapers, Young Global Leaders, Davos, or the Centre/Center for Urban Transformation.

This is bounded non-discovery. The public fiscal fields do not contain complete agreements, correspondence, travel records, invoice backup, or accepted deliverables.

## Depth 11 target

`starintel:investigation-target:wef-depth-11-po578849-invoice-payment-and-deliverables`

Track the order until it produces an invoice, payment voucher, check, cancellation, amendment, or closeout, and obtain the executed contract and deliverables.

## Validation

- 6 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `f9b94dd7c702befa0ba228627df44f26a48b6aa5cadf18ff3d1f89bc72497e14`
- deterministic gzip SHA-256: `9b959d2e861b344020889a39586c2bda6001360e83eb492bda8287977db8e225`
- base64 transport SHA-256: `133847178a3d34fbc3d68e0d56b23476c60a0b40bc6b620f2f76b1a9ea80857a`
