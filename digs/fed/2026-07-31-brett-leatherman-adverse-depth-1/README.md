# Brett Leatherman — adverse-information pass

**Dataset:** `fed`  
**Pass:** adverse depth 1  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 7

## High-signal inconvenient findings

### 1. Insider sponsorship and "double promotion"

A public LinkedIn comment by former FBI Cyber Division Outreach Section chief John Riggi says that roughly a decade earlier he selected Leatherman for an assistant section chief role over candidates with more tenure and "double promoted" him. Riggi said he predicted Leatherman would someday become assistant director.

This is verified evidence of unusually strong internal sponsorship and creates patronage/favoritism optics. It is not proof that rules were broken or that Leatherman was unqualified; Riggi explicitly defended the choice on expertise and leadership grounds.

### 2. Pending federal misconduct suit

`Lacroix v. Leatherman`, No. 25-cv-13452 in the District of Massachusetts, names Leatherman and other FBI officials. The plaintiff alleges covert surveillance, harassment, abuse of investigative authority, manufactured or unreliable evidence, and an internal misconduct inquiry.

The allegations are plaintiff-controlled, disputed and unadjudicated. The public case site itself says the allegations are unproven. This is adverse litigation exposure, not a substantiated misconduct finding.

### 3. Operation Cronos did not permanently remove LockBit

Leatherman represented the FBI at the February 2024 Operation Cronos announcement. LockBit restored a leak site and claimed renewed operations within five days using backups that were not seized.

Later reporting indicates the operation damaged LockBit's affiliate trust and reduced its activity. The inconvenient fact is that the immediate takedown did not deliver permanent elimination and some victory messaging proved too broad.

### 4. Repeated BreachForums whack-a-mole

Leatherman publicly promoted a later FBI seizure of BreachForums domains. The platform and successor versions had repeatedly returned after earlier FBI-led seizures, sometimes within weeks, while criminal users shifted toward Telegram and other channels.

This is a limitation of the disruption model he champions: takedowns impose cost but often relocate rather than eliminate the ecosystem.

### 5. Salt Typhoon accountability exposure

Leatherman held senior FBI roles overseeing state-sponsored cyber threats and later cyber operations. Salt Typhoon operated for years before discovery and ultimately penetrated major telecommunications providers, exposed call records and lawful-intercept information, and affected organizations across roughly 80 countries.

This is a serious institutional performance failure touching his portfolio during the campaign's later phase and public response. Public evidence does not establish that he personally caused the detection failure or controlled the full 2019–2024 period.

## Bottom line

The strongest adverse material is not a proven corruption case. It is:

- a documented internal sponsor describing a double promotion over more-tenured candidates;
- a pending federal misconduct lawsuit containing severe but unproven allegations;
- operational results that undercut permanent-takedown rhetoric;
- leadership accountability for major cyber failures and late detection within his mission area.

## Records

- `starintel:legal:lacroix-v-leatherman-25-cv-13452`
- `starintel:claim:john-riggi-double-promoted-brett-leatherman`
- `starintel:claim:operation-cronos-lockbit-returned-within-five-days`
- `starintel:claim:breachforums-repeatedly-returned-after-seizures`
- `starintel:claim:salt-typhoon-accountability-exposure-under-leatherman-portfolio`
- `starintel:analysis:brett-leatherman-adverse-information-2026-07-31`
- `starintel:research-pass:brett-leatherman-adverse-depth-1-2026-07-31`

## Validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman-adverse-depth-1/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
