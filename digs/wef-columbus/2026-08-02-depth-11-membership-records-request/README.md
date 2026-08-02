# WEF–Columbus membership records request — depth 11

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 11  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 5

## Public-data boundary

Depth 10 reconciled:

- 16 authorization-compatible invoices totaling **$127,846**
- 15 unique paid checks totaling **$127,631**
- no direct WEF-related payee

The remaining public-data gaps are:

- main account `63975` is omitted from the published Accounting Distribution extract;
- **$22,154** of the $150,000 ceiling has no compatible invoice in the bounded join;
- **$22,369** has no uniquely reconciled paid check; and
- invoices `20787` and `20801` both map to the same **$215** payment voucher/check in the bounded resolver.

## Records request

`public-records-request.md` specifies a narrow production request using:

- ordinance `0223-2026`
- `ACPO012949`
- account `63975`
- POs `PO546851` and `PO559530`
- invoices `20787` and `20801`
- invoice vouchers `APIN111443947` and `APIN111475818`
- payment voucher `APPY141944676`
- check `684939` / record `5638220265`
- vendor account `001891`

The request seeks complete accounting strings, POs, invoices, voucher applications, checks, remittances, reversals, authorization balances, and vendor-master linkage. Sensitive banking and taxpayer fields may be redacted.

## Depth 12 target

`starintel:investigation-target:wef-depth-12-citywide-membership-records-production`

Depth 12 is blocked pending records production. Once received, it should ingest the native ledger fields, finish the authorization reconciliation, resolve the PELRA ambiguity, and rerun WEF-specific tests.

## Validation

- 5 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `e5042e82633a11cf9d754078dcd22c13d8d2310820e69e261d76a4fbc4cf468b`
- deterministic gzip SHA-256: `155fa95bf406b63098b3bff67caea60e0c464a8d8cd8557f8f36519df66e36b8`
- base64 transport SHA-256: `bb6a44e5ab1de69c8f5025073b99b12df6200f409e84db37aaf6573e7ddbc71e`
