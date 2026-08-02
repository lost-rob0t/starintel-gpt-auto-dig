# DNC membership roster — January 2025 historical snapshot

Imports the public spreadsheet published with *The American Prospect* on January 10, 2025.

- roster rows: 450
- StarIntel documents: 1,125
- people: 445
- organizations: 57
- relations: 620
- sources: 3
- roster affiliation codes: 58

This is a dated historical roster, not a claim that every person remains a DNC member. Geographic delegations are linked to official state-party organizations. National and affiliate codes are preserved as source-scoped roster categories unless independently resolved. No phone numbers or email addresses are imported.

```bash
python3 scripts/import_dnc_membership_roster.py
python3 scripts/validate-for-merge.py --site
```
