# Area-code sweep shard B — NPAs 724, 727, 730

Issue: #2341  
Worker: 5/8  
Run: `area-code-hunt-b-724-727-730-2026-09-15`

## Coverage decision

Current NANPA reporting remains the admission authority for in-service U.S. geographic NPAs. Starting from the durable shard-B completed set through 718, the next eligible numeric batch is **724, 727, 730**. Each satisfies `NPA mod 3 == 1`. NPA 721 is excluded because NANPA assigns it to Sint Maarten rather than the United States.

NANPA's current annual reporting lists Pennsylvania 724/878, Florida 727, and Illinois 618/730; current planning-letter reporting also retains the 730 overlay of 618. This pass marks each code completed only after bounded corpus-first search, current-source review, identity dedupe, packet creation, and provenance recording.

## 724 — Westmoreland / southwestern Pennsylvania

### Grassroots Westmoreland

The current first-party site describes Grassroots Westmoreland as a community-powered nonprofit serving Westmoreland County through practical support, shared resources, civic education, mutual-aid coordination, community care, and nonviolent community-led action. Its public pages show active 2026 programs and events across Westmoreland County, inside the Pennsylvania 724/878 service region.

Sources:
- https://www.grassrootswestmoreland.org/
- https://www.grassrootswestmoreland.org/about

Canonicalization:
- new org: `starintel:org:grassroots-westmoreland`
- new target: `starintel:investigation-target:grassroots-westmoreland-area-code-expansion`
- NPA relation: `starintel:relation:grassroots-westmoreland-enumerated-from-npa-724-worker5-20260915`

Boundary: preserve the organization's own mutual-aid, civic-education, collective-action, and nonviolent community-action descriptions. Do not relabel it anarchist or infer political affiliation for volunteers, participants, partners, or beneficiaries.

## 727 — Pinellas / St. Petersburg–Clearwater, Florida

### Progressive People's Action

The current organization Linktree self-describes Progressive People's Action as **“Mutual aid in Pinellas FL”** and exposes current public organizational channels, a free-store wishlist, community-needs material, overdose-reversal reporting, and public health-resource links. Pinellas County is the core 727 service region.

Source:
- https://linktr.ee/progressivepeoplesaction

Canonicalization:
- new org: `starintel:org:progressive-peoples-action-pinellas`
- new target: `starintel:investigation-target:progressive-peoples-action-pinellas-area-code-expansion`
- NPA relation: `starintel:relation:progressive-peoples-action-pinellas-enumerated-from-npa-727-worker5-20260915`

Boundary: this is organization-level public mutual-aid discovery. Do not infer ideology, affiliation, health status, or other attributes for any individual from organizational proximity or use of public resources.

## 730 — southern Illinois 618/730 overlay

### DITO — Downstate Illinois Trans Organization

The current public organization Bluesky profile identifies DITO as the Downstate Illinois Trans Organization, says it provides mutual aid, social support, resources, and safe spaces, and locates the organization in Carbondale, Illinois. Independent current 2026 public reporting also describes DITO as a Carbondale mutual-aid and social-connection network. Carbondale lies in southern Illinois within the 618/730 overlay region.

Sources:
- https://bsky.app/profile/iltransorg.bsky.social
- https://main-stream.org/illinois-dailies-for-3-28-26-carbondales-tdov-dinner-community-baby-shower-isu-students-security-concerns/

Canonicalization:
- new org: `starintel:org:downstate-illinois-trans-organization`
- new target: `starintel:investigation-target:downstate-illinois-trans-organization-area-code-expansion`
- NPA relation: `starintel:relation:downstate-illinois-trans-organization-enumerated-from-npa-730-worker5-20260915`

Boundary: preserve only the organization's public self-description and locality. Create no person records, do not infer any individual's gender identity, political affiliation, membership, health status, or private contact information, and do not relabel the organization anarchist absent explicit organization-level evidence.

## Result

- codes completed: **3**
- useful-hit codes: **3/3**
- organizations represented: **3**
- new canonical orgs: **3**
- reused canonical orgs: **0**
- new organization-expansion targets: **3**
- person records created: **0**
- inferred person→organization relations: **0**

The durable shard-B ledger advances through **730** only with this bounded packet and canonical importer materialization. Future passes must recompute the live NANPA geographic set before selecting the next unresolved batch.