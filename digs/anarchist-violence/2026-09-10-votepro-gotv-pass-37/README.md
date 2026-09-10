# Auto-Dig election communications pass 37 — VotePro

Bounded public-source enumeration pass for the `anarchist-violence` investigation corpus.

## Fresh graph surface

This pass opens the RNC-funded VotePro GOTV technology cluster as a distinct election-communications surface. Current public VotePro materials describe campaign-branded GOTV pages, voter-action forms, automated email/SMS reminders, social-share prompts, custom domains, a WordPress-based CMS, and UTM/GTM/Google Analytics tracking. Public pages identify the Republican National Committee as the payer for VotePro.

## Materialized records

- 5 source records
- 3 product/communications records
- 1 public professional person record
- 6 explicit relation records
- 1 recursive investigation target
- 16 total canonical packet records

## Explicit graph edges

- Republican National Committee → operates/pays for → VotePro
- VotePro → includes → VotePro Activation Toolkit
- VotePro → provides → automated email/SMS reminders
- Brent Brooks → reported role at → Republican National Committee
- Brent Brooks → reported development role → VotePro
- Public Rob Bresnahan campaign-branded GOTV page → uses → VotePro
- VotePro voter-action/form capture → feeds opt-in follow-up → email/SMS reminders

The Brooks development edge is deliberately represented as reported evidence, not promoted to a first-party observation.

## Information-flow observation

Current VotePro documentation supports the public-facing path:

`campaign-branded GOTV page -> voter action/form -> contact/action + UTM tracking -> opt-in email/SMS follow-up`

VotePro also documents social-share prompts for X, Facebook and LinkedIn. This pass records the feature in source evidence but does not fabricate account-level amplification edges without observed public posts.

## Dedupe / identity handling

The existing canonical Republican National Committee ID is reused as `starintel:org:republican-national-committee`. The campaign deployment at `vote.robforpa.com` is represented as an unresolved external organization endpoint in the relation rather than inventing a duplicate canonical campaign entity without a separate identity-resolution pass.

## Next breadth-first frontier

The recursive target asks the next worker to enumerate additional publicly observable 2026 VotePro deployments; party, campaign and PAC users; public operators and staff; integrations and analytics infrastructure; branded domains/microsites; public training/documentation surfaces; and observable web-to-form-to-email/SMS/social distribution paths.

Private voter/supporter records, credentials, nonpublic campaign strategy and private delivery logs are out of scope.

## Sources

- https://votepro.gop/
- https://votepro.gop/features/
- https://votepro.gop/introducing-vote-pro/
- https://vote.robforpa.com/
- https://www.foxnews.com/politics/rnc-brings-new-senior-leadership-work-around-clock-support-trump-agenda-elect-republicans
