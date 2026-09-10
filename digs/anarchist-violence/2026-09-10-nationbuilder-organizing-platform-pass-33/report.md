# NationBuilder organizing / communications infrastructure pass 33

Bounded PUBLIC political-discourse / communications + election-ecosystem enumeration for the `anarchist-violence` corpus.

## Scope

Breadth-first expansion into a previously unsaturated public election-organizing software cluster centered on NationBuilder and its current 2026 integrations, products, data flows, fundraising, analytics, advocacy, calling/texting, candidate-recruitment tooling, and public professional leadership. Existing current-main code search was used for dedupe before materialization; adjacent Mobilize/Bonterra, voter-data, ad-tech, fundraising/compliance, texting-compliance, election-administration, and media-results clusters were skipped because recent passes already cover them.

## Coverage

- candidate/public nodes checked: 30+
- source records: 10
- organization records: 5
- product/public software-surface records: 7
- public professional person records: 4
- explicit relation records: 20
- inferred relations promoted to fact: 0
- recursive investigation targets: 1
- total StarIntel v0.9 packet records: 47
- identity collisions force-merged: 0
- principal source domains: `nationbuilder.com`, `support.nationbuilder.com`, `callhub.io`
- principal graph surfaces: organizing CRM; advocacy actions; voice/SMS outreach; fundraising/payment processing; donor intelligence; analytics; candidate/office discovery and recruitment

## Findings

NationBuilder's current company page identifies the company as infrastructure used by political parties, campaigns, charities, networks and other organizations, and lists its current leadership. This pass materializes the company separately from its software surfaces and records public professional roles for Lea Endres, Gina Davis and Jay Godfrey.

Current July 21, 2026 NationBuilder documentation shows that ActionButton can be embedded on NationBuilder sites, social media or elsewhere and can support petitions, polls, voter-registration checks, signups, legislator contact and custom email targets. When connected to a Nation, action-taker contact fields, opt-in preferences and action metadata can be synchronized into NationBuilder and used for tags, automations, point-person assignment and paths. The packet therefore separates the product-integration edge from the directional data-flow edge.

NationBuilder announced a current Speak4 integration on July 16, 2026. The public documentation describes advocacy data synchronization, including advocate records, recipient data and campaign tags. Speak4 is materialized as its own organization rather than folded into NationBuilder.

CallHub's current NationBuilder integration exposes another communications pathway: NationBuilder contacts/lists can feed calling and texting work, while field-dependent data such as tags, survey responses and event RSVPs can flow back. CallHub and founder/CEO Augustus Franklin are represented as distinct public nodes.

ConnectionsHub is documented by NationBuilder as a NationBuilder-built integration/utility hub. Its current tools include Kindsight iWave wealth screening, creating an explicit NationBuilder -> ConnectionsHub -> Kindsight public vendor/data-enrichment path.

Current 2026 payment documentation states that NationBuilder Payments is powered by Stripe and that NationBuilder is phasing out older third-party processors for NationBuilder donation pages. The payment processor is represented as a distinct product with a `powered_by` edge to Stripe rather than implying that Stripe owns or operates NationBuilder.

NationBuilder Insights currently uses Tableau for visualization and analysis of Nation data such as email engagement, fundraising, membership, volunteer and event metrics. This is recorded as a product integration, not as a claim that Tableau or its owner controls NationBuilder data.

RunForOffice.org was expanded in January 2026 with community nominations. NationBuilder describes the U.S. service as helping people identify elected offices and ballot-access procedures; Jay Godfrey is currently listed as President, Run for Office. The product and leadership edge are represented separately.

## Information-flow handling

This pass maps product-level public information flows only. It does not collect or expose private supporter, donor, voter, survey-response, campaign-CRM or administrative records. Documentation that says particular classes of information can synchronize is represented as product capability/data-flow evidence, not as evidence that any specific person's data was transferred.

## Recursive frontier

1. Enumerate current 2026 U.S. campaigns, committees, parties, advocacy organizations, nonprofits and civic groups that publicly disclose NationBuilder use through their own sites, public app integrations, public technology disclosures or vendor pages.
2. Expand the current NationBuilder app ecosystem into additional communications, compliance, field, event, fundraising, advocacy, analytics and data vendors.
3. Enumerate current public leadership and ownership relationships for mature partner/vendor nodes.
4. Trace observable public web -> signup/action -> email/SMS/voice/event/advocacy pathways while keeping private supporter/voter records out of scope.
5. Resolve public client/vendor edges only from direct public evidence; do not infer platform use merely from page appearance or similar branding.

## Canonicalization / execution

The current repository `AGENTS.md` and v0.9 executable schema were inspected first. Mature findings are materialized in canonical JSONL packet files under this bounded-pass directory; generated normalized `db/` was not hand-edited. Local git could not resolve `github.com`, so the repository-authorized GitHub connector fallback was used. Exact-head GitHub CI is the mandatory validator for this connector-created packet; the PR must remain draft and unmerged until both document and site/UI validation are conclusively successful.
