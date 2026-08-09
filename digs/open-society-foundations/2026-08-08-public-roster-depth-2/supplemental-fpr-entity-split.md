# Fund for Policy Reform — Two-Entity Legal and Governance Split

**Run:** `2026-08-08`  
**Parent:** OSF public-roster and cross-ties supplemental pass  
**Status:** evidence staging; not canonical

## Executive finding

Public IRS filings expose two legally distinct 501(c)(4) entities with nearly identical names:

1. **Fund for Policy Reform** — EIN `35-7090597`, Wilmington, Delaware, tax-exempt since 2015;
2. **Fund For Policy Reform Inc** — EIN `26-4351242`, New York, tax-exempt since 2009.

They are not aliases. The Delaware entity repeatedly makes very large grants to the New York Inc entity, which then reports its own domestic and foreign grantmaking and program operations.

## 1. Verified inter-entity funding series

IRS-derived grant data reports:

| Fiscal year | Fund for Policy Reform (35-7090597) -> Fund For Policy Reform Inc (26-4351242) |
|---|---:|
| 2020 | $196,000,000 |
| 2021 | $375,000,000 |
| 2022 | $332,700,000 |
| 2023 | $327,000,000 |
| 2024 | $412,000,000 |

The five-year observed total is **$1,642,700,000**.

That total is an arithmetic sum of five distinct filing-year grants; it is not a claim about lifetime funding, obligations outside those years, or ultimate downstream expenditure.

## 2. Upstream Delaware entity

**Fund for Policy Reform**, EIN `35-7090597`, is a Delaware 501(c)(4). Its FY2024 filing reports:

- total assets: approximately $3.258 billion;
- net assets: approximately $3.030 billion;
- 2024 grant to Fund For Policy Reform Inc: $412 million;
- no FY2024 revenue reported on Part VIII;
- one principal grantmaking program described as social-welfare grants.

Its FY2023 filing reports $978.123 million in revenue, entirely categorized in the extracted summary as sales of assets.

The current FY2024 filing identifies:

- Bryn Mawr Trust — Administrative Trustee;
- Debbie Fine — Secretary as of 2024-01-17;
- Maija Arbolino — Treasurer;
- Binaifer Nowrojee — Trustee as of 2024-12-01;
- Leonard Benardo — Trustee until 2024-12-01.

These are filing-year governance roles, not permanent titles.

## 3. Downstream New York Inc entity

**Fund For Policy Reform Inc**, EIN `26-4351242`, is a New York 501(c)(4). Its FY2024 filing reports:

- revenue: approximately $470.129 million;
- expenses: approximately $265.977 million;
- net assets: approximately $819.344 million;
- contributions and grants: approximately $415.965 million;
- $412 million in grant funding attributed to Fund for Policy Reform for FY2024.

The FY2024 filing identifies:

- Pedro Abramovay — Vice President, Programs;
- Maija Arbolino — Treasurer;
- Binaifer Nowrojee — Director as of 2024-12-01;
- Leonard Benardo — Director until 2024-12-01;
- additional program directors and managers listed in Part VII.

## 4. Synchronized 2024 governance transition

Both legal entities report the same transition date:

```text
2024-12-01
Leonard Benardo  -> out of trustee/director role
Binaifer Nowrojee -> into trustee/director role
```

The exact legal titles differ by filer, so preserve each filing's wording.

This synchronized transition is strong evidence that the two entities are operationally related in addition to their direct grant relationship. It does **not** establish that one is legally identical to, or automatically controls, the other.

## 5. OSF leadership bridge

The people named above overlap with current or recent Open Society Foundations leadership surfaces already mapped in the parent packet:

- Binaifer Nowrojee — OSF president;
- Leonard Benardo — OSF senior leadership;
- Debbie Fine — OSF general counsel / board secretary;
- Maija Arbolino — recurring OSF-network treasury role in tax filings;
- Pedro Abramovay — OSF vice president, programs, and Fund For Policy Reform Inc vice president, programs.

These are explicit filing or first-party institutional roles, not inferred associations.

## 6. Downstream ECFR Deutschland lead

The unresolved Candid-backed series remains:

```text
Fund For Policy Reform Inc (26-4351242)
  -> ECFR Deutschland GmbH
     2020  $1,000,261
     2021    $999,774
     2022  $2,132,355
```

Purposes describe `Unlock Europe's Majority` and related nonpartisan work.

The current simplified IRS-derived profile confirms foreign-grant spending but does not expose those Schedule F rows in its displayed Schedule I table. Direct Schedule F capture is still required before canonicalizing the three recipient rows.

## 7. Proposed canonical structure

```text
starintel:org:fund-for-policy-reform
  EIN=35-7090597

starintel:org:fund-for-policy-reform-inc
  EIN=26-4351242

fund-for-policy-reform --granted_to--> fund-for-policy-reform-inc
  annual 2020-2024 edges
```

Do **not** use one normalized ID for both.

## 8. Next targets

1. Capture Schedule R relationship statements between the two FPR entities if explicitly reported.
2. Capture Fund For Policy Reform Inc Schedule F entries for ECFR Deutschland in 2020, 2021, and 2022.
3. Trace whether FPR Inc reports any later ECFR/ECFR Deutschland grants in 2023–2024.
4. Resolve ECFR Deutschland's German registry number and audited group relation.
5. Reconcile OSF leadership-role dates across OSI, FPOS, FPR, FPR Inc, and OSF London.

## Sources

- https://projects.propublica.org/nonprofits/organizations/357090597
- https://philanthropy.org/990/report/357090597/fund-for-policy-reform
- https://projects.propublica.org/nonprofits/organizations/264351242
- https://philanthropy.org/990/report/264351242/fund-for-policy-reform-inc

## Guardrail

Repeated funding and shared officers establish documented organizational connections. They do not by themselves establish improper coordination, hidden control, or misconduct.
