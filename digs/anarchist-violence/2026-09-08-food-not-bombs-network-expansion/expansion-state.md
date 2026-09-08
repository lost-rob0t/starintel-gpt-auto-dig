# Food Not Bombs network expansion state

Last bounded pass: 2026-09-08T15:40:00Z

## Resolved this pass

- Food Not Bombs movement: current first-party movement/site and locations-directory structure verified.
- Food Not Bombs Portland Maine: existing org reused; current first-party branch relation to Food Not Bombs materialized; Instagram `@foodnotbombsmaine` queued through a typed public-account record.
- Food Not Bombs Kennebec: new current capital-area branch materialized from Midcoast Solidarity's first-party current page; Instagram `@foodnotbombskennebec` queued through a typed public-account record.
- Santa Cruz Food Not Bombs: current first-party chapter materialized with explicit autonomous-chapter relation.
- Midcoast Solidarity: existing org reused; direct public reference to Food Not Bombs Kennebec materialized without inferring affiliation.

## Structural invariant

Food Not Bombs states that chapters are independent/autonomous and that the movement has no headquarters or positions of leadership. `local_chapter_of` relations in this packet represent explicit chapter/branch membership in the named movement, not a command hierarchy.

## Do not reprocess without new evidence

- `starintel:org:food-not-bombs-portland-maine` -> `starintel:org:food-not-bombs`
- `starintel:org:food-not-bombs-kennebec` -> `starintel:org:food-not-bombs`
- `starintel:org:santa-cruz-food-not-bombs` -> `starintel:org:food-not-bombs`
- Instagram `foodnotbombsmaine`
- Instagram `foodnotbombskennebec`

## Next unresolved queue

1. Resolve Food Not Bombs Cleveland against a current first-party movement/chapter source before adding a chapter relation; the landed Cleveland record currently rests on a current third-party organization profile.
2. Enumerate additional current first-party public accounts for Santa Cruz Food Not Bombs.
3. Continue from the Food Not Bombs current locations directory only in bounded regional slices with current-status checks; do not bulk-promote stale historical map entries.
4. Follow any newly discovered exact public handles into the normal cross-platform enumeration path.
5. Keep Midcoast Solidarity resource-directory links distinct from affiliate/federation relations unless an explicit organizational relationship is published.

## Pass statistics

- seed orgs processed: 2
- new orgs: 3
- new autonomous chapter relations: 3
- direct public-reference relations: 1
- new public social endpoints: 2
- new public communications surfaces: 0
- source records: 5
- source domains: 4
- current orgs confirmed/materialized or reused in this slice: 4
- historical-only orgs promoted: 0
- duplicate collisions: 0
- unresolved structural leads: 3
