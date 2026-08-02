# Smart Columbus direct-recipient payment census — depth 11

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 11  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 7

## Result

- unique direct paid checks: **19**
- direct paid-check floor: **$5,324,209.54**
- identified ordinance ceilings: **$5,916,832.50**
- gross ceiling-to-check difference: **$592,622.96**
- paid-check share of identified ceilings: **89.98%**

The check total is internally reconciled both by direct vendor account and by exact payee name. Project vendors whose descriptions merely mention Smart Columbus were excluded.

## Vendor-account totals

- `033348`: **$1,176,882.50**
- `040255`: **$1,860,000.00**
- `045611`: **$2,287,327.04**

## Evidence boundary

This is a source-backed paid-check floor, not a complete disbursement total if non-check payment modes are absent. The gross difference from ordinance ceilings is not an unpaid residual until every ordinance, funding source, PO, invoice, reversal, and check is reconciled.

## WEF boundary

No retained direct-recipient check names the World Economic Forum or a tested WEF program as payee. This does not test internal allocation, subcontracting, travel, sponsorship, or other expenses.

## Depth 12 target

`starintel:investigation-target:wef-depth-12-smart-columbus-ordinance-payment-reconciliation-and-vendor-master`

## Validation

- 7 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `4861b7ac32e569e01006d29a24e6fb3f3c6cee886a47680b35a372c6fde944ec`
- deterministic gzip SHA-256: `fdb53449807c9b4603c250fecd6c7468ccee8498e433a346c1c74886e69818e3`
- base64 transport SHA-256: `351309233aa3d0a18762770768011ecb71bf96ad621d6489a90043079995945f`
