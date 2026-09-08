# FED hourly Auto-Dig — National Security Adviser / EOP location

This pass selected the existing `fed` dataset/topic through deterministic dataset-first sampling and then selected the remaining actionable FED target `starintel:target:fed:identify-current-national-security-advisor`.

## HQ / location boundary

The White House's Executive Branch page places many senior EOP advisers in the West Wing and most EOP staff in the Eisenhower Executive Office Building, both within the White House compound. The White House contact page publishes 1600 Pennsylvania Avenue NW, Washington, DC 20500 as the public White House mailing address.

The packet therefore records that address only as a public government-compound location connected to the Executive Office of the President. It does not infer that every EOP component, the National Security Council, or the National Security Adviser has a distinct headquarters at that street address. No coordinates are added.

## Role finding

Recent reporting identifies Marco Rubio as the current national security adviser while he also serves as Secretary of State. The pass does not treat that as proof of the formal acting/permanent designation. A recursive target remains queued for an authoritative appointment or personnel record that resolves the status and valid-from date.

The packet reuses the canonical `starintel:person:marco-rubio` identity created by the earlier cabinet seed. The current-role evidence lives on `starintel:relation:marco-rubio-national-security-adviser-eop-2026-08-19`, including its source, confidence, role qualifier, and unresolved formal-status qualifier. A redundant same-version FED person redefinition was removed on 2026-09-01 instead of weakening importer duplicate detection or silently replacing the canonical person record.

## Current news

The August 14, 2026 report that Deputy National Security Adviser Andy Baker is departing was ingested as a material personnel-transition event. Non-material commentary was not ingested.

## Selection

- dataset/topic universe: 54
- seed: `12498758852186736832`
- previous-three dataset exclusions: `drunk-drivers`, `greater-israel`, `cia`
- previous-three geography exclusions: Utah, Israel, California
- active direct-conflict exclusions: `dark-academia`, `ecfr-public-roster` due to the open ECFR hourly PR
- selected dataset/topic: `fed`
- selected target: `starintel:target:fed:identify-current-national-security-advisor`

The exact whole-corpus actionable-target total is not fabricated here: the connector-only runtime could enumerate repository surfaces but could not execute the complete Free-Range corpus loader over a conventional checkout after direct GitHub DNS failed.
