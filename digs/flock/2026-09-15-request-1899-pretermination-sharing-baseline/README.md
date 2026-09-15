# Request #1899 — Ithaca pre-termination Flock sharing baseline

Worker 3/8 bounded additive pass for the existing Ithaca municipal Flock offboarding investigation.

## What this adds

Contemporaneous WSKG reporting on March 6, 2026 attributes a concrete sharing description to the Ithaca Police Department: IPD said its Flock data was shared with neighboring Tompkins County police departments, New York State Police, New York State's Crime Analysis Center Network, and the Tompkins County Sheriff's Office.

This advances the existing `starintel:investigation-target:ithaca-sharing-history` target. It does **not** turn the report into a native Flock `SharedNetworks` snapshot. The evidence does not establish every exact municipal recipient, reciprocity, approval actors, effective dates, accounts, query activity, or when any sharing edge was removed after termination.

The City of Ithaca's March 4, 2026 termination resolution remains the offboarding boundary: it directed contract termination and immediate suspension, but technical execution still requires separate evidence.

## Sources

- WSKG, March 6, 2026, `Reporter debrief: more on Ithaca’s vote to sever ties with Flock Safety` — https://wskg.org/2026-03-06/reporter-debrief-more-on-ithacas-vote-to-sever-ties-with-flock-safety
- City of Ithaca Common Council, March 4, 2026 revised agenda/termination resolution — https://www.cityofithacany.gov/AgendaCenter/ViewFile/Agenda/_03042026-3165

## Remaining hard joins

`reported recipient class -> native SharedNetworks edge -> effective dates/approval -> account/query audit -> termination -> edge removal`

The next primary-source target is the pre/post-termination Flock `SharedNetworks`, Organization Audit, Network Audit, user/admin, query/event, and revocation package. The Cornell access question remains unresolved unless a native directed edge is recovered.

The packet is authored outside `db/`. Normalized records must be materialized through `python3 scripts/starintel.py import` and pass the repository's complete canonical merge/site gates before merge.