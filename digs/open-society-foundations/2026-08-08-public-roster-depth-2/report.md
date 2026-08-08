# Open Society Foundations — Public Roster and Cross-Ties, Depth 2

**Run:** `2026-08-08`  
**Dataset:** `wef`  
**Root target:** `starintel:target:wef:open-society-foundations-public-rosters-and-cross-ties`  
**Target organization:** `starintel:org:open-society-foundations`  
**Research status:** evidence-staging; canonical StarIntel import pending  
**Scope:** public organizational records, official rosters, official grant disclosures, public regulatory filings, and public institutional affiliations. No private contact data, inferred personal identifiers, or paywalled membership data.

## Executive finding

The queued target is materially under-mapped. The existing StarIntel node primarily captures Open Society Foundations (OSF) as a World Economic Forum Annual Meeting partner. Current first-party and government records expose a much denser graph: a nine-member governing board, an eight-person top leadership roster, a multi-jurisdiction legal/entity network, a 20,566-record public grant directory covering 2016–2024, a public fellowship roster, formal U.S. lobbying activity through the Open Society Action Fund, and direct board-level interlocks into organizations already represented elsewhere in StarIntel.

The strongest immediately actionable bridge is **Alex Soros → European Council on Foreign Relations (ECFR)**. OSF's current profile says Alex Soros sits on ECFR's board, and StarIntel already contains `starintel:org:european-council-on-foreign-relations`. The same OSF profile also identifies board ties to Bard College, Central European University, the Center for Jewish History, and International Crisis Group, plus his founding-chair role at Bend the Arc Jewish Action.

Nothing in this packet treats an affiliation, grant, lobbying filing, or shared governance role as evidence of misconduct. The value is the documented institutional topology.

## 1. Current governance roster

OSF states that its Board of Directors is the only body that reviews and advises across all OSF programs and entities, considers strategies submitted by OSF entities and programs, conducts reviews, and recommends corresponding budgets.

Current board roster:

| Person | Current OSF role |
|---|---|
| Alex Soros | Chair |
| Daniel Sachs | Vice Chair |
| Maria Cattaui | Board Member |
| Andrea E. Soros | Board Member |
| Chrystia Freeland | Board Member |
| Ivan Krastev | Board Member |
| Svante Myrick | Board Member |
| James C. O'Brien | Board Member |
| Tamiko Bolton Soros | Board Member |

Current top leadership roster:

| Person | Current OSF role |
|---|---|
| George Soros | Founder |
| Alex Soros | Chair |
| Binaifer Nowrojee | President |
| Pedro Abramovay | Vice President, Programs |
| Leonard Benardo | Vice President |
| Debbie Fine | General Counsel and Board Secretary |
| Leela Ramdhani | Chief Operating Officer |
| Laura Silber | Vice President, External Affairs and Office of the Chair |

The live roster is narrower than older cached versions that still expose former or superseded management titles. Current pages should be authoritative for present-tense records, while older pages remain useful only for temporal history.

## 2. Board-level interlocks: Alex Soros

OSF's current Alex Soros profile states that he is:

- chair of the OSF Board of Directors;
- founding chair of Bend the Arc Jewish Action;
- a board member of Bard College;
- a board member of the Center for Jewish History;
- a board member of Central European University;
- a board member of the European Council on Foreign Relations;
- a board member of International Crisis Group.

This yields at least seven organization-person edges from one current primary-source profile.

### Existing StarIntel bridge

`starintel:org:european-council-on-foreign-relations` already exists in the repository's `ecfr` dataset. That record currently reports low completeness and an empty member list because the earlier public-roster extraction returned no parseable entries. OSF's current profile therefore supplies a high-confidence source-backed membership edge that can improve **both** the OSF target and the ECFR component.

International Crisis Group is also already named in the repository's membership recursion queue and appears in prior research material, making the Alex Soros → ICG edge another useful cross-component join candidate.

## 3. Open Society Foundation London: government-record governance layer

OSF's offices page identifies **Open Society Foundation London**, company number **10187396**, as part of its network. UK Companies House independently shows the company as active and incorporated on May 18, 2016.

Companies House currently records:

- **Alex Soros** — active director since October 5, 2016;
- **Michael Vachon** — active director since January 3, 2024;
- **Debbie Fine** — active secretary since December 8, 2025;
- **Alex Soros** — active person with significant control, with more than 25% but not more than 50% of voting rights;
- **Laura Silber** — active person with significant control, with more than 25% but not more than 50% of voting rights.

The PSC register says Alex Soros was notified as a person with significant control effective March 31, 2024, while Laura Silber was notified effective December 19, 2024. The filing history shows full accounts for the year ended December 31, 2025 were filed July 1, 2026.

This is an important distinction: the OSF global board roster and the statutory control/officer roster of a specific UK entity are related but not interchangeable. StarIntel should model them as separate entity and relation records.

Companies House also records Alex Soros as an active director of **The International Crisis Group**, appointed October 4, 2018, independently corroborating the ICG interlock reported in the OSF biography.

## 4. The OSF network is a federation of named entities, not one monolith

The current OSF offices page explicitly describes the Foundations as a global network of entities. Named legal or foundation entities exposed on that page include:

- Open Society Foundation for Albania — Tirana;
- Open Society Fund–Bosnia and Herzegovina — Sarajevo;
- OSF Services Berlin GmbH — Berlin;
- Kosovo Foundation for Open Society — Pristina;
- Soros Foundation–Moldova — Chisinau;
- Foundation Open Society–Macedonia — Skopje;
- Open Society Foundation Serbia — Belgrade;
- International Renaissance Foundation — Kyiv;
- Open Society Foundation London — London, company 10187396;
- Open Society Action Fund — Washington, D.C.

The same page also lists OSF-branded offices in Nairobi, Dakar, Johannesburg, Brussels, Rio de Janeiro, Bogota, Mexico City, Amman, New York, and Washington, D.C.

### Modeling implication

Do not flatten all of these into aliases of `starintel:org:open-society-foundations`. Where a separately named or separately registered legal/foundation entity is disclosed, create a distinct organization node and connect it to the network with a source-backed predicate appropriate to the executable schema. Office locations without evidence of a distinct legal entity should remain locations/offices rather than invented corporations.

## 5. Grant graph: 20,566 public records ready for systematic extraction

OSF's official Awarded Grants directory currently reports **20,566 grants found**, with year filters from **2016 through 2024**.

The database exposes fields valuable for graph construction, including:

- grantee name;
- amount;
- year;
- grant description or purpose when disclosed;
- duration;
- region;
- specific OSF legal funding entity.

OSF's database documentation warns that:

- some grants or descriptions are omitted for privacy or safety;
- grants from some national and regional foundations may not appear;
- amount awarded can differ from amount ultimately paid because of contingencies, rescissions, or returns;
- the named funder identifies the specific legal OSF entity making the grant;
- each legal entity has its own fiduciary board.

That means the grant database should be treated as a large but explicitly incomplete public disclosure set, not a complete ledger of every OSF-related payment.

### Sample current database entries observed

Examples surfaced on the first pages include Access Now, Adalah, Advocates for Youth, Africa Centre for Energy Policy, African Development Solutions, African Futures Lab, African Peer Review Mechanism, and others. These samples demonstrate that the public directory can create `OSF legal entity → grant → recipient organization` paths at scale.

### High-value next move

Build a deterministic importer for the complete public grant directory rather than manually selecting politically interesting recipients. Preserve the funding legal entity, amount-awarded semantics, year, duration, region, and any source caveats. Then cross-join recipient organizations against existing StarIntel organization IDs.

## 6. Financial scale and allocation

OSF reports **$1.1901 billion** in total 2024 expenditures and more than **$24.2 billion** in expenditures to date. The 2024 regional categories shown by OSF are:

| Category | 2024 expenditures |
|---|---:|
| Global | $631.9M |
| United States | $242.0M |
| Latin America and the Caribbean | $117.1M |
| Europe and Central Asia | $83.7M |
| Africa | $69.9M |
| Asia Pacific | $26.0M |
| Middle East and North Africa | $19.4M |

OSF explicitly states that the `Global` category is a separate spending category, not the sum of the regional categories.

OSF also says its grantmaking awarded more than 2,350 grants in 2023 across more than 100 countries, and describes the Soros Economic Development Fund as its impact-investment arm. Historical OSF material states that SEDF has deployed more than $400 million in private-sector impact investments since 1997.

## 7. U.S. political/legislative activity is structurally separated by entity

OSF's own May 2024 elections fact sheet distinguishes two U.S. entities:

- **Open Society Institute** — a 501(c)(3) private foundation that OSF says does not lobby or engage in prohibited U.S. campaign activity;
- **Open Society Action Fund** — a 501(c)(4) social-welfare organization that OSF says makes grants to organizations seeking to pass or oppose legislation, presidential nominations, and ballot initiatives, while not supporting candidates or political parties.

OSF states that lobbying activities are undertaken by a 501(c)(4) where they constitute lobbying under U.S. tax law and that the Open Society Action Fund is registered under the federal Lobbying Disclosure Act.

### Federal lobbying filing

A U.S. Senate/House LDA filing for Open Society Action Fund covering Q1 2024 reports **$1.33 million** in lobbying expenses. The filing identifies lobbying on, among other items:

- S.316 / H.R.932, legislation to repeal authorizations for use of military force against Iraq;
- H.R.4928, the National Security Reforms and Accountability Act.

The filing names the U.S. Senate and U.S. House of Representatives as contacted institutions.

Separately, federal disclosure search results show outside lobbying firm **Pioneer Public Affairs** reporting Open Society Action Fund as a client at $50,000 in each of Q1, Q2, and Q3 2024 and $70,000 in Q4 2024, followed by a $30,000 Q1 2025 termination report. These outside-firm amounts should not be conflated with the Action Fund's own total lobbying-expense filing.

## 8. Current strategic commitments expose future grant clusters

OSF announced a **$300 million** U.S. initiative on May 20, 2026 focused on economic security, civil liberties, rule of law, economic opportunity, and political participation. It states that grants will be made at national, state, and local levels.

This is a forward-looking target generator. As awards appear in the grant database or entity announcements, a dedicated recursive target can connect the initiative to recipients, issue areas, legal funding entities, and any litigation or advocacy programs.

OSF also announced a **$30 million** 2026 initiative addressing antisemitism and anti-Muslim hate. These commitments are not equivalent to completed disbursements and should be modeled as commitments/initiatives until recipient-level evidence appears.

## 9. Fellowship roster: public subset only

OSF says the 2025–2026 Open Society Fellowship selected **31 public intellectuals** across Beirut, Buenos Aires, Colombo, Dar es Salaam, Jakarta, Lagos, and Taipei. The current public directory exposes **21 fellows** and explicitly says some fellows are not listed because of confidentiality concerns.

Publicly listed 2025 fellows observed in the directory:

1. Amita Arudpragasam — Colombo
2. Andrea Giunta — Buenos Aires
3. Anwuli Ojogwu — Lagos
4. Budi Hernawan — Jakarta
5. Camille Ammoun — Beirut
6. Carla Yumatle — Buenos Aires
7. Ermiza Tegal — Colombo
8. Ika Idris — Jakarta
9. Lamtiar Simorangkir — Jakarta
10. Lila Caimari — Buenos Aires
11. Madonna Adib — Beirut
12. Margareth Suhartin Aritonang — Jakarta
13. Mona Fawaz — Beirut
14. Moses Parlindungan Ompusunggu — Jakarta
15. Ossama Halal — Beirut
16. Sa'eed Husaini — Lagos
17. Tomás Pérez Vizzón — Buenos Aires
18. Tosin Oshinowo — Lagos
19. Uthpala Wijesuriya — Colombo
20. Victor Ehikhamenor — Lagos
21. Yudhanjaya Wijeratne — Colombo

Do **not** attempt to infer or identify the confidential fellows. The public 21-person roster is the correct extraction boundary.

## 10. Organizational change and temporal caution

OSF announced a major operating redesign in October 2023 that removed divisions between global and regional programming and moved toward objective-based teams. Binaifer Nowrojee was appointed president in March 2024 and took over in June 2024 from Mark Malloch-Brown.

This matters for historical ingestion: cached leadership pages and older reports can contain legitimate but superseded roles. Every employment/governance edge should carry observation or validity dates when available rather than overwriting history as if every title were simultaneously current.

## Confidence assessment

### High confidence

- current board and top leadership roster;
- current OSF office/foundation list;
- Open Society Foundation London company number and active status;
- current UK company directors, secretary, and persons with significant control;
- Alex Soros's OSF-described board interlocks;
- ECFR's existence as an existing StarIntel organization node;
- public grant-directory count and stated coverage/caveats;
- OSF-reported 2024 expenditure figures;
- Q1 2024 Open Society Action Fund federal lobbying disclosure;
- public 2025 fellowship names and confidentiality caveat.

### Requires further recursive verification

- current officers/directors and legal identifiers for every national OSF foundation;
- complete public grant extraction and deduplication against StarIntel;
- current board/member rosters for Bard, CEU, Center for Jewish History, ICG, and Bend the Arc from each organization's own primary sources;
- current federal lobbying totals after Q1 2024 and any 2025–2026 reports;
- recipient-level realization of the 2026 $300M and $30M initiatives;
- whether the specific legal funder relationships disclosed in the grants database align cleanly with existing OSF entity IDs.

## Proposed recursive targets

1. **Alex Soros institutional interlocks** — resolve Bard College, CEU, Center for Jewish History, ECFR, ICG, Bend the Arc from each institution's primary roster.
2. **OSF legal-entity registry map** — obtain authoritative registration IDs, directors, and fiduciary boards for the national foundations disclosed by OSF.
3. **Open Society Foundation London accounts** — ingest 2025 accounts and Section 172 report with audited financial fields, related-party disclosures, grants, and governance notes.
4. **Open Society Action Fund lobbying** — enumerate current LDA filings by quarter, issue code, bill, agency, and disclosed lobbyist, keeping self-reported expenses separate from outside-firm income.
5. **OSF grant corpus 2016–2024** — deterministic extraction of all 20,566 publicly exposed records, then entity resolution against the repository.
6. **2026 U.S. $300M initiative** — track commitments into named recipient grants as primary-source disclosure appears.
7. **2025–2026 Fellowship** — materialize only the 21 publicly disclosed fellows and their explicitly stated project topics/cities.
8. **Governance transition timeline** — reconstruct board and executive changes from 2023 restructuring through current leadership.

## Suggested graph edges for canonicalization

These are candidate relations only. They must be emitted through the repository's executable v0.9.0 schema and validated before import.

```text
Alex Soros --chairs--> Open Society Foundations
Alex Soros --board_member_of--> European Council on Foreign Relations
Alex Soros --board_member_of--> International Crisis Group
Alex Soros --board_member_of--> Bard College
Alex Soros --board_member_of--> Central European University
Alex Soros --board_member_of--> Center for Jewish History
Alex Soros --founding_chair_of--> Bend the Arc Jewish Action
Alex Soros --director_of--> Open Society Foundation London
Alex Soros --person_with_significant_control_of--> Open Society Foundation London
Laura Silber --person_with_significant_control_of--> Open Society Foundation London
Laura Silber --vice_president_of--> Open Society Foundations
Debbie Fine --general_counsel_and_board_secretary_of--> Open Society Foundations
Debbie Fine --secretary_of--> Open Society Foundation London
Michael Vachon --director_of--> Open Society Foundation London
Open Society Foundation London --network_entity_of--> Open Society Foundations
Open Society Action Fund --network_entity_of--> Open Society Foundations
International Renaissance Foundation --network_entity_of--> Open Society Foundations
```

## Source index

| Publisher | Source | URL |
|---|---|---|
| Open Society Foundations | Leadership | https://www.opensocietyfoundations.org/who-we-are/leadership?search=1 |
| Open Society Foundations | Board of Directors / Alex Soros profile | https://www.opensocietyfoundations.org/who-we-are/board-of-directors/alex-soros |
| Open Society Foundations | Offices & Foundations | https://www.opensocietyfoundations.org/who-we-are/offices-foundations |
| Open Society Foundations | Financials | https://www.opensocietyfoundations.org/who-we-are/financials?lv=true |
| Open Society Foundations | Awarded Grants | https://www.opensocietyfoundations.org/grants/past |
| Open Society Foundations | Open Society Fellowship | https://www.opensocietyfoundations.org/grants/open-society-fellowship |
| Open Society Foundations | How We Work | https://www.opensocietyfoundations.org/how-we-work |
| Open Society Foundations | Open Society and Free and Fair Elections in the United States | https://www.opensocietyfoundations.org/newsroom/open-society-and-free-and-fair-elections-in-the-united-states |
| Open Society Foundations | $300 Million U.S. Initiative | https://www.opensocietyfoundations.org/newsroom/open-society-foundations-launch-300-million-initiative-to-advance-economic-security-and-defend-civil-liberties-in-the-united-states |
| Open Society Foundations | Our History | https://www.opensocietyfoundations.org/who-we-are/our-history |
| Companies House | Open Society Foundation London overview | https://find-and-update.company-information.service.gov.uk/company/10187396 |
| Companies House | Open Society Foundation London officers | https://find-and-update.company-information.service.gov.uk/company/10187396/officers |
| Companies House | Open Society Foundation London PSC register | https://find-and-update.company-information.service.gov.uk/company/10187396/persons-with-significant-control |
| Companies House | Open Society Foundation London filing history | https://find-and-update.company-information.service.gov.uk/company/10187396/filing-history |
| Companies House | Alexander George Soros appointments | https://find-and-update.company-information.service.gov.uk/officers/kMzq3acSmBpiIvVvqLLZjmj61ck/appointments |
| U.S. Senate / House LDA | Open Society Action Fund Q1 2024 LD-2 | https://lda.gov/filings/public/filing/9e1dd704-5401-48b2-b229-09dcd91ad725/print/ |

## Validation / publication status

This file is a **research staging artifact**, not a completed canonical import. No normalized `db/` record has been hand-written. Before this target can be marked completed, candidate entities and relations must be generated through the repository-approved writer/import path and `python3 scripts/validate-for-merge.py --site` must pass on the exact PR head.
