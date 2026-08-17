# Palantir principal-executive-office enrichment

This hourly HQ/location slice uses existing Palantir and WEF corpus records. It does not create a new dataset.

## Reproducible selection

- seed: `15173172595770829640`
- seed derivation: first 64 bits of SHA-256 over `2026-08-17T18:00-04:00|hourly-auto-dig`
- method: bounded weighted selection over existing WEF-linked public-company organization inputs, favoring missing temporal HQ provenance and relevance to the active Palantir/WEF branch
- selected input: `starintel:org:palantir-technologies-inc`

## Source semantics

The materialized current-office edge uses Palantir Investor Relations' explicit **principal executive office address** change notice. The notice says the Aventura address is effective February 17, 2026. Palantir's 2025 Form 10-K, filed the same day, independently lists the same address as the address of principal executive offices.

Generic SEC business/mailing metadata, incorporation jurisdiction, employee location, and private-address inference are not promoted into this relation.

The SEC cover-page extractor remains covered by deterministic tests, including former-address separation and real-world combined-cell layouts. GitHub-hosted runners received HTTP 403 from SEC Archives during live materialization, so the one-shot materializer uses the authoritative company IR notice as its live source. If the company page itself is transiently unavailable, it may fall back to the exact reviewed primary-source notice captured during this run; the generated observation records which capture path was used.

## Geographic precision

The source supplies a full public organizational street address:

`19505 Biscayne Boulevard, Suite 2350, Aventura, Florida 33180`

No geocoding is performed. Exact coordinates would not add evidentiary value to this slice, and the system does not manufacture coordinates from address text.

## Materialization

`scripts/seed_palantir_sec_principal_offices.py`:

1. attempts live retrieval of the authoritative Palantir Investor Relations notice;
2. extracts the explicit effective date and principal-office address;
3. validates typed StarIntel `address`, `observation`, `relation`, `analysis`, `investigation-target`, `research-pass`, and versioned `org` documents;
4. writes the dig packet outside `db/`;
5. imports normalized records through `scripts/starintel.py import --replace` because the existing Palantir organization is intentionally version-updated.

The follow-up target preserves the unresolved duplicate Palantir organization IDs before any cross-dataset location propagation into the WEF-facing alias.
