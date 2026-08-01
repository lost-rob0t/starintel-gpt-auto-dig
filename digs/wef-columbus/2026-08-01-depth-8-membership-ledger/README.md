# WEF–Columbus membership ledger — depth 8

**Dataset:** `wef`  
**Date:** 2026-08-01  
**Recursion depth:** 8  
**Schema:** StarIntel v0.9.0  
**Records:** 4

## Resolved branch

`starintel:investigation-target:wef-depth-8-smart-columbus-vendor-ledger-and-contracts`

This pass followed the Citywide Memberships lead produced by ordinance `0223-2026`.

## Finding

The official attachment named `2026 Citywide membership funding.xlsx` is not an itemized organization roster. It contains a single accounting-certificate line authorizing up to **$150,000**:

- department `45`
- division `4501`
- object class `3`
- main account `63975`
- fund `1000`
- subfund `100010`
- program `FN001`

Every populated workbook row was parsed. No World Economic Forum, WEF, Global Shapers, Young Global Leaders, Davos, or Centre/Center for Urban Transformation entry appears.

The initial Auditor collector's apparent `WEF` hit was binary PDF noise and is explicitly rejected.

## Boundary

This does not prove that no WEF-related payment exists. The attachment is an authorization template, not a purchase-order, invoice, check, or payment ledger.

## Next target

`starintel:investigation-target:wef-depth-9-citywide-membership-purchase-orders-and-vendors`

Depth 9 should join ordinance `0223-2026`, `ACPO012949`, main account `63975`, purchase orders, PO lines, vendor master, invoice journals, bank checks, accounting distributions, and payments.
