# Trilateral Commission Mellon historical grant verification pass — 2026-08-08

## Scope

This same-depth donor-side pass verifies historical foundation funding from **donor-owned primary grant records** instead of repeating secondary donor lists. It also distinguishes verified award details from related grant records whose official pages are currently inaccessible.

## Findings

### 1. Mellon Foundation directly verifies a $150,000 grant in 1976

Mellon's official grant database records:

- recipient: **Trilateral Commission**
- purpose: **general support**
- amount: **$150,000**
- award date: **October 6, 1976**
- term: **36 months**
- location recorded by Mellon: New York, New York

This is a primary donor-side historical funding edge.

### 2. Mellon Foundation directly verifies a $165,000 grant in 1985

Mellon's official grant database separately records:

- recipient: **Trilateral Commission**
- purpose: **general support**
- amount: **$165,000**
- award date: **June 6, 1985**
- term: **36 months**
- location recorded by Mellon: New York, New York

### 3. Mellon itself exposes additional Trilateral grant records for 1979, 1982, and 1992

The 1976 Mellon page links related Trilateral Commission grants in **1979, 1982, 1985, and 1992**.

The unresolved official IDs are:

- 1979: `trilateral-commission-12431`
- 1982: `trilateral-commission-12589`
- 1992: `trilateral-commission-15674`

Those three official pages currently return cache misses through the research tool. Their existence is source-backed by Mellon's own related-grant index, but **their amounts and purposes are intentionally left unresolved**. Secondary sites are not being used to fill the gap.

### 4. Archival context supports a broader early foundation-funding environment

The Rockefeller Archive Center's Trilateral Commission (North America) finding aid says the organization began with David Rockefeller seed money and later obtained support from sources including the **Kettering Foundation** and **Ford Foundation**.

That supports further primary-source grant excavation. It does not establish that any historical funder remains a current funder.

## Data-model implications

1. Funding edges must be time-scoped by award date and term.
2. Preserve donor wording for the recipient before resolving old grants to a modern legal entity.
3. Do not backfill inaccessible grant amounts from secondary compilations.
4. Keep historical funding distinct from present-day funding.
5. A grant is an economic relation, not evidence of control, coordination, policy capture, or agreement.

## Next frontier

- recover the official 1979, 1982, and 1992 Mellon grant pages or archived copies;
- extract exact Ford Foundation grant amounts from Ford annual reports / archival grant files;
- extract Kettering and Rockefeller historical amounts from primary records;
- reconcile historical recipient names to the correct regional/legal entity for each award year.

## Primary sources

- https://www.mellon.org/grant-details/trilateral-commission-14772
- https://www.mellon.org/grant-details/trilateral-commission-12784
- https://dimes.rockarch.org/collections/2KaqPEr3JRZv5WBQsf9mKn
