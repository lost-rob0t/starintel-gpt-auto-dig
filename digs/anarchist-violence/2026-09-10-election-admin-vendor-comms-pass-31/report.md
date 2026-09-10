# Auto-Dig 2026 election administration vendor / communications pass 31

Bounded public-web enumeration pass for the `anarchist-violence` investigation corpus, focused on unsaturated election-administration vendors, professional-association ties, public communication surfaces, public leadership, and current 2026 government procurement/deployment edges.

## Coverage

- 10 source records
- 9 organization records
- 4 public professional person records
- 1 public URL / communications-surface record
- 17 explicit relation records
- 1 recursive investigation target
- 42 total canonical StarIntel v0.9 records

## New graph surface

This pass expands the still-open NASED corporate-affiliate frontier from the prior election-administration coordination pass. It materializes current affiliate relationships for Civix, Democracy Live, ElectSure Learning, Election Security Exchange, Ready for Tuesday, ReFrame Solutions, and The Elections Group. Corporate-affiliate membership is recorded only as membership; it does not imply endorsement by NASED.

The pass follows those nodes outward into public operational and communications relationships. Election Security Exchange is represented as a project of The Election Resource Center. ElectSure Learning is linked to founder/principal Bill Murphy. Ready for Tuesday is linked to president Noah Praetz and to its public VoterCast outreach surface, which provides jurisdiction-tailored content for social media, print, email, and SMS. The Elections Group is linked to CEO/co-founder Jennifer Morrell.

North Carolina provides two current 2026 procurement edges: the North Carolina State Board of Elections selected ReFrame Solutions for a $4.66 million modernization of the State Elections Information Management System in February 2026 and separately selected ReFrame for a $2.2 million campaign-finance reporting system replacement in August 2026. These are represented as separate evidence-backed relations rather than collapsed into a generic vendor/customer assertion.

## Dedupe / identity handling

Existing canonical `starintel:org:nased` is reused. The new organizations were checked against default-branch repository search before creation. Names and role overlaps are not used to merge people across unrelated records. Public person records contain only published professional identities and roles.

## Recursive frontier

Continue breadth-first through the remaining current NASED corporate-affiliate roster and connected election-administration ecosystem: products and public APIs, public deployments and procurements, state/local customers, leadership and official accounts, conference appearances, training and communications surfaces, voter-information and AI-facing website tooling, security partners, data flows, and cross-vendor relationships. Prioritize 2026 evidence and still-unmapped organizations over saturated nodes.

## Write / validation path

Canonical packet: `digs/anarchist-violence/2026-09-10-election-admin-vendor-comms-pass-31/starintel-documents.jsonl`.

This bounded pass used the GitHub connector fallback from current canonical `main`. Exact-head GitHub CI is the validator. The PR must remain draft and unmerged until all required exact-head checks are conclusively successful.
