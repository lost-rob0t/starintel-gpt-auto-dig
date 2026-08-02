# DNC key people: WEF and accountability queue

This packet creates a WEF-link verification target for every DNC person record and deeper accountability/network targets for current officers and high-priority people.

- people inventoried: 105,897
- StarIntel documents: 105,956
- investigation targets: 105,933

A failed WEF profile probe is search metadata, not proof of no relationship. Allegations, investigations, findings, settlements, dismissals, reversals, acquittals, exonerating outcomes, and corrections must remain separate.

## Target families

- `dnc_person_accountability_record`: 18
- `dnc_person_public_network`: 18
- `dnc_person_wef_link_verification`: 105,897

```bash
python3 scripts/generate_dnc_key_people_wef_accountability.py --all-people
python3 scripts/validate-for-merge.py --site
```
