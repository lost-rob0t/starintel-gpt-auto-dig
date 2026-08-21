# Foundation to Promote Open Society — FY2024 Outflow Supplement

**Run:** `2026-08-08`  
**Parent:** OSF public-roster and cross-ties supplemental legal-funding pass  
**Status:** evidence staging; not canonical

## Finding

IRS-derived FY2024 Form 990-PF grant data for **Foundation to Promote Open Society** (EIN `26-3753801`) adds several directly attributable funding edges to institutions already implicated by the OSF recursion.

The filer reports FY2024 revenue of **$935,043,439**, expenses of **$460,769,902**, and grants/contributions paid of approximately **$421.3 million**. Its Part XV grant listing includes two separate awards to **Open Society Foundation London**:

- **$44,927,239**;
- **$8,072,761**.

Both are separate grant rows. They should not be collapsed into one undocumented award. The filing-derived grant index describes the support as non-lobbying activities and programs promoting open, democratic societies worldwide.

This establishes that the FPOS -> OSF London funding channel observed in the FY2022 controlled-entity schedule persists into FY2024 through explicit grant rows.

## Cross-tie into the Ivan Krastev branch

The same FY2024 Part XV list contains a **$3,810,000** grant to the **Institute for Human Sciences** (IWM Vienna).

IWM's own current `Partners and Donors` page independently lists **Foundation to Promote Open Society, New York**. IWM also currently identifies Ivan Krastev as a senior institutional figure in the already-staged Krastev packet.

The defensible graph is therefore:

```text
Foundation to Promote Open Society
          |
          | FY2024 $3.81m grant
          v
Institute for Human Sciences (IWM Vienna)
          |
          | institutional role
          v
Ivan Krastev
```

This is a funding-plus-role topology. It is **not evidence that the funder controls Krastev, IWM, or its scholarship**.

## Additional FY2024 nodes exposed by the same filing

The FY2024 FPOS grant list also includes:

- **Soros Economic Development Fund** — $25,000,000;
- **Bard College** — $20,000,000;
- **Central European University** — $15,000,000;
- **Roma Foundation for Europe** — $15,602,337;
- **Amnesty International Limited** — $5,200,000;
- **Open Society Foundation for Albania** — $3,347,000;
- **Carnegie Endowment for International Peace** — $3,000,000;
- **Stefan Batory Foundation** — $2,900,000.

These are useful recursion candidates because several overlap the OSF board/leadership biographies or the OSF network's named legal entities. They should be imported systematically from the filing rather than selectively interpreted.

An exact-name repo search for `Institute for Human Sciences` and `Soros Economic Development Fund` returned no records during this pass, making both candidate new organization nodes.

## Longitudinal OSF London funding

We now have direct filing-derived evidence at two distinct time points:

### FY2022 controlled-entity schedule

- FPOS -> OSF London: **$46,999,529** `GRANT PAYMENT`;
- OSF London -> FPOS: **$5,668,104** `GRANT PAYMENT REFUND`.

### FY2024 Part XV grant rows

- FPOS -> OSF London: **$44,927,239**;
- FPOS -> OSF London: **$8,072,761**.

The values should remain separate because the filings classify and report them differently. No claim is made here that the FY2022 and FY2024 rows represent identical programs, accounting treatment, or recurring contractual obligations.

## New candidate nodes

```text
starintel:org:institute-for-human-sciences-vienna
starintel:org:soros-economic-development-fund
```

The Soros Economic Development Fund node must later be reconciled against the separately discovered UK establishment `BR021288` before a parent/branch/alias relation is asserted.

## Next moves

1. Capture the exact FY2024 Part XV purposes and recipient addresses for the two OSF London grants from raw filing data.
2. Capture the IWM $3.81m grant row with its exact filed purpose.
3. Search FPOS FY2023 and FY2022 for IWM funding to determine whether $3.81m is one-time or part of a recurring series.
4. Cross-resolve FPOS FY2024 recipients against existing StarIntel entities, especially Bard, CEU, Roma Foundation for Europe, Amnesty International, Carnegie, and Stefan Batory Foundation.
5. Resolve Soros Economic Development Fund's U.S. EIN and its relationship to UK establishment `BR021288`.

## Sources

- https://philanthropy.org/990/report/263753801/foundation-to-promote-open-society — IRS-derived FY2024 Form 990-PF grant data.
- https://projects.propublica.org/nonprofits/organizations/263753801 — FPOS filing series and IRS provenance.
- https://www.iwm.at/about/partners-and-donors — IWM current partners and donors.
- https://find-and-update.company-information.service.gov.uk/company/10187396 — OSF London legal identity.

## Guardrail

Funding is a documented financial relation. It is not, by itself, evidence of direction, control, misconduct, or agreement with every action of the recipient or its personnel.
