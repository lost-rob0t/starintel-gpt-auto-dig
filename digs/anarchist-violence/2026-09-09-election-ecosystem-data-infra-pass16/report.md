# 2026 election ecosystem data-infrastructure pass 16

Bounded public-web enumeration on 2026-09-09, branched from canonical `main` at `6c6160623c50889fca3844281e7d0179fcd88de1`.

## Coverage

- candidate organization names checked against current repository search: TargetSmart, Catalist, i360, Victory Waves, Tara Media
- mature new organizations materialized: 5
- public professional people materialized: 4
- public source / communications / product surfaces: 6
- explicit evidence-backed relations: 7
- inferred relationships promoted to fact: 0
- packet records: 22
- unique first-party domains: 4 (`targetsmart.com`, `catalist.us`, `i-360.com`, `victorywaves.com` via TargetSmart partnership release where first-party Victory Waves pages were not needed for the explicit edge)
- political-position handling: only organization self-description or explicit first-party client orientation is recorded; no private political affiliation is inferred for people

## Material findings

1. TargetSmart's current 2026 VoterBase material says it provides political data for Democratic campaigns and progressive organizations and describes a 2026 voter-file expansion reaching 210.3M registered-voter records with enriched demographic coverage. Its current leadership/press material identifies Liz Walters as CEO.
2. TargetSmart announced an August 20, 2026 partnership with Victory Waves in which Victory Waves' Petition Validator uses TargetSmart voter data for petition-signature validation; the release identifies Tom Goldenberg as Victory Waves CEO.
3. A June 2025 TargetSmart/Tara Media announcement describes TargetSmart and Tara Media as working together to expand data and political-advertising infrastructure for Democratic campaigns and progressive organizations; the release identifies Tom Bonier as CEO of The Tara Group and TargetSmart senior adviser.
4. Catalist's current site says it builds data infrastructure for progressive organizations and maintains a national database covering more than 263 million voting-age individuals. Its current board material identifies founder Laura Quinn as board chair; current Catalist material identifies Michael Frias as CEO.
5. i360's current public site says it works with right-of-center organizations and provides voter data, predictive models, canvassing, phone, text and grassroots software. Its site reports 270M+ voter profiles / 300M+ consumer profiles and 10,000+ organizational users. A current case-study page identifies Michael Palmer as president and founder.

## Explicit graph edges

- Liz Walters -> chief executive -> TargetSmart
- TargetSmart -> data partnership -> Victory Waves
- Tom Goldenberg -> chief executive -> Victory Waves
- TargetSmart -> communications/data collaboration -> Tara Media
- Laura Quinn -> founded -> Catalist
- Michael Frias -> chief executive -> Catalist
- Michael Palmer -> founded -> i360

## Recursive frontier

- enumerate TargetSmart's current Democratic/progressive campaign, advocacy, media-buying, cooperative and product-integration network from public first-party case studies and releases;
- enumerate Catalist public partner/client feedback-data, progressive civic-technology and board-network edges without treating board proximity as affiliation;
- enumerate i360 public GOP/right-of-center campaign, nonprofit, advocacy, technology-partner and case-study network;
- follow the TargetSmart -> Victory Waves petition-validation integration into public ballot-access campaigns and petition vendors;
- follow Tara Media / Tara Group public data, media-buying and campaign communications relationships where first-party evidence identifies specific organizational clients or partners.

No normalized generated `db/` record was hand-edited. Packet records follow current repository `AGENTS.md` and the v0.9 schema contract; exact-head repository CI is the executable merge validator.
