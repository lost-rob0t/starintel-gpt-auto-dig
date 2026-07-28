# AIPAC and U.S.–Israeli Territorial-Enabling Network

**Run:** `2026-07-26`  
**Dataset:** `greater-israel-aipac-enablement-2026-07-26`  
**Packet:** `86` StarIntel v0.9.0 documents  
**Transport:** `starintel-documents.jsonl.gz.b64` (base64-encoded deterministic gzip)  
**SHA-256:** `95f16b1a8faa5881101d2faa4d658cba1165d0c3f62505eedcc3edd4c260d52b`  
**Scope:** Public organizational, campaign-finance, lobbying, sanctions, budget, and administrative records. No private personal data.

## Assessment

The reviewed public record supports classifying **AIPAC as a primary U.S. political-enablement target**. AIPAC combines board-level policy direction, professional lobbying, direct candidate contributions through AIPAC PAC, independent electoral spending through United Democracy Project, and political education/travel through the affiliated American Israel Education Foundation.

The record does **not** establish that AIPAC commands the Israeli Civil Administration, settlement budgets, land surveys, or Israeli settlement organizations. Direct territorial implementation remains located inside Israeli government bodies and organizations such as the Civil Administration Supervision Unit, Amana, Nachala, Regavim, and Hashomer Yosh.

**Analytic confidence:** `0.93`

## New findings in this pass

### AIPAC Q2 2026 lobbying

AIPAC's [Q2 2026 LD-2 filing](https://lda.senate.gov/filings/public/filing/af43001f-9acf-4ea4-a5c2-4caf2b85814a/print/) reported **$810,990** in lobbying expenses. Combined with the [Q1 filing](https://lda.senate.gov/filings/public/filing/ad4e8e54-def8-4563-97c5-0ac5a0ca16a3/print/), this produces **$1,655,400** in disclosed lobbying expenses for the first half of 2026.

The Q2 filing continued work concerning:

- H.R.3045/S.2667, the West Bank Violence Prevention Act;
- H.R.3565, a limitation on defense articles and services to Israel;
- S.J.Res.32 and S.J.Res.138, arms-sale disapproval measures;
- FY2027 defense and foreign-operations appropriations;
- the FY2027 NDAA and U.S.–Israel defense and research programs.

The Q2 roster added **Adam Safran** to the eight lobbyists disclosed in Q1:

- Marvin Feuer
- David Gillette
- Deborah Saxon
- Alex Bronzo
- Oren Adaki
- Zachary Moses
- Daniel Grey
- Celia Glassman
- Adam Safran

The filing identifies contacts with the House, Senate, National Security Council, State, Treasury, Energy, Defense, Homeland Security, and Commerce.

### Electoral architecture

The network has distinct legal and operational components:

| Component | Documented function |
|---|---|
| AIPAC | Policy, lobbying, member mobilization, and organizational direction |
| AIPAC PAC | Direct contributions to candidate committees |
| United Democracy Project | Independent electoral expenditures |
| AIEF | Educational seminars, Israel travel, and access for political influentials |

The [FEC committee pages](https://www.fec.gov/data/committee/C00797670/) identify AIPAC as AIPAC PAC's connected organization. AIPAC's own [political page](https://www.aipac.org/politics) calls UDP AIPAC-backed.

The packet records the following 2025–June 2026 figures from FEC summaries:

| Committee | Measure | Amount |
|---|---|---:|
| AIPAC PAC | Total receipts | $47,521,820.85 |
| AIPAC PAC | Contributions to other committees | $43,960,130.82 |
| UDP | Total receipts | $103,988,109.27 |
| UDP | Independent expenditures | $27,928,913.21 |
| UDP | Ending cash | $80,255,176.92 |

These figures establish capacity and activity. They do not prove control of every supported candidate.

### Annexation-consequence shielding

Contemporaneous reporting recorded AIPAC arguing that weakening U.S.–Israel ties because of West Bank annexation would be a mistake. AIPAC reportedly allowed lawmakers latitude to criticize annexation so long as criticism did not threaten aid or the fundamentals of the bilateral relationship.

The supported relation is:

```text
AIPAC --politically_insulated--> U.S.–Israel aid and bilateral support
```

The unsupported relation is:

```text
AIPAC --commands--> Israeli territorial administration
```

### U.S. sanctions consequences

The [U.S. Treasury's January 24, 2025 action](https://ofac.treasury.gov/recent-actions/20250124) terminated the West Bank sanctions program after revocation of Executive Order 14115. OFAC removed designations including **Amana** and **Binyanei Bar Amana Ltd**.

This materially reduced U.S. consequences for those entities. This packet does **not** attribute the executive decision to AIPAC because no reviewed source establishes that causal link.

### Israeli implementation stack

The official [Civil Administration Supervision Unit page](https://www.gov.il/en/departments/Units/supervision_unit) assigns the unit responsibilities including:

- construction enforcement;
- preservation of state lands;
- state-directed land surveys;
- enforcement involving mining, water, electricity, telecommunications, roads, and environmental rules.

The page identifies **Marco Ben-Shabbat** as unit head. This creates a direct personnel-to-administrative-function node.

Separately, [Reuters reported on July 14, 2026](https://www.reuters.com/world/middle-east/israel-allocates-434-million-34-new-west-bank-settlements-2026-07-14/) that Israel's security cabinet approved:

- **1.3 billion shekels** for 34 new settlements;
- **1.075 billion shekels** for supporting infrastructure and roads.

Reuters reported that Bezalel Smotrich announced the plan, Benjamin Netanyahu supported it, and Smotrich framed it as obstructing a Palestinian state.

### Settlement organizations

The [Council of the European Union's May 28, 2026 decision](https://www.consilium.europa.eu/en/press/press-releases/2026/05/28/extremist-israeli-settlers-eu-lists-four-entities-and-three-individuals/) listed:

- Nachala and director Daniella Weiss;
- Regavim and director Meir Deutsch;
- Hashomer Yosh and president Avichai Suissa;
- Amana.

Those are EU sanctions determinations, not criminal convictions. The packet preserves that attribution.

## Evidence boundary

### Supported

- AIPAC is a major disclosed lobbying and electoral organization.
- AIPAC PAC and UDP provide separate direct-contribution and independent-spending mechanisms.
- AIEF is affiliated with AIPAC and funds political education and Israel travel.
- AIPAC lobbied on West Bank and Israel arms-related measures in Q1 and Q2 2026.
- AIPAC sought to prevent annexation disputes from damaging aid and bilateral ties.
- Israeli state units perform land-survey and enforcement work.
- U.S. and EU sanctions decisions materially altered consequences for named settlement organizations.
- Israel approved major settlement and infrastructure funding in July 2026.

### Not established

- AIPAC directly commands Israeli annexation or settlement administration.
- AIPAC caused the January 2025 sanctions termination.
- AIPAC directly lobbied for H.R. 902; it was not found in the inspected Q1 or Q2 2026 filings.
- Campaign contributions alone prove control of recipients.
- Travel alone proves that later votes were caused by the trip.

## Highest-value recursive targets

1. **AIEF traveler-to-policy crosswalk**  
   Resolve every funded traveler, itinerary, Israeli briefer, and subsequent vote, letter, bill, and sanctions position.

2. **UDP donor reconciliation**  
   Normalize original and amended filings, refunds, intermediaries, and name variants.

3. **AIPAC West Bank lobbying map**  
   Code all 2025–2026 LD-2 filings by bill, executive agency, lobbyist, and policy outcome.

4. **Settlement-budget recipient graph**  
   Resolve ministries, councils, tenders, construction firms, road projects, and disbursement records receiving the July 2026 allocation.

5. **Area C land-survey chain**  
   Map orders, staff, survey contractors, evidence standards, declarations, objections, and downstream allocation.

6. **Settlements Administration personnel graph**  
   Resolve delegated authorities, legal staff, prior organizational affiliations, and decision signatures.

## Record counts

```json
{
  "analysis": 1,
  "claim": 4,
  "event": 3,
  "financial-observation": 8,
  "lobbying-filing": 2,
  "org": 12,
  "person": 23,
  "relation": 25,
  "research-pass": 1,
  "target": 7
}
```

## Source index

- [AIPAC mission and organization](https://www.aipac.org/)
- [AIPAC political operation](https://www.aipac.org/politics)
- [AIPAC leadership](https://www.aipac.org/board)
- [AIPAC IRS-derived filings](https://projects.propublica.org/nonprofits/organizations/530217164)
- [AIEF mission](https://www.aiefdn.org/)
- [AIEF IRS-derived filings](https://projects.propublica.org/nonprofits/organizations/521623781)
- [AIPAC PAC — FEC](https://www.fec.gov/data/committee/C00797670/)
- [United Democracy Project — FEC](https://www.fec.gov/data/committee/C00799031/)
- [AIPAC Q1 2026 lobbying disclosure](https://lda.senate.gov/filings/public/filing/ad4e8e54-def8-4563-97c5-0ac5a0ca16a3/print/)
- [AIPAC Q2 2026 lobbying disclosure](https://lda.senate.gov/filings/public/filing/af43001f-9acf-4ea4-a5c2-4caf2b85814a/print/)
- [OFAC West Bank sanctions termination](https://ofac.treasury.gov/recent-actions/20250124)
- [EU settlement-organization designations](https://www.consilium.europa.eu/en/press/press-releases/2026/05/28/extremist-israeli-settlers-eu-lists-four-entities-and-three-individuals/)
- [Civil Administration Supervision Unit](https://www.gov.il/en/departments/Units/supervision_unit)
- [Reuters settlement allocation report](https://www.reuters.com/world/middle-east/israel-allocates-434-million-34-new-west-bank-settlements-2026-07-14/)

## Validation

- Base64 decoded successfully.
- Deterministic gzip decompressed successfully.
- `86` JSONL records parsed successfully.
- Required v0.9.0 common fields checked.
- dtype-specific field allowlists checked.
- Relation endpoints checked against packet IDs.
- Duplicate IDs checked.
- SHA-256 calculated over the exact JSONL bytes.

The connector publication uses compressed transport because the current environment cannot push a 117 KB plain-text blob through a local checkout. The decoded JSONL hash above is authoritative. The full repository merge gate was not run because this environment lacks a local authenticated GitHub checkout and cannot resolve `github.com`. Keep the pull request in draft until `python3 scripts/validate-for-merge.py --site` and all required GitHub checks pass.
