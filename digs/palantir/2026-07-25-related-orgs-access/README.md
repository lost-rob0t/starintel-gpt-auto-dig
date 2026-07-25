# Palantir recursive loop: related organizations and access infrastructure

**Root dataset:** `palantir-deep-dive-2026-07-25`  
**Schema:** StarIntel `0.9.0`  
**Research cutoff:** July 25, 2026  
**Maximum recursion depth:** 3  
**Documents emitted:** 21

## Research question

How does the Palantir–Thiel–Vance graph extend through venture firms, electoral-finance organizations, donor networks, investment firms and private Washington access infrastructure?

## Depth report

| Depth | Organizations | Analytical role |
|---:|---|---|
| 0 | Palantir Technologies | Root vendor and federal platform network. |
| 1 | Peter Thiel network | Founder, governance, investment and political-capital bridge. |
| 2 | Mithril Capital, Narya Capital, Protect Ohio Values PAC, Rockbridge Network | Venture employment, venture backing, electoral finance and donor/institution-building layers. |
| 3 | 1789 Capital, private Executive Branch club, United States executive branch | Investment-network convergence, private access venue and explicit government/private entity disambiguation. |

## Main findings

### 1. The related organizations perform different functions

The graph is not one undifferentiated political organization:

- **Mithril Capital** is the Thiel-linked venture firm where JD Vance worked.
- **Narya Capital** is the Vance-co-founded venture fund whose early investors included Thiel.
- **Protect Ohio Values PAC** was the electoral-finance vehicle supporting Vance's 2022 Senate campaign.
- **Rockbridge Network** is a donor and institution-building network co-founded by Vance and Chris Buskirk.
- **1789 Capital** is an investment firm whose team includes Buskirk, Omeed Malik and Donald Trump Jr.
- **Executive Branch** is an invitation-only private club reportedly founded by Trump Jr., Malik, Buskirk and associates.

This produces a functional sequence:

`venture capital -> electoral finance -> donor network -> investment firm -> private access venue`

### 2. Rockbridge is the least transparent high-value organization

Rockbridge appears central to long-term institution building, but its legal entities, fiscal sponsors, donors, vendors, grantees and expenditures are incompletely visible in the current public record. The packet therefore creates a dedicated legal-and-funding-ledger target rather than asserting a complete organizational structure.

### 3. Buskirk is the bridge into 1789 Capital

1789 Capital identifies Chris Buskirk as founder and CIO and states that he co-founded Rockbridge with JD Vance. The same firm lists Omeed Malik as founder and president and Donald Trump Jr. as a partner. That places 1789 at the intersection of the Vance-linked institution-building network and the Trump family business network.

### 4. The private “Executive Branch” club is an access-infrastructure lead

Reporting identifies a high-fee, invitation-only private club in Georgetown associated with Trump Jr., Malik and Buskirk. Its analytical significance is the possibility of concentrated informal access among investors, executives and administration-linked figures.

The evidence does **not** currently establish that membership, attendance or fees purchased a policy decision, appointment or Palantir contract. Those questions require an event, membership, payment, calendar and procurement chronology.

### 5. Entity resolution is mandatory

The private club named **Executive Branch** is not the constitutional **executive branch of the United States government**. The packet creates separate organization records and an explicit `distinct_from` relation so graph traversal and natural-language search cannot silently merge them.

## Recursive targets selected

1. `starintel:investigation-target:rockbridge-legal-funding-ledger`
   - Resolve legal entities, fiscal sponsors, donors, grantees, vendors and expenditures.
2. `starintel:investigation-target:executive-branch-club-access-ledger`
   - Identify disclosed owners, members, fees, events, guests, officials, lobbyists and contacts while keeping attendance separate from causation.
3. `starintel:investigation-target:1789-portfolio-government-map`
   - Map portfolio companies to contracts, grants, regulation, executive action and government meetings.

## Evidence posture

Official corporate pages establish the Mithril and 1789 personnel relations. Federal Election Commission records establish Protect Ohio Values PAC's identity and filings. Major reporting establishes the private-club launch and reported principals. The Rockbridge structure remains only partially resolved and is preserved as an open investigation target.
