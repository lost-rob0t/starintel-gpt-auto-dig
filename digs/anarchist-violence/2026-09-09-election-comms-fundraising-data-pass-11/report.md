# Bounded Auto-Dig — 2026 election communications / fundraising-data pass 11

## Scope

Bounded breadth-first public-web enumeration for the `anarchist-violence` investigation corpus, focused on a fresh election-infrastructure cluster: fundraising rails, campaign software, voter-data providers, organizing platforms, and data-to-advertising bridges.

## Coverage

`starintel-documents.jsonl` contains **51 typed StarIntel v0.9 records**:

- 17 `source`
- 14 `org`
- 3 `person`
- 14 explicit `relation`
- 3 `investigation-target`

No inferred relationship was promoted to direct observation.

### New organizations / platforms

ActBlue; WinRed; Impactive; Hey Victor; ActionKit; NGP VAN; EveryAction; Bonterra; Mobilize; TargetSmart; Victory Waves; The TARA Group LLC; Catalist; FreeWheel.

### Public people

- Regina Wallace-Jones — CEO and President, ActBlue.
- Chelsea Peterson — General Manager, NGP VAN.
- Tom Goldenberg — CEO, Victory Waves.

### Explicit graph edges

- Regina Wallace-Jones `executive_of` ActBlue.
- Chelsea Peterson `executive_of` NGP VAN.
- Tom Goldenberg `executive_of` Victory Waves.
- Impactive `acquired_by` ActBlue.
- Hey Victor `acquired_by` ActBlue.
- ActionKit `rolls_up_to` NGP VAN.
- Mobilize `rolls_up_to` NGP VAN.
- EveryAction `part_of` Bonterra.
- EveryAction `acquired` Mobilize (historical relationship).
- ActionKit `integrates_with` ActBlue.
- TargetSmart `part_of` The TARA Group LLC.
- TargetSmart `partnered_with` Victory Waves.
- DSPolitical `partnered_with` FreeWheel.
- DSPolitical `uses_data_model_from` Catalist.

## Communications / distribution surfaces

The packet preserves first-party public surfaces for online fundraising and conduiting, campaign field/texting tools, campaign website infrastructure, email, advocacy/petition systems, supporter CRMs, voter files and audience modeling, data marketplaces, canvassing/mail/SMS/phone activation, petition validation, connected-TV advertising, buyer/identity infrastructure, and programmatic voter targeting.

## Dedupe / identity handling

Repository search on current main returned no indexed canonical matches for the fresh group of ActBlue, WinRed, ActionKit, Hey Victor, Impactive, Catalist, TargetSmart, Victory Waves, and FreeWheel before materialization. Existing DSPolitical from the immediately preceding ad-tech pass is reused as a relation endpoint rather than duplicated. Historical product/company states are retained explicitly rather than silently merging pre-acquisition identities into their current parent brands.

## Recursive frontier

1. Fundraising rails: public campaign/committee/party usage, conduit and joint-fundraising relationships, integrations, campaign websites, and publicly documented distribution pathways around ActBlue and WinRed.
2. Progressive campaign-software stack: NGP VAN, ActionKit, Mobilize, EveryAction/Bonterra, Catalist and TargetSmart integrations, ownership history, campaign use, field/data flows, and communications surfaces.
3. Data → ad-tech bridges: TargetSmart/Victory Waves, DSPolitical/Catalist/FreeWheel, data onboarding, CTV/programmatic distribution, petition and field technology, and other evidence-backed vendor/platform relationships.

## Write path

Canonical packet fallback used: mature findings are materialized in `digs/anarchist-violence/2026-09-09-election-comms-fundraising-data-pass-11/starintel-documents.jsonl`. No generated normalized `db/` record was hand-edited. Exact-head CI is the validator for this connector-created bounded pass.
