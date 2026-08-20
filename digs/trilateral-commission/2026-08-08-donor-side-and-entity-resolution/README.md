# Trilateral Commission donor-side and entity-resolution pass — 2026-08-08

## Scope

This depth-4 pass pivots from recipient-side fundraising totals to donor-side verification. It also extracts dated North American trustee information and tests exact-name nonprofit collisions before those entities can enter the graph.

## Findings

### 1. FY2025 tax data provides a dated trustee snapshot

The IRS-derived FY2025 Trilateral Commission North America filing lists:

- Richard Fontaine — Executive Director, $125,000 compensation
- B. Marc Allen — North American Trustee
- Carla A. Hills — North American Trustee
- Joseph S. Nye Jr. — North American Trustee, `until 5/25`

This is useful governance history because it is dated by a filed tax return rather than inferred from an undated profile archive. Prior-year filings show the trustee surface changing over time, so trustee relations should carry filing-year/validity qualifiers.

### 2. William S. Paley Foundation is a repeat donor-side hit

The William S. Paley Foundation, EIN `13-6085929`, is a private foundation whose IRS-derived Form 990-PF grant tables report general operating support to Trilateral Commission North America:

| Year | Amount | Purpose |
| --- | ---: | --- |
| 2021 | $10,000 | General Operating Support |
| 2022 | $25,000 | General Operating Support |
| 2024 | $25,000 | General Operating Support |

The 2024 $25,000 grant is independently exposed by two IRS-derived filing parsers.

This is materially stronger than a recipient-side donor list because the grant appears on the donor's filing-derived grant schedule.

### 3. Henry Kissinger creates a documented historical overlap, not a causal funding claim

Paley Foundation filing data identifies Henry A. Kissinger as Chairman/Director through November 2023. Separately, the Trilateral Commission publishes historical material featuring Kissinger and hosted a Henry Kissinger tribute in 2022.

Those two facts establish a historical person/network overlap during two of the reported Paley grant years. They **do not** establish that Kissinger initiated, approved, directed, or influenced those grants. No such causal claim should be emitted without board minutes, grant authorization records, or equivalent evidence.

### 4. Exact-name collision: Pittsburgh nonprofit must not be merged

A separate U.S. 501(c)(3) is listed under the exact name `Trilateral Commission` in Pittsburgh, Pennsylvania with EIN `25-1804367`.

The North American Commission entity used in the finance pass is EIN `23-7309933`, Washington, D.C.

These are different legal identifiers and jurisdictions. The Pittsburgh organization belongs on an explicit **do-not-merge** identity list unless direct evidence later establishes a relationship.

### 5. Broader donor lists remain leads, not verified relations

Secondary grant aggregators surface additional possible funders. They are useful for target generation, but those names should not become StarIntel grant relations until checked against:

1. donor-side Form 990-PF / donor-advised-fund disclosure;
2. explicit foundation grant databases or annual reports; or
3. recipient acknowledgments that identify amount/date/purpose.

This prevents circular copying of unsourced donor lists.

## Data-model implications

1. Add filing-year validity to trustee/officer relations.
2. Represent grants as dated donor → recipient financial relations or grant documents with amount and purpose.
3. Attach donor-side filing provenance to every named funding edge.
4. Maintain an entity-resolution exclusion set keyed by EIN/jurisdiction for exact-name collisions.
5. Do not infer policy influence, control, coordination, or conflict from grant or governance overlap alone.

## Next frontier

- Obtain raw Paley 990-PF XML grant rows for archival-grade donor evidence.
- Verify the next donor candidates one-by-one from donor-side filings.
- Reconcile North American trustees across 2015–2025 filings.
- Resolve Canadian and Mexican regional legal entities.
- Convert verified research findings into normalized scripted records only after the research PR validation gate passes.

## Sources

- https://projects.propublica.org/nonprofits/organizations/237309933
- https://projects.propublica.org/nonprofits/organizations/136085929
- https://grantbay.org/form-990/136085929
- https://philanthropy.org/990/report/136085929/william-s-paley-foundation-inc
- https://www.trilateral.org/about/members-fellows/
- https://www.trilateral.org/events/henry-kissinger-tribute-video/
- https://www.charitynavigator.org/ein/251804367
