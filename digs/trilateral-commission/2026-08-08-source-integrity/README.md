# Trilateral.org: official domain, cursed metadata

Date: `2026-08-08`

## What happened

The official Trilateral Commission domain is useful. It is **not** uniformly trustworthy at the field level.

> open official publications index
>
> get gambling SEO text before the actual publications
>
> find a casino/tourism article living on the same official domain
>
> find Lorem ipsum in official templates
>
> find event metadata disagreeing with itself
>
> parser now needs trust issues

That is source contamination and stale/contradictory metadata. It is **not** proof the site was hacked. The root cause remains unresolved.

## Receipts

### Casino/SEO contamination

The publications index currently serves unrelated online-gambling text in Polish, French, and English before legitimate publication listings. A separate official-domain page at `https://www.trilateral.org/publications/deauville-casno-france/` serves French tourism/casino material with an outbound online-casino link.

Do not normalize unrelated text just because `trilateral.org` served it.

### Placeholder content

The North America contact page and historical publication pages expose `Lorem ipsum`; the contact template also displays the placeholder attribution `Frances Loremis`.

### Contradictory dates

The `T30 + T31 – Security & Disarmament` page surfaces a related event titled `2018 European Regional Meeting` while displaying an event date of **August 31, 2021**. The evidence establishes a contradiction, not which date is correct.

## Why this matters

Earlier passes already found stale current-role text, archive profiles mistaken for current membership, region-specific membership rules, and stale regional counts. These newer observations show a broader **field-freshness/source-integrity problem**, not one lonely scraper bug having a bad evening.

## Ingestion rules

1. Reject obvious `Lorem ipsum`, gambling/SEO injection, and unrelated promotional text.
2. Track source-domain trust separately from field-level freshness/confidence.
3. Preserve internal date contradictions instead of silently choosing a winner.
4. Prefer original downloadable artifacts or archival copies over contaminated wrapper HTML for historical publications.
5. Corroborate mutable roles and employers with current authoritative sources.
6. Keep roster status, biography text, event metadata, and publication descriptions as separate sourced claims.

## Next dig

- enumerate contaminated publication URLs into a quality-test corpus;
- compare wrapper pages against PDFs and archived snapshots;
- add scraper tests that fail on placeholder/SEO contamination;
- scan other dataset source domains for the same failure class.

## Primary observations

- https://www.trilateral.org/publications/?_publication_type=trialogue
- https://www.trilateral.org/publications/deauville-casno-france/
- https://www.trilateral.org/regions/north-american-group/contact-us/
- https://www.trilateral.org/publications/t30-t31-security-disarmament-summer-fall-1982/
