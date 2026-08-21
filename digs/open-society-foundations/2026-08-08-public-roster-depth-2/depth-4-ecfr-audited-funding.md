# Depth 4 — ECFR Audited Funding and Legal-Entity Structure

**Parent:** OSF ↔ ECFR institutional cluster  
**Run:** `2026-08-08`  
**Primary source:** Charity Commission for England and Wales, ECFR charity 1143536, audited accounts for year ended 31 December 2024  
**Status:** public-source evidence staging; canonical import pending

## Executive finding

The current donor relationship between Open Society and ECFR is quantifiable from ECFR's audited 2024 accounts.

ECFR reported total 2024 income of **€8,703,244**. In its Directors' Report, ECFR states that **“The Open Society Foundation provided an unrestricted grant of €3.7m to support ECFR.”** That rounded figure is approximately **42.5% of ECFR's total 2024 income**.

The financial-statement notes separately state that ECFR is grateful for the continuing support of **“the Open Society Foundation” for core funds of €2,497,698**, compared with €2,233,798 in 2023. That disclosed core-funds figure is approximately **28.7% of total 2024 income**.

These two figures must **not** simply be added together. The €2.4977m core-funds disclosure may be a component or characterization of the broader €3.7m unrestricted grant. The filing does not establish that they are disjoint cash flows.

The filing uses the singular label `Open Society Foundation`. Until the exact OSF legal funding entity is identified from grant records or an underlying agreement, preserve the audited label as reported rather than automatically resolving it to a specific foundation company.

## 1. Audited income and expenditure

ECFR's 2024 Statement of Financial Activities reports:

| Item | 2024 |
|---|---:|
| Total income | €8,703,244 |
| Grants / charitable activities income | €8,529,717 |
| Donations and legacies / gifts in kind | €171,250 |
| Total expenditure | €9,058,410 |
| Net expenditure before other gains | €355,166 deficit |
| Net movement in funds | €106,214 deficit |
| Funds carried forward | €2,852,368 |

The Directors' Report rounds total income to €8.7m and expenditure to €9.1m.

## 2. Open Society funding disclosed by ECFR

### Broad unrestricted grant

ECFR's Directors' Report states:

> The Open Society Foundation provided an unrestricted grant of €3.7m to support ECFR.

The Statement of Financial Activities reports total unrestricted grants of €3,687,744. The narrative's rounded €3.7m OSF grant is therefore approximately the size of the entire unrestricted-grant line for the year.

**Do not substitute €3,687,744 as an exact OSF-specific amount.** The audited narrative gives the OSF-specific figure only as a rounded €3.7m.

### Core-funds note

Note 2, Analysis of Income, separately reports continuing Open Society Foundation core funds of:

- **2024:** €2,497,698
- **2023:** €2,233,798

This is a precise audited figure, but its relationship to the rounded €3.7m unrestricted-grant disclosure must be resolved before modeling multiple transactions.

### Restricted funding

The Directors' Report says restricted donations of more than €300,000 were received from the Open Society Foundation, the Norwegian Ministry of Foreign Affairs, Stand Together Trust, and the Swedish Ministry of Foreign Affairs.

The wording does not assign the entire `>€300k` amount to Open Society, nor does it disclose an OSF-specific restricted amount. Do not infer one.

## 3. Program spending

ECFR's 2024 audited expenditure by charitable activity was:

| Program | 2024 expenditure |
|---|---:|
| European Power | €3,275,543 |
| Middle East & North Africa | €1,179,294 |
| Wider Europe | €560,753 |
| Advocacy & National Offices | €355,883 |
| Africa | €330,828 |
| US | €318,296 |
| Asia & China | €74,756 |
| Regrant | €2,963,057 |

The filing does not trace the Open Society grant to a specific one of these expenditure lines. An unrestricted grant should not be assigned to a program without a source-backed allocation.

## 4. Restricted-fund income by program

ECFR reported €4,841,973 of restricted income in 2024, allocated in the restricted-funds note as:

| Program | Restricted income |
|---|---:|
| European Power | €2,622,240 |
| Middle East & North Africa | €950,223 |
| US | €533,418 |
| Africa | €500,644 |
| Wider Europe | €170,439 |
| Asia & China | €65,009 |

Again, the filing does not identify which donor supplied which restricted-program amount in this table. Avoid donor-program attribution without a separate grant source.

## 5. ECFR is a multi-entity group

The audited Directors' Report says the UK charity is part of the first pan-European think-tank and a **Group of ECFR entities**.

The filing states that ECFR is made up of the UK company plus **five legal ECFR entities established in Germany, France, Spain, and Italy**, under the common control and unified management of the German **ECFR e.V. Board of Trustees**.

It also reports substantial inter-entity flows in 2024:

- the UK charity **re-granted €4.3m to other ECFR entities**;
- it **received €1.3m from other ECFR entities**;
- year-end ECFR Group debtors were **€9,437,182**;
- year-end ECFR Group creditors were **€9,185,066**.

These are group/internal financial relationships, not external grants to unrelated organizations.

### Modeling implication

Do not represent `European Council on Foreign Relations` as a single legal entity when financial or statutory claims are being modeled. At minimum distinguish:

- the UK charity/company, charity no. `1143536`, company no. `07154609`;
- German ECFR e.V.;
- the other disclosed legal ECFR entities in France, Spain, Italy, and Germany once their exact registered names and identifiers are resolved;
- the umbrella/public-facing ECFR organization identity.

## 6. Legal trustees vs public website board

The Charity Commission's **current** trustee register for UK charity 1143536 lists three legal trustees:

- Lykke Friis — Chair;
- Adam Thomas Lury — Trustee;
- Ian Clarkson — Trustee.

The 2024 audited report also listed Teresa Gouveia as a trustee/director at year end, indicating she has since left the current UK charity register.

By contrast, ECFR's current public website has a broader `Board of Trustees` roster including Ivan Krastev and others.

These surfaces should not be collapsed:

```text
UK charity 1143536 --legal_trustee--> Lykke Friis
UK charity 1143536 --legal_trustee--> Adam Thomas Lury
UK charity 1143536 --legal_trustee--> Ian Clarkson
public-facing ECFR / ECFR group --website_board_member--> Ivan Krastev
```

The precise legal entity governed by the website's broader board should be resolved from ECFR's constitutional/group records before assigning a statutory-director or UK-charity-trustee predicate.

## 7. Current governance and management snapshot from the audit

At 31 December 2024 the UK charity's Directors' Report identified:

- Lykke Friis — Chair of Board of Trustees/Directors;
- Ian Clarkson — Trustee/Director and Chair of Executive Committee;
- Teresa Gouveia — Trustee/Director;
- Adam Lury — Trustee/Director;
- Mark Leonard — Programme Director / key management personnel.

The audited filing is historical as of 31 December 2024. Use the current Charity Commission register for present-tense UK legal trustees.

## 8. Financial scale of the OSF → ECFR edge

Two defensible ratios, with different meanings:

```text
rounded OSF unrestricted grant / total ECFR income
€3.7m / €8.703244m ≈ 42.5%

precise disclosed OSF core funds / total ECFR income
€2.497698m / €8.703244m ≈ 28.7%
```

The first is the broader rounded grant disclosed by the Directors' Report. The second is a precise `core funds` figure in Note 2. They should be stored as separate source claims until their accounting relationship is resolved.

## 9. What this changes in the OSF ↔ ECFR assessment

Before the audit, current first-party web evidence established that OSF was an ECFR donor and that OSF says it supported ECFR's creation in 2006.

The audited filing upgrades the funding edge from qualitative to quantitative: **Open Society was a major disclosed source of ECFR support in 2024**, with a rounded unrestricted grant equal to roughly 42.5% of ECFR's total income and a separately disclosed €2.4977m core-funds figure.

That is evidence of material funding. It is **not** evidence that OSF controlled ECFR's editorial decisions, programs, governance, or spending. The accounts expressly characterize the €3.7m grant as unrestricted, and no source reviewed in this pass demonstrates donor control over particular ECFR outputs.

## 10. Depth-5 targets

1. **Resolve the exact Open Society legal funder** behind ECFR's audited `Open Society Foundation` label using OSF grant records, ECFR grant agreements, or statutory filings.
2. **Reconcile €3.7m vs €2.497698m** — determine whether core funds are a component of the unrestricted grant and identify any additional unrestricted OSF support.
3. **Map all five non-UK ECFR legal entities** with exact registration identifiers and intercompany relationships.
4. **Retrieve ECFR e.V. German filings** and governance records to resolve which entity the broader public website Board of Trustees legally governs.
5. **Trace 2024 inter-entity regrants** where public accounts identify destination legal entities and amounts.
6. **Build audited donor history 2020–2024** from successive Charity Commission filings to quantify Open Society support longitudinally rather than from a single year.

## Source index

- Charity Commission for England and Wales — ECFR charity 1143536, Accounts and Annual Returns
- ECFR — Report and Financial Statements for the Year Ended 31 December 2024, filed 8 October 2025
- Charity Commission for England and Wales — current Trustees, ECFR charity 1143536
- ECFR — current public Board of Trustees / About page

## Validation status

Research staging only. No normalized `db/` record was hand-written. Canonicalization must use the repository-approved writer/import path and pass `python3 scripts/validate-for-merge.py --site` on the exact PR head.
