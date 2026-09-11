# Auto-Dig election communications pass 38 — political data and audience activation

Bounded public-source enumeration pass for the `anarchist-violence` investigation corpus.

## Fresh graph surface

This pass opens a right-of-center political-data and audience-activation cluster centered on i360, Data Trust, and Deep Root Analytics. Current public materials describe voter/consumer data, predictive modeling, natural-language audience creation, peer-to-peer texting, field outreach, direct audience export to campaign Facebook Ad Accounts, voter-file enrichment, microtargeting, and paid/earned-media measurement.

## Materialized records

- 5 source records
- 3 organization records
- 5 product / communications records
- 4 public professional person records
- 9 explicit relation records
- 1 recursive investigation target
- 27 total canonical packet records

## Explicit graph edges

- i360 → provides → i360 GOTV Bundles
- i360 → provides → i360 Text
- i360 → provides → iKE
- iKE → builds audiences from → i360 political-data platform
- i360 GOTV Bundles → exports audiences to → campaign Facebook Ad Accounts (external unresolved surface)
- Data Trust → provides → Data Trust Voter File
- Deep Root Analytics → provides → Custom Microtargeting
- Deep Root Analytics → provides → Earned Media Measurement
- Public leadership/person records → public role at → Data Trust / Deep Root Analytics

## Information-flow observations

Current first-party i360 documentation supports the public-facing path:

`voter/consumer data + predictive models -> audience selection -> call/walk/text outreach and/or campaign Facebook Ad Account activation`

The iKE page adds a natural-language audience-construction step over i360 data. Deep Root separately documents a path from survey/voter/consumer data through modeled audiences into digital/addressable activation, while its earned-media product measures broadcast and cable mentions against campaign audiences.

## Dedupe / identity handling

This pass searched the current corpus first. It does not duplicate the previously materialized ActBlue, WinRed, TargetSmart, Catalist, NGP VAN, VotePro, NationBuilder, or other earlier election-communications clusters. Cross-source people are not merged from name similarity alone.

## Next breadth-first frontier

The recursive target asks the next worker to enumerate additional public political-data providers, modeling firms, campaign technology, audience-activation vendors, public integrations, public clients, training/event surfaces, public professional roles, and observable data-to-audience-to-text/call/walk/digital/media paths.

Private voter records, private supporter/donor lists, credentials, nonpublic audience exports, private campaign strategy, and private delivery logs are out of scope.

## Sources

- https://www.i-360.com/
- https://www.i-360.com/gotv-bundles/
- https://www.i-360.com/political-products/ai/
- https://thedatatrust.com/about/
- https://www.deeprootanalytics.com/
