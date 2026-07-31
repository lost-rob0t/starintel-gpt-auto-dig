# DNC FEC operating expenditures — 2026 cycle

Official FEC `oppexp26.zip` rows filtered to `C00010603`.

- raw matching rows: 28,517
- StarIntel documents: 59,066
- payee people: 721
- payee organizations: 1,310
- financial observations: 28,517
- graph relations: 28,517

This corpus preserves every raw amendment and memo row. It is not a netted or audited total. Payee identities are source-scoped and unresolved unless separately corroborated.

```bash
python3 scripts/import_dnc_fec_oppexp.py
python3 scripts/validate-for-merge.py --site
```
