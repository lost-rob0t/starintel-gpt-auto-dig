# Brett Leatherman — adverse policy recursion depth 2

**Dataset:** `fed`  
**Pass:** adverse depth 2  
**Date:** 2026-07-31  
**Schema:** StarIntel v0.9.0  
**Records:** 3

## Trump-era cyber-policy contradiction

Leatherman publicly fronts the administration's cyber strategy and the FBI's offensive disruption model. During the same period, the Trump administration reduced CISA's workforce and capabilities, proposed further major budget cuts, left the agency without stable confirmed leadership for an extended period, and shifted parts of the federal cyber agenda away from CISA.

The contradiction is straightforward:

```text
Public position:
  raise national cyber resilience and impose costs on adversaries

Government operating context:
  weaken the principal civilian agency responsible for asset response and infrastructure defense
```

This creates policy and leadership-accountability exposure for Leatherman because he publicly promotes the combined administration/FBI strategy while the civilian defensive side is materially weakened.

It does **not** establish that Leatherman designed, requested or supported the CISA cuts. FBI threat response and CISA asset response are legally distinct missions, and public evidence reviewed does not show his private position on CISA funding.

## Outside-employment check

Public bios confirm that Leatherman has simultaneously served as a Georgetown adjunct professor while holding senior FBI roles. No public evidence reviewed established an ethics violation, undisclosed payment, procurement conflict or misuse of office connected to that teaching role. It remains a disclosure/ethics-record lead rather than an adverse finding.

## Records

- `starintel:claim:leatherman-fronted-cyber-strategy-amid-cisa-cuts`
- `starintel:analysis:brett-leatherman-adverse-policy-context-2026-07-31`
- `starintel:research-pass:brett-leatherman-adverse-depth-2-2026-07-31`

## Validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-07-31-brett-leatherman-adverse-depth-2/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
