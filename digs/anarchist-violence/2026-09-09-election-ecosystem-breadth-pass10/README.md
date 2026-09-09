# 2026 election ecosystem breadth pass 10

Bounded breadth-first public election-ecosystem enumeration for the `anarchist-violence` investigation corpus.

## Novel primary pivots

- America Counts
- Fair Elections Center
- When We All Vote
- Civic Nation
- Hartford Votes-Hartford Vota Coalition

The primary pivots were checked against current repository search before materialization. Exact-domain/name searches for America Counts, When We All Vote, and Hartford Votes returned no indexed corpus records; Fair Elections Center search returned only unrelated token matches rather than an existing canonical organization record. Civic Nation is materialized because first-party sources explicitly identify it as the parent initiative network for When We All Vote.

## Yield

- 22 typed StarIntel v0.9 records
- 7 source / public communications / information surfaces
- 5 organization nodes
- 4 public people
- 6 explicit evidence-backed relations
- 4 investigation targets
- 0 inferred relations promoted as direct observations

## Public people and explicit edges

- Robert Brandon -> `founded` -> Fair Elections Center
- Rebekah Caruthers -> `chief_executive_of` -> Fair Elections Center
- Michelle Obama -> `founded` -> When We All Vote
- Beth Lynk -> `executive_director_of` -> When We All Vote
- When We All Vote -> `initiative_of` -> Civic Nation
- America Counts -> `operates_public_information_surface` -> Actual Vote / public audit surface

## Public communications / information surfaces

- America Counts website, Actual Vote app, public audit methodology and reporting
- Fair Elections Center website, newsletter, 2026 Election Survival Guide, staff/leadership pages
- When We All Vote website, voter registration/check tools, Party at the Polls, email signup, public contact
- Civic Nation initiative network and public updates
- Hartford Votes-Hartford Vota Coalition website, public 2026 candidate forums, public organizational email

## Evidence boundary

This pass maps only publicly observable organizational, professional-role, program, event, and communications/information edges. It does not infer private membership, personal political affiliation, private communications, or nonpublic personal information.

## Next graph frontier

High-value recursive targets include America Counts' civic-organization/campaign user network, Fair Elections Center's Campus Vote Project and Work Elections Project partner graph, When We All Vote's public co-chair/ambassador and Party at the Polls partner network, Civic Nation's adjacent ALL IN and We The Action initiatives, and Hartford Votes' public candidate-forum/community partner network.

## Canonical path

`digs/anarchist-violence/2026-09-09-election-ecosystem-breadth-pass10/starintel-documents.jsonl`

No generated normalized `db/` file was hand-edited. This connector-created packet is submitted to exact-head repository CI under the documented GitHub fallback path.
