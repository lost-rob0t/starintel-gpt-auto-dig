# Auto-Dig request #1903 — Syracuse Flock offboarding and Axon migration

**Dataset:** `flock-safety-new-york-governance-sharing-private-depth-2-2026-07-31`  
**Date:** 2026-08-20

This pass reuses four existing canonical targets:

- `starintel:investigation-target:syracuse-national-sharing-interval`
- `starintel:investigation-target:syracuse-flock-offboarding`
- `starintel:investigation-target:syracuse-removed-camera-inventory`
- `starintel:investigation-target:syracuse-axon-contract`
- `starintel:investigation-target:syracuse-migration-data-continuity`
- `starintel:investigation-target:syracuse-closed-system-verification`

## Findings

- Syracuse Common Council revoked Flock's city access on March 23, 2026 after concerns about national-network data sharing.
- The offboarding was not instantaneous. Reporting says the city-imposed removal deadline was May 26, yet Syracuse police continued using readers for nearly a month after that deadline.
- By July 2026, all **13 Flock readers on city property** had been removed. This narrows the city-owned/authorized Flock asset count for the terminal lifecycle pass.
- Syracuse separately approved **26 Axon readers** under a five-year **$422,000** agreement effective March 1, 2026.
- Flock removal and Axon deployment are separate network eras. No reviewed evidence establishes that Flock hotlists, historical reads, users, credentials, or case links were migrated into Axon.
- Syracuse's official Surveillance Technology Working Group archive preserves the earlier ALPR review surface and the city's Common Council archive exposes the March 23 meeting record. Those are first-party recovery anchors for the native decision and policy chain.

## Remaining scope

1. Exact Flock national-sharing opt-in actor, timestamps, accessible agencies, and completed searches.
2. Final Flock Organization/Network/SharedNetworks/event/user/configuration exports.
3. Deletion certificate, credential/API revocations, partner notifications, final export, and vendor-support records.
4. Serial-level lifecycle for all 13 removed city-property readers.
5. Native Axon contract/procurement file, 26 final locations, deployment dates, retention, audit, sharing, support, and termination terms.
6. Evidence for or against migration of Flock hotlists, case links, user identities, alerts, or historical records.
7. Configuration evidence for the claim that Axon operates as a Syracuse-only closed system.

## Sources

- Syracuse Common Council meeting archive: https://www.syr.gov/Departments/Common-Council/Meetings-and-Agendas
- Syracuse Surveillance Technology Working Group archive: https://www.syr.gov/Departments/API/API-Initiatives/Surveillance-Technology
- Spectrum News, Mar. 23, 2026: https://spectrumlocalnews.com/nys/central-ny/public-safety/2026/03/23/syracuse-common-council-revokes-contract-with-flock
- Spectrum News, Jul. 23, 2026: https://spectrumlocalnews.com/nys/central-ny/politics/2026/07/23/all-flock-cameras-in-syracuse-have-been-removed
- Central Current, Jun. 26, 2026: https://centralcurrent.org/syracuse-police-used-flock-safety-readers-for-nearly-a-month-after-readers-were-supposed-to-be-taken-down/
