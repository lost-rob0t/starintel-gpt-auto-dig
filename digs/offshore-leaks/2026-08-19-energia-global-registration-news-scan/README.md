# Energia Global International registration geography and news scan

## Selection

This hourly Auto-Dig pass sampled the complete current 54-entry dataset/topic universe before choosing a target.

- run seed: `5852110873523907261`
- target-stage seed: `4390573403258482353`
- hard recent exclusions: `chatham-house-public-roster`, `boao-forum-public-roster`, `graphika`
- recent geography exclusions: London / United Kingdom; China / Beijing-Hainan; New York / United States
- current direct-conflict exclusions: `piie-public-roster`, `rand-public-roster`, `hunter-biden`, `topic:hunter-biden`, `milken-institute-public-roster`, `drunk-drivers`, `dark-academia`, `ecfr-public-roster`, `violent-offenders`, `flock`, `gop`, `topic:gop`, `dnc`, `topic:dnc`, `wef`, `topic:wef`, `wef-columbus`
- initial pre-conflict draw: `milken-institute-public-roster`, rejected because open PR #2065 already owns that exact location/news surface
- final eligible dataset/topic pool: **34**
- selected dataset/topic: **`topic:offshore-leaks`**
- target candidate pool: `starintel:org:energia-global-international-ltd`
- selected target: **`starintel:org:energia-global-international-ltd`**

The completed research-pass stores the full 54-entry candidate pool, exclusions, both seeds, algorithm, and selected target.

## HQ / location enrichment

The existing Paradise Papers record identifies Energia Global International, Ltd. as a Bermuda company. ICIJ's current entity page records it as registered in Bermuda, incorporated on **23 October 1997**, and closed on **7 November 2012**. IFC independently described the company as incorporated in Bermuda.

The reviewed sources do **not** establish a street headquarters or registered-office address. This pass therefore adds a typed historical Bermuda registration jurisdiction and a time-bounded `was_registered_in_jurisdiction` relation. It does not relabel incorporation jurisdiction as headquarters, does not infer project sites as corporate offices, and adds no coordinates.

A bounded recursive target asks for historical Bermuda Registrar, Gazette, Appleby, annual-report, or contemporaneous company evidence that can distinguish registered office, headquarters, principal office, and operating locations.

## Current-news scan

Only after completing the location slice, current web/news searches covered Energia Global International, Paradise Papers / Offshore Leaks, Bermuda registration, ownership, closure, and location changes through **19 August 2026**. The reviewed results were historical ICIJ/IFC material or generic Offshore Leaks database surfaces. No material new event, correction, ownership update, or location change specific to the selected entity warranted ingestion, so no filler event was created.

## Records

The packet contains six additive StarIntel v0.9.0 records:

- 2 `source`
- 1 `location`
- 1 `relation`
- 1 `investigation-target`
- 1 `research-pass`

Entity-specific records retain the existing `paradise-papers` source dataset. The run ledger remains in `offshore-leaks`, which is the existing topic/source structure; no per-run dataset was created.

## Validation

Direct Git transport cannot resolve `github.com` in the execution sandbox, but the GitHub connector remains healthy and authoritative. The changed packet was reconstructed locally and checked for JSONL parsing, six unique IDs, current v0.9.0 common/data-field allowlists, relation/target required fields, source/confidence bounds, relation endpoint integrity against the existing canonical organization plus packet-local location, ISO timestamps, canonical dataset preservation, terminating newline, and absence of invented coordinates.

The exact-head GitHub `Validate StarIntel documents` workflow remains the authoritative full-corpus/source-audit gate and must be green before this PR is ready or squash-merged.
