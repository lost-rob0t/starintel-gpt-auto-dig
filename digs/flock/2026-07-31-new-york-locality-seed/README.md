# New York Flock locality seed — statewide issue-backed recursion

Generated: 2026-07-31

## Scope

This pass expands the Flock investigation from Columbus into New York and installs a deterministic GitHub Issues control plane for statewide locality coverage.

New York's official locality hierarchy currently contains 1,605 rows. Rather than create an unusable wall of more than 1,600 issues immediately, the tracker uses:

1. one statewide index issue;
2. one generated county/borough issue containing every official locality as a stable SWIS-keyed task;
3. one locality issue when research begins or evidence is found; and
4. recursive issues for agencies, private operators, contracts, sharing edges, audits, users, and named personnel.

The synchronization is idempotent. Existing checked locality tasks are preserved when the official source is refreshed.

## Initial confirmed leads

### Western New York

Investigative Post reported nearly 400 license-plate readers in Western New York and more than 218,000 Flock searches by 20 Erie and Niagara County agencies between January 2025 and early June 2026. The reporting distinguishes Flock from Genetec and Axon systems rather than treating all ALPRs as Flock.

High-value directed-sharing leads:

- Cheektowaga: 31 Flock cameras; reported sharing with 170 agencies and access to more than 600 Flock networks.
- Amherst: reported sharing with 114 agencies while moving from Flock to Axon.
- Town of Tonawanda: 13 Flock cameras; reported sharing with 65 departments and access to roughly three dozen networks.
- Lancaster, Kenmore, Buffalo State University, Erie County, Niagara County, and the private retail/housing network operators remain roster and permission targets.

### Troy

Troy retained Flock while adopting policy changes in May 2026 after a dispute over the mayor's emergency declaration and council authority. The next pass must recover the native contract, policy versions, audits, sharing configuration, user roster, administrator events, and actual enforcement of the announced restrictions.

### Syracuse

Public reporting said Syracuse operated 13 Flock readers and had inadvertently enabled national sharing, potentially exposing local data to thousands of agencies, including immigration authorities. This is a configuration-history and audit-log target, not merely a policy-text target.

### Saranac Lake

The village cancelled its Flock agreement in March 2026 after public opposition. The cancellation creates a useful negative-control locality: recover the proposal, contract, cancellation action, any installation/removal records, residual data, and access termination evidence.

### Beacon

A March 2026 FOIL request seeks records concerning planning, procurement, authorization, or attempted Flock deployment. The request remains a live evidence-production target.

### New York City

A pending NYPD request seeks video-analytics vendor information including possible Flock Condor use. NYC should remain `unknown` until contracts, deployments, or agency responses establish the vendor and product relationships.

## Issue-system invariants

- Every official locality is represented by `ny:<SWIS code>`.
- A checked county task means an evidence-backed first pass or a documented no-deployment result—not merely that someone searched the locality name.
- Flock, Axon, Genetec, Motorola/Avigilon, Rekor, Vigilant, and other vendors remain separate product and deployment entities.
- Government-owned and private camera networks remain separate.
- Outbound access to local data and inbound access to other networks remain separate directed edges.
- Policy claims, vendor claims, observable configuration, audit events, and analyst inference remain separate record classes.

## Next targets

- Generate all county/borough tracker issues from the official 1,605-row inventory.
- Crosswalk the locality hierarchy with the DCJS criminal-justice-agency directory and the 500-plus police/sheriff personnel reporting agencies.
- Materialize locality issues for Troy, Syracuse, Cheektowaga, Amherst, Town of Tonawanda, Beacon, Saranac Lake, Buffalo, Rochester, Albany, and NYC.
- Recover Western New York Organization Audit and Network Audit exports and reconstruct the 218,000-search corpus.
- Enumerate every private Flock network visible to New York agencies.
- Recover current and historical sharing rosters with effective dates.
- File standardized FOIL requests for contracts, inventories, users, administrators, audits, policies, and vendor support.
