# U.S.–Israel Military Integration — Pass 6

**Run:** `2026-08-02`  
**Dataset:** `us-israel-military-integration`  
**New records:** `156` StarIntel v0.9.0 documents  
**Merged records after known `_id` override:** `798`  
**JSONL SHA-256:** `c501f3f68c04b17b18af10aa4175ba6b17a9050ad4c8bedf9b5a44a763122c57`  

## Added

- **78 relations**
- **28 people**
- **22 organizations**
- **10 campaign-finance observations**
- **13 recursive targets**
- **3 claims**
- one analysis and one research-pass record

## Defense PAC layer

Five active qualified corporation PACs designated by the FEC as lobbyist/registrant PACs were added or expanded:

| PAC | FEC ID | Treasurer | Receipts, Jan. 2025–Jun. 2026 | Disbursements |
|---|---|---|---:|---:|
| Lockheed Martin Employees PAC | C00303024 | Michael McBride | $3,151,969.98 | $3,761,521.64 |
| Employees of RTX Corporation PAC | C00097568 | Tim Prince | $2,177,875.64 | $1,966,576.00 |
| The Boeing Company PAC | C00142711 | Howard Goodloe Sutton | $3,405,836.30 | $3,616,445.00 |
| General Dynamics Employee PAC | C00078451 | Pete Eckerson | $1,951,956.77 | $2,343,206.00 |
| Northrop Grumman Employees PAC | C00088591 | Joel Elliott | $2,912,268.04 | $3,481,009.63 |

**Combined reported receipts:** `$13,599,906.73`  
**Combined reported disbursements:** `$15,168,758.27`

These totals are cumulative FEC summaries through June 30, 2026. They are not Israel-specific spending totals.

## Corporate political-oversight layer

Board-level oversight nodes and relations were added for:

- Lockheed Martin Nominating and Corporate Governance Committee;
- RTX Governance and Public Policy Committee;
- Boeing Governance & Public Policy Committee;
- Northrop Grumman Policy Committee.

The graph links those committees to their parent companies and to public oversight responsibility for PAC governance, political contributions, lobbying or government-relations activity.

Additional named nodes include:

- Krissi Fauser → Northrop Grumman employee PAC leadership;
- Robert Bradway → chair, Boeing Governance & Public Policy Committee;
- Mortimer Buckley → member, Boeing Governance & Public Policy Committee;
- Steven Mollenkopf → member, Boeing Governance & Public Policy Committee.

## AIA governance layer

The pass adds the Aerospace Industries Association Executive Committee and 2026 governance relations connecting:

- Eric Fanning → AIA;
- Phebe Novakovic → AIA and General Dynamics;
- Christopher Calio → AIA and RTX;
- Kelly Ortberg → AIA and Boeing;
- Kathy Warden → AIA and Northrop Grumman;
- Christopher Kubasik → AIA and L3Harris;
- Tom Arseneault → AIA and BAE Systems;
- Thomas Bell → AIA and Leidos;
- Jim Currier → AIA and Honeywell Aerospace;
- Scott Donnelly → AIA and Textron;
- Amy Gowder → AIA and GE Aerospace;
- Christopher Kastner → AIA and HII.

AIA says it represents more than 300 manufacturers and suppliers and gives full members access to more than 100 councils, committees and working groups. Complete enumeration remains queued.

## FARA personnel layer

Nine short-form names under Show Faith by Works registration `7653` were added as unresolved identities linked only to the filing:

- Kelli Ayotte;
- Barbara Peil;
- Matthew Davis;
- Tye McClain;
- Melissa Lundie;
- Robert Pursley;
- Emily Hemingway;
- Richard Tuong Do;
- Chad Jonson Schnitger.

No identification with similarly named public figures is asserted.

Current active-registration relations were also added for:

- Bluelight Strategies → B Yahad Natzliach;
- Bridges Partners → Government of Israel through Havas Media Group Germany;
- Steptoe → Economic and Trade Mission at the Embassy of Israel;
- Holland & Knight → Israel Ministry of Foreign Affairs.

## Merge

`merged-quasar-manifest.json` adds the pass-6 transport to the ordered baseline-through-pass-5 import plan.

- records before deduplication: `799`
- known overridden `_id`: `starintel:org:lockheed-martin-employees-pac`
- expected merged records: `798`
- duplicate policy: `last-write-wins`

## Queued recursion

- recipient-level PAC contributions;
- PAC boards and approval chains;
- AIA's complete 300+ membership;
- AIA's 100+ councils, committees and working groups;
- AIA legislative priorities mapped to company lobbying;
- complete active Israel-related FARA registrants and short forms;
- association dues and lobbying-expense allocations;
- corporate political-spending oversight committee membership.

## Limits

PAC, trade-association, board and FARA records establish disclosed governance, finance, membership or representation relationships. They do not independently establish corruption, unlawful coordination or policy capture.
