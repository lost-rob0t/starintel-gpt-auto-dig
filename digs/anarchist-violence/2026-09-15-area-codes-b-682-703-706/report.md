# Area-code sweep shard B — NPAs 682, 703, 706

Issue: #2341  
Worker: 5/8  
Run: `area-code-hunt-b-682-703-706-2026-09-15`

## Coverage decision

Current NANPA NPA Reports remains the admission authority for in-service geographic NPAs. After subtracting the durable shard-B completed set through 679, the next bounded numeric batch is **682, 703, 706**. Each satisfies `NPA mod 3 == 1`.

This pass marks a code completed only after bounded corpus-first search, source review, canonical identity dedupe, packet creation, and provenance recording.

## 682 — North Texas / Fort Worth

### La Colectiva NTX

Current first-party material describes La Colectiva NTX as a community-led North Texas initiative providing accompaniment, mutual support, resource navigation, practical assistance, and collective action outside the Dallas ICE Field Office. The organization publishes a 682 contact number.

Canonicalization:
- new org: `starintel:org:la-colectiva-ntx`
- new target: `starintel:investigation-target:la-colectiva-ntx-area-code-expansion`
- NPA relation: `starintel:relation:la-colectiva-ntx-enumerated-from-npa-682-worker5-20260915`

Boundary: the organization is preserved at its own community-support description. This pass does **not** label it anarchist and does not infer any individual's political affiliation or private membership.

### Fort Worth Community Collaborative

Current first-party material describes Fort Worth Community Collaborative (FWCC) as a community-care organization providing clothing, food, hygiene items, shared meals, mutual aid, and sustainable redistribution. Its Fort Worth public contact uses NPA 682.

Canonicalization:
- new org: `starintel:org:fort-worth-community-collaborative`
- new target: `starintel:investigation-target:fort-worth-community-collaborative-area-code-expansion`
- NPA relation: `starintel:relation:fort-worth-community-collaborative-enumerated-from-npa-682-worker5-20260915`

Boundary: no political or ideological label is inferred.

## 703 — Northern Virginia

Corpus-first search found the existing canonical organization `starintel:org:northern-virginia-mutual-aid`, so no duplicate org or target was created.

A public May 17, 2026 Action Network page identifies the Northern Virginia Mutual Aid Working Group and a mutual-aid distribution at Court House Metro in Arlington. This pass adds only the 703 overlay discovery relation:
- `starintel:relation:northern-virginia-mutual-aid-enumerated-from-npa-703-worker5-20260915`

The prior 571 identity and current 703 locality evidence are treated as the same organization in the 703/571 overlay region, not two entities.

## 706 — Athens / northeast Georgia

Corpus-first search found the existing canonical organization `starintel:org:athens-mutual-aid-network`, previously resolved from the 762 overlay, so no duplicate org or target was created.

A public Open Collective record shows a paid August 3, 2026 mutual-aid distribution expense for Athens Mutual Aid Network / Athens Housing Advocacy Team. This pass uses the public activity record only to corroborate current 2026 organizational activity and adds the 706 overlay discovery relation:
- `starintel:relation:athens-mutual-aid-network-enumerated-from-npa-706-worker5-20260915`

Private payout information is neither collected nor promoted.

## Result

- codes completed: **3**
- useful-hit codes: **3/3**
- organizations represented: **4**
- new canonical orgs: **2**
- reused canonical orgs: **2**
- new organization-expansion targets: **2**
- person records created: **0**
- inferred person→organization relations: **0**

The durable shard-B ledger advances through **706** only with this packet and its canonical importer materialization.
