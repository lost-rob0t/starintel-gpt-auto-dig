# NEED / HEPPAC chapter-affiliate expansion state

Last pass: 2026-09-08T23:42:00Z
Dataset: `anarchist-violence`
Worker: chapter/affiliate expansion

## Resolved this pass

- Reused existing canonical `starintel:org:berkeley-need`; no duplicate NEED organization was created.
- Materialized current HEPPAC as `starintel:org:heppac` from first-party identity and program pages.
- Materialized West Oakland Punks With Lunch separately as `starintel:org:west-oakland-punks-with-lunch`; this is not collapsed with Sacramento Punks With Lunch or another similarly named local.
- Materialized J&MP Innovations separately as `starintel:org:j-and-mp-innovations`.
- Recorded current NEED ↔ HEPPAC `collaborates_with` evidence for FTIR drug checking.
- Recorded HEPPAC fiscal sponsorship of West Oakland Punks With Lunch and J&MP Innovations from current first-party pages.
- Recorded West Oakland Punks With Lunch collaboration with both Berkeley NEED and HEPPAC at its current Wednesday fixed site.
- Cross-enumerated the first-party-linked West Oakland Punks With Lunch Instagram `@west.oakland.punks.with.lunch` and Facebook `Punkswithlunch` pages.
- Recorded current public organization email surfaces for HEPPAC, West Oakland Punks With Lunch, and J&MP Innovations.

## Current-status / identity boundary

- Fiscal sponsorship is not modeled as parent membership or chapter hierarchy.
- Collaboration is not modeled as affiliation or shared membership.
- West Oakland Punks With Lunch remains distinct from Sacramento Punks With Lunch and other organizations using similar branding absent explicit structural evidence.
- No individual membership, political affiliation, event attendance, or private identity is inferred.
- Historical links remain discovery leads until current status is independently verified.

## Durable no-repeat organization IDs

- `starintel:org:berkeley-need` — reused existing canonical record
- `starintel:org:heppac`
- `starintel:org:west-oakland-punks-with-lunch`
- `starintel:org:j-and-mp-innovations`

Reprocess these only when current first-party structure/status evidence changes or one of the unresolved child targets needs a deeper bounded pass.

## Next unresolved structural leads

1. Expand HEPPAC's current public program/partner graph while distinguishing internal programs from independent organizations.
2. Determine whether any other current Punks With Lunch organizations publicly describe an explicit network relationship with West Oakland Punks With Lunch; shared naming alone is insufficient.
3. Expand J&MP Innovations' current public child programs/partner graph where first-party pages identify distinct organizations rather than services.
4. Expand West Oakland Punks With Lunch's current partner/funder graph and public account network without treating service-site collaboration as chapter affiliation.

## Pass stats

- seed orgs processed: 2
- distinct new orgs: 3
- new parent/sponsor orgs: 1
- new sponsored orgs: 2
- new structural/collaboration edges: 5
- new public social endpoints: 2
- new public communications surfaces: 5
- source records: 6
- source domains: 4
- current orgs: 3
- historical-only orgs promoted: 0
- duplicate collisions avoided: 1
- unresolved structural leads: 4
