# FBI Threat Screening Center AI procurement lineage — depth 2

**Dataset:** `fed`  
**Parent targets:** #1960, #1961  
**Notice:** `FBI-TSC-AIE`  
**Date:** 2026-08-02

## Result

The public respondent list is still unavailable. No company is classified as a confirmed applicant, respondent, briefing participant, offeror, subcontractor, reseller, or awardee.

The next public layer is the acquisition and personnel chain around the notice.

## Direct procurement contact

The March 27, 2026 RFI names **Brandon James** as the contracting officer and directs every capability package to his FBI email address.

The same public contracting contact appears on a broader set of FBI market-research notices:

| Date | Notice | Public scope |
|---|---|---|
| 2025-05/07 | BlueKey | Secret-network intelligence production and dissemination modernization |
| 2025-11 | Big Data Extraction | ETL and analytics over enterprise data |
| 2026-01 | Cellular Analysis Survey | Communications-data analysis and mapping |
| 2026-03 | `FBI-TSC-AIE` | TSC AI knowledge, federated search, reporting, synthesis, predictive modeling and visualization |
| 2026-03/04 | `FBI-OCIO-SCRM` | ICT supply-chain illumination and continuous monitoring |
| 2026-05 | `FBI-CJIS-DISE` | Decentralized criminal-justice information sharing and knowledge-graph exchange |
| 2026-07 | `FBI-IMD-IC` | Image capture and document-processing modernization |

This is a **procurement-lineage finding**, not proof that these notices share respondents, evaluators, systems, funding, or a single acquisition program.

## Named people

- **Brandon James** — direct contracting officer for `FBI-TSC-AIE`; also the public contact on the adjacent notice cluster.
- **Harriett Williams** — public co-contact on the Supply Chain Illumination RFI only. No reviewed source ties her to `FBI-TSC-AIE`.
- **Michael Glasheen** — publicly identified as TSC director during the March 2025 renaming and as FBI Operations Director by December 2025. The March 2026 TSC director remains unresolved.
- **Nicholas Dimos** — appointed in 2022 as assistant director of the Finance and Facilities Division and head of contracting activity. His 2026 role and responsibility for this notice remain unresolved.

## Applicant boundary

No authenticated public source reviewed provides:

- a response-receipt log;
- respondent legal or DBA names;
- capability packages;
- briefing invitations;
- demonstration rosters;
- evaluation sheets;
- a market-research report naming firms;
- a follow-on solicitation;
- an award or task order;
- a selected vendor.

Product fit, prior FBI work, GSA availability, lobbying, and employment history are not respondent evidence.

## Depth 3

The next pass is records-driven:

1. obtain response-receipt and email-metadata logs;
2. obtain the market-research report and capability matrix;
3. obtain briefing invitations, schedules, attendee lists and presentation metadata;
4. identify the current TSC director, IT Unit requirement owner, acquisition planner and technical evaluators;
5. identify FBI AI Ethics Council reviewers tied to this requirement;
6. search every procurement system for a descendant notice or award using identifiers and distinctive RFI language;
7. enumerate company personnel only after direct participation is established.

## Packet

- `README.md`
- `source-notes.md`
- `records-request.md`
- `starintel-documents.jsonl`

## Validation target

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-08-02-fbi-tsc-ai-procurement-lineage-depth-2/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
