# Request #2100 — Axon Fusus 2026.31 ALPR control delta

Worker 4/8 bounded continuation of `Auto-Dig: Axon ALPR surveillance system`.

## What this adds

Axon's first-party August 2026 Fusus release notes document two ALPR control changes in version 2026.31, scheduled for August 31, 2026:

1. Agencies can opt to disable the ALPR Fleet Search tab in Evidence.com and route users to Fusus LPR Search. Axon says Fusus captures **Case Number**, **Offense Category**, and **Reason for search**, and frames this as a consistent audit trail / documented-search-purpose control.
2. Authorized users can add a plate directly to a hotlist from ALPR search table, card, or detail views. Access remains permission-gated.

These are additive to the already-canonical #2100 Axon/Fusus control matrix. Current main did not contain the 2026.31 release URL or this routing control when this pass was claimed.

## Evidence boundary

This packet records **platform capability**, not Syracuse configured state.

It does **not** claim that Syracuse:

- enabled the Fusus-only ALPR search route;
- disabled Evidence.com ALPR Fleet Search;
- has any particular Case Number setting or complete audit coverage;
- gave any named user hotlist-management permission;
- migrated a Flock hotlist, user, read, case, credential, or sharing relationship into Axon/Fusus.

The next native join is:

`Syracuse search-route setting → search user/role → Case Number + Offense Category + Reason → source/device → audit event`

and separately:

`hotlist permission → hotlist create/update event → alert routing → audit event → explicit Flock migration record (if any)`

## Source

- Axon, **Fusus August 2026 release notes**, version 2026.31: https://www.axon.com/help/release-notes/fusus/2026/08-2026.htm

## Remaining #2100 gaps

The parent request remains open for Syracuse-native current configuration: executed contract and complete source/device inventory, live retention/search settings, roles and permissions, Sharing Management, partner relationships, audit exports, hotlists, and any explicit Flock-to-Axon migration or coexistence record.
