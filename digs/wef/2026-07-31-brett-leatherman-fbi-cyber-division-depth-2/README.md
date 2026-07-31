# Brett Leatherman — WEF institutional recursion depth 2

**Dataset:** `wef`  
**Pass:** depth 2  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 9

## Stronger link established

Depth 1 found an event/content path through Operation Cronos.

Depth 2 found a stronger institutional path:

```text
Brett Leatherman
  -> leads the FBI Cyber Division
FBI Cyber Division
  -> contributed experts to WEF's Partnership Against Cybercrime study
World Economic Forum
  -> created and operates the Partnership Against Cybercrime
```

The critical primary-source statement is FBI Director Christopher Wray's November 16, 2020 address to the World Economic Forum. Wray said experts from the FBI Cyber Division participated in the Forum's Partnership Against Cybercrime study.

WEF's publication page states that WEF created the Partnership Against Cybercrime and assembled public- and private-sector stakeholders, including leading law-enforcement agencies.

## Classification

This is a **verified institutional division-level WEF tie**.

It is stronger than shared article coverage because an FBI organizational unit contributed personnel to a WEF study.

It does **not** establish that Brett Leatherman personally participated in the 2020 working group. The FBI statement does not name the participating Cyber Division experts.

## Records

- `starintel:org:federal-bureau-of-investigation`
- `starintel:org:fbi-cyber-division`
- `starintel:org:wef-partnership-against-cybercrime`
- `starintel:relation:brett-leatherman-leads-fbi-cyber-division`
- `starintel:relation:fbi-cyber-division-contributed-to-wef-partnership-against-cybercrime-study`
- `starintel:relation:world-economic-forum-operates-partnership-against-cybercrime`
- `starintel:analysis:brett-leatherman-wef-fbi-cyber-division-path-depth-2-2026-07-31`
- `starintel:research-pass:brett-leatherman-wef-depth-2-2026-07-31`
- `starintel:investigation-target:brett-leatherman-wef-named-participant-depth-3`

## Depth-3 resolution

The depth-3 pass found the named 2020 FBI contributors were Steven Kelly and Mike Shanahan, not Brett Leatherman, and verified the FBI as a WEF Partnership Against Cybercrime member organization.

See `digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/README.md`.

## Import and validation

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
