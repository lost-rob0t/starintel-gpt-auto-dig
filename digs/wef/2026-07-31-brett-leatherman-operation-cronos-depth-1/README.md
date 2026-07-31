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
  -> was officially covered and amplified by the World Economic Forum
```

The FBI published Leatherman's remarks on February 20, 2024. WEF published dedicated Operation Cronos coverage on February 21, 2024 and continued surfacing the operation through its Centre for Cybersecurity and Cybercrime Atlas materials.

## Classification at this pass

This is a **verified indirect operational/content tie**. It does not establish that Leatherman is a WEF member, employee, adviser, contributor, event participant or operational partner. It also does not establish that WEF directed or participated in Operation Cronos.

Subsequent recursion strengthened the institutional path:

- Depth 2 verified FBI Cyber Division participation in WEF's Partnership against Cybercrime study.
- Depth 3 verified the FBI as a WEF Partnership against Cybercrime member organization and found that the named 2020 FBI contributors were Steven Kelly and Mike Shanahan, not Leatherman.

See:

- `digs/wef/2026-07-31-brett-leatherman-fbi-cyber-division-depth-2/README.md`
- `digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/README.md`

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
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-fbi-cyber-division-depth-2/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
