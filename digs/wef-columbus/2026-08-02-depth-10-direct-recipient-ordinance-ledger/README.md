# Smart Columbus direct-recipient ordinance ledger — depth 10

**Dataset:** `wef`  
**Date:** 2026-08-02  
**Recursion depth:** 10  
**Schema:** StarIntel v0.9.0  
**Canonical records:** 7

## Bounded ledger

Fifteen identified City of Columbus ordinances from 2021 through 2026 directly authorized contracts, grants, or reimbursements involving Smart Columbus or a Columbus Partnership DBA.

- operational or organizational support: **$3,770,000.00**
- program-specific administration or delivery: **$2,146,832.50**
- combined authorization and expenditure ceilings: **$5,916,832.50**

This is an identified-ordinance minimum, not a paid-cash total or proof of a complete all-years census.

## Operational-support series

- `3301-2021`: $800,000.00
- `0670-2022`: $263,574.98
- `1817-2022`: $236,425.02
- `2657-2022`: $560,000.00
- `1462-2023`: $500,000.00
- `2266-2023`: $610,000.00
- `1663-2025`: $500,000.00
- `1850-2026`: $300,000.00

## Program-specific series

- Opportunity Port administration (`0165-2021`, `1581-2021`): **$556,832.50**
- Resident E-bike Subsidy Program (`3548-2022`, `2872-2023`, `1111-2024`): **$1,000,000.00**
- digital-equity outreach reimbursement (`2132-2023`): **$340,000.00**
- Ride & Drive Program (`2840-2024`): **$250,000.00**

## Funding-origin boundary

The gross ceiling cannot be described as entirely City-origin funding.

- Opportunity Port used OSU Alliance for the American Dream / Schmidt Futures grant funds.
- `0670-2022` used the Smart City Grant Fund.
- `2132-2023` combined a $200,000 FCC grant with $140,000 in City operating funds.
- Ride & Drive also references external CFI program support beyond the $250,000 ordinance expenditure.

Authorization ceilings are not proof that the full amounts were invoiced or paid.

## Vendor identity boundary

The ordinances and fiscal records expose at least three Smart Columbus-related vendor identifiers:

- `040255`
- `033348`
- `045611`

They are not treated as interchangeable without vendor-master history and legal-counterparty records.

## WEF boundary

None of the fifteen identified direct-recipient ordinance titles or reviewed descriptions names the World Economic Forum or a tested WEF program as a payee or funding recipient.

The ledger establishes repeated Smart Columbus authorization, not a direct WEF payment nexus.

## Depth 11 target

`starintel:investigation-target:wef-depth-11-smart-columbus-payment-census-and-vendor-crosswalk`

This target will map every ordinance to purchase orders, invoices, unique paid checks, reversals, residual balances, and vendor-master identities while separating City-origin funds from federal and third-party grant pass-throughs.

## Validation

- 7 JSONL records generated
- record IDs are unique
- normalized JSONL SHA-256: `22d65ba0cab3bbfe8001d59d463414bd8e470623b92bb34e3fc11378f705c426`
- deterministic gzip SHA-256: `d50047f21505100031cf6ac0d3a4f10ebda49ba2c696b68ed244536749b58be5`
- base64 transport SHA-256: `0f15dec7f82b3781682dd191fb1fe415a98ff03c38de31f2ba1336e6289b5a7e`
