# Palantir recursive pass — depth 7

## Scope

Depth 7 expands the unresolved IRS authorization-boundary branch from depth 6, refreshes the Barbaccia, Better Tomorrow/Rockbridge, and Vulcan Elements side branches, and emits the deterministic depth-8 target.

## Main finding

Palantir's IRS footprint is not just the Unified API order. Public procurement records identify six calls under single-award BPA `2023H225A00002`:

| Call | Public scope | Identified obligation |
|---|---|---:|
| `205AE925F00202` | Unified API / semantic access layer | $14,244,448.96 |
| `205AE925F00203` | Compliance Hub models and workflows | $13,325,955.00 |
| `2023H225F00144` | Criminal Investigation Foundry case management | $6,594,996.00 |
| `2023H225F00145` | Procurement management | $4,458,164.60 |
| `2023H225F00156` | Lead Case Analysis support | $8,972,810.00 |
| `205AE926F00047` | SNAP fraud and compliance analytics | $2,250,363.27 |

**Total identified obligations: $49,846,737.83.** The parent vehicle ceiling is $100 million.

This topology supports modeling the deployment as an IRS Palantir application estate spanning semantic/API access, compliance models, case management, procurement management, LCA support, and SNAP analytics. It does **not** establish that every application shares data, roles, users, or authorization boundaries.

## Remaining control gap

The public award descriptions do not resolve:

- the BPA and call-level SOW/PWS;
- the `2025-LCABPA` limited-sources justification and attachments;
- ATO/SSP boundaries and inherited controls;
- connected datasets and permitted application consumers;
- identities, service accounts, roles, approvals, and screening;
- privacy-impact inheritance;
- audit-log retention and review rules.

## Side-branch status

- **Gregory Barbaccia:** no public PLTR disposition, Palantir recusal memorandum, screening arrangement, waiver, or participation log was located. The disclosed holding remains in the $1,001–$15,000 range; absence from the public index is not proof no nonpublic ethics instruction exists.
- **Better Tomorrow / Rockbridge:** the 2024 Form 990 index strengthens evidence of related-party activity and reports Schedule L, but the accessible index does not expose counterparties or transaction amounts.
- **Vulcan Elements / OSC:** the official release describes a $620 million conditional commitment and states that funds are not disbursed before conditions and financial close. A June 24, 2026 congressional release called the loan awarded, but no public closing or disbursement record was located.

## Depth 8 selected target

Acquire and hash the BPA and task-order control documents, beginning with the limited-sources justification, every available SOW/PWS and modification, ATO/SSP material, PIA determination, interface inventory, role/service-account matrix, and audit-retention schedule.

## Records

`starintel-documents.jsonl` contains:

1. the completed depth-7 `research-pass` record;
2. the queued depth-8 `investigation-target` record.

## Validation state

The records were checked against the current v0.9.0 field contract before publication. The branch remains draft-only until `python3 scripts/validate-for-merge.py --site` and all required GitHub checks pass on the final head.
