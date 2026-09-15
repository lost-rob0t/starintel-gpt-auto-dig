# Syracuse Axon policy and activation — request #1903

Worker 7/8 bounded Auto-Dig pass for issue #1903.

## What this pass adds

This pass reuses the six existing canonical Syracuse transition targets and advances the Axon-era control/deployment state without merging Flock and Axon into one network era.

- Syracuse Police Department **Policy 427**, published July 28, 2026, is now captured as the public policy baseline.
- Policy 427 states a **30-day baseline ALPR retention period**, with a three-month felony-investigation preservation extension and longer preservation for evidence/discovery/lawful-production obligations.
- Policy 427 requires logged access, a call type, justification and associated DR number, plus **quarterly Compliance audits**.
- External law-enforcement/prosecutorial sharing requires a written request and approval; the published policy says ALPR data shall not be shared with the vendor and bars ICE/DHS immigration-enforcement sharing absent a judicial or court order.
- Central Current reported Syracuse Police Department confirmation that **14 of 26 new stationary Axon readers were installed and activated at 7:00 a.m. July 27, 2026**, while 12 still awaited installation.
- The Axon transparency portal existed alongside the published policy.

## Evidence-state boundaries

These are policy and source-backed deployment facts, not proof of all production configuration:

- published policy != native retention/access/sharing configuration;
- 14/26 active on July 27 != final 26-reader deployment completion;
- controlled external sharing != a zero-sharing "closed system";
- no Flock hotlist, read, case, user, credential, or historical-data migration is inferred;
- the executed Axon contract/procurement package remains unresolved.

## Canonicalization

The normalized `db/` records in this PR were materialized through the repository-owned `scripts/starintel.py import` path from the packet JSONL. No normalized DB record in this pass was hand-written.

## Sources

1. Syracuse Police Department, **Automated License Plate Readers (ALPRs), Policy 427**: https://www.syr.gov/files/bd93959e-cc8b-4737-ad1a-26247a042b56/Automated_License_Plate_Readers__ALPRs.pdf
2. Central Current, **Axon license plate readers go live in Syracuse**, July 29, 2026: https://centralcurrent.org/axon-license-plate-readers-go-live-in-syracuse-state-legislator-calls-it-a-constant-warrantless-surveillance-system/
3. Syracuse Police Department / Axon public ALPR transparency portal: https://syracusepdny.evidence.com/alpr/public/policy

## Canonical IDs

New records:

- `starintel:source:syracuse-alpr-policy-427-2026-07-28`
- `starintel:source:central-current-syracuse-axon-go-live-2026-07-29`
- `starintel:policy:syracuse-police-alpr-policy-427-2026-07-28`
- `starintel:analysis:syracuse-axon-policy-activation-request-1903-2026-09-15`
- `starintel:research-pass:request-1903-syracuse-axon-policy-activation-2026-09-15`

Reused unresolved targets:

- `starintel:investigation-target:syracuse-national-sharing-interval`
- `starintel:investigation-target:syracuse-flock-offboarding`
- `starintel:investigation-target:syracuse-removed-camera-inventory`
- `starintel:investigation-target:syracuse-axon-contract`
- `starintel:investigation-target:syracuse-migration-data-continuity`
- `starintel:investigation-target:syracuse-closed-system-verification`

Issue #1903 remains open after this bounded pass because its full completion criteria still require native Flock closeout, complete Axon procurement/inventory/configuration/audit evidence, and migration reconciliation.
