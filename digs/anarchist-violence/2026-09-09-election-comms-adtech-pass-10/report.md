# Bounded Auto-Dig — 2026 election communications / political ad-tech pass 10

## Scope

Bounded breadth-first public-web enumeration for the `anarchist-violence` investigation corpus, focused on a new political communications, campaign-advertising, media-buying and professional-services cluster in the 2026 U.S. election ecosystem.

## Coverage

`starintel-documents.jsonl` contains **31 typed StarIntel v0.9 records**:

- 10 `source`
- 6 `org`
- 5 `person`
- 7 explicit `relation`
- 3 `investigation-target`

No inferred relation was promoted to direct observation.

### New organizations

1. DSPolitical — first-party material describes Democratic/progressive programmatic advertising, voter-file targeting and Deploy.
2. Targeted Victory — current first-party site describes political/public-affairs communications and membership in Stagwell Global.
3. Bully Pulpit International — strategic communications/public-affairs agency with documented political-campaign roots.
4. Majority Strategies — current first-party site self-describes as a Republican political advertising firm.
5. IMGE — digital political/advocacy agency; current site says it is a GP3 Company and exposes fundraising, advertising, email/SMS, influencer, AI and media-buying surfaces.
6. GP3 Partners — professional-services network exposing a large recursive firm graph spanning digital, canvassing, research, public affairs and communications.

### Public people

- Mark Jablonowski — CEO, DSPolitical.
- Zac Moffatt — Founder, Targeted Victory.
- Andrew Bleeker — CEO & Founder, Bully Pulpit International.
- Ben Coffey Clark — Founding Partner / co-founder, Bully Pulpit International.
- Ethan Eilon — current leader of IMGE per GP3's firm profile.

### Explicit relations

- Mark Jablonowski `executive_of` DSPolitical.
- Zac Moffatt `founded` Targeted Victory.
- Andrew Bleeker `founded` Bully Pulpit International.
- Ben Coffey Clark `co_founded` Bully Pulpit International.
- Ethan Eilon `executive_of` IMGE.
- IMGE `member_of` GP3 Partners.
- Targeted Victory `member_of` unresolved Stagwell Global endpoint; left unresolved pending canonical dedupe rather than manufacturing a duplicate org.

## Communications / distribution surfaces

The pass preserved organization websites plus the following publicly documented election-communications capabilities and surfaces: programmatic advertising, connected TV, online video, streaming/digital audio, display, voter-file targeting, data onboarding/licensing, digital fundraising, email, SMS/P2P, social media, influencer marketing, direct mail, mobile advertising, public affairs, campaign strategy, media buying and web development.

## Dedupe / uncertainty

- Repository code search returned no current indexed canonical record matches for the six organization names as a group before materialization.
- Stagwell Global was observed as a first-party Targeted Victory membership edge but is represented as an unresolved relation endpoint in this packet pending a dedicated canonical identity check.
- Political-sector descriptions are preserved only where the organization itself or its current first-party material states them; no individual political belief is inferred from employment or professional history.

## Recursive frontier

1. Democratic/progressive political ad-tech: DSPolitical data/onboarding partners, campaign/client evidence, CTV/programmatic inventory, public advertiser surfaces, and BPI public campaign/advocacy/media relationships.
2. Republican/conservative political ad-tech: Majority Strategies campaign/public-organization client graph, Targeted Victory political/public-affairs and Stagwell network, and IMGE campaign/IE/advocacy client and vendor graph.
3. GP3 network: enumerate 50 State, 76 Group, Ascent Media, Blitz Canvassing, Bullpen Strategy Group, FLS Connect, GP3 Tech, GuidePost Strategies, P2 Public Affairs, Public Opinion Strategies, Red Maverick Media, Strategic Partners & Media and UpONE Insights before following evidence-backed client/vendor/collaboration edges.

## Write path

Canonical packet fallback used: mature findings are materialized in `digs/anarchist-violence/2026-09-09-election-comms-adtech-pass-10/starintel-documents.jsonl`. No generated normalized `db/` records were hand-edited. Exact-head CI is the validator for this connector-created bounded pass.
