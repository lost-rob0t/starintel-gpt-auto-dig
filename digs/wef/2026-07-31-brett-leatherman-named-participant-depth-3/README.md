# Brett Leatherman — WEF named-participant verification depth 3

**Dataset:** `wef`  
**Pass:** depth 3 of 3  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 4

## Final result

The final recursion pass did not find Brett Leatherman named personally in the World Economic Forum's 2020 Partnership against Cybercrime contributor list.

The report names the FBI contributors as **Steven Kelly** and **Mike Shanahan**.

A later official WEF Partnership against Cybercrime report lists the **Federal Bureau of Investigation** among the initiative's member organizations.

## Strongest verified path

```text
Brett Leatherman
  -> leads the FBI Cyber Division
FBI Cyber Division
  -> contributed experts to WEF's Partnership against Cybercrime study
Federal Bureau of Investigation
  -> listed by WEF as a Partnership against Cybercrime member organization
World Economic Forum
  -> created and operates the Partnership against Cybercrime
```

## Classification

- **Institutional WEF tie:** verified.
- **FBI organizational membership in WEF PAC:** verified from the official WEF annex.
- **FBI Cyber Division participation in the 2020 WEF study:** verified from the FBI director's official remarks.
- **Brett Leatherman personally named as a WEF contributor, member, adviser or attendee:** not established.
- **Inference that Leatherman personally participated because he later became division head:** rejected.

The WEF record is retained because the organizational chain is real and relevant. It must not be represented as personal WEF membership.

## Records

- `starintel:relation:fbi-member-of-wef-partnership-against-cybercrime`
- `starintel:analysis:brett-leatherman-wef-named-participant-resolution-depth-3-2026-07-31`
- `starintel:claim:wef-2020-report-names-fbi-contributors-kelly-shanahan`
- `starintel:research-pass:brett-leatherman-wef-depth-3-2026-07-31`

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
