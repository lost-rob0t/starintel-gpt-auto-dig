# Public institutional listings, observed 2026-10-10

This separate packet contains eight public-page URL observations and four
bounded findings prepared from supplied verified observations. It keeps the
original thirteen-record institutional adaptation unchanged and reproducible.
No additional browsing, people extraction, employee collection, or main-DB
import is performed by this generator.

## What the observations establish

- Ohio Voice's partner page is explicitly a **2025** listing with **33**
  organization entries counted in the supplied review. A 2026 roll was not
  confirmed; this does not establish current membership.
- OVRC's About Us page names **five steering organizations**. Its separate
  gallery says **Some of Our Coalition Partners**, so it is a partial listing.
  No complete or independently current membership roll is inferred.
- Three official governance-directory URLs are retained as links only.
  No directory members or personal profiles are extracted.
- Three public organization-level LinkedIn pages are retained with the supplied
  website/location correlation. Employees are not treated as members or
  endorsements, and no person's political beliefs are inferred.

`observations.json` records the exact supplied facts and URL list used to produce
the draft. `generation-receipt.json` records input/output hashes and every ID.
All canonical records are `url` or `finding` documents validated by the pinned
published runtime through `scripts/starintel.py create --fields`.

Only a retrieval **date** was supplied. It is preserved in each record's notes;
`fetchedAt`, `sourceRetrievedAt`, `collectedAt`, `createdAt`, and `updatedAt` are
omitted rather than fabricating a clock time. Empty source arrays on URL
observations avoid self-citation and remain visible in `unverifed`. Every finding
cites its supporting URL records through typed source and evidence references.

The retained historical `anarchist-violence` dataset name does not imply
violence or wrongdoing by any institution described.

## Reproduce

From the repository root, with the pinned runtime installed or available in
`PYTHONPATH` (for example `../python-runtime-current`):

```bash
python3 digs/anarchist-violence/2026-10-10-columbus-election-official-listings/generate-packet.py
python3 digs/anarchist-violence/2026-10-10-columbus-election-official-listings/generate-packet.py --check
python3 -m unittest discover -s tests -p test_columbus_official_listings_packet.py -v
```

The repository's full native merge gate and current-head required CI remain
mandatory before marking ready or merging; successful draft generation is not
a readiness claim.
