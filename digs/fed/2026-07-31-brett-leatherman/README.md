# Brett Leatherman — FED investigation

**Dataset:** `fed`  
**Passes:** depth 0 plus WEF bridge depth 1  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0

## FED result

Brett Leatherman is added to the `fed` research packet as the assistant director of the FBI Cyber Division.

### Confirmed

- FBI primary sources confirm his current role and his earlier role overseeing the Cyber Operations Branch.
- Two independent reports say FBI Director Kash Patel selected or elevated him to lead the Cyber Division in June 2025.
- FBI primary material shows Leatherman publicly implementing and explaining President Trump's Cyber Strategy for America.

### Corruption and scandal scan

- The Trump connection is institutional: appointment chain and policy implementation. No evidence reviewed establishes a personal political affiliation, campaign role or private relationship with Trump.
- No credible adjudicated corruption or misconduct finding involving Leatherman was located.
- A plaintiff-controlled site describes a pending case, *Lacroix v. Leatherman*, and explicitly says its allegations are unproven. The FED packet stores it only as a low-confidence litigation lead.
- Published court opinions describe Leatherman investigating fraud and public corruption; the cited opinions do not identify misconduct by him.

## WEF recursion result

Depth 0 found no direct personal WEF profile, membership, employment, advisory role, authorship or event appearance.

Depth 1 established a bounded two-edge path:

```text
Brett Leatherman
  -> represented the FBI at the Operation Cronos / LockBit announcement
Operation Cronos
  -> was officially covered and repeatedly amplified by WEF
```

This supports adding the graph path and investigation to dataset `wef` as an **indirect operational/content tie**. It does not support labeling Leatherman a WEF member, employee, adviser, contributor or participant.

See:

- `digs/wef/2026-07-31-brett-leatherman-operation-cronos-depth-1/README.md`
- `starintel:analysis:brett-leatherman-wef-operation-cronos-link-2026-07-31`

## FED records

- `starintel:person:brett-leatherman`
- `starintel:analysis:brett-leatherman-trump-wef-corruption-scan-2026-07-31`
- `starintel:investigation-target:brett-leatherman-depth-1`
- `starintel:research-pass:brett-leatherman-fed-depth-0-2026-07-31`

## Import and validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman/starintel-documents.jsonl

python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-operation-cronos-depth-1/starintel-documents.jsonl

python3 scripts/validate-for-merge.py --site
```
