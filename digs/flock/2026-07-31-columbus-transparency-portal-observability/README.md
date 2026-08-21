# Flock Safety: Columbus transparency-portal and access-state observability recursion

Generated: `2026-07-31T01:50:00-04:00`

This pass follows the July 2026 287(g) sharing-control failure into the new public Flock transparency portal. It asks a narrower question than another general Flock overview:

> What record actually proves every organization that can access Columbus data, when that access began or ended, and whether the public description matches the configured state?

## Result

The public record shows a direct divergence between **declared policy state** and **actual access state**:

1. CPD withdrew from nationwide sharing and said it retained individually vetted relationships that excluded 287(g) agencies.
2. At the July 15 audit briefing, Deputy Chief Tim Myers said the remaining one-to-one relationships included no 287(g) agencies.
3. On July 17, CPD removed four agencies with current 287(g) agreements after journalists compared public records against the sharing roster.
4. By July 27, a Flock-hosted CPD transparency portal was publicly circulating, creating a new representation of usage and sharing state.
5. The portal is evidence, not yet an authoritative ledger: this pass could not directly retrieve its native page/export, historical snapshots, schema, or edge-change log.

The eight Tennessee police departments reported as remaining direct partners are preserved as an unresolved identity target. This packet does **not** guess their names.

## Control-plane finding

Point-in-time vetting cannot enforce an eligibility condition that changes after access is approved.

A durable control requires:

```text
authoritative agency identity + current 287(g) status
                         ↓
versioned Columbus sharing policy
                         ↓
active Flock sharing edges + administrator events
                         ↓
automatic diff, fail-closed revocation, human exception review
                         ↓
signed public snapshot + immutable edge history
```

A portal can expose the result, but it cannot substitute for the underlying configuration ledger and audit trail.

## Counts

- analysis: 3
- claim: 4
- dataset-manifest: 1
- event: 5
- investigation-target: 11
- org: 4
- person: 5
- policy: 4
- relation: 10
- research-pass: 1
- source: 11
- total: **59**

## Evidence boundaries

- The July 15 statement and July 17 removals establish a control-state mismatch; they do not establish that the four agencies used Columbus data for civil immigration enforcement while access remained active.
- The CPD portal URL was publicly circulated by July 27. That bounds public availability but does not prove the platform's original publication timestamp.
- Flock portals for other agencies describe “Sharing Network Data With” as organizations granted access. The exact CPD portal still requires a native snapshot to verify its contents and semantics.
- Community reports of broad out-of-state and private entities are retained only as collection leads, not verified graph edges.
- The eight Tennessee police departments are not named in the reviewed article text and remain unresolved.

## Next recursion

The top queued targets are:

1. recover the native CPD portal HTML, CSV, JSON/API responses, and update metadata;
2. identify the eight Tennessee police departments and normalize them to stable organization IDs;
3. reconstruct every active and historical sharing edge;
4. reconcile portal edges against native Flock configuration and query logs;
5. resolve private/non-police entities and their exact permissions;
6. recover administrator and configuration-change events;
7. implement a fail-closed partner-eligibility reconciliation actor.

## Validation

- JSONL parse: passed
- unique IDs: passed
- relation endpoints: passed
- related-document references: passed
- investigation-target seed references: passed
- source URLs: reviewed
- repository schema, merge gate, and research-site build: pending GitHub Actions
