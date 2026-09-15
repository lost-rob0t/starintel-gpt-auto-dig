# 2026 election ecosystem breadth pass 1

Run: `election-ecosystem-2026-09-08-pass1`
Dataset: `anarchist-violence-election-ecosystem-2026-09-08-pass1`
Scope: public political-discourse, communications, election infrastructure, people, media and information-flow enumeration.

## Coverage summary

This bounded pass intentionally pivoted away from previously saturated 50501 / ABCF / Black Rose / General Strike material and from organizations already handled in the immediately preceding election-communications passes.

### Materialized graph

- canonical typed records: **66**
- organizations / organizational projects / media entities: **11**
- primary newly enumerated ecosystem roots: **7**
  - TurnUp
  - Defend 2026
  - New Bull Moose Party of the USA
  - Libertarian Party of Ohio
  - College Republicans of America
  - National High School Conservatives of America
  - Keep Arizona Blue Student Coalition
  - Voting Village is also materialized as a distinct election-security community node; the root count above treats Defend 2026 + YPAC and Voting Village + Election Integrity Foundation as project/parent pairs rather than double-counting their support entities.
- additional parent/media/support entities: **3**
  - Youth Progressive Action Catalyst (YPAC)
  - NHSC News LLC
  - Election Integrity Foundation, Inc.
- public people: **9**
- public source / communications / media / event surfaces: **20**
- explicit typed relations: **18**
- investigation targets: **8**
- inferred relations promoted to mature records: **0** (this slice kept all materialized edges explicit/source-backed)

### Communication and distribution surfaces

Observed public surfaces include:

- exact New Bull Moose Discord invite: `https://discord.gg/UcgtTQQr`
- exact Libertarian Party of Ohio Discord invite: `https://discord.gg/Bm5vDC2hQh`
- exact Clermont County Libertarian Club recurring Discord invite: `https://discord.gg/ef3wa5absn`
- TurnUp activism app/social network
- TurnUp organization/event distribution paths
- Defend 2026 public volunteer/member recruitment surface
- New Bull Moose newsletter
- New Bull Moose public X account `@NewBullMooseUSA`
- CRA website news, newsletter and social distribution surfaces
- NHSC News publication
- Keep Arizona Blue campaign-update/volunteer surfaces
- Coffee with KABSC recurring public interview series
- Voting Village public research/event hub
- Voting Village / DEF CON 34 event surface

### Public people materialized

- Zev Shapiro — founder and executive director, TurnUp
- Michael Sweeney — Libertarian Party of Ohio Executive Committee chair
- Martin Bertao — College Republicans of America president
- Colson Thomas — CRA vice president of operations
- Lily Sumner — CRA vice president of communications
- Kai Schwemmer — CRA political director
- Evan Archer — NHSC founder/CEO; NHSC News founder; Red Wave Rising host
- Jacob Marson — Keep Arizona Blue executive director
- Francesca Martin — Keep Arizona Blue co-founder and current deputy director

### Graph / information-flow edges

Notable explicit public graph edges include:

- Zev Shapiro -> founded -> TurnUp
- TurnUp -> operates_public_community -> TurnUp app
- Defend 2026 -> project_of -> Youth Progressive Action Catalyst
- New Bull Moose -> advertises_public_channel -> Discord
- Libertarian Party of Ohio -> advertises_public_channel -> statewide Discord
- Michael Sweeney -> chair_of -> Libertarian Party of Ohio
- CRA executive leadership -> role relations -> CRA
- Evan Archer -> founded -> NHSC
- Evan Archer -> founded -> NHSC News LLC
- Keep Arizona Blue -> operates_media_surface -> Coffee with KABSC
- Francesca Martin -> co_founded -> Keep Arizona Blue
- Voting Village -> project_of -> Election Integrity Foundation
- Voting Village -> participated_in_public_event -> DEF CON 34 surface

## Search / novelty metrics

- candidate organizations / communities inspected during discovery: **18+**
- prior saturated/recent clusters intentionally skipped: **8+**
  - 50501 family
  - ABCF family
  - Black Rose
  - General Strike
  - Project 535
  - Common Power
  - Protect The Vote 2026
  - Scrutineers
- novel primary ecosystem roots materialized: **8** when Voting Village is counted as its own root
- unique first-party domains represented in mature records: **7** (`turnup.us`, `defend2026.org`, `newbullmoose.com`, `lpo.org`, `uscollegegop.com`, `national-hsc.org`, `keepazblue.org`, plus `votingvillage.co` = **8** total)
- states/localities with explicit mature locality: Arizona, Ohio; national organizations span multiple states
- party/campaign infrastructure entities: LPO, CRA, Keep Arizona Blue, Defend 2026/YPAC
- media entities/surfaces: NHSC News LLC, Coffee with KABSC, CRA news distribution, TurnUp app, Voting Village event/research surface
- information-flow edges materialized: **5+** direct publication/community/event/operator edges
- identity collisions promoted: **0**

## Unresolved / next breadth leads

These were discovered but deliberately left for a later bounded pass rather than weakening evidence quality or overloading this PR:

- Try and Stop Us — 2026 voting-rights nonprofit with public partner/creator and newsletter surfaces
- Independence.org — independent-voter community with chapter and event structure
- Libertarian Party of Washington — public Discord and volunteer coordination
- Maryland Federation of College Republicans — state/campus chapter network
- Michigan College Republicans — multi-campus federation
- Hope for Democracy — cross-partisan citizen-assembly network
- Independent Center Voice — independent political infrastructure / data-support organization
- Swing Left Ground Truth — 2026 voter-listening program with explicit campaign/state-party information distribution and public media appearances
- Feel Good Action — named TurnUp voting-tools partner requiring independent identity resolution
- Red Wave Rising Podcast — NHSC-linked media surface requiring canonical URL resolution

## Evidence policy

All mature records in this packet are based on public first-party pages or directly linked first-party public surfaces. No private membership, private political affiliation, or hidden account ownership is inferred. Historical/event observations retain their time context. Search-only leads are not promoted to facts.
