# 2026 election ecosystem data-infrastructure pass 16 — current-main reconciliation

This bounded public-web election-ecosystem pass was reconciled on 2026-09-15 against canonical `main` at `2556ffbe9910eb3fc30155826b3599cd7e0aeb9b` after later merged passes independently materialized several of the original pass-16 identities.

## Reconciliation

The original packet was exact-head schema/site green on 2026-09-09, but current `main` now already owns canonical same-version records for TargetSmart, Catalist, i360, Victory Waves, Liz Walters, Tom Goldenberg, and their already-materialized TargetSmart/Victory Waves and leadership edges. Those duplicate identities were removed instead of replayed with conflicting bytes.

The retained delta is limited to evidence and graph facts still absent from current `main`:

- the 2025 TargetSmart/Tara Media collaboration source and a distinct source-backed `Tara Media` organization node;
- Catalist founder/board-chair Laura Quinn and CEO Michael Frias, with explicit first-party leadership/founder relations to the existing canonical Catalist organization;
- i360 president/founder Michael Palmer, with an explicit first-party founder relation to the existing canonical i360 organization;
- the TargetSmart ↔ Tara Media collaboration relation, reusing the existing canonical TargetSmart organization.

## Retained packet

11 typed StarIntel v0.9 records:

- 3 first-party `source` records;
- 1 `org` record;
- 3 public professional `person` records;
- 4 explicit evidence-backed `relation` records.

No inferred relationship is promoted to fact. Political orientation remains organization-level first-party description only; no private political affiliation is inferred for people.

## Provenance / lineage

This is a collision-repair replay of PR #2535, not a new research pass. The old head remains in Git history; the live PR branch was reset to current `main` only because the original packet developed real canonical-ID collisions with later merged work. The retained source observations and original 2026-09-09 collection provenance are preserved unchanged.

No normalized `db/` record is hand-edited. Exact-head repository CI is the executable merge validator; merge only after `Validate StarIntel documents` successfully includes `Run complete canonical merge gate`, the required site workflow is green, and GitHub reports the PR mergeable.
