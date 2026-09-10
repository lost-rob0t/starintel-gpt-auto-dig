# Election communications / administration coordination pass 15

Bounded PUBLIC political-discourse / communications + election-ecosystem enumeration for the `anarchist-violence` corpus.

## Scope

Breadth-first expansion into election-administration professional associations, cyber-information sharing, cross-sector ISAC coordination, and the current NASS corporate-affiliate communications/vendor surface. Existing corpus was searched for the primary NASS/NASED entities before materialization; no exact existing records were found in current `main` by repository code search.

## Coverage

- candidate/public nodes checked: 30+
- new source records: 11
- new organization records: 11
- new public person records: 8
- new explicit/inferred relation records: 17
- explicit relations: 16
- inferred relations: 1
- recursive investigation targets: 2
- identity collisions force-merged: 0
- unique source domains: 5 (`nass.org`, `nased.org`, `cisecurity.org`, `nationalisacs.org`, `civicroundtable.com`)
- principal graph surfaces: national election-administration associations; cyber-information sharing; professional leadership; current corporate-affiliate/vendor ties; public vendor contacts; election-office communications-platform use; issue-paper distribution

## Findings

NASS is a current nonpartisan professional association for Secretaries of State and related officials. Its July 20, 2026 announcement identifies Washington Secretary of State Steve Hobbs as 2026-2027 president. NASS's current corporate-affiliate roster exposes a public network that includes Meta, MTX Group, Tyler Technologies, Bugcrowd and Civic Roundtable, along with named public contacts. NASS explicitly states that corporate-affiliate status and issue-paper publication do not constitute endorsement.

NASED is the professional organization for state election directors. Its current 2026-2027 board names Mark Goins of Tennessee as president and exposes representation into Election Assistance Commission advisory/standards structures. Its public February 2026 conference agenda provides a substantial next-hop graph across election security, USPS election mail, accessibility, state/local training and government AI.

The Elections Infrastructure Information Sharing and Analysis Center (EI-ISAC) remains a public election-security coordination node. Historical first-party CIS material states that EI-ISAC operates under CIS and joined the National Council of ISACs in 2019; the current NCI roster continues to list EI-ISAC. The historical establishment material also identifies a partnership among CIS, CISA and the Election Infrastructure Subsector Government Coordinating Council, retained as a lead for later canonicalization rather than over-expanding this bounded packet.

Civic Roundtable is a current NASS corporate affiliate and publicly describes government workspaces, knowledge-base, communications and CRM functions. Its current site includes a testimonial attributed to Brian Leach of the South Carolina State Election Commission describing Roundtable use. The organization-level platform-use edge is therefore stored explicitly as an inference with an alternate explanation that the deployment may be limited rather than commission-wide.

## Canonicalization / uncertainty

All mature findings are represented as StarIntel v0.9 packet records with source provenance. No generated normalized `db/` record was hand-edited. Public contacts are represented only from source-visible professional roles. No person identities were merged solely from names. Historical claims are date-scoped in source records. The Civic Roundtable deployment edge is explicitly graded as inference and includes competing scope explanations.

## Recursive frontier

1. Expand the remaining current NASS corporate-affiliate roster into organizations, named public contacts, election products, conference appearances, issue papers, state/local deployments and cross-vendor relationships.
2. Expand the public NASED 2026 conference agenda into speakers, organizations, agencies, civic groups, technology vendors, recurring co-appearances and communication relationships.

Canonical packet fallback used: mature findings are materialized in `digs/anarchist-violence/2026-09-10-election-comms-admin-coordination-pass-15/starintel-documents.jsonl`. Exact-head GitHub CI is the validator for this connector-created bounded pass.
