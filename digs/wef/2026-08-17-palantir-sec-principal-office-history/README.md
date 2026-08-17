# Palantir SEC principal-executive-office history

This hourly HQ/location slice uses existing Palantir and WEF corpus records. It does not create a new dataset.

## Reproducible selection

- seed: `15173172595770829640`
- seed derivation: first 64 bits of SHA-256 over `2026-08-17T18:00-04:00|hourly-auto-dig`
- method: bounded weighted selection over existing WEF-linked public-company organization inputs, favoring missing temporal HQ provenance and relevance to the active Palantir/WEF branch
- selected input: `starintel:org:palantir-technologies-inc`

## Source semantics

Only SEC filing cover-page text explicitly labeled **Address of principal executive offices** is promoted into the office-history graph. SEC business/mailing address metadata is not silently reclassified as headquarters.

Filing dates are observation boundaries. They are not assumed physical move dates.

No geocoding is performed in this slice because exact public street addresses are already supplied by the primary filings and precise coordinates would not add evidentiary value.

## Primary filings

- 2025-11-03 Form 8-K: 1200 17th Street, Floor 15, Denver, Colorado 80202
- 2026-02-02 Form 8-K: 518 17th Street, Suite 1015, Denver, Colorado 80202; the filing separately identifies the 1200 17th Street address as former
- 2026-02-17 Form 10-K: 19505 Biscayne Blvd., Suite 2350, Aventura, Florida 33180; the filing separately identifies 518 17th Street as former
- 2026-06-09 Form 8-K: confirms the Aventura principal-executive-office address

## Materialization

`scripts/seed_palantir_sec_principal_offices.py` fetches the primary filings through the SEC connector, extracts the explicit cover-page office address, validates typed StarIntel documents, writes the dig packet, and imports normalized records through `scripts/starintel.py import --replace`.

The materialized graph uses separate `address`, `observation`, and `relation` records and intentionally carries forward an entity-resolution target for the existing duplicate Palantir organization IDs.
