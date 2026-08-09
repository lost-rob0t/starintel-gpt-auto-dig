# Fund For Policy Reform Inc ↔ Open Society Institute — Resource-Sharing Agreement

**Run:** `2026-08-08`  
**Status:** evidence staging; not canonical  
**Source class:** IRS-derived full filing reconstruction

## Finding

Fund For Policy Reform Inc's FY2022 Form 990 Schedule J states that **Fund For Policy Reform Inc and Open Society Institute had a written resource-sharing agreement in place**.

The filing explains that:

- certain Open Society Institute employees performed functions and activities necessary for Fund For Policy Reform Inc to pursue its tax-exempt mission;
- Fund For Policy Reform Inc paid Open Society Institute for its allocated share of those costs;
- Fund For Policy Reform Inc advanced funds to Open Society Institute to cover allocable costs;
- employee compensation was determined by Open Society Institute and documented in Open Society Institute records.

This is a formal operating relationship and should be modeled separately from grants, shared officers, or umbrella-network membership.

## Candidate relation structure

```text
Fund For Policy Reform Inc
  --resource_sharing_agreement_with--> Open Society Institute

Fund For Policy Reform Inc
  --reimbursed_allocated_costs_to--> Open Society Institute

Fund For Policy Reform Inc
  --advanced_funds_for_allocable_costs_to--> Open Society Institute

Open Society Institute
  --provided_employee_functions_to--> Fund For Policy Reform Inc
```

The filing does not, in the rendered Schedule J text currently captured, provide an aggregate dollar value for these resource-sharing flows. Do not invent one.

## Why this matters

The broader supplemental research already distinguishes:

- `Open Society Institute` — EIN `13-7029285`;
- `Fund For Policy Reform Inc` — EIN `26-4351242`;
- `Fund for Policy Reform` — EIN `35-7090597`.

The resource-sharing agreement establishes an explicit operational tie between OSI and the New York FPR Inc entity, while separate IRS-derived records establish the repeated upstream grants from the Delaware Fund for Policy Reform into FPR Inc.

That gives a defensible structure:

```text
Fund for Policy Reform (35-7090597)
        |
        | large annual grants
        v
Fund For Policy Reform Inc (26-4351242)
        |
        | written resource-sharing agreement
        v
Open Society Institute (13-7029285)
```

This is **not** a basis to merge the three legal entities or infer misconduct. It is a basis to model their documented legal and operational relationships accurately.

## Source

ProPublica Nonprofit Explorer / IRS e-file reconstruction, FY2022 Form 990 Schedule J, filing object `202303199349322205`.

Public rendered source indexed at:

`https://pp-990-rendered.s3.us-east-1.amazonaws.com/202303199349322205_IRS990ScheduleJ_0.html`

Organization filing series:

`https://projects.propublica.org/nonprofits/organizations/264351242`

## Next acquisition

1. Inspect Schedule R for explicit related-organization classification involving OSI and other Open Society entities.
2. Capture any dollar values or cost-allocation methodology disclosed elsewhere in Schedule O/R or related filings.
3. Reconstruct the agreement longitudinally to determine when it began and whether it remained in place after FY2022.
4. Keep resource sharing, grants, officer overlap, and program grants as separate relation types.
