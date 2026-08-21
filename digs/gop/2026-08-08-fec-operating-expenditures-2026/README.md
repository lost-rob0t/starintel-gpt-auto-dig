# GOP FEC operating expenditures — 2026 cycle

Official FEC `oppexp26.zip` rows filtered to `C00003418`.

- raw matching rows: 15,687
- StarIntel documents: 33,917
- payee people: 399
- payee organizations: 2,143
- financial observations: 15,687
- graph relations: 15,687

This corpus preserves every raw amendment and memo row. It is not a netted or audited total. Payee identities are source-scoped and unresolved unless separately corroborated.

```bash
python3 scripts/run_gop_fec_variant.py import_dnc_fec_oppexp.py
python3 scripts/validate-for-merge.py --site
```
