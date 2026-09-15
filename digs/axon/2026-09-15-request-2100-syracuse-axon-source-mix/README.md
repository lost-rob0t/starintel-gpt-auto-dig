# Auto-Dig #2100 — Syracuse Axon source mix / transparency portal

Worker 4 bounded continuation for issue #2100. This packet is additive to the already-merged #1903 Syracuse policy/activation baseline and #2670 Axon/Fusus platform-control baseline; it does not duplicate those records.

## Finding

Central Current's July 29, 2026 report says Syracuse's public Axon transparency portal already showed **697,104 ALPR reads before the new 26 stationary Axon readers went live**. Syracuse Police Sgt. Tom Blake attributed those earlier reads to previously integrated technologies, including traffic-division Axon dash cameras with ALPR capability. The City of Syracuse Police Public Information page continues to expose the Axon Transparency Portal as an official public information surface.

That means the 26-reader stationary rollout is **not the whole Syracuse Axon ALPR source universe**. Aggregate portal counts must not be assigned solely to the new stationary readers.

## Evidence boundary

- `697,104` is preserved only as the reported July 29 portal snapshot; it is not a September 15 total.
- The SPD attribution is source-backed but is not a native source/device inventory export.
- Preexisting Axon/mobile ALPR activity does **not** establish Flock-to-Axon migration.
- Missing public portal partner/access detail does **not** establish zero sharing.
- Public portal disclosure is a cross-check, not a substitute for native Sharing Management, roles, source inventory, or audit exports.
- The final serial/location/activation state for all 26 stationary readers remains unresolved.

## New canonical records

- `starintel:analysis:syracuse-axon-prestationary-source-mix-request-2100-2026-09-15`
- `starintel:research-pass:request-2100-syracuse-axon-source-mix-2026-09-15`

## Reused canonical records

- `starintel:source:central-current-syracuse-axon-go-live-2026-07-29`
- `starintel:source:syracuse-alpr-policy-427-2026-07-28`
- `starintel:policy:syracuse-police-alpr-policy-427-2026-07-28`
- `starintel:analysis:syracuse-axon-policy-activation-request-1903-2026-09-15`
- `starintel:analysis:axon-alpr-platform-controls-request-2100-2026-09-15`

## Sources

1. City of Syracuse / Syracuse Police Department, Public Information: https://www.syr.gov/Departments/Police/Public-Information
2. Central Current, *Axon license plate readers go live in Syracuse*, July 29, 2026: https://centralcurrent.org/axon-license-plate-readers-go-live-in-syracuse-state-legislator-calls-it-a-constant-warrantless-surveillance-system/
3. Syracuse Police Department Policy 427 — Automated License Plate Readers: https://www.syr.gov/files/bd93959e-cc8b-4737-ad1a-26247a042b56/Automated_License_Plate_Readers__ALPRs.pdf

## Still unresolved

Issue #2100 stays open. Native evidence is still needed for the current stationary/mobile/third-party source inventory, source-separated metrics, final 26-reader serial/location/activation state, live Sharing Management relationships, users/roles, retention/search settings, audit exports, and any actual Flock continuity or migration edge.
