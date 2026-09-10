# Election communications / legal-information ecosystem pass 16

Bounded PUBLIC political-discourse / communications + election-ecosystem enumeration for the `anarchist-violence` corpus.

## Scope

Breadth-first expansion into election-law organizations, public-interest litigation, voter-data/privacy litigation, civic-engagement plaintiffs, campus and military-family voter-mobilization programs, and public information-distribution surfaces. The pass intentionally pivots away from the previously expanded fundraising/data, voter-protection hotline, voting-system certification, and election-administration coordination clusters.

## Coverage

This packet materializes 59 StarIntel v0.9 records:

- 18 public sources
- 11 organizations
- 5 publicly identified people
- 3 media/communications surfaces
- 1 civic-engagement program/event
- 19 explicit relations
- 2 recursive investigation targets

All 19 materialized relations are direct-source relations in this bounded pass; no inferred identity merge or inferred organizational relationship was promoted to fact.

## New graph surface

Organizations added include Campaign Legal Center, Protect Democracy, Democracy Defenders Fund, Citizens for Responsibility and Ethics in Washington (CREW), Electronic Privacy Information Center (EPIC), Secure Families Initiative, Arizona Students' Association, AGUILA Youth Leadership Institute, Elias Law Group, Democracy Docket, and LULAC.

Public people added include Trevor Potter, Norm Eisen, Susan Corke, Donald K. Sherman, and Marc Elias. Their organization-role/founder edges are represented separately as explicit relations rather than only embedded in person records.

Communication/distribution surfaces include Campaign Legal Center's `From the Desk of Trevor Potter` newsletter and `Democracy Decoded` podcast plus EPIC's public email-alert surface.

## Relationship findings

The packet preserves first-party evidence for, among other edges:

- Campaign Legal Center and Democracy Defenders Fund serving as co-counsel in a September 2026 election-related matter involving LULAC, Secure Families Initiative, and Arizona Students' Association.
- Protect Democracy and CREW representing EPIC in a September 2026 voter-data/privacy matter.
- Protect Democracy and Campaign Legal Center jointly filing an amicus brief in *Watson v. Republican National Committee*.
- Arizona Students' Association partnering with AGUILA Youth Leadership for its 2026 nonpartisan voter-registration canvassing program.
- Secure Families Initiative operating its 2026 Voting Ambassador Program for military-connected voters.
- Founder/leadership edges for Trevor Potter/Campaign Legal Center, Norm Eisen and Susan Corke/Democracy Defenders Fund, Donald K. Sherman/CREW, and Marc Elias/Elias Law Group and Democracy Docket.

## Source strategy

First-party/current sources were preferred: official organization pages, staff biographies, case updates, program pages, publication profiles, and public contact/newsletter surfaces. Historical dates remain explicit where an edge is time-bounded.

## Dedupe / identity handling

Repository code search against current `main` was used to check the principal candidate canonical IDs before materialization. No exact hits were found for the selected new organization IDs checked in this pass. This is a bounded dedupe check rather than a claim that every alias or historical representation across the full corpus has been exhaustively resolved.

No people were merged from name similarity alone. Cross-source identities in this packet use directly attributable first-party organization/publication profiles.

## Coverage accounting

- candidate cluster: election-law / voter-data litigation / civic mobilization
- new organizations: 11
- new people: 5
- new media/communication surfaces: 3
- new program/event nodes: 1
- explicit relations: 19
- inferred relations: 0
- identity collisions promoted/merged: 0
- recursive graph leads: 2
- source records: 18

## Recursive frontier

Two queued targets preserve the next high-yield surface:

1. expand the election-law client/co-counsel network across public 2026 cases, filings, represented organizations, recurring counsel relationships, publications, newsletters, and associated public accounts;
2. expand the military-family and campus voter-mobilization network from Secure Families Initiative, Arizona Students' Association, and AGUILA into partner organizations, chapters, events, communication surfaces, and public organizers.

## Validation

The packet is written only under `digs/anarchist-violence/2026-09-10-election-comms-legal-information-pass-16/`; normalized `db/` was not hand-edited. The GitHub-connector fallback path is used for the packet, with exact-head repository CI serving as the required validator before any same-run merge.
