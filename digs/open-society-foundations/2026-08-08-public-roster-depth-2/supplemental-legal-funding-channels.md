# Open Society Foundations — Supplemental Legal Funding Channels

**Run:** `2026-08-08`  
**Parent target:** `starintel:target:wef:open-society-foundations-public-rosters-and-cross-ties`  
**Status:** post-max-depth evidence staging; not canonical  
**Reason:** the original target reached `max_depth=5`; this is a separate user-directed follow-on pass rather than a silent recursion-ceiling change.

## Executive finding

The generic edge `Open Society Foundations -> European Council on Foreign Relations` is legally and financially under-specified. Public records expose multiple distinct Open Society entities, different recipient entities, and different accounting concepts. **Award commitments, annual filing-reported payments, refunds, and recipient-side audited income must remain separate.**

Candidate legal nodes not returned by exact-name repository search in this pass include:

- Open Society Institute — EIN `13-7029285`;
- Foundation to Promote Open Society — EIN `26-3753801`;
- Fund For Policy Reform Inc — EIN `26-4351242`;
- Fund for Policy Reform — EIN `35-7090597`;
- Open Society Foundation London — Companies House `10187396`;
- ECFR Deutschland GmbH — German registry identifier still unresolved;
- Soros Economic Development Fund Open Society Foundation - London — UK establishment `BR021288`, requiring entity resolution.

## 1. Open Society Institute -> ECFR: award versus payment

Two source families describe related but non-equivalent financial facts.

### Archived OSF award record

A historical first-party OSF grant record preserved by Wikidata references reports:

- recipient: European Council on Foreign Relations;
- award amount: **$5,000,000**;
- displayed point in time: **2022**;
- purpose: general support;
- historical OSF grant ID: **`OR2021-83857`**.

This is an **award/commitment record**, not automatically an annual cash-payment amount.

### IRS-derived Open Society Institute payment records

Open Society Institute's IRS-derived funder index separately reports:

- **$5.0 million total across two ECFR grant rows in 2022–2023**;
- FY2023 directly reports **$2.5 million** to ECFR;
- therefore the other 2022–2023 IRS row is **$2.5 million**;
- another **$2.5 million total across two ECFR grant rows in 2020–2021**, with the annual split unresolved in this pass.

### Reconciliation

Do **not** call the $5m award and the $2.5m FY2022 filing row contradictory. A multi-year or installment award can produce annual tax-return payments smaller than the original award amount. The sources currently support this as the leading accounting explanation, but the actual payment schedule still needs the underlying grant agreement or complete first-party grant record.

Canonical modeling should therefore distinguish something like:

```text
award / commitment:  $5,000,000  (historical OSF grant record)
payment / outlay:     $2,500,000  (OSI FY2022 IRS-reported grant row, inferred from two-year aggregate)
payment / outlay:     $2,500,000  (OSI FY2023 direct IRS-derived row)
```

Do not sum the award and payments as if they were three independent grants.

**Sources:**

- historical OSF reference: `https://www.opensocietyfoundations.org/grants/past?grant_id=OR2021-83857` (preserved in Wikidata reference index);
- https://philanthropy.org/990/report/137029285/open-society-institute/2023
- https://philanthropy.org/990/grants-by/137029285/open-society-institute

## 2. Foundation to Promote Open Society -> ECFR: large 2023 award lead

Indexed historical OSF grant references identify a **$17,732,000** general-support award to **European Council on Foreign Relations**, beginning in 2023, with archived OSF grant ID:

`OR2023-88176`

Indexed grant sources identify **Foundation to Promote Open Society** as the legal funder and describe a 2023–2028 term.

Treat **$17.732m as the award/commitment amount**, not automatically as the amount paid in any one FPOS tax year or recognized by ECFR in one audited year. Direct FPOS filing-row capture remains pending.

## 3. Verified FPOS -> Open Society Foundation London channel

FPOS FY2022 IRS e-file controlled-entity data reports two separate flows involving **Open Society Foundation London**:

- **$46,999,529** transferred to OSF London — `GRANT PAYMENT`;
- **$5,668,104** transferred from OSF London — `GRANT PAYMENT REFUND`.

Do not net these silently.

FPOS FY2024 IRS-derived Part XV grant data directly lists two additional OSF London awards/payments as filed:

- **$44,927,239**;
- **$8,072,761**.

Open Society Foundation London is independently an active UK company, number `10187396`.

## 4. Foundation to Promote Open Society filing identity

FPOS is a distinct U.S. private foundation, EIN `26-3753801`. IRS-derived filings report FY2024 revenue of about **$935.0 million** and end assets above **$10.8 billion**.

Its FY2024 grant list also directly exposes funding to several institutions that recur in the OSF recursion, including:

- Soros Economic Development Fund — $25.0m;
- Bard College — $20.0m;
- Central European University — $15.0m;
- Roma Foundation for Europe — $15.602337m;
- Amnesty International Limited — $5.2m;
- Institute for Human Sciences — $3.81m;
- Open Society Foundation for Albania — $3.347m;
- Carnegie Endowment for International Peace — $3.0m;
- Stefan Batory Foundation — $2.9m.

Those direct rows are broken out further in `supplemental-fpos-2024-outflows.*`.

## 5. Two different Fund for Policy Reform entities

The IRS data exposes **two distinct 501(c)(4) entities** whose names are dangerously easy to collapse:

### Fund for Policy Reform

- EIN `35-7090597`;
- Wilmington, Delaware;
- tax-exempt since 2015.

### Fund For Policy Reform Inc

- EIN `26-4351242`;
- New York;
- tax-exempt since 2009.

The Delaware entity repeatedly funds the New York Inc entity:

| Fiscal year | Fund for Policy Reform -> Fund For Policy Reform Inc |
|---|---:|
| 2020 | $196,000,000 |
| 2021 | $375,000,000 |
| 2022 | $332,700,000 |
| 2023 | $327,000,000 |
| 2024 | $412,000,000 |

This is a documented inter-entity funding chain, not an alias relationship.

The New York Inc entity's FY2024 filing also names current OSF leadership figures in governance/management roles, including Pedro Abramovay, Binaifer Nowrojee, Leonard Benardo, Debbie Fine, and Maija Arbolino. These are organization-reported roles and should be modeled temporally.

## 6. Fund For Policy Reform Inc -> ECFR Deutschland leads

Historical first-party OSF grant references preserved in Wikidata independently preserve the exact values, purposes, and old OSF grant IDs for the `Unlock Europe's Majority` series:

| Display year | Amount | Historical OSF grant ID |
|---|---:|---|
| 2020 | $1,000,261 | `OR2020-70385` |
| 2021 | $999,774 | `OR2021-80195` |
| 2022 | $2,132,355 | `OR2022-85024` |

A separate Candid-backed compilation attributes those awards to **Fund For Policy Reform Inc** and recipient **ECFR Deutschland GmbH**. That legal-payer/recipient-entity attribution still needs direct Schedule F capture before canonicalization.

So the amount/purpose/source-recovery keys are stronger than before, while the exact legal payer remains one verification step lower.

## 7. Separate UK SEDF establishment

Companies House exposes **SOROS ECONOMIC DEVELOPMENT FUND OPEN SOCIETY FOUNDATION - LONDON**, establishment `BR021288`, opened 17 August 2016, associated with company reference `FC036200`.

Do not merge this with Open Society Foundation London `10187396` based on naming similarity.

## 8. Modeling consequence

The defensible graph now contains different relation classes:

```text
Open Society network / grant system
    -> award or commitment records

Open Society Institute (EIN 13-7029285)
    -> annual IRS-reported ECFR grant payments

Foundation to Promote Open Society (EIN 26-3753801)
    -> annual IRS-reported grants / controlled-entity transfers

Fund for Policy Reform (EIN 35-7090597)
    -> Fund For Policy Reform Inc (EIN 26-4351242)
        -> ECFR Deutschland GmbH [legal payer/recipient attribution awaiting Schedule F]

ECFR legal entities
    -> recipient-side audited income
```

Never collapse these accounting layers into one edge amount.

## Next source-acquisition targets

1. Capture the direct FPOS filing row/payment schedule for award `OR2023-88176` / $17.732m.
2. Recover the full first-party grant record for `OR2021-83857` to confirm term and installment schedule for the $5m ECFR award.
3. Resolve the individual 2020 and 2021 OSI ECFR payment rows; only their combined $2.5m is currently filing-index verified.
4. Capture Fund For Policy Reform Inc Schedule F rows for ECFR Deutschland, 2020–2022.
5. Parse OSF London 2023–2025 accounts for grant income, related-party flows, and onward grants.
6. Resolve ECFR Deutschland's legal registry identifier.
7. Resolve SEDF's U.S./foreign legal identity against UK establishment `BR021288`.

## Guardrails

- Keep **award value**, **obligation/commitment**, **annual payment/outlay**, **refund**, and **recipient recognized income** separate.
- Funding is not evidence of policy control or misconduct.
- Preserve exact legal names, EINs, company numbers, grant IDs, and filing-year roles.
- Do not collapse similarly named entities.
