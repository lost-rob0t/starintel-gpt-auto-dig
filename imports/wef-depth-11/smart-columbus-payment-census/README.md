# Smart Columbus payment census — depth 11

Work in progress.

This pass will scan the City of Columbus Auditor datasets for 2021–2026 and reconcile Smart Columbus-related vendor accounts and names across purchase orders, vendor invoices, vendor transactions, and unique paid bank checks.

## Guardrails

- Paid totals will be calculated from unique bank-check records only.
- Settlement and invoice rows will not be counted as additional cash payments.
- Canceled, voided, and reissued checks will remain linked in the evidence trail.
- Vendor accounts `040255`, `033348`, and `045611` will not be merged without source-backed crosswalk evidence.
- Authorization ceilings will remain separate from paid totals.
