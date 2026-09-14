# 2026 election ecosystem breadth pass 15

Bounded public-web enumeration on 2026-09-09, branched from current canonical `main` at `4439a08b6dc9f07988b422130697ed8b612afd7a`.

## Coverage

- candidate organization names checked against repository search: BallotReady, Democracy Live, Enhanced Voting, KNOWiNK, Runbeck Election Services, Civitech
- mature new organizations materialized: 6
- public professional people materialized: 6
- first-party public source / communications / election-technology surfaces materialized: 6
- explicit evidence-backed relations: 6
- inferred relationships promoted to fact: 0
- recursive investigation targets: 2
- packet records: 26
- unique primary first-party domains represented in the packet: 6 (`ballotready.org`, `democracylive.com`, `enhancedvoting.com`, `knowink.com`, `runbeck.net`, `civitech.io`)
- additional government/public-source domains checked for recursive expansion: `azsos.gov`, `eac.gov`
- localities/states explicitly checked: Arizona plus national U.S. election-information/election-technology infrastructure
- identity collisions retained rather than merged: none observed in this bounded slice

## Material findings

1. BallotReady currently publishes personalized 2026 ballot/election information and describes its mission as comprehensive, accurate, nonpartisan civic information. Its public partner toolkit identifies Alex Niemczewski as CEO and enumerates public distribution surfaces including Facebook, Instagram, Threads, X, LinkedIn, and TikTok under the BallotReady identity.
2. Democracy Live identifies Bryan Finney as founder and CEO. Separate current company material states that its remote/accessibility election technology has been deployed in more than 7,000 elections across more than 2,500 jurisdictions in 36 states, giving the recursive pass a large jurisdiction/procurement frontier.
3. Enhanced Voting identifies Aaron Wilson as founder and president. Public Arizona election-administration material was also checked and documents use of Enhanced Voting technology for UOCAVA electronic ballot delivery; this deployment is retained as a recursive verification/procurement lead rather than an unsourced packet relation.
4. KNOWiNK identifies Scott Leiendecker as founder and CEO and publicly describes Poll Pad, voter-registration, election-management and election-night reporting products. U.S. Election Assistance Commission material was checked and records a 2026 Poll Pad 4.2.1 certification, which is queued for the deployment/certification frontier rather than being collapsed into a generic affiliation edge.
5. Runbeck Election Services publicly describes ballot printing, mailing, ballot-on-demand, vote-center and election-management services; current first-party press material identifies Jeff Ellington as CEO. Its jurisdiction footprint, procurement relationships and 2026 acquisition history remain explicit recursive targets.
6. Civitech describes itself as political technology for Democratic candidates and progressive causes and exposes voter-registration, data and voter-engagement infrastructure. Its current about page identifies Jeremy Smith as CEO and co-founder. A secondary corporate-data source reports that Civitech acquired BallotReady, but because first-party or filing corroboration was not established during this bounded run, that acquisition was not materialized as a fact and remains an unresolved verification lead.

## Recursive frontier

- enumerate BallotReady's current organizational customers/partners, API/data distribution graph, embedded voter-guide deployments, and platform-by-platform public accounts;
- enumerate Democracy Live jurisdiction deployments, public procurement/contracts, cloud/technology partners, accessible-ballot systems, and election-official relationships;
- enumerate Enhanced Voting state/county deployments, EnhancedBallot/Ballot Scout/Enhanced Results surfaces, public procurement records, and election-administration partners;
- enumerate KNOWiNK and Runbeck jurisdiction footprints, EAC certification/testing edges, acquisitions, product deployments, procurement contracts, and shared election-administration customers;
- verify the reported Civitech -> BallotReady acquisition from first-party or filing evidence and enumerate Civitech's current public campaign/nonprofit/client and data-partner graph without inferring private political affiliation of individuals.

No normalized generated `db/` record was hand-edited. Packet records follow the current repository `AGENTS.md` and v0.9 schema contract; exact-head repository CI remains the executable merge validator.