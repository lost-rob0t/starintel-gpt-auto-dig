# Bounded Auto-Dig pass 32 — election results / media distribution infrastructure

## Scope

Public-source, breadth-first enumeration of the 2026 U.S. election-results and media-distribution layer. This pass focuses on how official/local vote results and voter-research products move through election-data providers, national news organizations, technology/platform customers, and public election-information surfaces.

## New graph surface

The Associated Press publicly documents a results-distribution network spanning ABC News, CBS News, CNN, NBC News, FOX News Media, OpenAI, and Kalshi. AP's network announcement explicitly states that the television networks continue making their own independent race calls. AP's vote-count methodology describes local precinct/county collection, official web sources, automated feeds from election officials in some states, verification, and real-time delivery to customers.

A second branch captures Edison Research and the National Election Pool. Edison identifies ABC, CBS, CNN, and NBC as NEP members and says Edison conducts NEP exit polling and nationwide election-night vote collection. AP separately documents its AP VoteCast partnership with NORC at the University of Chicago and its 2026 Voter Poll evolution.

A third branch adds Decision Desk HQ as an independent election-data provider. DDHQ states that it sources results from official state election sources and combines automated collection with remote reporting rather than reselling a single wire feed.

## Coverage

- 7 source records
- 12 organization records
- 3 public professional people
- 2 public URL/data surfaces
- 16 explicit typed relations
- 1 recursive investigation target
- 41 total canonical v0.9 packet records
- 0 inferred relations promoted to direct observation
- 0 private voter/respondent records

## Dedupe / identity handling

Current `main` was searched before writing for the core Associated Press, Edison Research, National Election Pool, Decision Desk HQ, OpenAI, Kalshi, and network IDs used here. No matching canonical IDs were found. Similar names or editorial relationships are not treated as identity equivalence.

## Recursive frontier

Expand current 2026 election-results customers, newsroom decision desks, official state/local result feeds, additional public election-data vendors, survey/research partners, public APIs and embeddable result products, technology/financial customers, election-night broadcast integrations, and downstream public publication paths. Preserve distinctions among raw/official results, vendor tabulation, survey data, projections, and independent race calls.

## Write / validation path

Local git could not resolve `github.com`, so this bounded run used the authorized GitHub connector fallback from current canonical `main`. Only packet/report source files are materialized; generated normalized `db/` is not hand-edited. Keep the PR draft until exact-head document and site/UI validation are conclusively green.
