# Request #1900 — Cornell MOU access-authority reconciliation

This bounded Worker 4 pass advances the Cornell Flock sharing model without creating new camera, organization, user, or sharing-edge identities.

Current `main` already contains the primary-document harvest for Tompkins County's February 2026 signed Flock LPR MOU under request #1904. This pass reuses that canonical evidence and maps only its Cornell-specific consequence into request #1900:

- Cornell University Police Department is one of the visible signed MOU participants.
- The MOU preserves each participant's administrative control over its own Flock system and data while defining a bounded inter-agency access framework.
- Searches under the agreement require an active legitimate law-enforcement matter, a traceable case number, and a specific articulable justification, with audit cooperation and suspension/revocation mechanisms.
- MOU membership does **not** prove a live directed `SharedNetworks` edge, reciprocal access, an approval/effective date, a particular user account, or an actual query.
- No CUPD ↔ Ithaca Police sharing edge is inferred merely because both agencies appear in the broader Tompkins Flock history.

## Canonical lineage

Upstream evidence reused rather than duplicated:

- `starintel:analysis:tompkins-request-1904-harvest-termination-mou-2026-08-25`

Existing Cornell targets retained:

- `starintel:investigation-target:cornell-sharing-configuration`
- `starintel:investigation-target:cornell-audit-exports`
- `starintel:investigation-target:cornell-centralized-access-roster`

New bounded records:

- `starintel:analysis:cornell-flock-mou-authority-request-1900-2026-09-15`
- `starintel:research-pass:request-1900-cornell-mou-authority-2026-09-15`

## Remaining evidence gap

The next hard join is native Flock state:

`MOU participant → directed sharing edge → approval/effective date → user/role → case + justification → query event → audit → suspension/revocation`

Until `SharedNetworks`, Organization Audit, Network Audit, users/admins, and query/event exports are recovered, the Cornell sharing graph remains authority-backed but technically unresolved.

Primary publication surface: https://www.tompkinscountyny.gov/News-articles/February-27-2026-Flock-Safety-MOU-2026
