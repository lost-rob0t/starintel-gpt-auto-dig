# Election communications / ecosystem enumeration — pass 40

## Scope

Bounded breadth-first public-web expansion of the Scale to Win political communications ecosystem. This pass focuses on public product surfaces, campaign/organization communication infrastructure, public client relationships, messaging compliance, data/integration paths, and one concrete public deployment surface. It does not collect private voter/supporter records, contact lists, credentials, private message contents, delivery logs, or nonpublic campaign strategy.

## Coverage

- 30 canonical StarIntel v0.9 packet records.
- 7 source records.
- 4 products/services.
- 3 public URL/communications surfaces.
- 15 explicit relations.
- 1 recursive investigation target.
- No person record was created in this pass because the current first-party materials reviewed describe the founding team collectively rather than naming individual founders; the recursive target explicitly retains public professional leadership/founder resolution as follow-up work.

## Findings

Scale to Win's current public materials describe an election-communications stack spanning Scale to Win Text, Scale to Win Dialer, Scale to Win Spoke, and managed `We Text` services. The current careers page states that the company works with 4,000+ Democratic and progressive campaigns and organizations and names current or past clients including the Democratic National Committee, Working Families Party, AFL-CIO, UFCW, MoveOn, and For Our Future. Because that source does not disambiguate which relationships are current versus historical, the packet preserves `current_or_past` rather than promoting all of them to current-client claims.

The texting layer supports SMS/MMS over 10DLC, toll-free and short-code channels. Scale to Win's current 10DLC documentation states that political organizations use Campaign Verify for identity vetting and The Campaign Registry for 10DLC registration; these external endpoints are represented as unresolved relation endpoints here rather than creating duplicate canonical organizations before corpus-wide identity resolution.

The Dialer adds browser-based calling, voicemail, VAN/Votebuilder synchronization, optional text-message follow-up, and polling-place lookup. Current support documentation also describes a Google BigQuery export that synchronizes new and updated Dialer data to an organization's BigQuery project every 15 minutes.

A concrete public deployment surface is DSA Org Tools' Scale to Win Text page. It documents chapter/member texting, shared reply handling, segmentation, and opt-out synchronization with ActionKit and Action Network. Those edges are represented as deployment-specific observations rather than generalized claims that every Scale to Win account has those integrations.

## Information-flow relevance

Observed public pathways include:

- organization/campaign list -> Scale to Win Text -> SMS/MMS/10DLC/toll-free/shortcode outreach;
- VAN/Votebuilder list -> Scale to Win Dialer -> volunteer/staff calling -> conversation results synchronized back to VAN;
- Dialer campaign data -> BigQuery export -> organization analytics environment;
- political texting organization -> Campaign Verify identity vetting -> The Campaign Registry 10DLC registration -> carrier messaging path;
- DSA chapter/member lists -> Scale to Win Text -> shared reply inbox / segmentation -> opt-out synchronization with ActionKit and Action Network.

## Dedupe / identity handling

Current-main repository search found an existing `starintel:org:scale-to-win` record in the DNC corpus, so this pass does not create a duplicate organization node. Fresh product IDs were checked before materialization and no current-main match was found for `starintel:product:scale-to-win-text`. Named clients and external infrastructure are left as explicit unresolved endpoints where corpus-wide identity resolution was not completed during this bounded pass.

## Recursive frontier

Next useful pivots are additional public 2026 Scale to Win deployments; public client confirmations from campaign, party, union, nonprofit and PAC sites; ActBlue/NGP VAN integration details; texting and dialer trainings; public FEC/vendor disclosures; campaign-specific Caller URLs and opt-in surfaces; additional data-export/integration infrastructure; and strongly corroborated public professional leadership/founder identities.
