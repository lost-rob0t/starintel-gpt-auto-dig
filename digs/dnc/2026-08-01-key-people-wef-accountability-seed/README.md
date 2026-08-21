# DNC key people: WEF and accountability seed

This seed begins the people-first pass after the large DNC corpus merge.

## Current officer sweep

The official DNC leadership page currently lists eleven national officers:

- Ken Martin — Chair
- Jane Kleeb — ASDC President, Vice Chair
- Reyna Walters-Morgan — Vice Chair for Civic Engagement and Voter Participation
- Malcolm Kenyatta — Vice Chair
- Artie Blanco — Vice Chair
- Shasti Conrad — Vice Chair
- Jason Rae — Secretary
- Virginia McGregor — Treasurer
- Chris Korge — National Finance Chair
- Joyce Beatty — Associate Chair
- Stuart Appelbaum — Associate Chair

The initial exact-name search of official WEF-domain results found no direct profile or exact-name result for these eleven officers. That result is retained only as search metadata. It does **not** establish that no direct, historical, indirect, employer, board, event, Young Global Leaders, Global Shapers, council, partner, contributor or archived relationship exists.

## Verified WEF records added

- Gavin Newsom — official WEF people profile
- Gavin Newsom — explicitly identified by an official WEF article as a Young Global Leader alumnus
- Pete Buttigieg — official WEF people profile
- Gretchen Whitmer — official WEF 2026 Annual Meeting participant and public-session speaker
- Chris Coons — official WEF 2026 Annual Meeting participant

These are source-scoped seeds. Their identities and exact paths into the existing DNC graph must be resolved before creating DNC-membership or internal-party relations.

## Initial accountability records

- **Joyce Beatty:** House Ethics Report 117-108 concerned her July 2021 protest arrest. The committee declined to create an investigative subcommittee, took no further action and closed the matter. This is stored as an official no-further-action disposition and counterevidence, not as corruption.
- **Ken Martin:** the FEC record concerns a Minnesota DFL rulemaking petition. It is policy advocacy, not an enforcement matter or misconduct finding.

## Queue generator

`scripts/generate_dnc_key_people_wef_accountability.py` inventories every DNC person record and creates:

1. a WEF/YGL/Global Shapers verification target for every person;
2. a complete accountability-record target for current officers and high-priority people;
3. a public-network target for current officers and high-priority people.

The accountability lane searches official ethics, campaign-finance, inspector-general, court, DOJ, attorney-general, professional-discipline, lobbying, financial-disclosure, procurement, nonprofit, labor and corporate records. Complaints, allegations, investigations, findings, settlements, dismissals, reversals, acquittals, exonerating outcomes and corrections must remain separate.

```bash
python3 scripts/generate_dnc_key_people_wef_accountability.py --all-people
python3 scripts/validate-for-merge.py --site
```
