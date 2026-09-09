# 2026 election ecosystem breadth pass 14

Bounded public-web enumeration on 2026-09-09, branched from current canonical `main` at `8c96a8d6b56c51a5b621e8777b2123c8c73c392b`.

## Coverage

- candidate organization names checked against repository search: Election Integrity Network, Honest Elections Project, Restoring Integrity and Trust in Elections, Center for Election Confidence, Constitution Party of Georgia, VoterGA
- mature new primary organizations materialized: 5
- public professional people materialized: 5
- public source / communications / policy surfaces: 10
- explicit evidence-backed relations: 9
- inferred relationships promoted to fact: 0
- recursive investigation targets: 3
- packet records: 32
- unique primary first-party domains: 5 (`electionintegritynetwork.org`, `honestelections.org`, `riteusa.org`, `electionconfidence.org`, `gaconstitutionparty.org`)
- localities/states explicitly expanded: Georgia plus national U.S. election-law/election-integrity infrastructure
- identity collisions retained rather than merged: none observed in this bounded slice

## Material findings

1. Election Integrity Network states it was founded by Cleta Mitchell in 2021 and incubated by the Conservative Partnership Institute. Its current leadership page identifies Mitchell as founder/chair and Sharon P. Bemis as president. In June 2026 EIN announced receipt of a Heritage Foundation Innovation Prize for its state-based election-integrity infrastructure.
2. Honest Elections Project identifies Jason Snead as executive director and published a January 2026 election-policy report with 14 policy items and seven model bills.
3. On September 8, 2026 Honest Elections Project, Center for Election Confidence, and Restoring Integrity and Trust in Elections publicly announced a joint amicus filing in `Republican National Committee v. Mi Familia Vota`, creating three explicit co-filing edges among those organizations.
4. Center for Election Confidence identifies itself as the former Lawyers Democracy Fund and currently identifies T. Michael Andrews as president and Lisa L. Dixon as executive director.
5. Constitution Party of Georgia currently identifies itself as an Election Integrity Network partner since 2022 and advertises September 2026 poll-watcher training. Its current officers page identifies Ricardo Davis as state chairman and Garland Favorito as elections director.

## Recursive frontier

- enumerate EIN state coalitions, national working groups, partner organizations, public events/training surfaces, and public funding/support edges;
- enumerate HEP/RITE/CEC 2026 litigation, amicus, model-policy, partner, case, and recurring co-filer networks;
- enumerate CP-GA Election Integrity Update guests, poll-watcher trainers, partner organizations, recurring public speakers, event surfaces, and downstream Georgia election-integrity graph;
- follow the EIN Heritage Innovation Prize relationship into other publicly listed 2026 recipients only where election/civic relevance is evidenced;
- resolve VoterGA as a subsequent mature node from current first-party material before promoting additional leadership/partner relations.

No normalized generated `db/` record was hand-edited. Packet records follow the current repository `AGENTS.md` and v0.9 schema contract; exact-head repository CI remains the executable merge validator.
