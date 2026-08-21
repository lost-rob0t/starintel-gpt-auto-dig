# FEC administrative fines involving Republican committee records and explicit name leads

Official FEC administrative-fine bulk records classified by current FEC committee-master party code where available. Explicit Republican/REP/GOP committee names without a current REP code remain name-derived leads and are not represented as verified party affiliation.

- matching cases: 309
- official REP committee-master classifications: 284
- explicit-name leads pending party resolution: 25
- StarIntel documents: 2,021
- recursive investigation targets: 927
- final approved fine amounts in selected bulk rows: $1,629,284.00

The FEC metadata defines `FIN_AMO` as the fine ultimately approved by the Commission. Payment codes are preserved but require reconciliation to case-level payment, collection, and Treasury records. A fine case is represented by its procedural record and disposition—not as a generic corruption or criminal label.

## Classification

- `explicit_republican_name_lead_pending_party_resolution`: 25
- `official_current_committee_master_party_code`: 284

## Target families

- `fec_administrative_fine_complete_case_record`: 309
- `fec_administrative_fine_leadership_compliance`: 309
- `fec_administrative_fine_report_audit`: 309

```bash
python3 scripts/run_gop_fec_variant.py import_dnc_fec_administrative_fines.py
python3 scripts/validate-for-merge.py --site
```
