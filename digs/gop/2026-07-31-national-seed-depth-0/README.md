# GOP national committee seed — depth 0

This pass establishes the public national committee layer for the `gop` dataset.

## Seed graph

- Republican National Committee (`C00003418`)
- NRCC (`C00075820`)
- NRSC (`C00027466`)
- RNC chairman Joe Gruters
- RNC co-chair KC Crosbie
- official party commitments preserved as attributed claims
- FEC financial summaries through May 31, 2026

## Confirmed findings

- The current RNC site identifies Joe Gruters as chairman and KC Crosbie as co-chair.
- The official 2024 platform contains explicit border, deportation, and inflation-policy commitments.
- FEC summaries expose large affiliated-transfer, other-receipt, committee-contribution, and disbursement totals across the three national committees.

These summary categories are leads, not transaction-level attribution.

## Depth-1 queue

1. Resolve affiliated transfers, other committee contributions, and other receipts to itemized committees and transactions.
2. Normalize major vendors and disbursement recipients across RNC, NRCC, and NRSC.
3. Expand RNC leadership, officers, members, prior roles, and state-party links.
4. Separate platform commitments, implementation actions, and measurable outcomes.

## Guardrails

- public sources only
- claims remain attributed until independently adjudicated
- no voter-persuasion work
- no private-person dossiers
- no guilt-by-association edges
