# Brett Leatherman — FED investigation

**Dataset:** `fed`  
**Passes:** FED depth 0, adverse depths 1–2, plus WEF recursion depths 1–3  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0

## FED result

Brett Leatherman is added to the `fed` research packet as the assistant director of the FBI Cyber Division.

### Confirmed

- FBI primary sources confirm his current role and his earlier role overseeing the Cyber Operations Branch.
- Two independent reports say FBI Director Kash Patel selected or elevated him to lead the Cyber Division in June 2025.
- FBI primary material shows Leatherman publicly implementing and explaining President Trump's Cyber Strategy for America.

## Adverse-information result

### Depth 1 — personnel, litigation and operational accountability

The strongest verified personally inconvenient fact is a public statement by former FBI Cyber Division executive John Riggi. Riggi said he selected Leatherman over candidates with more tenure, **double promoted** him and predicted that he would eventually run the division. This documents unusually strong internal sponsorship and creates favoritism or patronage optics, but it does not establish a rules violation.

Additional adverse material:

- *Lacroix v. Leatherman*, No. 25-cv-13452, is a pending federal action alleging surveillance, harassment, abuse of authority and evidence misconduct. The allegations are plaintiff-controlled, disputed and unadjudicated.
- LockBit restored public infrastructure within five days of Operation Cronos, undercutting any permanent-elimination narrative even though the operation later damaged LockBit's affiliate trust and activity.
- BreachForums and successor communities repeatedly returned after FBI-led seizures, illustrating the displacement limits of the disruption strategy Leatherman publicly promotes.
- Salt Typhoon operated for years before discovery and compromised telecommunications and lawful-intercept information, creating institutional leadership-accountability exposure within Leatherman's mission portfolio. Public evidence does not establish personal causation.

### Depth 2 — Trump-era policy contradiction

Leatherman publicly fronts the administration's aggressive cyber strategy and the FBI's offensive disruption model. During the same period, CISA lost a substantial portion of its workforce, faced further proposed budget cuts and was sidelined in parts of the federal cyber agenda.

That creates a policy-accountability contradiction: publicly demanding stronger national cyber resilience while the administration weakens the principal civilian agency responsible for asset response and infrastructure defense.

No public evidence reviewed establishes that Leatherman designed, requested or supported the CISA cuts. The FBI and CISA also perform distinct missions.

Public bios confirm Leatherman concurrently taught as a Georgetown adjunct professor while holding senior FBI roles. No public evidence reviewed established an ethics violation, undisclosed payment, procurement conflict or misuse of office connected to that role.

No verified bribery, illicit payment, campaign-finance link or adjudicated personal-corruption finding was identified.

See:

- `digs/fed/2026-07-31-brett-leatherman-adverse-depth-1/README.md`
- `digs/fed/2026-07-31-brett-leatherman-adverse-depth-2/README.md`
- `starintel:analysis:brett-leatherman-adverse-information-2026-07-31`
- `starintel:analysis:brett-leatherman-adverse-policy-context-2026-07-31`

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
- `starintel:analysis:brett-leatherman-adverse-information-2026-07-31`
- `starintel:analysis:brett-leatherman-adverse-policy-context-2026-07-31`
- `starintel:investigation-target:brett-leatherman-depth-1`
- `starintel:research-pass:brett-leatherman-fed-depth-0-2026-07-31`
- `starintel:research-pass:brett-leatherman-adverse-depth-1-2026-07-31`
- `starintel:research-pass:brett-leatherman-adverse-depth-2-2026-07-31`

## Import and validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman-adverse-depth-1/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman-adverse-depth-2/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-operation-cronos-depth-1/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-fbi-cyber-division-depth-2/starintel-documents.jsonl
python3 scripts/starintel.py import \
  digs/wef/2026-07-31-brett-leatherman-named-participant-depth-3/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
