# Smart Columbus ordinance-to-payment reconciliation — depth 12

Work in progress.

This pass joins the 19 direct paid checks from the Depth 11 census back through:

`bank check → payment transaction → settlement group → invoice journal → purchase order → ordinance`

## Attribution rules

- Exact identifiers and explicit descriptions outrank amount similarity.
- Checks aggregating multiple invoices remain grouped.
- Amount/date matches without documentary labels are classified as candidates, not confirmed ordinance links.
- Voided, canceled, and reissued checks remain linked but are not counted as additional paid cash.
- Vendor accounts `033348`, `040255`, and `045611` remain separate pending vendor-master history.
