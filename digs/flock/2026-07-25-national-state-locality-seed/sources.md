# Sources and evidence boundaries

## Primary national index

- Atlas of Surveillance ALPR search: https://www.atlasofsurveillance.org/search?sort=state_asc&technologies=automated-license-plate-readers
- Atlas ALPR CSV export downloaded July 25, 2026: https://kiosk.atlasofsurveillance.org/download.csv?sort=state_asc&technologies%5B%5D=automated-license-plate-readers

The CSV contained 4,084 automated-license-plate-reader records. Filtering the `Vendor` field for `Flock` produced 2,629 agency records.

A single clear data-quality error was normalized: Des Peres Department of Public Safety had Missouri ORI data and a Missouri locality but the `State` field contained `PS`; this packet records it under Missouri.

## Vendor scope claim

- Flock Safety license plate reader product page: https://www.flocksafety.com/products/license-plate-readers

The vendor page states that Flock is trusted by more than 5,000 law-enforcement agencies and more than 6,000 communities. Those categories are not necessarily identical to Atlas agency rows and are not treated as a direct count comparison.

## State legal context used for no-entry and current-law targets

- New Hampshire ALPR registration rules: https://gc.nh.gov/rules/state_agencies/saf-c7200.html
- Vermont ALPR statute: https://legislature.vermont.gov/statutes/section/23/015/01607
- Vermont automated-law-enforcement chapter: https://legislature.vermont.gov/statutes/fullchapter/23/015
- Montana captured-license-plate-data retention law: https://law.justia.com/codes/montana/title-46/chapter-5/part-1/section-46-5-118/
- Flock state-specific contractual provisions: https://www.flocksafety.com/legal/state-required-provisions

## Evidence boundaries

- An Atlas row is encoded as a locality investigation lead, not conclusive proof that the deployment remains active.
- Camera counts parsed from summaries are lower bounds.
- No-entry states remain active targets.
- This seed pass does not claim comprehensive lobbying, procurement, grant, personnel, policy, audit, or data-sharing coverage.
- Follow-on state and locality passes must prefer official contracts, legislative packets, lobbying registries, purchase orders, policies, audits, and public-records releases.
