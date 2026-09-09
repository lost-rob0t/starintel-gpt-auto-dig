# Area-code-hunt shard A — 510 / 513 / 516 / 531

Bounded organization-enumeration pass for `anarchist-violence`.

## Coverage

Current NANPA Geographic Area Codes reporting is the admission authority. Shard A owns admitted U.S. geographic NPAs satisfying `NPA mod 3 == 0`. This pass processes the next unresolved admitted batch after durable coverage through 507: **510, 513, 516, 531**. Durable coverage advances to **534**.

## Results

| NPA | Region | Hit | Organizations | New / reused | Current / historical-only | Explicit anarchist-associated | Public social endpoints | Public communications | Unresolved leads |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| 510 | Berkeley / Oakland / East Bay, CA | yes | East Bay Food Not Bombs; The Long Haul; Long Haul Infoshop; Slingshot Collective; Berkeley NEED; Berkeley Anarchist Study Group | 1 / 5 | 6 / 0 | 4 | 3 | 4 | 1 |
| 513 | Cincinnati / southwest Ohio | yes | Cincinnati Food Not Bombs; SWELL Café | 2 / 0 | 2 / 0 | 1 | 2 | 4 | 3 |
| 516 | Nassau County / western Long Island, NY | yes | Community Solidarity | 0 / 1 | 1 / 0 | 1 | 0 | 1 | 0 |
| 531 | Eastern Nebraska 402 overlay | yes | Mutual Aid Omaha; Omaha Food Not Bombs | 0 / 2 | 2 / 0 | 2 | 2 | 4 | 0 |

**Pass totals:** 4 codes attempted; 4 codes with hits; 11 organization identities found/reused; 3 newly materialized orgs; 8 reused canonical orgs; 11 current/recent observations; 0 historical-only promotions; 8 explicit anarchist/anarchist-associated classifications; 0 people enumerated; 0 explicit or inferred person↔org relations; 0 person identity collisions. Person-level political/ideological affiliation profiling is intentionally excluded.

## Materialization

New canonical packet identities:

- `starintel:org:east-bay-food-not-bombs`
- `starintel:org:cincy-food-not-bombs`
- `starintel:org:swell-cafe`

Each new organization has a separate `investigation-target`. Existing Long Haul/Slingshot/NEED/Berkeley Anarchist Study Group, Community Solidarity, Mutual Aid Omaha and Omaha Food Not Bombs identities are reused rather than duplicated. Explicit area-code locality relations were added for every retained organization in this batch. East Bay Food Not Bombs and SWELL receive explicit public-communications relations.

## Evidence/status notes

### 510

East Bay Food Not Bombs' current first-party site describes an all-volunteer collective active in Berkeley/Oakland since 1991, grounded in cooperation, sharing, sustainability, nonviolence and consensus. Its organization-owned contact surface publishes Instagram `@foodnotbombs.eastbay`, a Riseup list address, a public organization phone and volunteer routes. Existing Long Haul affiliate-expansion identities were deduplicated and reused.

### 513

WVXU reporting dated April 21 and April 22, 2026 independently corroborates Cincinnati Food Not Bombs among recurring Piatt Park food-distribution/mutual-aid groups. No current organization-owned Cincy Food Not Bombs social/contact surface was resolved, so no handle was invented. SWELL's first-party site currently describes a Cincinnati cafe/bookstore/bar for revolutionary community solidarity and inspiration and exposes public Facebook/Instagram/contact surfaces.

`513 Hygiene Care` remains a lead because the strongest current result is a partner/event description rather than a sufficiently resolved first-party organization identity. `Community Survival Network` is retained as a recursive lead because WVXU describes it as the collective name used by several Piatt Park distribution organizations, but this pass does not collapse that label into any member organization.

### 516

Community Solidarity is reused from the existing canonical record discovered through NPA 363. Its current first-party site documents weekly Hempstead food shares in Nassau County; this pass adds the missing 516 locality edge instead of creating a duplicate identity.

### 531

531 overlays the already-covered 402 geography. Current first-party evidence still shows Mutual Aid Omaha active and explicitly stating socialist, communist and anarchist ideals, while Omaha Food Not Bombs still advertises weekly Sunday distribution and public Slack/email. This pass therefore adds 531 locality relations to those canonical orgs without cloning them.

## Source domains

`nanpa.com`, `eastbayfoodnotbombs.org`, `wvxu.org`, `swellartcafe.com`, `thelonghaul.org`, `communitysolidarity.org`, `mutualaidomaha.org`, `omaha.foodnotbombs.us`, plus previously canonical Long Haul affiliate sources used for dedupe/locality reuse.
