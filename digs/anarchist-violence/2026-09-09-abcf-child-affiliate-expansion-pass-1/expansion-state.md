# Chapter/affiliate expansion state — ABCF child links pass 1

Timestamp: 2026-09-09T11:35:37Z
Base main: `c5d4bb8f9b3e67e09ebebfc3ed68d58b2ce8b229`

## Scope completed

This bounded pass reused already-canonical ABCF/ABC organization nodes and expanded unresolved public organization/account edges rather than re-enumerating the completed ABCF chapter directory.

Resolved:
- Los Angeles ABCF: current 2026 first-party ABCF publication lists Instagram `@laabcf`, X `@la_abcf`, Facebook `/labcf`.
- Chicago Anarchist Black Cross: current 2026 ABCF Running Down the Walls page directly links Instagram `@chicagoabc`.
- Philly ABC: current first-party About page explicitly states membership in Solidarity International Network and links Instagram `@philly_abc` and Mastodon `@phillyabc@kolektiva.social`.
- Solidarity International Network: created as a separate canonical organization and recursive investigation target; its current first-party member page independently lists Philly ABC.

## Canonical reuse / dedupe

Reused without creating duplicate organization records:
- `starintel:org:los-angeles-abcf`
- `starintel:org:chicago-anarchist-black-cross`
- `starintel:org:philly-anarchist-black-cross`
- the existing Anarchist Black Cross Federation chapter structure

The existing ABCF directory slice remains authoritative for current ABCF collectives. Independent ABC groups remain distinct and are not collapsed into ABCF merely because names are similar.

## Evidence boundary

Only public organization structure and organization-controlled/publicly linked account surfaces are materialized. No private membership is inferred. No person-level political/ideological affiliation profile is created from organizational proximity.

## Stats

- seed organizations processed: 4 (ABCF structure, Los Angeles ABCF, Chicago ABC, Philly ABC)
- new locals/chapters: 0
- new parent/network organizations: 1
- new organization-to-organization relations: 1 explicit / 0 inferred
- new people: 0
- explicit vs inferred person-org relations: 0 / 0
- person-identity collisions: 0
- new public social endpoints: 6
- new public communications/account surfaces: 6
- source records: 4
- source domains: 4 (`abcf.net`, `phillyabc.org`, `solidarity.international`, `instagram.com` destination evidenced through first-party link)
- current-status findings: 4 seed/network structures current or current-first-party corroborated
- historical-only findings promoted: 0
- duplicate/canonical collisions avoided: 3 organization nodes reused plus completed ABCF chapter directory reused

## Unresolved structural/account leads

- Bakersfield and Lancaster ABCF still need strong current first-party public social endpoint discovery.
- Chicago ABC publicly advertises additional platforms; exact current Bluesky/Mastodon destinations should be resolved before materialization rather than guessed.
- Philly ABC Bluesky is publicly linked but was left for the next child-account slice to keep this pass bounded.
- Solidarity International exposes additional public member organizations; recurse from its investigation target in a later independent pass, with current-status checks and canonical dedupe.
