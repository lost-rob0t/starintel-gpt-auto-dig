# Smart Columbus authority gaps and records request — depth 13

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 13  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 7

## Opportunity Port grant structure

Official City legislation separates grant receipts from Smart Columbus contract authority:

- `0165-2021` accepted a **$500,000** OSU / Alliance for the American Dream / Schmidt Futures grant and authorized a **$235,750** Smart Columbus administration contract.
- `1581-2021` accepted an additional **$107,027.50** and authorized up to **$321,082.50** for Smart Columbus.

The fiscal ledger shows:

- checks `385079` and `390967` total **$235,750**, exactly matching `0165-2021`, but the complete direct identifier chain remains absent.
- check `401423` is explicitly tied to `1581-2021` through `PO299090`, but the paid amount is **$331,132.50**, which is **$10,050** above the ordinance-stated amount.

The difference is an unresolved authority or accounting question. It is not a finding of impropriety.

## Administrator transition

Smart Columbus served as Opportunity Port grant administrator under the 2020–2021 OSU / Alliance for the American Dream structure. By 2024, City legislation funded Opportunity Port through The Ohio State University's Drug Enforcement and Policy Center:

- `1642-2024`: **$120,000**
- `2803-2025`: **$55,500**
- `1834-2026`: **$59,229**

The reviewed public legislation documents a transition in funding recipient and program administration, but does not expose the handoff, contract closeout, asset transfer, or final Smart Columbus grant ledger.

## Other authority gaps

- Leadership Retreat Program: **$1,327.04**, `PO479218`, invoice `2024-1120`, check `602588`
- Emissions Mapping Pilot with Energi.AI: **$36,000**, `PO507105`, invoice `SC-2025-602`, included in check `672135`
- vendor-master history for accounts `033348`, `040255`, and `045611`

## Records request

`public-records-request.md` requests the native grant ledger, executed contracts, amendments, invoice images, settlement applications, payment approvals, accounting distributions, closeout records, and vendor-master crosswalk needed to resolve these issues.

## WEF boundary

No reviewed Opportunity Port, retreat, emissions-pilot, invoice, PO, or legislative descriptor names the World Economic Forum or a tested WEF program.

This is bounded non-discovery. It does not test unpublished correspondence, internal allocation, travel, sponsorship, subcontracting, or records outside the public fiscal extracts.

## Depth 14 target

`starintel:investigation-target:wef-depth-14-smart-columbus-records-production-and-closeout`

Depth 14 is blocked pending custodian records production.

## Validation

- 7 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `46b78c1c77ecd62a4a4e6c51f6c7ca114b59bd491966d55f95ffa9f7cde49507`
- deterministic gzip SHA-256: `9331eba291bca6ef427521de0a7d0f01da5f5e00d3e2d01caaf2990065ae27d0`
- base64 transport SHA-256: `ebf590b640b765958d1442f797e7f77b1bbd7ade738c5c9488244f2353420652`
