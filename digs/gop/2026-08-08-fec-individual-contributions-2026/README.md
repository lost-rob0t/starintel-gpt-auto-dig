# GOP FEC de-identified individual-receipt ledger — 2026 cycle

Official FEC `indiv26.zip` rows filtered to `C00003418`.

- raw matching FEC rows: 1,788,508
- duplicate `SUB_ID` rows skipped: 894,254
- unique FEC receipt rows: 894,254
- published StarIntel documents: 894,255
- contributor names emitted: no
- contributor locations emitted: no
- contributor employers/occupations emitted: no
- raw contributor rows embedded: no

Each campaign-finance record retains the FEC `SUB_ID`, filing/transaction/image identifiers, transaction amount/date/type, amendment/memo flags, and the RNC recipient linkage. Duplicate physical rows caused by overlapping FEC archive members are not counted twice. Contributor identity fields are never materialized.

```bash
python3 scripts/import_gop_fec_deidentified_receipts.py
python3 scripts/validate-for-merge.py --site
```
