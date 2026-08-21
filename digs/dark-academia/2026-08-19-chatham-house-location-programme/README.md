# Chatham House location semantics and current-news pass

This hourly Auto-Dig pass selected `chatham-house-public-roster` through the repository's global dataset-first diversity rule, then selected its sole canonical organization target, `starintel:org:chatham-house`.

## Selection

- complete dataset/topic universe: 54 candidates
- source-roster manifests: 19
- existing dig roots: 27
- topic views: 8
- previous-three dataset exclusions: `boao-forum-public-roster`, `graphika`, `fed`
- previous-three dominant geography exclusions: China / Beijing-Hainan, New York, Washington, D.C.
- eligible dataset-stage pool: 51
- reproducible 64-bit seed: `13682783343080073306`
- algorithm: lexicographically sort the complete pool, remove hard recency exclusions, choose `eligible_pool[seed mod len(eligible_pool)]`, then select inside the chosen dataset
- selected dataset/topic: `chatham-house-public-roster`
- selected target: `starintel:org:chatham-house`
- normalized `db/investigation-target` records enumerated on current main: 36

The complete 54-entry candidate pool and the selected dataset's target pool are preserved in the `research-pass` record.

## HQ / public-location result

Chatham House's current first-party contact page identifies the Royal Institute of International Affairs as a charity registered at **10 St James's Square, London SW1Y 4LE, United Kingdom**. Its current organizational page also says the institute and its wholly owned trading subsidiary, Chatham House Enterprises Limited, share that registered address.

The reviewed first-party pages do **not** explicitly call this address the organization's headquarters. The packet therefore creates a typed `location` and a `has_registered_organizational_address` relation rather than promoting a registered/trading address to an unsupported headquarters assertion. No coordinates are invented.

A recursive target asks for current Royal Charter, Charity Commission, Companies House, annual-report, or first-party evidence that can resolve explicit headquarters semantics while keeping legal, trading, venue, office, and headquarters locations distinct.

## Current-news result

After the location slice was bounded, current Chatham House organizational/news surfaces were searched for a material update since the July 31 source-roster capture.

The current Latin America Programme page and its September 8 launch page establish a material organizational change: the **Latin America Initiative, founded in 2019, was formally established as a research programme earlier in 2026**. The exact establishment date is not stated in the reviewed first-party material, so the event is recorded at year-level precision and the exact date remains queued for recursive verification.

Routine commentary and unrelated policy analysis were not ingested as organizational events.

## Records

The packet adds nine typed v0.9.0 records:

- four first-party `source` records;
- one `location` record;
- one location `relation`;
- one organizational `event`;
- one `investigation-target`; and
- one `research-pass`.

Canonical dataset remains `chatham-house`; this source-roster pass is routed through the existing `dark-academia` research root rather than creating a new top-level dataset.
