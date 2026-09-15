# 2026 election ecosystem fundraising/comms pass 17

Bounded public-web enumeration originally collected on 2026-09-09 and reconciled against canonical `main` at `bdee24750613af95bf32c802e1b216289b709e66` before landing.

## Current-main reconciliation

Current `main` already owns canonical coverage for ActBlue, WinRed, NGP VAN, NationBuilder, Regina Wallace-Jones, Chelsea Peterson's NGP VAN leadership, and Lea Endres's NationBuilder leadership. It also already owns the exact WinRed source IDs used by the original packet. Those stale same-version redefinitions and semantically duplicate person/leadership records are omitted rather than replayed.

The retained additive delta is limited to records not already materialized on `main`:

- Grassroots Analytics
- Quiller AI
- Meghan McAnespie
- Meghan McAnespie -> executive_of -> Grassroots Analytics
- Grassroots Analytics -> acquired -> Quiller AI
- WinRed -> competes_with -> ActBlue, using the already-canonical first-party WinRed source on `main`
- two first-party Grassroots Analytics sources supporting the new organization/person/acquisition records

## Coverage

- packet records: 8
- sources: 2
- organizations: 2
- public professional people: 1
- explicit evidence-backed relations: 3
- inferred relationships promoted to fact: 0
- same-version/current-main redefinitions retained: 0
- political-position handling: organization orientation is recorded only from first-party organizational material; no private political affiliation is inferred for people

## Material findings

1. Grassroots Analytics describes itself as a Washington, DC fundraising data/technology company serving forward-thinking/progressive campaigns, nonprofits and organizations, with more than 3,000 campaigns and organizations supported over recent cycles. Its current team material identifies Meghan McAnespie as CEO.
2. Grassroots Analytics announced on August 6, 2025 that it was acquiring Quiller AI, an AI-powered digital fundraising tool for campaigns and nonprofits. The acquisition is represented as an explicit directed edge from the first-party acquisition announcement.
3. WinRed's already-canonical first-party About source states that the platform was created to enable Republicans to compete with ActBlue; this pass preserves that explicit competition edge without redefining either organization or the source.

No normalized generated `db/` record was hand-edited. Packet records remain strict v0.9 documents, and exact-head repository CI is the executable merge validator.
