# Auto-Dig election communications pass 18 — election mail and ballot tracking

Bounded breadth-first public-web enumeration for the `anarchist-violence` investigation corpus, replayed onto current `main` after resolving canonical overlap with later merged passes.

## Scope

This pass intentionally moved into a new election-ecosystem surface: election mail, ballot printing/mailing, ballot tracking, mail automation, and public jurisdiction/vendor relationships. It used current first-party sources where available and historical first-party sources where they establish durable product, leadership, or deployment relationships.

## Materialized records

- 10 `source`
- 6 `org`
- 4 `person`
- 10 `relation`
- 1 `investigation-target`
- **31 total records**

## New graph surface

New organization records in this packet: BallotTrax; i3logix; BlueCrest; Chicago Board of Elections; Dauphin County, Pennsylvania; Orange County Registrar of Voters.

Public people newly materialized here: Kevin Runbeck; Ken Matta; Rick Becerra; Justin O'Donnell.

The packet reuses current-main canonical identities for United States Postal Service (`starintel:org:usps`), Runbeck Election Services (`starintel:org:runbeck-election-services`), and Jeff Ellington (`starintel:person:jeff-ellington`) instead of redefining them. Current main also already carries the Jeff Ellington → Runbeck chief-executive relation, so the stale packet-local duplicate relation was removed.

Explicit edges retained here include BallotTrax → i3logix (`division_of`), BallotTrax → USPS (`integrates_with`), Runbeck → Chicago Board of Elections (`provides_printing_and_mailing_services_to`), Dauphin County → Runbeck (`uses_election_mail_sorting_solution_from`), BlueCrest ↔ Runbeck (`partnered_with`), Orange County Registrar of Voters → BlueCrest (`uses_vote_by_mail_solution_from`), and additional public leadership/communications roles for Runbeck and BlueCrest.

## Communications / information-flow observations

BallotTrax publicly describes proactive ballot-status notifications over text, email, and voice and states that its system combines state/county election-office, print-vendor, and USPS observations. USPS's 2026 Election Mail guidance documents serialized Intelligent Mail barcodes, tracking/reporting and election-mail support surfaces. Runbeck documents USPS-compliant ballot printing/mailing and IMb creation. BlueCrest documents end-to-end vote-by-mail automation and jurisdiction deployments.

## Dedupe / uncertainty

The current-main replay removed same-version canonical-ID collisions for USPS, Runbeck Election Services, and Jeff Ellington, and removed the semantically duplicate Jeff Ellington → Runbeck leadership edge. The remaining packet records are additive relative to the current corpus based on exact-ID searches performed during replay. Vendor-published testimonials are represented only as the specific relationships they support; they are not generalized into broader procurement or exclusivity claims. Historical leadership/product announcements are retained as public-source evidence and should be refreshed if contradictory current first-party material appears.

## Recursive frontier

Continue through USPS-certified Mail Service Providers, additional Runbeck/BlueCrest jurisdiction deployments, BallotTrax state/county integrations, ballot-printing vendors, mailing/sortation providers, public procurement records, and election-office notification/tracking surfaces. Preserve product-vendor-jurisdiction directionality and distinguish current deployments from historical references.
