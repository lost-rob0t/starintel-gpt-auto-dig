# Area-code org enumeration — shard A pass 18

Bounded dedicated `area-code-hunt` pass for `anarchist-violence`.

## Coverage

| NPA | Region | Result |
| --- | --- | --- |
| 567 | Northwest Ohio / 419 overlay incl. Toledo | 4Winds419 |
| 570 | Northeastern Pennsylvania incl. Scranton / Wilkes-Barre | Fruits & Roots Community Fridge Project; NEPA DSA (reused canonical identity) |
| 573 | Eastern / central Missouri incl. Columbia | CoMo Mobile Aid Collective; Food Not Bombs COMO |
| 582 | 814 overlay across western / central Pennsylvania incl. Erie | Erie Free Store |

NANPA admission was checked before research. All four are current U.S. geographic NPAs and satisfy `integer(area_code) % 3 == 0`. `567` is the 419 overlay, `570` is in the 272/570 complex, and `582` overlays 814. NPA locality relations are discovery geography only and do **not** assert ownership of a telephone number.

## Materialized organization graph

- `starintel:org:4winds419` — current first-party Toledo site identifies a grassroots, community-led effort founded in January 2026 with participatory decision-making, neighborhood support systems, rapid response, and a public community web surface.
- `starintel:org:fruits-roots-community-fridge` — current Scranton Area Community Foundation fund page describes a volunteer-run mutual-aid community-fridge project serving Lackawanna County through open-access refrigerators.
- `starintel:org:nepa-dsa` — reused rather than duplicated. The canonical record already exists from prior 272 coverage; this pass adds the explicit 570 locality edge for the same northeastern Pennsylvania geography.
- `starintel:org:como-mobile-aid-collective` — current first-party site explicitly describes a mutual-aid structure and distinguishes its direct aid from charity; current 2026 operations include food, water, survival supplies, basic medical care and advocacy.
- `starintel:org:food-not-bombs-como` — current first-party site advertises 2026 weekly hot meals and a downtown free market in Columbia, Missouri.
- `starintel:org:erie-free-store` — current first-party site confirms a volunteer-run free store open weekly to anyone, with goods provided free of charge and public email/social surfaces.

Each newly materialized organization has a separate `investigation-target`. The already-canonical NEPA DSA target is reused rather than duplicated. Public communications are preserved only when directly published by the organization/project or its public administering page.

## Yield

- codes attempted: 4
- codes with hits: 4
- organizations found/reused: 6
- new organizations: 5
- reused canonical organizations: 1
- current/recent: 6
- historical-only promotions: 0
- explicit Food Not Bombs / anarchist-associated identities: 1
- broader mutual-aid/free-store/adjacent identities: 5
- public communication surfaces: 9
- public social/contact endpoints resolved: 7
- people materialized: 0
- explicit person↔org relations: 0
- inferred person↔org relations: 0
- identity collisions: 0

Person-level political/ideological affiliation profiling was not materialized. Public organization-level evidence, organizational contact surfaces and directly evidenced organization relations only.

## Sources / unresolved leads

Primary domains: `nanpa.com`, `4winds419.org`, `safdn.org`, `comomobileaid.org`, `sites.google.com`, `eriefreestore.com`, plus the already-canonical `nepadsa.org` source.

Unresolved leads retained without promotion: The People's Pantry NWO; Surviving Capitalism Together — Northwest Ohio; People's Guild; Scranton Solidarity Project; Tallgrass Collective; historical Columbia Alternative Library; People's Erie; 1020 Collective / The Bastion; historical Centre County 4CR. Reddit/community/event surfaces remain discovery leads unless a sufficiently strong current organization identity is resolved.
