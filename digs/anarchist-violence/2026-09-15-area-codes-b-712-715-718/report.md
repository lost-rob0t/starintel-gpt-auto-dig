# Area-code sweep shard B — NPAs 712, 715, 718

Issue: #2341  
Worker: 5/8  
Run: `area-code-hunt-b-712-715-718-2026-09-15`

## Coverage decision

Current NANPA reporting remains the admission authority for in-service U.S. geographic NPAs. Starting from the durable shard-B completed set through 706, the next eligible numeric batch is **712, 715, 718**. Each satisfies `NPA mod 3 == 1`; non-geographic 710 and Canadian 709 are excluded rather than treated as arithmetic candidates.

This pass marks each code completed only after bounded corpus-first search, current-source review, identity dedupe, packet creation, and provenance recording.

## 712 — western Iowa / Sioux City

### Support Siouxland Soldiers

The current first-party site identifies Support Siouxland Soldiers as a 100% volunteer-run nonprofit founded by military families in 2007. Its current 2026 calendar lists Sioux City food-pantry and community-support events, and the organization describes grocery distributions, hot meals, emergency resources, and peer-to-peer mutual support for the Siouxland military community.

Source:
- https://supportsiouxlandsoldiers.com/

Canonicalization:
- new org: `starintel:org:support-siouxland-soldiers`
- new target: `starintel:investigation-target:support-siouxland-soldiers-area-code-expansion`
- NPA relation: `starintel:relation:support-siouxland-soldiers-enumerated-from-npa-712-worker5-20260915`

Boundary: this is community-support discovery, not evidence of anarchist, anti-authoritarian, or other political identity. No political label or individual affiliation is inferred.

## 715 — Eau Claire / northern Wisconsin

### Power Up Eau Claire

The current first-party site describes Power Up Eau Claire as a 501(c)(3) serving the HMoob/Hmong community in the greater Chippewa Valley through culturally rooted programming, leadership development, advocacy, community organizing, community care, mutual-aid efforts, and rapid-response support. The organization publishes an Eau Claire address inside the 715/534 overlay region.

Source:
- https://www.powerupec.org/about-us

Canonicalization:
- new org: `starintel:org:power-up-eau-claire`
- new target: `starintel:investigation-target:power-up-eau-claire-area-code-expansion`
- NPA relation: `starintel:relation:power-up-eau-claire-enumerated-from-npa-715-worker5-20260915`

Boundary: preserve the organization's own descriptions of advocacy, grassroots organizing, community care, and mutual aid. Do not convert those descriptions into an inferred anarchist label or infer political affiliation for any individual.

## 718 — Brooklyn / outer-borough New York City

### Bed-Stuy Strong

The current first-party site describes Bed-Stuy Strong as a neighborhood mutual-aid network founded in March 2020, with more than 3,000 neighbors participating in solidarity-oriented community support. Its public materials describe current member infrastructure, neighborhood resource-sharing, community initiatives, and a Central Brooklyn / Bedford-Stuyvesant geographic focus inside the 718/347/917/929/465 overlay region.

Sources:
- https://www.bedstuystrong.com/
- https://www.bedstuystrong.com/principles/

Canonicalization:
- new org: `starintel:org:bed-stuy-strong`
- new target: `starintel:investigation-target:bed-stuy-strong-area-code-expansion`
- NPA relation: `starintel:relation:bed-stuy-strong-enumerated-from-npa-718-worker5-20260915`

Boundary: Bed-Stuy Strong's public site discusses solidarity, mutual aid, political education, and civic engagement. Those organization-level descriptions are preserved without inferring the political affiliation of members or turning neighborhood membership into a person-level political relation.

## Result

- codes completed: **3**
- useful-hit codes: **3/3**
- organizations represented: **3**
- new canonical orgs: **3**
- reused canonical orgs: **0**
- new organization-expansion targets: **3**
- person records created: **0**
- inferred person→organization relations: **0**

The durable shard-B ledger advances through **718** only with this packet and canonical importer materialization. Future passes must recompute the live NANPA geographic set before selecting the next unresolved batch.
