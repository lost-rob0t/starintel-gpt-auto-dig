# Flock Safety: Columbus asymmetric-sharing recursion

Generated: `2026-07-31T02:12:00-04:00`

This is the third consecutive recursive pass over the Columbus Flock graph. It follows the 287(g) recipient failure and transparency-portal pass into a directed-access question:

> When Columbus stops another organization from searching Columbus cameras, does Columbus also stop searching that organization's network?

## Result

No. The reviewed public record describes two different permissions:

- **outbound access** — another organization can search Columbus-owned or Columbus-shared camera data;
- **inbound access** — Columbus users can search data another organization shares with Columbus.

CPD's national, statewide, and 287(g)-recipient restrictions primarily changed the first direction. Reporting found that Columbus still had access to data from roughly two dozen organizations with ICE-linked agreements as of the reviewed July 15 state.

That does not prove Columbus used those networks for immigration enforcement. It proves the policy boundary was not closed merely by removing prohibited recipients from Columbus data.

## Core finding

A single undirected `shares-with` relation is wrong for this system. Every Flock sharing edge must be represented as:

```text
camera-owning organization
        -- grants-data-access-to -->
searching organization
```

and tracked independently from the reverse edge.

A compliant reconstruction needs:

```text
stable organization IDs
+ directed active edges
+ activation/revocation timestamps
+ policy version
+ administrator events
+ organization audit
+ network audit
+ query-level purpose
```

## Counts

- analysis: 3
- claim: 4
- dataset-manifest: 1
- event: 5
- investigation-target: 9
- org: 7
- person: 2
- policy: 3
- relation: 8
- research-pass: 1
- source: 8
- total: **51**

## Evidence boundaries

- Access does not establish use.
- A 287(g) agreement does not establish that every query by an organization concerns civil immigration enforcement.
- The reported roughly two dozen inbound ICE-linked organizations remain an unresolved set until native organization IDs and edge exports are recovered.
- The current portal is not treated as a historical configuration ledger.
- Vendor descriptions of logging and customer control are labeled as vendor statements.
- Public Network Audit exports may omit officer names, plates, vehicle fingerprints, and free-text reasons.

## Next recursion

1. Identify the roughly two dozen ICE-linked inbound organizations.
2. Recover current and historical directed sharing exports.
3. Test whether CPD queried those inbound networks.
4. Join Organization Audit and Network Audit records by unique search ID.
5. Recover portal `Sharing Network Data With` and `Receiving Network Data From` fields and native CSV/API schema.
6. Reconstruct administrator changes and support interventions.
7. Test policy closure across prohibited recipients, providers, purposes, and proxy queries.
8. Implement a fail-closed directed-sharing reconciliation actor.

## Validation

- JSONL parse: passed
- unique IDs: passed
- relation endpoints: passed
- target seed references: passed
- transport SHA-256: `ba228450d0593663e2a1117e091c3d9608f83fe1925deff2bb44bb62155c42d0`
- StarIntel schema, repository merge gate, conformance, and site build: pending GitHub Actions
