# 2026 election certification / testing infrastructure — bounded pass 14

## Scope

Breadth-first public election-ecosystem enumeration focused on federal voting-system testing/certification infrastructure and the public organizational/personnel edges exposed by the U.S. Election Assistance Commission (EAC).

## Materialized graph

- 5 first-party/public-government sources.
- 6 organizations: U.S. Election Assistance Commission, NIST, Pro V&V, SLI Compliance, Election Systems & Software (ES&S), and VotingWorks.
- 2 public professional contacts: Jack Cobb (Pro V&V) and Traci Mapps (SLI Compliance).
- 7 explicit relations covering EAC laboratory accreditation, NIST-to-EAC laboratory recommendation, current manufacturer-to-VSTL testing relationships, and named lab program-manager roles.
- 20 typed StarIntel v0.9 records total.

## Key findings

The EAC identifies Pro V&V and SLI Compliance as its currently accredited Voting System Test Laboratories. The EAC states that it generally considers laboratories evaluated and recommended by NIST under HAVA when making accreditation decisions.

The EAC's current systems-under-test table identifies ES&S EVS 7.0.0.0 with Pro V&V and VotingWorks VxSuite 4.0 with SLI Compliance under VVSG 2.0 review. These are represented as current testing relationships rather than certification claims.

The same EAC VSTL registry identifies Jack Cobb as Pro V&V's Laboratory Director / Program Manager and Traci Mapps as SLI Compliance's Vice President / Program Manager.

The broader EAC manufacturer registry exposes additional mature next-hop nodes—including Avante International Technology, Clear Ballot Group, Hart InterCivic, Liberty Vote USA, MicroVote General, Smartmatic USA, Unisyn Voting Solutions, and Voterite/Votrite—which are deliberately left as unresolved expansion leads in this bounded slice rather than partially normalized without their full relation/person packet.

## Provenance / caveats

Registration with the EAC is not an endorsement and does not itself mean a voting system is certified. Likewise, an entry in the systems-under-test table is represented as a testing/certification-process relationship, not a claim that certification has been granted.

Mature findings are materialized in `starintel-documents.jsonl`. No normalized `db/` records were hand-edited. Connector packet creation is used as the repository-authorized fallback path; GitHub exact-head CI remains the validator/merge gate.
