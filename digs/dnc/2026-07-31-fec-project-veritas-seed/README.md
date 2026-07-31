# DNC FEC and Project Veritas seed

This depth-0 AutoDig packet starts a public-source graph for the Democratic National Committee.

## Coverage

- current DNC officers and senior staff
- official FEC committee identity and 2025–2026 financial summary for `C00010603`
- high-value vendor leads derived from a Schedule B aggregation
- FEC Matter Under Review 7157 participants and disposition
- Project Veritas reporting concerning Democracy Partners, Scott Foval, Robert Creamer, and the 2025 David Hogg series
- civil-litigation outcome reporting connected to the 2016 undercover operation
- eight queued recursive investigation targets

## Evidence boundaries

Official DNC and FEC records are represented as source-backed facts. Vendor totals from Capitol Hill Access are leads derived from FEC filings and must be reconciled against raw, amendment-aware Schedule B records before being treated as final totals.

Project Veritas publications are represented as attributed reporting. The packet records that the reporting was published, who it named, and what follow-up questions it creates. It does **not** convert allegations, edited-video interpretations, opinions, or hearsay into verified findings.

FEC MUR 7157 is represented with its actual disposition: the Commission voted 4–0 to find no reason to believe the specified excessive or prohibited in-kind contribution violations and closed the file.

The 2022 Democracy Partners verdict is represented from independent reporting and Project Veritas' own response. The recursive queue calls for the court docket and verdict form so claim-by-claim outcomes are not flattened.

## Packet statistics

- 15 sources
- 18 organizations
- 20 people
- 53 relations
- 8 investigation targets
- 114 StarIntel v0.9.0 documents total

## Recursive queue

1. reconcile the complete DNC Schedule B vendor ledger
2. map vendor ownership, executives, campaign alumni, and related entities
3. expand the current DNC leadership employment and committee network
4. trace loans, debt, collateral, lenders, and creditor exposure
5. build the complete MUR 7157 complaint-response-evidence graph
6. reconstruct the 2016 Project Veritas raw-media and edit chain
7. verify the 2025 Project Veritas David Hogg series against raw media and independent records
8. map DNC transfers and shared vendors across state and territory parties

## Validation

JSON syntax, unique document IDs, and internal relation endpoints were checked while generating the packet. Full StarIntel schema validation and site generation are delegated to repository CI; the pull request must remain draft unless `python3 scripts/validate-for-merge.py --site` and all required checks pass.
