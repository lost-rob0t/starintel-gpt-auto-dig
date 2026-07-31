# Brett Leatherman — FEC and pre-FBI employment pass

**Dataset:** `fed`  
**Pass:** depth 3  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0

## FEC result

Official OpenFEC Schedule A searches returned **zero itemized individual-contribution records** for both exact-name forms:

- `Brett Leatherman`
- `Leatherman, Brett`

Additional surname checks found no Brett match when constrained to:

- employer `FBI`
- employer `Federal Bureau of Investigation`
- Washington, D.C.
- Dallas or Frisco, Texas
- Detroit, Michigan
- Cleveland, Ohio

This is a bounded negative finding. It does not exclude unitemized contributions, filing errors, misspellings, contributions under an unknown middle name or initial, or records outside the federal FEC system.

## Employment result

Leatherman entered the FBI in 2003 and has remained within the Bureau across Cleveland, Detroit, Cyber Division and Dallas assignments. Public biographies also identify a concurrent adjunct-professor role at Georgetown University.

A March 2024 Lawfare interview adds a previously omitted lead: Leatherman said he had **worked in the cyber discipline before joining the Bureau** and was recruited after 9/11 because of that background. He did not identify the employer or company.

No reliable public source reviewed identifies the pre-FBI employer. Therefore:

- pre-FBI private-sector cyber employment is confirmed by Leatherman's own statement;
- the company remains unresolved;
- no private company should be assigned to him without another source.

## Records

- `starintel:claim:brett-leatherman-no-exact-name-fec-records-2026-07-31`
- `starintel:analysis:brett-leatherman-fec-employment-scan-2026-07-31`
- `starintel:research-pass:brett-leatherman-fec-employment-depth-3-2026-07-31`

## Import

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman-fec-employment-depth-3/starintel-documents.jsonl
```
