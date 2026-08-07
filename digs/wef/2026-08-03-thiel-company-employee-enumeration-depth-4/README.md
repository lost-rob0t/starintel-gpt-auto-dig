# Thiel-company employee → WEF enumeration — depth 4

**Dataset:** `wef`  
**Run:** `wef-thiel-company-employee-enumeration-2026-08-03-depth-4`  
**Standing rule:** every Thiel-network pass begins with company enumeration, continues through all publicly identifiable personnel levels, and tests each identity against exact WEF relationship types.

## Scope completed

This pass expands direct Thiel-linked company personnel through three distinct surfaces:

1. official Valar and Mithril biographies;
2. the Palantir employee PAC's official FEC record;
3. inventors named on a Palantir-assigned patent.

Role types remain separate. A patent inventor is not labeled an employee without independent corroboration.

## Historical Valar → Thiel organization bridges

Valar's official biographies add historical relations missing from the existing current-roster graph:

- **James Fitzgerald** previously served as COO and General Counsel of Thiel Capital and helped manage Peter Thiel's network, including Founders Fund and Clarium.
- **Erin Porterfield** worked at Thiel Capital as Fitzgerald's executive assistant from 2011 through 2013 before becoming Valar's first employee.
- **Andrew McCormack** helped launch Clarium and rejoined Thiel Capital in 2008 to lead international initiatives for the firm and Peter Thiel personally.

These are stored as historical employment, launch and management relations rather than broad affiliation edges.

## Mithril and Clarium

Mithril's official biography identifies **Ajay Royan** as founder and managing general partner. Mithril states that Royan founded the firm with Peter Thiel in 2012. Royan previously worked as a macro and growth-equity investor at Clarium.

## Palantir employee PAC

The FEC's current public summary for committee `C00498691`, covering posted activity from January 1, 2025 through June 30, 2026, reports:

| Observation | Amount |
|---|---:|
| Total receipts | $82,414.41 |
| Total disbursements | $95,283.32 |
| Ending cash | $56,444.16 |

These totals are materialized as separate financial observations. Contributor-level normalization remains queued.

## Palantir employee → nonprofit and command structure

A June 2025 John F. Kennedy Library Foundation release identifies **Mehdi Alhassani** as Palantir's Head of Government Affairs and Public Policy, says he reports directly to Alex Karp, and records his unanimous election to the Foundation's board. Depth 4 therefore adds both the internal `reports_to` edge and the external nonprofit-board edge.

## Palantir technical-personnel surface

Patent `US11870666B2`, assigned to Palantir Technologies, names nine inventors:

- Cody Moore
- Yiwei Gao
- Andrew Colombi
- David Karesh
- William Ward
- Alexander Ince-Cushman
- Mohammad Bukhari
- Daniel Kozlowski
- Jason Richardson

Each inventor receives a person node and a typed `named_as_inventor_on` relation to the patent asset. The relation explicitly disables employment inference.

A corporate-primary Tonic biography independently corroborates **Andrew Colombi** as an early Palantir employee who led the commercial-sector engineering launch and began the Foundry product. The other eight inventor identities remain employment candidates pending corroboration.

## WEF cross-match boundary

The bounded official-WEF exact-name sweep did not establish an identity match for Ajay Royan, the three Valar bridge personnel, or the nine patent inventors. A same-name WEF result for a Syracuse professor named William Ward was rejected as a different identity.

Search misses are coverage gaps, not proof of no WEF relationship.

## Depth 5 queued

1. Corroborate patent inventors against employment, conference, author and procurement records.
2. Normalize the complete FEC itemized receipt and disbursement exports for `C00498691`.
3. Build all-level historical rosters for Thiel Capital, Mithril and Clarium.
4. Trace confirmed personnel into government, NGOs, boards, portfolio companies, policy and procurement.
5. Run exact and fuzzy identity resolution against WEF profiles, meetings, Young Global Leaders, councils, reports and Global Shapers.
6. Acquire, screenshot and hash unresolved WEF participant PDFs if their host becomes accessible.

## Validation

- 39 StarIntel v0.9 records
- 39 unique IDs
- required common fields present
- relation and investigation-target required fields present
- HTTPS-only source URLs
- content SHA-256: `f60558ac092ee2b32f668df42428b1e4747d920eeae56fc87248bde80e5b2153`
