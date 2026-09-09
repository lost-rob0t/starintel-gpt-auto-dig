# Area-code org enumeration — shard A pass 17

Bounded dedicated `area-code-hunt` pass for `anarchist-violence`.

## Coverage

| NPA | Region | Result |
| --- | --- | --- |
| 534 | Northern Wisconsin / 715 overlay | complete zero-current-hit |
| 540 | Western/northern Virginia incl. New River Valley | Future Economy Collective |
| 561 | Palm Beach County, Florida | Palm Beach Food Not Bombs |
| 564 | Western Washington distributed overlay incl. Seattle | Seattle Food Not Bombs; Left Bank Books Collective |

NANPA admission was checked before research. All four are current U.S. geographic NPAs and satisfy `integer(area_code) % 3 == 0`. The next unresolved shard-A NPA is `567`.

## Materialized organization graph

- `starintel:org:future-economy-collective` — current first-party site describes a volunteer-run, non-hierarchical mutual-aid and organizing collective in southwest Virginia's New River Valley, with a free fridge and essential-needs distribution.
- `starintel:org:palm-beach-food-not-bombs` — current public Florida resource listing identifies recurring Food Not Bombs distribution in West Palm Beach; retained conservatively as `active-current-directory-2026` because a current first-party website was not resolved.
- `starintel:org:seattle-food-not-bombs` — current first-party site advertises weekly meal shares and explicitly states mutual aid over charity, horizontal consensus, anti-oppression and nonviolence.
- `starintel:org:left-bank-books-seattle` — current first-party site documents a collectively operated radical bookstore; Pike Place Market describes it as an anarchist collective using consensus governance.

Each organization has a separate `investigation-target` and an explicit locality/area-code relation. Seattle Food Not Bombs and Left Bank Books also receive public-communications relations. NPA locality relations do **not** claim that an organization owns a telephone number in that NPA.

## Yield

- codes attempted: 4
- codes with hits: 3
- zero-current-hit codes: 1
- organizations found: 4
- current/recent: 4
- historical-only: 0
- explicit anarchist/anti-authoritarian/FNB-associated: 3
- public communication surfaces: 4
- public social endpoints resolved: 1
- people materialized: 0
- explicit person↔org relations: 0
- inferred person↔org relations: 0
- identity collisions: 0

Person-level political/ideological affiliation profiling was not materialized. Public organization-level evidence and communications surfaces only.

## Sources / unresolved leads

Primary domains: `nanpa.com`, `futureeconomycollective.org`, `homelessfl.org`, `seattlefoodnotbombs.org`, `leftbankbooks.com`, `pikeplacemarket.org`.

Unresolved: a current first-party Palm Beach Food Not Bombs web identity; Seattle Food Not Bombs Free Market as a potentially separate canonical organization; 534 locality leads that did not clear the inclusion threshold.
