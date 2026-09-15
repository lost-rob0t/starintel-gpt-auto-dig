# Request #2100 — Axon/Fusus ALPR platform-control baseline

Worker 4/8 bounded continuation pass.

## Added in this slice

This packet promotes the already-researched Axon/Fusus ALPR capability findings into canonical StarIntel records and joins them to the landed Syracuse transition evidence without turning vendor documentation into Syracuse configuration facts.

Current primary Axon documentation establishes a testable control matrix:

- **source/device boundary:** search can span Axon-connected sources and third-party providers, including `Flock V3`; `Fusus present` therefore does not prove Axon-owned readers;
- **search:** offense category and reason are recorded, while case number can be hidden, optional, or required by administrators;
- **retention:** read retention and hotlist-hit retention are separate administrator-controlled values;
- **roles:** read/hit search, hotlist management, and ALPR system administration are separately permissioned;
- **sharing:** donor-initiated partner access requires recipient acceptance, is revocable by either side, keeps donor data in the donor tenant, and applies donor-controlled offense-category eligibility;
- **exports:** shared partner detections are queryable in place but excluded from bulk CSV and bulk PDF exports; individual record PDFs can include a shared detection labeled with its originating agency;
- **audit:** Internal ALPR Activity, Network ALPR Activity, ALPR Data Sharing, and Hotlist Management reports expose distinct activity/control surfaces;
- **public accountability:** Axon says its Transparency Portal can disclose partner agencies with access to shared ALPR data.

Axon also documents two evidence-quality caveats that must survive downstream analysis: some fields for roughly pre-April-2026 activity can be incomplete because of the legacy audit system, and the ALPR Data Sharing report's `Device Scope` / `Data Conditions` columns can show generic `All Devices` / `Full Sharing` values regardless of the actual relationship. Live Sharing Management therefore outranks those summary columns for configured sharing conditions.

Primary sources:

- https://www.axon.com/help/fusus/software/fusus/alpr/alpr-sharing.htm
- https://www.axon.com/help/fusus/software/fusus/alpr/alpr-search-interface.htm
- https://www.axon.com/help/fusus/software/fusus/alpr/alpr-administration.htm
- https://www.axon.com/help/fusus/software/fusus/alpr/alpr-audit.htm

## Syracuse evidence boundary

This pass reuses already-landed #1903 Syracuse records, including SPD Policy 427, the City procurement baseline, and the Axon activation reporting. It **does not** assert:

- Syracuse's live read/hit retention values solely from Axon product defaults;
- Syracuse's case-number setting, allowed offense categories, hotlists, users, roles, or partner relationships;
- that all 26 readers are installed or that every active source is Axon-owned;
- that a Flock V3 feed remains connected because Axon supports that integration;
- any migration of Flock users, hotlists, cases, plate reads, exports, credentials, or sharing state;
- that Transparency Portal disclosure is complete or equivalent to native Sharing Management/audit state.

The next native Syracuse package should capture `ALPR Settings`, `LPR Search Settings`, Roles & Permissions, current source/device inventory, Sharing Management, Transparency Portal disclosure, and the four audit-report families, then reconcile them against Policy 427 and the 26-reader procurement/deployment trail.

## Canonical IDs

New records:

- `starintel:source:axon-fusus-alpr-sharing-2026-07-30`
- `starintel:source:axon-fusus-alpr-search-2026`
- `starintel:source:axon-fusus-alpr-administration-2026`
- `starintel:source:axon-fusus-alpr-audit-2026`
- `starintel:analysis:axon-alpr-platform-controls-request-2100-2026-09-15`
- `starintel:research-pass:request-2100-axon-platform-control-baseline-2026-09-15`

Reused Syracuse records/targets include:

- `starintel:source:syracuse-alpr-policy-427-2026-07-28`
- `starintel:source:syracuse-stwg-axon-alpr-procurement-2026-01-27`
- `starintel:analysis:syracuse-axon-policy-activation-request-1903-2026-09-15`
- `starintel:analysis:syracuse-axon-procurement-baseline-request-1903-2026-09-15`
- `starintel:investigation-target:syracuse-axon-contract`
- `starintel:investigation-target:syracuse-migration-data-continuity`
- `starintel:investigation-target:syracuse-closed-system-verification`

Issue #2100 remains open after this bounded pass because Syracuse's current source inventory, configured controls, roles, partner-sharing state, native audit exports, and Flock-to-Axon migration state still require native evidence.
