# Syracuse Axon procurement baseline — request #1903

This bounded Worker 7 pass advances the existing Syracuse Axon contract target with a primary City of Syracuse record while preserving the separation between procurement/governance evidence, executed-contract evidence, technical configuration, deployment, and the prior Flock era.

## New canonical records

- `starintel:source:syracuse-stwg-axon-alpr-procurement-2026-01-27`
- `starintel:analysis:syracuse-axon-procurement-baseline-request-1903-2026-09-15`
- `starintel:research-pass:request-1903-syracuse-axon-procurement-baseline-2026-09-15`

## What the primary record establishes

The City of Syracuse Surveillance Technology Working Group's January 27, 2026 Meeting #79 presentation describes the proposed Axon ALPR agreement as covering 26 license-plate readers plus purchase, installation, and maintenance. It records a March 1, 2026 effective date, a 60-month period, the first 12 months free, a total amount not to exceed $422,636.28, and waiver of the RFP process. The presentation also says Common Council discussion was still being scheduled at that point.

Independent Central Current reporting says Common Council later voted 7-1 on February 9, 2026 to approve the Axon contract. That later reporting corroborates approval but is not the executed contract itself.

## Evidence boundary

This packet does **not** treat the January 27 presentation as the signed Master Service Agreement. It does not claim that the final executed attachment set matched every proposal-stage term without amendment. It also does not establish the final 26-reader serial/location/ownership/activation inventory, native Axon retention/access/sharing/audit/hotlist configuration, final Flock offboarding state, or any Flock-to-Axon migration of users, cases, hotlists, credentials, plate reads, or historical data.

The six existing canonical Syracuse investigation targets are reused; no competing target identity is created.

## Sources

- City of Syracuse, Surveillance Technology Working Group, January 27, 2026 meeting page and Meeting #79 presentation.
- Central Current, February 9, 2026 report on the Common Council's 7-1 approval vote.

Normalized `db/` records for this packet must be materialized through the canonical `scripts/starintel.py import` transactional path; they must not be hand-written.
