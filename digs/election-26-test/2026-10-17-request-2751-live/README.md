# #2751 live case 01 — official nonpolitical government dataset description

**Date:** 2026-10-17  
**Dataset:** `election-26-test` (experimental benchmark; NOT production `election-26`)  
**Request key:** `auto-dig:election-26-test-boundary-10`  
**Case ID:** `01`  
**Source:** United States Geological Survey, [ANSS Comprehensive Earthquake Catalog (ComCat)](https://earthquake.usgs.gov/data/catalog/).

This live research control independently consulted the official USGS ComCat documentation. ComCat contains earthquake source parameters and related products contributed by worldwide seismic networks. The canonical `document` record is a *public dataset description*, not an earthquake event, a model claim, a political record, or a synthetic fixture. No ComCat individual events were queried or ingested.

The source page was reviewed on 2026-10-17 through a web retrieval. No canonical raw HTML bytes or source-byte hash were available, so the record declares that limitation. Source authority is the official `earthquake.usgs.gov` publisher page; source status is NOT evidence of independently authenticated page-byte custody.

## Boundaries

- This is a genuine official-source research case, separate from the 337 synthetic baseline records in `2026-10-17-boundary-probe/`.
- No personal identities, locations, contacts, voter profiles, campaign finance rows, or contributor fields were collected.
- This case demonstrates bounded public-source research and packet preparation; it does not prove live FEC acquisition, bulk import, source-byte archival, or a complete end-to-end StarIntel deployment.
- The generated `Document` schema field/type/reference projection was inspected; the maintained Python runtime and Nim merge gate must be tested independently.
- No production `db/` entries were written. Do not mistake this test-only packet for a published production research record.

## Reproduce

```sh
python3 -m unittest tests.test_election26_live_case01 -v
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype document
nimble buildFast
bin/validate-for-merge --site
```

Report each command as RUN only if it actually executed. New exact-head hosted CI must be inspected separately. Other cases 02–10 are untouched; OpenCode comparison is NOT TESTED.
