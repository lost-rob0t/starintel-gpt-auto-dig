# 2026 election ecosystem fundraising/comms pass 17

Bounded public-web enumeration on 2026-09-09, branched from canonical `main` at `d4fb5dbe9f4c9d9ad6bcda5b414a27b72fc7a04f`.

## Coverage

- candidate organization names checked against current repository search: ActBlue, WinRed, NGP VAN, NationBuilder, Grassroots Analytics, Quiller AI
- mature new organizations materialized: 6
- public professional people materialized: 4
- public source / communications / product surfaces: 8
- explicit evidence-backed relations: 6
- inferred relationships promoted to fact: 0
- packet records: 24
- unique first-party source domains: 5 (`actblue.com`, `winred.com`, `ngpvan.com`, `nationbuilder.com`, `grassrootsanalytics.com`)
- political-position handling: organization orientation is recorded only from first-party self-description; no private political affiliation is inferred for people

## Material findings

1. ActBlue describes itself as an independent nonprofit technology platform for Democratic campaigns and progressive organizations. Its July 9, 2026 release says donors raised $586 million through the platform in Q2 2026 and identifies Regina Wallace-Jones as CEO.
2. WinRed describes itself as Republican fundraising technology created by a united front of the 2020 Trump campaign and GOP committees to compete with ActBlue. A March 23, 2026 first-party release says more than 8,000 Republican candidates and organizations use the platform and that it has processed more than $6.4 billion for Republican campaigns.
3. NGP VAN describes itself as technology for Democratic and progressive campaigns and organizations. Its 2026 public material documents an agentic-AI interface for campaign databases, expanded Mobilize volunteer/event tooling, and API/data-product investment. Chelsea Peterson Thompson is identified as General Manager.
4. NationBuilder describes itself as community-organizing infrastructure used by political parties, advocacy groups, charities, companies and other organizations across more than 110 countries. Its current leadership page identifies co-founder Lea Endres as CEO and lists public Instagram, X, Facebook, LinkedIn and YouTube surfaces.
5. Grassroots Analytics describes itself as a Washington, DC fundraising data/technology company serving forward-thinking/progressive campaigns, nonprofits and organizations, with more than 3,000 campaigns and organizations supported over recent cycles. Its current team page identifies Meghan McAnespie as CEO and exposes the GA Insider newsletter as a communications surface.
6. Grassroots Analytics announced on August 6, 2025 that it was acquiring Quiller AI, an AI-powered digital fundraising tool for campaigns and nonprofits. The acquisition is materialized as an explicit directed edge rather than inferred product proximity.

## Explicit graph edges

- Regina Wallace-Jones -> executive_of -> ActBlue
- WinRed -> competes_with -> ActBlue (based on WinRed's own stated origin and purpose)
- Chelsea Peterson Thompson -> executive_of -> NGP VAN
- Lea Endres -> executive_of -> NationBuilder
- Meghan McAnespie -> executive_of -> Grassroots Analytics
- Grassroots Analytics -> acquired -> Quiller AI

## Recursive frontier

- enumerate ActBlue and WinRed public committee/campaign directories, partner tooling, payment/conduit infrastructure, public APIs or integrations, and shared fundraising pathways without treating platform use as organizational affiliation;
- enumerate NGP VAN's public Partner Program and API/data integrations across messaging, digital advertising, analytics, fundraising, organizing and state-party infrastructure;
- enumerate NationBuilder's public app/integration ecosystem, political-party/campaign deployments, and public social/distribution surfaces across U.S. election actors;
- enumerate Grassroots Analytics and Quiller AI public clients, fundraising products, digital communications products, acquisitions, event/newsletter surfaces and integration partners;
- preserve source -> platform -> campaign/organization -> downstream donor/volunteer communications directionality where first-party material supports it.

No normalized generated `db/` record was hand-edited. Packet records follow current repository `AGENTS.md` and the v0.9 schema contract; exact-head repository CI is the executable merge validator.
