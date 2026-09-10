# Election communications / civic-information infrastructure — bounded pass 19

## Scope

Fresh breadth-first PUBLIC POLITICAL-DISCOURSE / COMMUNICATIONS + ELECTION-ECOSYSTEM enumeration pass for the `anarchist-violence` corpus. This pass deliberately opens a new graph surface around voter-information distribution, civic technology, election-administration data, voter-engagement tools, corporate civic-engagement infrastructure, and public communications channels rather than revisiting the texting/ad-tech clusters from prior draft passes.

## Materialized graph

`starintel-documents.jsonl` contains 30 typed StarIntel v0.9 records:

- 11 `source`
- 9 `org`
- 3 `person`
- 7 explicit `relation`
- 0 inferred relations promoted as direct observation
- 0 normalized `db/` hand edits

### Organizations

- Democracy Works
- Vote.org
- Rock the Vote
- Center for Tech and Civic Life (CTCL)
- OpenAI
- Google
- CAA Foundation
- Civic Alliance
- Cox / Cox Communications

### Public people

- Luis Lozada — current Democracy Works CEO on the organization's leadership page.
- Andrea Hailey — current Vote.org CEO on Vote.org's team page.
- Tiana Epps-Johnson — identified by CTCL as CEO in its April 2026 annual-report announcement.

### Explicit relations

- Luis Lozada `executive_of` Democracy Works.
- Andrea Hailey `executive_of` Vote.org.
- Tiana Epps-Johnson `executive_of` CTCL.
- Democracy Works `partnered_with` OpenAI for 2026 U.S. election-logistics/voting information distribution through Democracy Works' Elections API.
- Democracy Works `distributes_data_through` Google via the Voting Information Project -> Google Civic Information API path.
- Democracy Works and CAA Foundation each `co_founded` Civic Alliance.
- Cox `partnered_with` Rock the Vote for a public 2026 voter-engagement surface embedding registration, registration-status, pledge and voting-information tools.

The packet contains seven relation records because Civic Alliance co-founding is represented as one edge per co-founder.

## Communication / information surfaces discovered

- Democracy Works: TurboVote, Elections API, Voting Information Project, Civic Alliance, public news/updates.
- Vote.org: voter-registration and registration-check tools, ballot information, election reminders, polling-place locator, drop-box locator, vote-by-mail guidance, public WhatsApp bot, CEO Newsletter, `theVOICE` publication.
- Rock the Vote: voter registration/status tools, pledge-to-vote flow, state voting information and partner-hosted embedded voter tools.
- CTCL: election-administration training, Ballot Information Project, civic data sets and the `ELECTricity` email publication.
- Google Civic Information API: downstream distribution surface for Voting Information Project data.
- OpenAI products: 2026 public election-information distribution endpoint described in Democracy Works' May 27, 2026 partnership announcement.

## Evidence / provenance discipline

Current-status claims use current first-party pages wherever available. Historical creation/operation dates are preserved as dates rather than silently treated as timeless facts. No person's political beliefs or partisan affiliation are inferred from employment, leadership, board service, technology partnerships, or civic-engagement activity.

## Coverage and recursive frontier

Candidate nodes checked during this bounded cluster expansion included Democracy Works, Vote.org, Rock the Vote, CTCL, BallotReady, Civic Alliance, Google, OpenAI, CAA Foundation, Cox, Microsoft, HeadCount, Propeller, The Pew Charitable Trusts and multiple election-data/public-distribution programs. The mature packet favors the nodes and edges with strong current first-party evidence and leaves weaker or identity-sensitive pivots unresolved rather than forcing them into the graph.

High-value unresolved leads for a subsequent pass include:

- Democracy Works' current platform customers/partners explicitly named on first-party pages, including TikTok and Perplexity AI, with exact product/data-flow edges.
- Voting Information Project co-creator/history edges involving The Pew Charitable Trusts and state/local election officials, modeled without collapsing government offices into generic organizations.
- Civic Alliance's public member-company list and workplace civic-engagement distribution pathways.
- Rock the Vote's current partner graph beyond Cox, including WNBPA and additional public partner pages.
- Vote.org's public corporate/nonprofit/influencer partner graph and Vote.org+ embedded-tool distribution network.
- CTCL's U.S. Alliance for Election Excellence, certification participants, training/event surfaces, and public election-office relationships.
- BallotReady's current customer graph and public election-information API distribution partners.
- Public social accounts, newsletters, podcasts, event calendars and public contact surfaces for each mature node.

## Write / validation path

This run used the repository-authorized GitHub connector fallback from current `main` SHA `6e4bc6b7c5078f83379602265a1c8576fe325a12`, writing only canonical packet/source files beneath `digs/anarchist-violence/2026-09-09-election-comms-civic-info-pass-19/`. Generated normalized `db/` was not hand-edited. Exact-head CI remains mandatory before this pass may be marked ready or merged.
