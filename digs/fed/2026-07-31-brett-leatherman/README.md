# Brett Leatherman — FED investigation

**Dataset:** `fed`  
**Passes:** FED depth 0 plus WEF recursion depths 1–3  
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
- A plaintiff-controlled site describes a pending case, *Lacroix v. Leatherman*, and labels its allegations unproven. The FED packet stores it only as a low-confidence litigation lead.
- Published court opinions describe Leatherman investigating fraud and public corruption; the cited opinions do not identify misconduct by him.

## WEF recursion result

### Depth 1 — shared operation

```text
Brett Leatherman
  -> represented the FBI at the Operation Cronos / LockBit announcement
Operation Cronos
  -> was officially covered and amplified by WEF
```

### Depth 2 — division participation

```text
Brett Leatherman
  -> leads the FBI Cyber Division
FBI Cyber Division
  -> contributed experts to WEF's Partnership against Cybercrime study
World Economic Forum
  -> created and operates the Partnership against Cybercrime
```

### Depth 3 — organizational membership and named-person resolution

- An official WEF annex lists the **Federal Bureau of Investigation** as a Partnership against Cybercrime member organization.
- The 2020 report names the FBI contributors as **Steven Kelly** and **Mike Shanahan**.
- Brett Leatherman is not named in that contributor list.

The final classification is a **verified institutional WEF tie** through FBI organizational membership and Cyber Division participation. It does not support labeling Leatherman personally as a WEF member, employee, adviser, contributor or attendee.

See:

- `digs/wef/2026-07-31-brett-leatherman-operation-cronos-depth-1/README.md`
- `digs/wef/2026-07-31-brett-leatherman-fbi-cyber-division-depth-2/README.md`
- `digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/README.md`

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
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-fbi-cyber-division-depth-2/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
