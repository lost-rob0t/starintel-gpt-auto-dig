# Auto-Dig 2026 election political-ad transparency pass 26

Bounded public-source election-ecosystem enumeration pass for the `anarchist-violence` corpus.

## Scope

This pass opens a fresh political-ad delivery and transparency-infrastructure cluster rather than overlapping the still-open fundraising, voter-data, GP3, political-texting, or election-mail passes. It focuses on public platform policies, ad/transparency libraries, disclosure paths, federal disclaimer rules, and public company leadership directly connected to advertising platforms.

## Materialized graph surface

- Federal Election Commission public-communication and internet-ad disclaimer guidance.
- Meta Platforms, Facebook, Instagram, and Meta Ad Library transparency pathways.
- Snap Inc., Snapchat, Snap Political Ads Library, and current political-ad policy/disclosure behavior.
- Reddit and the historically documented `r/RedditPoliticalAds` transparency surface, preserving the dated 2024 policy status rather than silently treating it as unchanged 2026 policy.
- TikTok's documented prohibition on paid political advertising, retained as a policy observation rather than a platform-to-campaign relation.
- Public company leadership nodes for Mark Zuckerberg, Evan Spiegel, Ronan Harris, and Steve Huffman.

## Evidence handling

First-party/current sources are preferred. Dated policy material is explicitly preserved as historical where current 2026 policy was not independently verified. No private advertiser dashboards, private audience data, individual voter targeting records, or inferred political preferences are collected. Relationships are limited to source-backed operational, transparency-surface, or public leadership edges.

## Coverage

Packet contains 41 typed StarIntel v0.9 records:

- 12 `source`
- 11 `org`
- 4 `person`
- 13 `relation`
- 1 recursive `investigation-target`

All records are materialized in `starintel-documents.jsonl`; normalized `db/` is not hand-edited.

## Recursive frontier

Next breadth-first expansion should enumerate current 2026 political advertisers and payors from public ad libraries; campaign/committee/vendor relationships; additional platform political-ad policies and archives; publicly disclosed spend, placement and targeting metadata; ad creative reuse/syndication; agency and media-buying relationships; verification vendors; FEC disclosure joins; and public downstream amplification/distribution paths. Historical platform rules should be revalidated before being marked current.
