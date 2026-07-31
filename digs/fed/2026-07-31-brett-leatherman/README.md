# Brett Leatherman — FED depth-0 investigation

**Dataset:** `fed`  
**Pass:** depth 0  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 4

## Result

Brett Leatherman is added to the `fed` research packet as the assistant director of the FBI Cyber Division.

### Confirmed

- FBI primary sources confirm his current role and his earlier role overseeing the Cyber Operations Branch.
- Two independent reports say FBI Director Kash Patel selected or elevated him to lead the Cyber Division in June 2025.
- FBI primary material shows Leatherman publicly implementing and explaining President Trump's Cyber Strategy for America.

### Bounded findings

- The Trump connection is institutional: appointment chain and policy implementation. This pass found no evidence establishing a personal political affiliation, campaign role or private relationship with Trump.
- No direct personal World Economic Forum profile, event appearance, membership, authorship, employment or named initiative role was found.
- WEF materials show generic overlap with the FBI and law-enforcement cyber ecosystem. That is not enough to cross-add Leatherman to dataset `wef`.
- No credible adjudicated corruption or misconduct finding involving Leatherman was located.
- A plaintiff-controlled site describes a pending case, *Lacroix v. Leatherman*, and explicitly says its allegations are unproven. The packet stores it only as a low-confidence litigation lead.
- Published court opinions describe Leatherman investigating fraud and public corruption; the cited opinions do not identify misconduct by him.

## Records

- `starintel:person:brett-leatherman`
- `starintel:analysis:brett-leatherman-trump-wef-corruption-scan-2026-07-31`
- `starintel:investigation-target:brett-leatherman-depth-1`
- `starintel:research-pass:brett-leatherman-fed-depth-0-2026-07-31`

## WEF decision

**Do not add to `wef` at depth 0.** The current evidence supports only generic FBI-WEF institutional overlap. The queued depth-1 target includes exact-name WEF conference, initiative and contributor checks.

## Import and validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman/starintel-documents.jsonl

python3 scripts/validate-for-merge.py --site
```
