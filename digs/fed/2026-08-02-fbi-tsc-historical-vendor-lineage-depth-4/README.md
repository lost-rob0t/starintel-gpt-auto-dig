# FBI TSC historical vendor and offeror lineage — depth 4

**Dataset:** `fed`  
**Root:** FBI Threat Screening Center Analysis Services / `FBI-TSC-AIE`  
**Purpose:** reconstruct the public contractor lineage before the 2025 BAE award without mislabeling historical firms as current bidders or AI-RFI respondents.

## Confirmed historical layers

| Period | Requirement | Confirmed public roles |
|---|---|---|
| 2014 | TSC operational support bridge and consolidation | SAVA Workforce Solutions and Sotera were described as incumbent TSC support contractors; SAVA received a short bridge notice |
| 2014 | RFP `DJF-14-1200-R-0000040` | Strategic Operational Solutions received the operational-support award; Lynxnet submitted a proposal and protested |
| 2019–2020 | RFQ `15F067-19-Q-0000075` | Koniag Technology Solutions received the TSC critical-facilities task order; INTELiTEAMS submitted a quotation and protested |
| 2020 | TSC analytic-support program | BAE Systems was prime and Cyberspace Solutions, an Illuminate company, publicly identified itself as a teammate |
| 2025 | TSC Analysis Services | BAE Systems Technology Solutions & Services won task order `15F06725F0001209` from seven offers |

These requirements are not interchangeable. Operational support, IT support, critical-facilities operations, analytic support, and AI-enhancement market research are preserved as separate scopes.

## Named people added

- **Lafayette Mabry** — FBI/DOJ forecast point of contact for the 2014 TSC support forecast. This establishes a public forecast contact, not source-selection authority.
- **Jerry Mannes II** — publicly represented INTELiTEAMS in the GAO cost request arising from its TSC critical-facilities protest.
- **James Nowotny** — recent public career announcements describe historical FBI TSC systems work and later KeyW/Sotera-lineage program leadership. This is a personnel lead requiring primary employment records before finer attribution.

## Current boundary

No record in this packet establishes that SAVA, Sotera, STOPSO, Lynxnet, Koniag, INTELiTEAMS, Cyberspace Solutions, KeyW, or any named person:

- was one of the six unsuccessful 2025 TSC Analysis Services offerors;
- responded to `FBI-TSC-AIE`;
- attended an AI-RFI briefing or demonstration;
- currently subcontracts to BAE on the 2025 award.

## Next layer

1. Run the FBI procurement collector over the FBI Business repository, SAM.gov and USAspending.
2. Extract all FY26 forecast entries, awardee lists, industry-day registration lists and TSC-linked notices.
3. Recover the 2025 solicitation and offer-receipt record.
4. Obtain unsuccessful-offeror notices, source-selection metadata and BAE subcontract records.
5. Cross-match every confirmed 2025 offeror and 2026 RFI respondent against this historical roster.
6. Enumerate proposal, capture, program, transition and technical personnel only with role-specific evidence.

## Files

- `README.md`
- `source-notes.md`
- `starintel-documents.jsonl`

## Validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-08-02-fbi-tsc-historical-vendor-lineage-depth-4/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
