# 2026 election ecosystem breadth pass 15

Bounded public-web enumeration on 2026-09-09, branched from current canonical `main` at `4439a08b6dc9f07988b422130697ed8b612afd7a`.

## Coverage

- candidate organization names checked against repository search: BallotReady, Democracy Live, Enhanced Voting, KNOWiNK, Runbeck Election Services, Civitech
- mature new organizations/institutions materialized: 7
- public professional/public-official people materialized: 7
- public source / communications / election-technology surfaces: 15
- explicit evidence-backed relations: 13
- inferred relationships promoted to fact: 0
- recursive investigation targets: 4
- packet records: 46
- unique primary first-party/government domains: 8 (`ballotready.org`, `democracylive.com`, `enhancedvoting.com`, `azsos.gov`, `knowink.com`, `eac.gov`, `runbeck.net`, `civitech.io`)
- localities/states explicitly expanded: Arizona plus national U.S. election-information/election-technology infrastructure
- identity collisions retained rather than merged: none observed in this bounded slice

## Material findings

1. BallotReady currently publishes personalized 2026 ballot/election information and states that its mission is comprehensive, accurate, nonpartisan civic information. Its public partner toolkit identifies Alex Niemczewski as CEO and enumerates public distribution surfaces including Facebook, Instagram, Threads, X, LinkedIn, and TikTok under the BallotReady identity.
2. Democracy Live states that its remote/accessibility election technology has been deployed in more than 7,000 elections across 2,500 jurisdictions in 36 states, and its current leadership page identifies Bryan Finney as founder and CEO. Its company material also documents strategic technology relationships including Amazon Web Services.
3. Enhanced Voting identifies Aaron Wilson as founder and president. The Arizona Secretary of State publicly documents a partnership with Enhanced Voting for its military/overseas UOCAVA electronic ballot-delivery system; Arizona county election pages continue to identify Enhanced Voting as the delivery provider for 2026 UOCAVA communications.
4. KNOWiNK identifies Scott Leiendecker as founder and CEO and describes Poll Pad, Total Vote, election-night reporting, voter-registration, and election-management products. The U.S. Election Assistance Commission records KNOWiNK Poll Pad 4.2.1 as certified in 2026 under the federal voluntary electronic-poll-book program.
5. Runbeck Election Services currently advertises election printing, mailing, ballot-on-demand, vote-center, election-management, petition-management, secure-dropbox, and related services affecting a large share of U.S. registered voters. Its company history records a 2026 acquisition of the Fidlar/Cathedral Election Print Division from FSSI; first-party leadership material identifies Jeff Ellington as CEO.
6. Civitech describes itself as political technology for Democratic candidates and progressive causes and exposes voter-registration, data, voter-engagement, SMS/GOTV, and partner infrastructure. Its current about page identifies Jeremy Smith as CEO and co-founder. A secondary corporate-data source reports that Civitech acquired BallotReady; the packet records this relation with reduced confidence rather than treating it as first-party corroborated.

## Recursive frontier

- enumerate BallotReady's current organizational customers/partners, API/data distribution graph, embedded voter-guide deployments, and platform-by-platform public accounts;
- enumerate Democracy Live jurisdiction deployments, public procurement/contracts, cloud/technology partners, accessible-ballot systems, and election-official relationships;
- enumerate Enhanced Voting state/county deployments, EnhancedBallot/Ballot Scout/Enhanced Results surfaces, public procurement records, and election-administration partners;
- enumerate KNOWiNK and Runbeck jurisdiction footprints, EAC certification/testing edges, acquisitions, product deployments, procurement contracts, and shared election-administration customers;
- verify Civitech -> BallotReady acquisition from first-party or filing evidence and enumerate Civitech's current campaign/nonprofit/client and data-partner graph without inferring private political affiliation of individuals.

No normalized generated `db/` record was hand-edited. Packet records follow the current repository `AGENTS.md` and v0.9 schema contract; exact-head repository CI remains the executable merge validator.