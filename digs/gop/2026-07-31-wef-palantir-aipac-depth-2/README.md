# GOP AutoDig — WEF, Palantir funding, and AIPAC money network (depth 2)

## Scope

This pass recurses from the GOP national committee and joint-fundraising graph into three evidence-separated paths:

1. World Economic Forum links involving Palantir Technologies and Alex Karp.
2. Federal political contributions by the Employees of Palantir Technologies Inc. PAC.
3. AIPAC-linked direct PAC contributions and United Democracy Project spending.

## Confirmed findings

- The World Economic Forum lists Palantir Technologies as a partner for its Annual Meeting 2026.
- WEF identifies Alex Karp as Palantir's CEO and co-founder and published a January 20, 2026 Annual Meeting session featuring him.
- The Palantir employee PAC reported $84,000 in contributions to other committees through June 30, 2026.
- Palantir's 2025 year-end LD-203 report disclosed six Republican-linked FECA contributions totaling $20,000:
  - $1,500 — Building A National Knowledgeable Security PAC — Sen. Jim Banks
  - $2,500 — Mullin for America — Sen. Markwayne Mullin
  - $2,500 — Rob Wittman for Congress — Rep. Rob Wittman
  - $3,500 — Heartland Values PAC — Sen. John Thune
  - $5,000 — Cole for Congress — Rep. Tom Cole
  - $5,000 — Ken Calvert for Congress Committee — Rep. Ken Calvert
- AIPAC PAC reported $43,960,130.82 in contributions to other committees through June 30, 2026.
- AIPAC describes United Democracy Project as its backed super PAC. UDP reported $27,928,913.21 in independent expenditures and $9,331,200 in contributions to other committees through June 30, 2026.
- A FEC-derived secondary aggregation reports $924,879 in AIPAC PAC direct contributions to Republican federal candidates during the 2026 cycle. This remains queued for exact itemized FEC reconciliation.

## Classification rules

- WEF partnership and event participation are not treated as proof of policy control, ideological alignment, or membership beyond the documented link.
- Direct PAC contributions and independent expenditures are separate legal and graph edge types.
- Independent expenditures are not direct donations to candidates.
- Contribution and expenditure records establish financial support or spending, not quid pro quo or policy causation.
- Secondary aggregate totals remain leads until reconciled against official itemized records.

## Queued depth-3 recursion

- Full Palantir PAC Schedule B recipient graph.
- Exact AIPAC PAC Republican recipient, date, amount, amendment, and refund reconciliation.
- UDP Schedule E candidate support/opposition and vendor graph.
- Historical WEF–Palantir partner, personnel, and event expansion.

## Output

- 27 normalized StarIntel v0.9.0 records.
- Dataset: `gop`
- Run: `gop-wef-palantir-aipac-2026-07-31-depth-2`
