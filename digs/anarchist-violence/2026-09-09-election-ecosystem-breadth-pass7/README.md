# 2026 election ecosystem breadth pass 7

Bounded breadth-first public election-ecosystem enumeration for the `anarchist-violence` corpus.

## Scope and novelty

Primary pivots:
- DC Latino Caucus
- Cleveland VOTES
- Massachusetts Peace Action
- Friends Committee on National Legislation

Current `main` was searched before materialization. All four primary pivots returned no indexed corpus matches. Prior election-ecosystem passes and saturated 50501 / ABCF / Black Rose / General Strike clusters were skipped.

## Materialized graph

- 4 organization nodes
- 4 public people
- 9 public source / communications / election-program surfaces
- 8 explicit source-backed relations
- 4 investigation targets
- 29 total StarIntel v0.9 records
- 0 inferred relations promoted as fact

Public surfaces include DCLC's 2026 election/endorsement pages and newsletter, Cleveland VOTES' 2026 voter-education/news surface, MAPA's Vote Peace 2026 endorsements plus email/event/working-group participation, and FCNL's 2026 election-engagement page plus public advocacy/event network.

## Boundary

Only public, attributable organizational and professional information is represented. Participation, proximity, or issue overlap is not treated as private membership or personal political affiliation. First-party ideological or partisan descriptions are preserved only where the organization itself states them.

## Validation

Packet records use the repository's established v0.9 packet shapes. No normalized `db/` records are hand-edited. Exact-head repository CI is the fallback validator for this connector-created packet. Merge only when the exact PR head is non-draft, mergeable, and all required checks are successful.