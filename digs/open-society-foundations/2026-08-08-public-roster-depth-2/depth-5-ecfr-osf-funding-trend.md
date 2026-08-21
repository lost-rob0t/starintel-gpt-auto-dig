# Depth 5 — ECFR / Open Society Audited Core-Funding Trend

**Parent:** ECFR audited funding depth-4 pass  
**Run:** `2026-08-08`  
**Recursion:** depth 5 / configured target maximum 5  
**Status:** public-source evidence staging; canonical import pending

## Finding

ECFR's audited 2024 financial-statement note provides a two-year comparative for Open Society-labeled core funding:

| Year | Open Society core funds | ECFR total income | Core funds / total income |
|---|---:|---:|---:|
| 2023 | €2,233,798 | €7,694,227 | ~29.0% |
| 2024 | €2,497,698 | €8,703,244 | ~28.7% |

The disclosed core-funds amount increased by approximately **11.8%** year over year, while its share of ECFR's total income remained near 29%.

This supports a persistent, material core-funding relationship across at least the two audited periods directly exposed in the 2024 filing. It is stronger evidence than a one-year donor-list snapshot.

## Accounting guard

The 2024 Directors' Report separately says `The Open Society Foundation` provided a rounded **€3.7m unrestricted grant** in 2024.

Do not add €3.7m and €2.497698m. The filing does not establish that the core-funds figure is separate from the broader unrestricted grant. Treat them as two descriptions/accounting claims until reconciled.

## Legal-entity resolution remains open

The audited filing uses the singular label **Open Society Foundation**. OSF's public grant database demonstrates that grants are made by multiple legal funders, including entities such as Foundation to Promote Open Society and Open Society Institute, and OSF's database documentation says the displayed funder identifies the specific legal entity that made a grant.

Indexed web search during this pass did not surface an OSF Awarded Grants entry for `European Council on Foreign Relations`. That absence is **not evidence that no grant record exists** because:

- the OSF directory contains 20,566 records and uses interactive search/pagination;
- OSF explicitly states that some grants/descriptions and some national/regional foundation grants may be omitted;
- the ECFR audited accounts independently prove Open Society-labeled funding.

Therefore the exact legal OSF entity behind ECFR's audited `Open Society Foundation` label remains unresolved.

## Maximum-depth assessment

The root target's configured recursion maximum is five. At depth 5, the strongest defensible chain is:

```text
Open Society Foundations
    ├─ supported creation of ECFR (OSF history, 2006)
    ├─ current donor to ECFR (ECFR donor page)
    ├─ audited core support to ECFR
    │    ├─ 2023: €2,233,798 (~29.0% of ECFR income)
    │    └─ 2024: €2,497,698 (~28.7% of ECFR income)
    └─ 2024 Directors' Report: rounded €3.7m unrestricted grant

ECFR
    ├─ multi-entity European group
    ├─ UK charity 1143536 / company 07154609
    ├─ German ECFR e.V. governance layer
    ├─ five non-UK legal ECFR entities disclosed in audited report
    └─ 2024 internal flows: €4.3m regranted out / €1.3m received from other ECFR entities
```

Alongside that institution-level chain, current person-level cross-ties include OSF/ECFR Council, website-board, and fellowship roles documented in the parent packets.

## What is established

- Open Society support was material to ECFR in both 2023 and 2024.
- The precise core-funding figure rose 11.8% year over year.
- Core support represented roughly 29% of ECFR total income in both years.
- ECFR described a broader rounded €3.7m unrestricted Open Society grant in 2024.
- OSF says it supported ECFR's creation in 2006.
- ECFR currently lists OSF as a donor.

## What is not established

- the exact OSF legal entity behind the audited funder label;
- whether the €2.497698m core-funds disclosure is wholly contained inside the €3.7m unrestricted grant, though that is a plausible accounting interpretation;
- donor control over ECFR editorial decisions, programs, research conclusions, or governance;
- an OSF-specific amount for the collectively described `>€300k` restricted-donation group;
- a complete consolidated financial picture of every ECFR legal entity.

## Follow-up queue beyond configured recursion

Do not automatically recurse further from this target. Queue separately if approved:

- deterministic OSF grant-database extraction and entity resolution;
- ECFR 2020–2023 audited filing extraction for a longer time series;
- German ECFR e.V. registry/accounts and exact legal-entity map;
- source-backed tracing of ECFR inter-entity regrants;
- exact Open Society legal funder resolution.

## Validation status

Research staging only. No normalized `db/` record was hand-written. Canonicalization must use the repository-approved writer/import path and pass `python3 scripts/validate-for-merge.py --site` on the exact PR head.
