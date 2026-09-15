# Request #1907 — Onondaga official locality universe

Worker 3/8 fills one explicit gap from request #1907: a deterministic city/town/village jurisdiction universe to drive later locality → operator → vendor → reader/owner/admin recursion.

## Evidence

New York State Office of Real Property Tax Services publishes the SWIS Municipal Reference List. Its Onondaga rows establish Syracuse, the county's towns, village SWIS identities, and split-village rows. Because that reference PDF is dated 2019, this pass cross-checks the city/town universe against the New York State 2026–2027 STAR exemption page (updated August 14, 2026) and the village universe against the Tax Department's RPTL §1402 village-status table (records on file through August 12, 2025).

The resulting municipality universe is 35 distinct jurisdictions: one city, 19 towns, and 15 villages. North Syracuse spans Cicero and Clay in the SWIS reference, and Baldwinsville spans Lysander and Van Buren; each village is counted once using its dominant village identity.

## Evidence boundary

This is jurisdiction evidence only. It does **not** establish that every municipality has a separate police agency, ALPR deployment, Flock contract, reader, sharing relationship, platform account, or query history. Those layers remain separate follow-up work.

## Canonical records

- `starintel:analysis:onondaga-county-official-locality-universe-2026-09-15`
- `starintel:research-pass:request-1907-onondaga-official-locality-universe-2026-09-15`

The packet in `starintel-documents.jsonl` must be materialized with the repository's canonical `python3 scripts/starintel.py import ...` path. Issue #1907 remains open after this bounded pass because operator enumeration, county/special-district/campus coverage, vendor/contracts/readers, native sharing/audit state, and actual query/event evidence are still incomplete.
