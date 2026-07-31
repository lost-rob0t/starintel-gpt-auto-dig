# Brett Leatherman — WEF bridge depth 1

**Dataset:** `wef`  
**Pass:** depth 1  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 5

## Link established

A documented two-edge path connects Brett Leatherman to the World Economic Forum:

```text
Brett Leatherman
  -> represented the FBI at the Operation Cronos / LockBit disruption announcement
Operation Cronos
  -> was officially covered and repeatedly amplified by the World Economic Forum
```

The FBI published Leatherman's remarks on February 20, 2024. WEF published a dedicated Operation Cronos article on February 21, 2024 and continued surfacing the operation through its Centre for Cybersecurity and Cybercrime Atlas materials.

## Classification

This is a **verified indirect operational/content tie**. It is sufficient to add the investigation and graph path to dataset `wef`.

It does **not** establish that Leatherman is a WEF member, employee, adviser, contributor, event participant or operational partner. It also does not establish that WEF directed or participated in Operation Cronos.

## Records

- `starintel:event:operation-cronos-lockbit-disruption-2024`
- `starintel:relation:brett-leatherman-represented-fbi-operation-cronos`
- `starintel:relation:world-economic-forum-covered-operation-cronos`
- `starintel:analysis:brett-leatherman-wef-operation-cronos-link-2026-07-31`
- `starintel:research-pass:brett-leatherman-wef-depth-1-2026-07-31`

The existing identity `starintel:person:brett-leatherman` is reused from the FED packet rather than duplicated.

## Import order and validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman/starintel-documents.jsonl

python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-operation-cronos-depth-1/starintel-documents.jsonl

python3 scripts/validate-for-merge.py --site
```
