# 2026 election ecosystem breadth pass 6

Bounded breadth-first public election-ecosystem enumeration for the `anarchist-violence` corpus.

## Scope and novelty

Primary pivots:
- Run for Something
- All Voting is Local
- Protect Democracy

Current `main` was searched before materialization. Prior election-ecosystem passes and saturated 50501 / ABCF / Black Rose / General Strike clusters were not revisited.

## Materialized graph

- 3 organization nodes
- 6 public people
- 14 public source / community / program surfaces
- 15 explicit source-backed relations
- 3 investigation targets
- 41 total StarIntel v0.9 records
- 0 inferred relations promoted as fact

Public surfaces include Run for Something's online community, 2026 candidate/volunteer directory, and Future Candidates Cohort; All Voting is Local's 2026 poll-worker, poll-monitor and Election Protection recruitment; and Protect Democracy's Democracy Playbook plus VoteShield/BallotShield election-monitoring program.

## Boundary

Only public, attributable organizational and professional information is represented. Participation in a public program or proximity to an organization is not treated as private membership or political affiliation. Candidate-level expansion is intentionally deferred except where needed to describe a public organizational program.

## Validation

Packet records use the repository's established v0.9 packet shapes. No normalized `db/` records are hand-edited. Exact-head repository CI is the fallback validator for this connector-created packet. Merge only when the exact PR head is non-draft, mergeable, and all required checks are successful.
