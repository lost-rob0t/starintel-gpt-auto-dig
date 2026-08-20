# Trilateral Commission dataset research pass — 2026-08-08

## Scope

This pass audits the existing `trilateral-commission` dataset against the Commission's public current-roster surface and selected official profile pages. It does not treat network membership as evidence of wrongdoing, control, coordination, or shared views.

## Existing corpus

The July 31 scraper produced a dataset manifest with 484 person records, 484 `member_of` relations, and 484 cross-tie targets. The source surface was the Commission's paginated `/people/` archive.

The earlier global `dark-academia-membership-recursion-2026-07-31` research pass recorded the Trilateral scrape, but it was not a `trilateral-commission` dataset-specific research-pass record. That is why the dataset page did not have its own research ledger entry.

## Findings

### 1. The 484-profile scrape is not a clean current-membership census

The Commission exposes two materially different surfaces:

- `https://www.trilateral.org/people/` — a paginated people archive.
- `https://www.trilateral.org/about/members-fellows/` — the current Leadership, Members & Fellows roster.

The current roster explicitly distinguishes regional members, leadership, David Rockefeller Fellows, and global members. The current page reports 135 North America members, 184 Europe members, and 96 Asia Pacific members, and states that members who enter government roles rotate off.

The existing scraper normalized every captured profile into a generic `member_of` relation. That is too strong without a current-roster check.

### 2. Archive-only profile presence can survive after current membership changes

Sample checks demonstrate the problem:

- Ajay Banga still has an official Commission profile page describing his World Bank role.
- Doug Beck still has an official Commission profile page describing his Defense Innovation Unit role.
- Neither name appears on the current Leadership, Members & Fellows page reviewed in this pass.

These records should therefore remain as official-profile evidence, but their current membership status must be classified as historical/archive/unresolved unless separately established.

### 3. Governance roles are under-modeled

The current roster publishes explicit chairs, deputy chairs, executive directors, and a 74-member Executive Committee. The existing Trilateral scrape is dominated by generic `member_of` edges.

High-value normalization should produce exact predicates/roles for governance positions rather than treating every relationship as equivalent membership.

Examples from the current page include:

- Meghan L. O'Sullivan — North America Chair.
- Richard Fontaine — Executive Director, North America Group.
- Axel A. Weber — European Chairman.
- Barry Desker — Asia Pacific Deputy Chairman.
- Herminio Blanco Mendoza — Mexico Deputy Chair.
- Jeffrey Simpson — Canada Deputy Chair.

### 4. Profile role/employer extraction is incomplete

The official current roster identifies Laurence D. Fink as Chairman and CEO of BlackRock and Richard Fontaine as CEO of CNAS plus North America Executive Director.

Their current repository person records contain the Commission affiliation but leave `employers`, `positions`, and `public_roles` empty. This is a concrete extraction/normalization gap.

### 5. Official pages themselves require freshness handling

The North America region page contains older membership-ceiling language: 87 U.S., 20 Canadian, and 13 Mexican members, while later on the same page it refers to a Canadian Group of 24. The current Leadership, Members & Fellows page reports 135 North America members.

For current status, prefer the current roster surface. Preserve the region page as historical/contextual evidence rather than silently reconciling conflicting official text.

## Classification rules for the next pass

For each of the 484 archive-derived profiles, classify status into one or more explicit categories:

1. current member
2. current leadership
3. current David Rockefeller Fellow
4. current global member
5. archived/historical profile
6. unresolved status

Do not infer current membership from `/people/<slug>/` existence alone. Preserve historical profile evidence even when a current relationship is not established.

## Next research frontier

1. Deterministically reconcile all 484 profiles against the current roster and fellows/global-member sections.
2. Downgrade or time-bound archive-only `member_of` relations instead of deleting the underlying profile evidence.
3. Extract role/employer text from current official profiles into canonical person/employment/relation records.
4. Add exact Commission governance relations for chairs, deputies, executive directors, and Executive Committee members.
5. Resolve historical membership intervals where official archives or dated lists support them.
6. Re-run cross-network linking only after identity and current-status classification are stable.

## Primary sources

- https://www.trilateral.org/people/
- https://www.trilateral.org/about/members-fellows/
- https://www.trilateral.org/regions/north-american-group/
- https://www.trilateral.org/people/ajay-banga/
- https://www.trilateral.org/people/doug-beck/
- https://www.trilateral.org/people/laurence-d-fink/
- https://www.trilateral.org/people/richard-fontaine/

## Repository records inspected

- `db/dataset-manifest/starintel:dataset-manifest:trilateral-commission-public-roster.ndjson`
- `db/research-pass/starintel:research-pass:dark-academia-membership-recursion-2026-07-31.ndjson`
- `db/org/starintel:org:trilateral-commission.ndjson`
- `db/person/starintel:person:trilateral-commission:laurence-d-fink.ndjson`
- `db/person/starintel:person:trilateral-commission:richard-fontaine.ndjson`
- `scripts/scrape_dark_academia_memberships.py`
- `scripts/starintel_site/render.py`
- `scripts/starintel_site/builder.py`
