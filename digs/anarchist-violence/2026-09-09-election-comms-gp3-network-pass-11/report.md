# Bounded Auto-Dig — 2026 election communications / GP3 network pass 11

## Scope

Bounded breadth-first public-source enumeration for the `anarchist-violence` corpus, extending the prior election-communications ad-tech pass into GP3 Partners' current member-firm network and political/public-affairs technology surface.

## Materialized coverage

`starintel-documents.jsonl` contains 16 typed StarIntel v0.9 records:

- 4 `source`
- 3 `org`
- 2 `person`
- 5 explicit `relation`
- 2 `investigation-target`

### New organizations

- **FLS Connect** — GP3's current first-party profile describes voter contact, data management, analytics/modeling, fundraising, issue advocacy, text, email, calls and town halls.
- **Public Opinion Strategies** — GP3's current first-party profile describes a political/public-affairs research firm with election and media-polling work.
- **GP3 Technology Group** — GP3's launch release describes a subsidiary for technology solutions in corporate public affairs and political work.

### Public people

- **David Seawright** — identified by GP3 as GP3 Tech President at launch.
- **Eric Wilson** — identified by GP3 as GP3 Tech Vice President at launch; GP3's release records prior campaign and political-technology roles.

### Explicit relations

- FLS Connect `member_of` GP3 Partners.
- Public Opinion Strategies `member_of` GP3 Partners.
- GP3 Technology Group `subsidiary_of` GP3 Partners.
- David Seawright `executive_of` GP3 Technology Group.
- Eric Wilson `executive_of` GP3 Technology Group.

No individual political belief or ideology was inferred from employment or professional history. No inferred relation was promoted to direct observation.

## Communications / distribution surface

This pass adds evidence-backed campaign-communications infrastructure spanning voter-contact data, modeling, fundraising, issue advocacy, SMS/text, email, phone contact, town halls, polling/survey research, public-affairs research, political technology, full-stack development and data systems.

## Recursive frontier

1. Enumerate the remaining current GP3 network: 50 State, 76 Group, Ascent Media, Blitz Canvassing, Bullpen Strategy Group, GuidePost Strategies, P2 Public Affairs, Red Maverick Media, Strategic Partners & Media and UpONE Insights.
2. Resolve public leadership, account/handle and communications surfaces for each member firm.
3. Resolve GP3 Tech products, inherited Bullpen Technology Group systems, public data/platform/vendor edges and cross-firm technology relationships.
4. Use public filings and first-party/reputable reporting to resolve historical/current campaign, committee, client and vendor edges, with explicit dates and provenance.

## Write path

Canonical packet fallback used because local git/DNS was unavailable. Findings were written beneath `digs/anarchist-violence/2026-09-09-election-comms-gp3-network-pass-11/`; generated normalized `db/` was not hand-edited. Exact-head CI is the required validator for this connector-created pass.
