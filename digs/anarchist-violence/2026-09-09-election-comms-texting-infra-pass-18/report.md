# Election communications texting infrastructure — bounded pass 18

## Scope

Fresh breadth-first PUBLIC POLITICAL-DISCOURSE / COMMUNICATIONS + ELECTION-ECOSYSTEM pass for the `anarchist-violence` corpus, focused on mobile/texting infrastructure rather than revisiting the already-covered political ad-tech cluster.

## Materialized graph

- 18 typed StarIntel v0.9 packet records
- 7 public source records
- 8 organization records
- 3 explicit relations
- 0 inferred relations promoted as fact
- 0 normalized `db/` hand edits

### Organizations

- Scale to Win — current first-party site documents texting/dialer infrastructure, ActBlue and NGP VAN integrations, fundraising/organizing workflows, and Democratic/progressive organizing roots.
- RumbleUp — current first-party site documents P2P SMS/MMS/video texting for campaigns and organizations and states use by 3,500+ campaigns.
- Tatango — current first-party site documents high-volume fundraising SMS, political fundraising and PAC/SuperPAC use cases, integrations, and public social accounts.
- Hustle — current first-party site documents broadcast, video, P2P texting and dialer products plus political-campaign use.
- Mobile Commons — Upland first-party material documents political/advocacy SMS, fundraising, polling locators, legislator calls and agent conversations.
- Upland Software — historical first-party corporate material documents acquisition of Mobile Commons.
- Twilio — Upland first-party material documents a Mobile Commons/Twilio SaaS partnership for SMS and Facebook Messenger integration.
- NAACP — Hustle current first-party material documents organizational use of Hustle for voter communications and mobilization.

### Explicit relations

- Upland Software -> Mobile Commons: `owns_and_operates`
- Mobile Commons -> Twilio: `technology_partner`
- NAACP -> Hustle: `used_communications_platform`

## Coverage / unresolved frontier

This pass deliberately did not duplicate unmerged work already present in other draft PRs. High-value unresolved pivots include named founders/current executives for each messaging vendor, current public social-account records, Scale to Win's ActBlue and NGP VAN integration edges, RumbleUp's disclosed committee/customer infrastructure, Tatango integration partners, Hustle political customer relationships, and Mobile Commons' broader advocacy/customer graph. Those require a subsequent bounded pass with identity-resolution checks against current main.

Historical corporate sources are retained with explicit source dates rather than silently treated as current-state proof. Current-status claims use current first-party pages wherever available.
