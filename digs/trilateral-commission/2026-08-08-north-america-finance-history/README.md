# Trilateral Commission North America finance and institutional-history pass — 2026-08-08

## Scope

This depth-3 pass separates the Commission's current global membership surface from the **U.S. legal/financial entity**, its regional fundraising model, and the archival record of its founding and early financing. It uses public tax-return data, the Commission's own regional history, IRS disclosure rules, and the Rockefeller Archive Center's Trilateral Commission collection.

## Findings

### 1. North America has a concrete U.S. nonprofit entity that should be modeled separately

`Trilateral Commission North America` is a Washington, D.C. tax-exempt organization with EIN **23-7309933**, recognized as tax-exempt since August 1976 and classified as a 501(c)(3) public charity / policy-analysis organization in IRS-derived Form 990 data.

The current StarIntel corpus primarily models a single global `The Trilateral Commission` organization. A regional legal-entity record would make tax filings, officers, compensation, fundraising, and regional governance much easier to represent without incorrectly attributing North American filings to the entire global Commission.

### 2. The latest North American filing is overwhelmingly contribution-funded

For the fiscal year ending June 2025, the IRS-derived filing reports:

- revenue: **$792,627**
- expenses: **$1,839,874**
- net income: **-$1,047,247**
- net assets: **$895,435**
- contributions: **$749,531**, or **94.6%** of revenue
- investment income: **$43,096**, or **5.4%** of revenue

The same filing lists Richard Fontaine as Executive Director with **$125,000** compensation.

This independently corroborates Fontaine's operational role and gives the dataset a source-backed financial observation surface rather than relying only on biographies.

### 3. The entity has reported consecutive annual deficits, but the filings alone do not establish distress

IRS-derived data shows negative net income for fiscal years ending June 2022, 2023, 2024, and 2025. Net assets moved from approximately **$2.49 million** in FY2022 to **$895,435** in FY2025.

That is a material reserve drawdown. It could reflect planned program/event expenditure, timing of contributions, or other operating choices. Do **not** label the organization financially distressed without examining the full returns, Schedule O explanations, major program expenses, and subsequent filings.

### 4. The Commission itself describes a decentralized regional fundraising model

The Commission's North America page says Canadian and Mexican groups are separately organized for membership choices and for raising/expending funds covering member participation, program contributions, and hosting costs. It also states that:

- a Ford Foundation grant was the most important part of the Commission's financial base during the first triennium (1973-1976);
- fundraising was decentralized after that period; and
- in the United States, an increasing share of support came from corporations, while foundations and individuals also remained important.

This supports modeling regional financial entities/flows rather than treating the global Commission as one undifferentiated bank account.

### 5. The Rockefeller archival record documents founding intent, organizers, and seed funding

The Rockefeller Archive Center holds **167.02 cubic feet** of Trilateral Commission (North America) records covering 1972-2001. Its finding aid describes the Commission's aims as including:

- facilitating communication among the member regions;
- proposing policy recommendations, particularly in foreign policy, economics, security, and relations with developing or communist countries; and
- fostering understanding and support for Commission recommendations among governmental and private-sector non-member leaders.

The finding aid traces the 1972 formation process through David Rockefeller, Zbigniew Brzezinski, George S. Franklin, and other North American, European, and Japanese participants, culminating in the July 23-24, 1972 Pocantico Hills meeting.

It states that initial financing included David Rockefeller seed money supplemented by support including the Kettering Foundation and Ford Foundation.

### 6. Rockefeller Brothers Fund independently confirms historical grant support

The Rockefeller Brothers Fund's own institutional history says David Rockefeller helped found the Trilateral Commission in 1973 and that the Fund made grants to the Commission during its 1970s international-program work on global interdependence.

This is a stronger source for a historical RBF→Trilateral funding edge than unsourced donor-list compilations.

### 7. Recipient Form 990 data cannot reveal a complete donor list

IRS disclosure guidance states that, for organizations such as ordinary 501(c)(3) public charities, contributor names and addresses reported on Schedule B generally are **not required to be publicly disclosed**. Therefore the North American Commission's own public Form 990 cannot be used to enumerate all current donors.

The correct next method is an **inverse donor search**: inspect donor-side private-foundation filings, foundation grant databases, corporate-foundation disclosures, donor-advised-fund records where available, and Commission acknowledgments. Each grant should remain date- and amount-specific.

## Data-model implications

1. Create/resolve a distinct `Trilateral Commission North America` organization identity tied to EIN `23-7309933`.
2. Relate that regional legal entity to the global Commission without assuming the same legal identity for Europe or Asia Pacific.
3. Add annual `financial-observation` records from Form 990 totals instead of putting mutable financials on the core org record.
4. Add exact officer/governance/employment relations, including Richard Fontaine's North American executive-director role, with filing-year timestamps.
5. Treat donor identities as incomplete unless found from donor-side disclosures or explicit Commission acknowledgments.
6. Preserve early Ford/Kettering/Rockefeller/RBF support as historical, source-dated funding relationships rather than implying current funding.

## Next research frontier

1. Extract the full FY2025 Form 990 and Schedule O fields into a finance packet.
2. Enumerate North American trustees/officers across the 2015-2025 filing sequence and reconcile them with current Commission leadership.
3. Invert the grant search across major private-foundation 990-PF filings for recipient EIN/name variants.
4. Search the Rockefeller Archive Center financial-record series for specific historical grant files, amounts, and dates.
5. Resolve whether Canadian and Mexican regional groups have separate legal entities/registrations and add them only when directly supported.

## Primary sources

- https://www.trilateral.org/regions/north-american-group/
- https://projects.propublica.org/nonprofits/organizations/237309933
- https://www.irs.gov/charities-non-profits/public-disclosure-and-availability-of-exempt-organizations-returns-and-applications-contributors-identities-not-subject-to-disclosure
- https://dimes.rockarch.org/collections/2KaqPEr3JRZv5WBQsf9mKn
- https://www.rbf.org/about/about-us/international-philanthropy
