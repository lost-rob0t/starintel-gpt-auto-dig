# ECFR — Historical Open Society Grant-ID Recovery Index

**Run:** `2026-08-08`  
**Status:** source-recovery evidence staging; not canonical financial ledger

## Purpose

Historical Open Society Foundations grant pages have moved or become difficult to retrieve. Wikidata currently preserves a set of ECFR funding statements whose references point to the old first-party OSF grant URLs and exact grant IDs.

This file treats those records as **source-recovery keys and award records**, not as proof that the full award amount was paid in the displayed calendar year or by a particular Open Society legal entity.

## Recovered reference index

| Display year | Amount | Purpose | Historical OSF grant ID |
|---|---:|---|---|
| 2023 | $17,732,000 | general support | `OR2023-88176` |
| 2023 | $250,000 | general support | `OR2022-87658` |
| 2022 | $2,132,355 | Unlock Europe's Majority | `OR2022-85024` |
| 2022 | $5,000,000 | general support | `OR2021-83857` |
| 2021 | $999,774 | nonpartisan Unlock Europe's Majority activities | `OR2021-80195` |
| 2020 | $2,500,000 | general support | `OR2020-76192` |
| 2020 | $1,000,261 | Unlock Europe's Majority | `OR2020-70385` |
| 2019 | $585,000 | Unlocking Europe's Hidden Internationalist Majority | `OR2019-50856` |
| 2019 | $136,304 | final phase of ECFR Unlocking Europe project | `OR2019-64873` |
| 2019 | $3,000,000 | general support | `OR2019-62721` |
| 2019 | $792,821 | Unlocking Europe's Hidden Internationalist Majority | `OR2019-62725` |
| 2018 | $500,000 | general support | `OR2018-45803` |
| 2017 | $3,000,000 | general support | `OR2017-34725` |
| 2016 | $95,000 | analytical framework relating to Palestinian rights | `OR2016-27844` |
| 2016 | $74,334 | EU military action / non-state armed groups research | `OR2015-25954` |

## Important temporal warning

The `ORYYYY-...` prefix does **not always equal the display year** preserved by the secondary reference. Examples include:

- display year 2022 / grant ID `OR2021-83857`;
- display year 2023 / grant ID `OR2022-87658`;
- display year 2016 / grant ID `OR2015-25954`.

Do not derive an award date from the ID prefix. Recover the underlying grant record and preserve its explicit dates/term.

## Award versus payment warning

The $5m general-support award indexed for 2022 (`OR2021-83857`) illustrates why this index cannot be treated as an annual cash ledger.

IRS-derived Open Society Institute data reports only **$5m total across two ECFR filing-year grant rows in 2022–2023**, with FY2023 explicitly $2.5m. The most defensible current model is therefore:

```text
OSF historical grant record: award/commitment = $5m
OSI tax filing: FY2022 payment/outlay = $2.5m [inferred from aggregate]
OSI tax filing: FY2023 payment/outlay = $2.5m [direct row]
```

The installment interpretation is plausible and reconciles the records, but the actual grant agreement/payment schedule remains to be recovered.

## Two recurring funding tracks

The historical reference index exposes at least two recurring categories:

1. **general support**;
2. **Unlock Europe / Unlock Europe's Majority / internationalist-majority work**.

These should remain separate grant/program relations even when the recipient umbrella is the same ECFR network.

## Legal-payer resolution status

- `OR2023-88176` — secondary grant indexes attribute the $17.732m award to **Foundation to Promote Open Society**; direct filer-row capture pending.
- `OR2020-70385`, `OR2021-80195`, `OR2022-85024` — secondary Candid-backed data attributes the Unlock Europe's Majority series to **Fund For Policy Reform Inc** and **ECFR Deutschland GmbH**; direct Schedule F capture pending.
- `OR2021-83857` — annual IRS-derived ECFR payments are present under **Open Society Institute**, but the full award/payment schedule needs first-party recovery before asserting that OSI is the legal party to the entire $5m commitment.

## Recovery strategy

For every grant ID:

1. query the old OSF URL directly;
2. search the OSF current grant database by exact ID, recipient, amount, and purpose;
3. search archived captures by exact URL;
4. cross-match the amount and recipient against OSI / FPOS / FPR Inc IRS filing rows;
5. preserve commitment and payment records as separate StarIntel documents or relation evidence.

## Primary-reference URL pattern

```text
https://www.opensocietyfoundations.org/grants/past?grant_id=<GRANT_ID>
```

## Current preservation source

- https://www.wikidata.org/wiki/Q1376496

The Wikidata statements cite the historical OSF grant pages and record retrieval on 21 January 2025. Their purpose here is source recovery; canonical financial facts should prefer restored first-party pages and filer-side public records whenever those can be recovered.
