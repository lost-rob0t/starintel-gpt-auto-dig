# RAND headquarters and current-news scan

This hourly Auto-Dig pass used the complete 54-entry current dataset/topic universe and a reproducible two-stage draw. The previous three successful hourly datasets were excluded, directly overlapping draft slices were avoided, and the target-stage geography filter avoided London/United Kingdom, China/Beijing-Hainan, and New York when alternatives existed. The selected composite topic was `dark-academia`; the selected source dataset was `rand-public-roster`; the canonical target was `starintel:org:rand-corporation`.

## Headquarters / location

RAND's current first-party contact page explicitly labels **Santa Monica** as **Headquarters** and publishes **1776 Main Street, Santa Monica, CA 90401-3208** as the physical delivery address. Washington, Pittsburgh, Boston, RAND Europe, and RAND Australia are separately presented as offices. This packet therefore creates a typed headquarters location and a `headquartered_at` relation without inferring headquarters from a generic contact address. The standard-mail ZIP variant is not collapsed into the physical-delivery address, and no coordinates are invented.

No new connector or schema path was justified. The existing v0.9.0 `location` and `relation` dtypes already represent this evidence cleanly.

## Current news

After the location slice, the pass searched RAND's current press/news surface and current web results with overlap from July 28 through August 19, 2026. The reviewed results were research/commentary or unrelated entities with similar names; no material post-refresh RAND corporate, governance, relationship, or headquarters change warranted ingestion. No filler event was created.

## Records

The packet contains six v0.9.0 records: two `source` records, one `location`, one `relation`, one queued `investigation-target`, and one completed `research-pass`. The canonical `dataset` remains `rand`.

## Recursive target

The next bounded target is to recover dated authoritative evidence for headquarters continuity at 1776 Main Street and a parseable current RAND leadership/people roster, while preserving headquarters, mail, offices, and affiliated organizational locations as distinct semantics.

## Validation

The packet is designed against the current executable `starintel_doc` v0.9.0 field registry and generated schema. Pre-PR sandbox checks cover JSONL parsing, unique IDs, dtype field allowlists, required relation/target fields, source/confidence shape, relation endpoint resolution against the canonical RAND org plus packet-local location, canonical dataset preservation, terminating-newline/whitespace checks, and exact packet paths. The full repository merge gate and all exact-head GitHub checks remain mandatory before merge.
