# Bounded Auto-Dig — 2026 election communications / consulting-media pass 12

## Scope

Bounded breadth-first public-web enumeration for the `anarchist-violence` investigation corpus, focused on a fresh election-infrastructure cluster: political consulting networks, communications/advocacy agency groups, media buying, direct mail, digital advertising, fundraising/direct-response agencies, field operations, research/polling, and campaign communications.

## Coverage

`starintel-documents.jsonl` contains **38 typed StarIntel v0.9 records**:

- 7 `source`
- 13 `org`
- 4 `person`
- 12 explicit `relation`
- 2 `investigation-target`

No identity collision was force-merged. Two Axiom-network `part_of` edges are confidence-graded at 0.95 where the current team/portfolio presentation establishes the operating-network context more directly than formal legal ownership; Vanguard Field Strategies is recorded at 0.99 because Axiom explicitly describes it as a subsidiary.

## New organizations / platforms

Axiom Strategies; Remington Research Group; Vanguard Field Strategies; AxMedia; Stagwell; Targeted Victory; SKDK; HarrisX; Allison; Majority Strategies; Google; GMMB; MissionWired.

## Public people

Jeff Roe; Zac Moffatt; Liam Donovan; Kate Kline.

## Explicit graph surface

- Jeff Roe -> Axiom Strategies leadership.
- Remington Research Group, Vanguard Field Strategies and AxMedia -> Axiom operating-network edges.
- Targeted Victory, SKDK, HarrisX and Allison -> Stagwell communications/advocacy network edges.
- Zac Moffatt -> Stagwell communications/advocacy leadership.
- Liam Donovan -> Targeted Victory leadership.
- Majority Strategies -> Google Premier Partner relationship for political digital advertising.
- Kate Kline -> MissionWired leadership.

## Communications / distribution surfaces

The packet preserves public first-party surfaces covering campaign strategy, polling, research, field/canvassing, paid media, media buying, political advertising, digital fundraising, risk/reputation communications, public affairs, direct mail and campaign direct response.

## Dedupe / identity handling

Repository search on current main returned no indexed canonical match for the combined Targeted Victory / GMMB / Axiom Strategies / Majority Strategies / MissionWired / Stagwell cluster before materialization. Brands remain distinct entities even when a parent/network relationship is observed. Public people are materialized only from first-party professional-role pages.

## Recursive frontier

1. Political consulting holding networks: subsidiaries, acquisitions, shared executives, service lines, publicly documented clients, integrations and communication surfaces around Axiom and Stagwell.
2. Campaign media buying/distribution: advertising platforms, data providers, publishers, CTV, direct mail and digital-distribution relationships around Targeted Victory, GMMB and Majority Strategies.

## Write path

Canonical connector-created packet fallback used: mature findings are materialized in `digs/anarchist-violence/2026-09-09-election-comms-consulting-media-pass-12/starintel-documents.jsonl`. No generated normalized `db/` record was hand-edited. Exact-head CI is the mandatory validator for this connector-created bounded pass.
