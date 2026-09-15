# 2026 election ecosystem breadth pass 10

Bounded breadth-first public election-ecosystem enumeration for the `anarchist-violence` investigation corpus, reconciled onto current `main`.

## Current-base reconciliation

Current `main` already owns canonical `starintel:org:fair-elections-center` version 1 from a later validated election packet. This replay therefore reuses that canonical organization ID and omits the stale same-version duplicate from the original pass-10 packet. The distinct first-party Fair Elections Center sources, public professional people, explicit relations, and recursive target remain additive and resolve to the canonical organization on `main`.

## Primary pivots

- America Counts
- Fair Elections Center (canonical organization reused from current `main`)
- When We All Vote
- Civic Nation
- Hartford Votes-Hartford Vota Coalition

## Additive yield

- 25 typed StarIntel v0.9 records
- 7 source / public communications / information surfaces
- 4 additive organization nodes
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

## Canonical path

`digs/anarchist-violence/2026-09-09-election-ecosystem-breadth-pass10/starintel-documents.jsonl`

No generated normalized `db/` file was hand-edited. The packet is submitted to exact-head repository CI under the connector-backed execution path.
