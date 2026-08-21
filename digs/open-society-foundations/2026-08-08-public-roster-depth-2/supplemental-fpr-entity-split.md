# Fund for Policy Reform: same-ish name, two actual entities

**Run:** `2026-08-08`  
**Parent:** OSF public-roster and cross-ties supplemental pass  
**Status:** evidence staging; not canonical

## What happened

Public IRS filings expose two legally distinct 501(c)(4)s whose names are almost designed to make entity resolution miserable:

1. **Fund for Policy Reform** - EIN `35-7090597`, Delaware, tax-exempt since 2015.
2. **Fund For Policy Reform Inc** - EIN `26-4351242`, New York, tax-exempt since 2009.

> same name with one extra `Inc`
>
> definitely separate legal filers
>
> Delaware entity sends New York entity hundreds of millions
>
> please do not merge them because string similarity felt persuasive

They are not aliases.

## Follow the money

IRS-derived grant data reports the Delaware entity granting the New York Inc entity:

| Fiscal year | Amount |
|---|---:|
| 2020 | $196,000,000 |
| 2021 | $375,000,000 |
| 2022 | $332,700,000 |
| 2023 | $327,000,000 |
| 2024 | $412,000,000 |

Observed five-year total: **$1,642,700,000**.

That is the arithmetic sum of five filing-year grants. It is not lifetime funding and it is not proof of where every downstream dollar ultimately went.

## Delaware side: EIN 35-7090597

FY2024 filing-derived figures:

- assets: about **$3.258B**;
- net assets: about **$3.030B**;
- 2024 grant to FPR Inc: **$412M**;
- no FY2024 revenue reported on Part VIII in the extracted filing summary;
- principal program described as social-welfare grantmaking.

Filing-year governance includes Bryn Mawr Trust as Administrative Trustee, Debbie Fine as Secretary from 2024-01-17, Maija Arbolino as Treasurer, Binaifer Nowrojee as Trustee from 2024-12-01, and Leonard Benardo as Trustee until that date.

Those are dated filing roles, not eternal character classes.

## New York side: EIN 26-4351242

FY2024 filing-derived figures:

- revenue: about **$470.129M**;
- expenses: about **$265.977M**;
- net assets: about **$819.344M**;
- contributions and grants: about **$415.965M**;
- **$412M** attributed to Fund for Policy Reform for FY2024.

The filing identifies Pedro Abramovay as Vice President, Programs; Maija Arbolino as Treasurer; Binaifer Nowrojee as Director from 2024-12-01; Leonard Benardo as Director until 2024-12-01; plus additional program directors/managers.

## The synchronized handoff

Both filers report the same date:

```text
2024-12-01
Leonard Benardo   -> out of trustee/director role
Binaifer Nowrojee -> into trustee/director role
```

That is strong evidence the entities are operationally related alongside the direct grant chain. It does **not** establish legal identity or automatically prove one controls the other.

## OSF leadership bridge

The filings overlap with current/recent OSF leadership already mapped in the parent packet:

- Binaifer Nowrojee - OSF president;
- Leonard Benardo - OSF senior leadership;
- Debbie Fine - OSF general counsel / board secretary;
- Maija Arbolino - recurring OSF-network treasury role in filings;
- Pedro Abramovay - OSF VP, Programs and FPR Inc VP, Programs.

Those are filing or first-party roles, not inferred associations.

## ECFR Deutschland lead

A still-unresolved Candid-backed series attributes these grants to FPR Inc and ECFR Deutschland GmbH:

```text
2020  $1,000,261
2021    $999,774
2022  $2,132,355
```

Direct Schedule F capture is still required before those recipient rows become canonical. The simplified IRS-derived profile confirms foreign-grant spending but does not expose the needed rows in the displayed Schedule I table.

## Canonicalization rule

```text
starintel:org:fund-for-policy-reform
  EIN=35-7090597

starintel:org:fund-for-policy-reform-inc
  EIN=26-4351242
```

Then model the annual 2020-2024 `granted_to` edges between them. **Do not collapse the two organizations into one ID.**

## Next dig

1. Capture Schedule R relationship statements between the two entities where reported.
2. Capture FPR Inc Schedule F entries for ECFR Deutschland in 2020-2022.
3. Check 2023-2024 for later ECFR / ECFR Deutschland grants.
4. Resolve ECFR Deutschland's German registry number and audited group relation.
5. Reconcile OSF leadership-role dates across OSI, FPOS, FPR, FPR Inc, and OSF London.

## Sources

- https://projects.propublica.org/nonprofits/organizations/357090597
- https://philanthropy.org/990/report/357090597/fund-for-policy-reform
- https://projects.propublica.org/nonprofits/organizations/264351242
- https://philanthropy.org/990/report/264351242/fund-for-policy-reform-inc

## Evidence boundary

Repeated funding and shared officers establish documented organizational connections. They do not by themselves establish improper coordination, hidden control, or misconduct.
