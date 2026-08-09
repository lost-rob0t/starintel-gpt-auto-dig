# Open Society Foundations — Supplemental Legal Funding Channels

**Run:** `2026-08-08`  
**Parent target:** `starintel:target:wef:open-society-foundations-public-rosters-and-cross-ties`  
**Status:** post-max-depth evidence staging; not canonical  
**Reason for supplemental pass:** the original target reached its configured `max_depth=5`; this user-directed continuation does not silently raise that target's recursion ceiling. It records a separate follow-on pass instead.  
**Scope:** public tax filings, public company filings, OSF grant identifiers, and institution-side financial records. No inferred private identifiers.

## Executive finding

The generic graph edge `Open Society Foundations -> European Council on Foreign Relations` is too coarse for financial analysis.

Public tax and regulatory records expose multiple legally distinct Open Society entities that must not be collapsed into one donor node:

1. **Open Society Institute** — EIN `13-7029285`, U.S. 501(c)(3) private foundation;
2. **Foundation to Promote Open Society** — EIN `26-3753801`, U.S. 501(c)(3) private foundation;
3. **Fund For Policy Reform Inc** — EIN `26-4351242`, U.S. 501(c)(4);
4. **Open Society Foundation London** — UK company `10187396`;
5. **Soros Economic Development Fund Open Society Foundation - London** — UK establishment `BR021288`, a separate registry surface that requires entity resolution before canonicalization.

Exact-name repository searches on 2026-08-08 did not return existing normalized records for Open Society Institute, Foundation to Promote Open Society, Fund For Policy Reform, Open Society Foundation London, or ECFR Deutschland. These are therefore candidate new entity nodes rather than obvious aliases of an existing normalized record.

## 1. Verified U.S. tax-filing edge: Open Society Institute -> ECFR

An IRS-derived FY2023 Form 990-PF rendering for **Open Society Institute**, EIN `13-7029285`, lists:

- recipient: **European Council on Foreign Relations**;
- fiscal year: **2023**;
- amount: **$2,500,000**.

The filing mirror identifies the legal filer as Open Society Institute, not generic `Open Society Foundations`.

### Modeling consequence

Create a separate legal organization node for Open Society Institute and model the grant from that node. Do not attach this grant directly to the generic OSF network node merely because the filer uses the OSF website.

**Source:** https://philanthropy.org/990/report/137029285/open-society-institute/2023

## 2. Strong archived-OSF grant lead: Foundation to Promote Open Society -> ECFR

Indexed copies of OSF's historical grant directory identify a **$17,732,000** general-support award to the **European Council on Foreign Relations**, beginning in 2023 and described as a five-year grant. The archived OSF grant identifier is:

`OR2023-88176`

The indexed grant record identifies the funder as **Foundation to Promote Open Society**.

This is a high-value lead with an unusually strong provenance trail because the record retains an exact OSF grant ID and historical first-party URL. However, the current OSF site no longer exposes that old URL cleanly through indexed retrieval in this pass, and the corresponding recipient row has not yet been reproduced directly from FPOS's IRS grant schedule.

### Verification state

- amount: strong source-backed lead;
- recipient: strong source-backed lead;
- purpose: strong source-backed lead (`general support`);
- legal funder: strong source-backed lead (`Foundation to Promote Open Society`);
- direct IRS-row reproduction: **pending**.

Do not upgrade this to the same verification class as the Open Society Institute $2.5m FY2023 row until the FPOS filing row or a restored first-party OSF grant page is captured directly.

**Discovery sources:**

- https://www.wikidata.org/wiki/Q1376496 — preserves the old OSF grant reference and `OR2023-88176` identifier;
- https://www.developmentaid.org/organizations/awards/view/603539/europe-and-central-asia-to-provide-general-support — indexed grant record identifying FPOS as funder and a 2023–2028 term;
- historical first-party reference target: `https://www.opensocietyfoundations.org/grants/past?grant_id=OR2023-88176`.

## 3. Verified controlled-entity transfer: FPOS -> Open Society Foundation London

Foundation to Promote Open Society's IRS FY2022 e-file identifies **OPEN SOCIETY FOUNDATION LONDON** in its controlled-entity schedule and reports two separate flows:

- **$46,999,529** transferred **to** Open Society Foundation London, described as `GRANT PAYMENT`;
- **$5,668,104** transferred **from** Open Society Foundation London, described as `GRANT PAYMENT REFUND`.

These are separate accounting events. They must not be silently netted into one synthetic amount.

This establishes a direct legal-entity funding channel:

```text
Foundation to Promote Open Society (US, EIN 26-3753801)
             |
             | grant payment / refund flows
             v
Open Society Foundation London (UK, company 10187396)
```

Open Society Foundation London is independently confirmed by Companies House as an active company limited by guarantee. Its 2025 full accounts were filed on 1 July 2026.

**Sources:**

- IRS-derived FPOS filing render / ProPublica filing archive;
- https://projects.propublica.org/nonprofits/organizations/263753801
- https://find-and-update.company-information.service.gov.uk/company/10187396
- https://find-and-update.company-information.service.gov.uk/company/10187396/filing-history

## 4. Current FPOS filing establishes a durable legal entity

ProPublica's current IRS-derived profile for **Foundation to Promote Open Society** reports:

- EIN `26-3753801`;
- 501(c)(3) private foundation;
- New York;
- FY2023 revenue: **$842,821,637**;
- FY2023 expenses: **$874,683,497**;
- FY2023 year-end assets: **$10,502,606,362**;
- current filing series through FY2024.

The existence of this filing series is important because large grants attributed generically to `Open Society Foundations` can often be resolved to this exact filer rather than treated as network-level spending.

**Source:** https://projects.propublica.org/nonprofits/organizations/263753801

## 5. Fund For Policy Reform is another distinct legal funding channel

**Fund For Policy Reform Inc**, EIN `26-4351242`, is independently present in IRS-derived filings as a U.S. **501(c)(4)** organization.

Its ProPublica filing series reports FY2024 revenue of **$470,129,351** and net assets of **$819,344,248**.

Secondary grant datasets tied to tax/grant records identify the following ECFR Deutschland leads:

| Year | Recipient | Amount | Stated purpose | Verification |
|---|---|---:|---|---|
| 2020 | ECFR Deutschland GmbH | $1,000,261 | Unlock Europe's Majority | IRS-row capture pending |
| 2021 | ECFR Deutschland GmbH | $999,774 | nonpartisan Unlock Europe's Majority activities | IRS-row capture pending |
| 2022 | ECFR Deutschland GmbH | $2,132,355 | Unlock Europe's Majority | IRS-row capture pending |

The three values are **not yet canonical facts** in this packet because the exact Schedule F / grant rows have not been reproduced directly from the IRS filing during this pass.

Their significance is as a source-acquisition target: if verified, they would prove that ECFR funding also traveled through a 501(c)(4) Open Society legal entity and specifically into the German ECFR entity rather than the UK charity.

**Primary entity source:** https://projects.propublica.org/nonprofits/organizations/264351242

**Lead source:** https://www.influencewatch.org/non-profit/fund-for-policy-reform-trust/

## 6. Open Society Institute has its own ECFR funding history

Open Society Institute's FY2023 IRS-derived filing gives us the direct $2.5m ECFR row. Secondary grant compilations also identify a **$5,000,000 2022 general-support grant** to ECFR.

That 2022 amount remains a lead pending direct retrieval of the corresponding FY2022 IRS grant row. It should not be merged with the $17.732m FPOS award or the $2.5m OSI FY2023 award.

The key analytic point is legal separation:

```text
Open Society Institute              -> ECFR
Foundation to Promote Open Society  -> ECFR
Fund For Policy Reform Inc          -> ECFR Deutschland GmbH   [verification pending]
Foundation to Promote Open Society  -> Open Society Foundation London
```

Even if all entities operate inside the broader Open Society network, their filings, tax status, grant obligations, and recipient entities are distinct.

## 7. OSF London is itself funded across multiple years

The FPOS FY2022 controlled-entity transfer proves a large OSF London funding channel directly from the U.S. foundation.

Current IRS-derived grant indexes also surface later FPOS grants to **Open Society Foundation London**, including two 2024-filing-era amounts of approximately **$44.927m** and **$8.073m**, both described as support for non-lobbying activities and programs promoting open democratic societies worldwide.

Those later values are useful targets but remain one verification tier below the directly rendered FY2022 controlled-entity transfer until their exact IRS grant rows are captured.

Companies House independently confirms that OSF London's accounts are current through 31 December 2025.

## 8. Newly exposed UK establishment: SEDF / OSF London

Companies House exposes a UK establishment named:

**SOROS ECONOMIC DEVELOPMENT FUND OPEN SOCIETY FOUNDATION - LONDON**

- establishment number: `BR021288`;
- status: open;
- opened: 17 August 2016;
- UK establishment of `SOROS ECONOMIC DEVELOPMENT FUND`, company `FC036200`.

This should not be assumed to be the same legal person as Open Society Foundation London company `10187396` merely because the names overlap.

It is a separate entity-resolution target.

**Source:** Companies House registry search / establishment record.

## 9. Implication for the existing ECFR audited-funding packet

The ECFR UK charity's 2024 audited accounts use the singular label **`Open Society Foundation`** for its large unrestricted/core funding disclosure.

This supplemental pass demonstrates why that label must remain unresolved at the legal-funder level unless a matching invoice, grant agreement, donor note, OSF grant ID, or filer-side tax row ties the audited euro amount to a specific legal entity.

There are already at least two independently evidenced U.S. Open Society grantmakers with ECFR-related funding surfaces:

- Open Society Institute;
- Foundation to Promote Open Society.

A third Open Society entity, Fund For Policy Reform Inc, has strong unresolved ECFR Deutschland grant leads.

Therefore:

> `Open Society Foundations` is appropriate as a network/umbrella analytical node, but it is not sufficiently precise as the legal payer for every ECFR grant.

## 10. Candidate canonical nodes

These are proposed only. They must go through the executable v0.9.0 schema and transactional writer/importer before entering `db/`.

```text
starintel:org:open-society-institute
starintel:org:foundation-to-promote-open-society
starintel:org:fund-for-policy-reform-inc
starintel:org:open-society-foundation-london
starintel:org:ecfr-deutschland-gmbh
starintel:org:soros-economic-development-fund-open-society-foundation-london
```

Identifiers to preserve:

```text
Open Society Institute               EIN 13-7029285
Foundation to Promote Open Society   EIN 26-3753801
Fund For Policy Reform Inc           EIN 26-4351242
Open Society Foundation London       Companies House 10187396
SEDF OSF - London establishment      Companies House BR021288
```

## 11. Candidate relations by verification tier

### Verified / high confidence

```text
Open Society Institute --granted_to--> European Council on Foreign Relations
  amount_usd=2500000
  fiscal_year=2023
  source=IRS-derived Form 990-PF

Foundation to Promote Open Society --grant_payment_to--> Open Society Foundation London
  amount_usd=46999529
  fiscal_year=2022
  source=IRS e-file controlled-entity schedule

Open Society Foundation London --grant_payment_refund_to--> Foundation to Promote Open Society
  amount_usd=5668104
  fiscal_year=2022
  source=IRS e-file controlled-entity schedule
```

### Strong leads; direct filing-row capture still required

```text
Foundation to Promote Open Society --granted_to--> European Council on Foreign Relations
  amount_usd=17732000
  grant_id=OR2023-88176
  term_start=2023
  purpose="general support"

Open Society Institute --granted_to--> European Council on Foreign Relations
  amount_usd=5000000
  year=2022
  purpose="general support"

Fund For Policy Reform Inc --granted_to--> ECFR Deutschland GmbH
  amount_usd=1000261
  year=2020

Fund For Policy Reform Inc --granted_to--> ECFR Deutschland GmbH
  amount_usd=999774
  year=2021

Fund For Policy Reform Inc --granted_to--> ECFR Deutschland GmbH
  amount_usd=2132355
  year=2022
```

## 12. Next source-acquisition targets

1. Retrieve FPOS FY2023 Part XV / foreign-grant row for the $17.732m ECFR award and reconcile it to grant ID `OR2023-88176`.
2. Retrieve Open Society Institute FY2022 Part XV row for the reported $5m ECFR general-support grant.
3. Retrieve Fund For Policy Reform Inc FY2020–FY2022 foreign-grant schedules for ECFR Deutschland GmbH and capture recipient address, purpose, and exact amount from each filing.
4. Parse OSF London 2023–2025 accounts for related-party income, grant income, funder names, onward grants, and amounts.
5. Resolve whether ECFR's audited `Open Society Foundation` euro funding corresponds to FPOS, OSI, OSF London, another Open Society legal entity, or a mixture.
6. Resolve ECFR Deutschland's exact legal registry identifier and reconcile it to the audited ECFR group structure.
7. Resolve UK establishment `BR021288` against SEDF's U.S./foreign legal identity before any alias or parent relation is created.

## Analytic guardrails

- Do not sum grant commitments, annual payments, and audited income unless the accounting basis and period align.
- Do not treat a grant award as proof of policy control or misconduct.
- Do not collapse OSI, FPOS, Fund For Policy Reform, OSF London, or SEDF into aliases merely because they share the Open Society network.
- Preserve filer legal names and registry/tax identifiers exactly.
- Preserve refund flows as separate events.
- Historical OSF grant IDs are source-recovery keys, not substitutes for captured primary evidence.
