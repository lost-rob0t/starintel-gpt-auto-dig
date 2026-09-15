# Auto-Dig election communications pass 23

## Scope

Bounded breadth-first public-source enumeration pass for the `anarchist-violence` investigation corpus, focused on unsaturated campaign fundraising/compliance infrastructure rather than revisiting already-covered ActBlue/WinRed clusters.

## New graph surface

This pass opens the Anedot-centered donation, CRM, compliance, messaging, and automation layer. Current first-party Anedot documentation describes an end-to-end political donation platform/payment processor and a broad integration directory spanning campaign-compliance systems, CRMs, messaging vendors, and automation services.

Materialized new nodes include Anedot, NetFile, Trail Blazer, Partyline, FrontRunner, Campaign Nucleus, and public founder/CEO Paul Dietzel. The pass reuses the current canonical Aristotle and ISPolitical organization IDs already present on `main` rather than creating same-version duplicate records. Mature relations capture documented integration/data-relay edges from Anedot into NetFile, ISPolitical, Aristotle, Trail Blazer, Partyline, FrontRunner, Campaign Nucleus, and the already-known RumbleUp node.

The RumbleUp relation preserves a material limitation from the source: Anedot documents text-to-donate promotion of Action Pages but explicitly states that this integration does not relay data from Anedot back to RumbleUp.

## Coverage

- Candidate nodes checked: 18+
- Already-covered/saturated or canonical nodes intentionally skipped/reused: ActBlue, WinRed, RumbleUp, Aristotle, ISPolitical
- New source records: 9
- New organization records: 6
- Reused canonical organization records: 2
- New public people: 1
- New explicit relations: 9
- New inferred relations: 0
- Identity collisions force-merged: 0
- New recursive targets: 1
- Source domains: anedot.com / help.anedot.com
- Primary infrastructure class: fundraising/payment -> CRM/compliance -> messaging/automation

## Provenance / uncertainty

All materialized edges in this pass are explicit first-party Anedot claims. Third-party platform descriptions are attributed to Anedot rather than silently treated as independent self-descriptions. No campaign/client relationship was inferred merely from compatibility or integration availability. Aristotle and ISPolitical retain their newer independently sourced canonical records already on `main`; this packet adds only Anedot-specific sources and relations involving those IDs.

## Recursive frontier

Next breadth-first work should enumerate current 2026 campaign/committee users of these systems, vendor leadership/ownership, additional Anedot integrations, public campaign forms, compliance reporting pathways, Tandem Pages/joint fundraising surfaces, event fundraising, text-to-donate paths, and API/webhook transport relationships.
