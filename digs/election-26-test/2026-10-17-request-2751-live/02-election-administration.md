# #2751 live case 02 — election administration date and official office directory

**Date inspected:** 2026-10-17
**Dataset:** `election-26-test` (isolated experiment; not production `election-26`)
**Case:** `02`; **request key:** `auto-dig:election-26-test-boundary-10`
**Record ID:** `starintel:document:autodig-2751-case02-election-admin-20261017`

## Two primary official sources

1. [United States Postal Service, Postal Bulletin 22701, "Key Dates"](https://about.usps.com/postal-bulletin/2026/pb22701/html/cover_003.htm): identifies Tuesday, November 3, 2026 as the 2026 general-election date. USPS is not the authority for state election administration.
2. [U.S. Election Assistance Commission, "Register And Vote in Your State"](https://www.eac.gov/voters/register-and-vote-in-your-state): directs visitors to state/territory and local election offices, registration, and ballot information. The EAC explicitly warns that procedures differ and deadlines/details must be confirmed with state or local sources.

These pages were inspected on 2026-10-17. Raw source bytes and an independently authenticated content hash were NOT obtained. Source text may change after inspection. The EAC directory is a navigation source, NOT a nationwide registration deadline table. This packet asserts no candidate preference, party preference, ballot-choice recommendation, individual voter identity, eligibility status, or jurisdiction-specific registration deadline.

## Bounded research result

One canonical-shaped StarIntel 0.10.1 `document` references both sources. No individual-level voter records, contact details, personal location, or political persuasion. This is official-source documentation research, not a production election scrape or transactional ingest. The unrelated production request #2749 remains untouched. OpenCode comparison: NOT TESTED.

The focused native regression is at `tests/test_election26_live_case02.py`; only count tests as RUN if executed. Complete maintained canonical validation and the Nim merge gate must be observed separately before promoting or merging.

## Required verification

```sh
python3 -m unittest tests.test_election26_live_case02 -v
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype document
nimble buildFast
bin/validate-for-merge --site
```
