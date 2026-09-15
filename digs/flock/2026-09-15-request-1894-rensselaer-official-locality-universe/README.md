# Request #1894 — Rensselaer County official locality universe

Worker 6/8 fills one explicit parent gap from request #1894: a deterministic city/town/village jurisdiction universe to drive later locality → operator → vendor → reader/owner/admin recursion.

## Evidence

Rensselaer County's official participating-jurisdictions page enumerates every city, town, and village in the county. The County's current delinquent-property-tax guidance publishes the corresponding SWIS rows used by its tax system, including town-outside-village and split-village rows. New York State ORPTS's Municipal Reference List and current state tax tables independently cross-check the municipal/SWIS identities.

The resulting municipality universe contains **22 distinct jurisdictions: 2 cities, 14 towns, and 6 villages**.

- Cities: Rensselaer; Troy.
- Towns: Berlin; Brunswick; East Greenbush; Grafton; Hoosick; Nassau; North Greenbush; Petersburgh; Pittstown; Poestenkill; Sand Lake; Schaghticoke; Schodack; Stephentown.
- Villages: Castleton-on-Hudson; East Nassau; Hoosick Falls; Nassau; Schaghticoke; Valley Falls.

Village of Nassau spans Nassau and Schodack tax/SWIS rows, and Valley Falls spans Pittstown and Schaghticoke rows. Each village is counted once as a municipality rather than once per containing town.

## Evidence boundary

This is jurisdiction evidence only. It does **not** establish that every municipality has a separate police agency, ALPR deployment, Flock contract, reader, platform account, administrator, sharing relationship, or query history. Hamlets are also not municipalities: the County explicitly notes that hamlets have no official municipal status/SWIS identity.

## Canonical records

- `starintel:analysis:rensselaer-county-official-locality-universe-2026-09-15`
- `starintel:research-pass:request-1894-rensselaer-official-locality-universe-2026-09-15`

The packet in `starintel-documents.jsonl` must be materialized through the repository's canonical `python3 scripts/starintel.py import ...` path; the bounded branch materializer exists only to execute that importer and is removed before promotion. Issue #1894 remains open after this bounded pass because operator enumeration, the eight-reader county inventory, PO/AP/payment/renewal chain, native sharing/audit/configuration/users, site permissions, Stewart's exact placements, and actual query/event evidence are still incomplete.
