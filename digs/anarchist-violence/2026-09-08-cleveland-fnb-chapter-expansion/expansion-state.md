# Cleveland Food Not Bombs chapter expansion state

Last bounded pass: 2026-09-08T19:44:24Z

## Resolved this pass

- Reused the canonical Food Not Bombs movement and the pre-existing generic Cleveland Food Not Bombs seed.
- Materialized **Food Not Bombs Lake County & Cleveland East** as a distinct current local from the current `fnbeastcle` first-party profile cluster plus current locality directories.
- Materialized **Food Not Bombs Cleveland West** as a separately named current local from Cleveland Pandemic Response; first-party identity remains unresolved.
- Added autonomous `local_chapter_of` relations from both locals to the Food Not Bombs movement. These edges do not imply hierarchy.
- Added first-party public social endpoints for the East/Lake County cluster: Instagram `@foodnotbombs_cle`, TikTok `@fnbeastcle`, and Facebook `fnblc`.

## Identity/dedupe invariant

Do **not** collapse `starintel:org:food-not-bombs-cleveland`, `starintel:org:food-not-bombs-lake-county-cleveland-east`, or `starintel:org:food-not-bombs-cleveland-west` based on naming similarity. Resolve umbrella/predecessor/alias/successor identity only from direct public organizational evidence.

## Do not reprocess without new evidence

- Lake County/Cleveland East -> Food Not Bombs movement.
- Cleveland West -> Food Not Bombs movement at current third-party confidence.
- Instagram `foodnotbombs_cle`.
- TikTok `fnbeastcle`.
- Facebook `fnblc`.

## Next unresolved queue

1. Find a current first-party Cleveland West profile/site before raising its chapter confidence or attaching social accounts.
2. Resolve whether the pre-existing generic Cleveland Food Not Bombs record represents an umbrella, predecessor, alias, or separate chapter.
3. Follow the three exact East/Lake County public handles through normal cross-platform enumeration.
4. Follow first-party `fnbeastcle` community-connection links only as discovery leads; do not infer affiliation from Linktree proximity.
5. Continue bounded Ohio Food Not Bombs expansion with current-status checks; Central Ohio/Columbus still has conflicting public naming and should not be merged without stronger identity evidence.

## Pass statistics

- seed orgs processed: 3
- new locals/chapters: 2
- new parent orgs: 0
- new chapter relations: 2
- new public social endpoints: 3
- new public communications surfaces: 1 Linktree hub
- source records: 3
- source domains: 3
- current orgs confirmed/materialized: 2
- historical-only orgs promoted: 0
- duplicate/identity collisions preserved: 1
- unresolved structural leads: 5
