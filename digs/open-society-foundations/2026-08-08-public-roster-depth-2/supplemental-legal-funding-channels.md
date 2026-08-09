# Open Society Foundations — Supplemental Legal Funding Channels

**Run:** `2026-08-08`  
**Parent target:** `starintel:target:wef:open-society-foundations-public-rosters-and-cross-ties`  
**Status:** post-max-depth evidence staging; not canonical  
**Reason:** the original target reached `max_depth=5`; this is a separate user-directed follow-on pass rather than a silent recursion-ceiling change.

## Executive finding

The generic edge `Open Society Foundations -> European Council on Foreign Relations` is legally under-specified. Public filings expose multiple distinct Open Society entities and multiple recipient entities. They must not be collapsed into one donor or one recipient node.

Candidate legal nodes not returned by exact-name repository search in this pass include:

- Open Society Institute — EIN `13-7029285`;
- Foundation to Promote Open Society — EIN `26-3753801`;
- Fund For Policy Reform Inc — EIN `26-4351242`;
- Fund for Policy Reform — EIN `35-7090597`;
- Open Society Foundation London — Companies House `10187396`;
- ECFR Deutschland GmbH — German registry identifier still unresolved;
- Soros Economic Development Fund Open Society Foundation - London — UK establishment `BR021288`, requiring entity resolution.

## 1. Open Society Institute -> ECFR: corrected longitudinal series

IRS-derived grant data for **Open Society Institute** identifies **European Council on Foreign Relations** as a repeated grantee.

The funder-level grant index reports:

- **$5.0 million across two ECFR grants in 2022–2023**;
- **$2.5 million across two ECFR grants in 2020–2021**.

The FY2023 filing directly shows a **$2.5 million** ECFR grant. Therefore the 2022 member of the 2022–2023 pair is **$2.5 million**, not $5 million.

This corrects an earlier secondary-database lead that described a $5 million 2022 award. The secondary value is superseded and must not be canonicalized.

The 2020–2021 pair totals $2.5 million, but this pass has not resolved the exact split between those two years; do not invent it.

**Sources:**

- https://philanthropy.org/990/report/137029285/open-society-institute/2023
- https://philanthropy.org/990/grants-by/137029285/open-society-institute

## 2. Foundation to Promote Open Society -> ECFR: large 2023 award lead

Indexed historical OSF grant references identify a **$17,732,000** general-support award to **European Council on Foreign Relations**, beginning in 2023, with archived OSF grant ID:

`OR2023-88176`

Indexed grant sources identify **Foundation to Promote Open Society** as the legal funder and describe a 2023–2028 term.

Verification remains below direct-filing-row level until the exact FPOS Part XV/foreign-grant row or restored first-party OSF grant page is captured. The exact grant ID is a strong source-recovery key, not a substitute for the filing row.

## 3. Verified FPOS -> Open Society Foundation London channel

FPOS FY2022 IRS e-file controlled-entity data reports two separate flows involving **Open Society Foundation London**:

- **$46,999,529** transferred to OSF London — `GRANT PAYMENT`;
- **$5,668,104** transferred from OSF London — `GRANT PAYMENT REFUND`.

Do not net these silently.

FPOS FY2024 IRS-derived Part XV grant data then directly lists two additional OSF London awards:

- **$44,927,239**;
- **$8,072,761**.

The earlier staging note that treated these FY2024 values as pending is superseded: the rows are now filing-derived and are staged as verified public filing facts.

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

The New York Inc entity's FY2024 filing also names current OSF leadership figures in governance/management roles, including Pedro Abramovay, Binaifer Nowrojee, Leonard Benardo, and Maija Arbolino. These are organization-reported roles and should be modeled temporally.

## 6. Fund For Policy Reform Inc -> ECFR Deutschland leads

A secondary Candid-backed grant compilation identifies:

| Year | Recipient | Amount | Purpose | Verification |
|---|---|---:|---|---|
| 2020 | ECFR Deutschland GmbH | $1,000,261 | Unlock Europe's Majority | direct foreign-grant row pending |
| 2021 | ECFR Deutschland GmbH | $999,774 | nonpartisan Unlock Europe's Majority activities | direct foreign-grant row pending |
| 2022 | ECFR Deutschland GmbH | $2,132,355 | Unlock Europe's Majority | direct foreign-grant row pending |

The current IRS-derived Fund For Policy Reform Inc profile confirms substantial foreign-grant spending, but its simplified Schedule I display does not expose these foreign-recipient rows. They remain strong acquisition targets, not canonical facts.

## 7. Separate UK SEDF establishment

Companies House exposes **SOROS ECONOMIC DEVELOPMENT FUND OPEN SOCIETY FOUNDATION - LONDON**, establishment `BR021288`, opened 17 August 2016, associated with company reference `FC036200`.

Do not merge this with Open Society Foundation London `10187396` based on naming similarity.

## 8. Modeling consequence

The defensible legal-funding graph now contains at least:

```text
Open Society Institute
    -> European Council on Foreign Relations

Foundation to Promote Open Society
    -> Open Society Foundation London
    -> European Council on Foreign Relations [large 2023 award lead; direct row pending]
    -> Institute for Human Sciences
    -> Bard College
    -> Central European University
    -> Soros Economic Development Fund

Fund for Policy Reform (35-7090597)
    -> Fund For Policy Reform Inc (26-4351242)
        -> ECFR Deutschland GmbH [2020-2022 foreign-grant series pending direct row capture]
```

This is why `Open Society Foundations` should remain an umbrella/network analytical node rather than being used as the legal payer for every transaction.

## Next source-acquisition targets

1. Capture the direct FPOS filing row for grant ID `OR2023-88176` / $17.732m ECFR award.
2. Resolve the 2020 and 2021 Open Society Institute ECFR grant amounts individually; only their combined $2.5m is presently filing-index verified.
3. Capture Fund For Policy Reform Inc Schedule F rows for ECFR Deutschland, 2020–2022.
4. Parse OSF London 2023–2025 accounts for grant income, related-party flows, and onward grants.
5. Resolve ECFR Deutschland's legal registry identifier.
6. Resolve SEDF's U.S./foreign legal identity against UK establishment `BR021288`.

## Guardrails

- Do not sum grant commitments, annual payments, refunds, and recipient-side audited income unless periods and accounting bases match.
- Funding is not evidence of policy control or misconduct.
- Preserve exact legal names, EINs, company numbers, and filing-year roles.
- Do not collapse similarly named entities.
