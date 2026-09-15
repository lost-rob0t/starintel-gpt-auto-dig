# Auto-Dig request #1899 — native Ithaca Flock termination resolution

## Bounded finding

This pass upgrades the March 4, 2026 termination event from reporting-only evidence to the City of Ithaca's own Common Council agenda packet. The official packet contains the proposed resolution language directing the Acting City Manager and City Attorney's Office to pursue contract termination at the earliest legally available opportunity, immediately suspend use of Flock services/equipment, require Flock equipment to be turned off and disconnected within fourteen days of enactment upon contract termination, and require removal of related technology as soon as practicable.

WSKG's contemporaneous report corroborates that Common Council adopted the measure unanimously on March 4, 2026. This pass therefore resolves the previously missing native resolution/implementation directive at the public agenda-packet level without pretending that the directive proves backend execution.

## Existing identities reused

No new Ithaca target is created. This pass reuses the canonical targets already present on `main`:

- `starintel:investigation-target:ithaca-termination-compliance`
- `starintel:investigation-target:ithaca-offboarding-data-deletion`
- `starintel:investigation-target:ithaca-sharing-history`
- `starintel:investigation-target:ithaca-removal-work-orders`

## Evidence boundary

The native resolution proves Council's policy/legal directive. It does **not** prove the exact vendor-confirmed shutdown timestamp, user/admin credential revocations, SharedNetworks removal, data deletion, audit preservation, serial-level reader disposition, billing closeout, or an Ithaca Police ↔ Cornell Police access edge. Those remain unresolved.

## Sources

- City of Ithaca Common Council, March 4, 2026 agenda packet: https://www.cityofithacany.gov/AgendaCenter/ViewFile/Agenda/_03042026-3165
- City of Ithaca agenda HTML/index: https://www.cityofithacany.gov/AgendaCenter/ViewFile/Agenda/3165?html=true
- WSKG, March 4, 2026: https://www.wskg.org/regional-news/2026-03-04/ithaca-common-council-votes-to-end-contract-with-flock-safety

## Remaining scope

Request #1899 stays open for the exact 22-reader serial/location lifecycle, contract closeout, final Organization Audit / Network Audit / SharedNetworks exports, users/admins and credential revocations, deletion/retention proof, removal work orders and custody/disposition, historical National Lookup state, partner notifications, and any documented IPD↔CUPD directed-access edge.
