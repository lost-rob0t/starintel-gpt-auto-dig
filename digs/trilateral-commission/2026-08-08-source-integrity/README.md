# Trilateral.org source-integrity and stale-metadata audit — 2026-08-08

## Scope

This pass audits whether `trilateral.org` can be treated as uniformly authoritative at the **field level**. The answer is no: the official domain is still valuable, but current HTML contains unrelated SEO/casino content, template placeholders, and contradictory metadata that require ingestion guards and corroboration.

## Findings

### 1. The official publications index contains unrelated casino SEO content

The current Trilateral publications index serves long blocks of unrelated online-gambling text in Polish, French, and English before the legitimate publication listing.

This is not normal publication metadata and must never be normalized into research records merely because it comes from the official domain.

### 2. The official domain exposes a standalone unrelated casino/tourism publication page

`https://www.trilateral.org/publications/deauville-casno-france/` currently serves a French tourism article about Deauville that includes casino promotion and an outbound online-casino link.

Observed facts support describing this as **source contamination / SEO-spam-like content**. They do not establish the root cause. Do not state that the site was definitively hacked without infrastructure, incident, or administrative evidence.

### 3. Multiple official templates expose placeholder content

The North America contact page and historical publication pages expose `Lorem ipsum` blocks. The contact template even displays the placeholder attribution `Frances Loremis`.

This demonstrates that official-domain text can include unfinished template content unrelated to the Commission's substantive record.

### 4. Event metadata can contradict itself

The official `T30 + T31 – Security & Disarmament` publication page surfaces a related event titled `2018 European Regional Meeting` but displays the event date as **August 31, 2021**.

That does not tell us which date is correct. It tells us the HTML cannot be treated as internally self-validating.

### 5. The source-quality problem explains several earlier data issues

The previous passes found:

- stale current-role text for John B. Hess and Marek Belka;
- archive profiles being mistaken for current membership;
- regional/global membership-policy wording that differs in scope;
- internally stale regional membership counts.

The casino/placeholder/date findings show those are part of a broader **field freshness and source-integrity problem**, not merely one scraper bug.

## Recommended ingestion controls

1. Add hard rejection patterns for obvious `Lorem ipsum`, gambling/SEO injection, and unrelated promotional text.
2. Store source-domain trust separately from field-level freshness/confidence.
3. Flag internal date contradictions instead of choosing one silently.
4. For historical publications, prefer the original downloadable artifact or archival copy over contaminated wrapper HTML.
5. Corroborate mutable roles/employers with employer, government, regulator, or other current authoritative sources.
6. Keep current roster inclusion, biography text, event metadata, and publication description as separately sourced claims.

## Next frontier

- enumerate contaminated publication URLs and build a deny/quality-test corpus;
- compare publication wrapper pages against downloadable PDFs and archived snapshots;
- add scraper tests that fail on placeholder/SEO contamination;
- scan other source domains in the dataset for the same class of source-integrity failure.

## Primary observations

- https://www.trilateral.org/publications/?_publication_type=trialogue
- https://www.trilateral.org/publications/deauville-casno-france/
- https://www.trilateral.org/regions/north-american-group/contact-us/
- https://www.trilateral.org/publications/t30-t31-security-disarmament-summer-fall-1982/
