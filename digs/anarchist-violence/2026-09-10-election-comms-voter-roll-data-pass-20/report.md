# Auto-Dig 2026 election communications — voter-roll data infrastructure pass 20

## Scope

Bounded breadth-first public political-discourse / communications and 2026 U.S. election-ecosystem enumeration for the `anarchist-violence` corpus. This pass deliberately moved to a new graph surface: voter-registration list-maintenance data exchange, federal data feeds, entity-resolution infrastructure, current ERIC governance, and public contact/distribution surfaces.

## Coverage

- Candidate nodes checked: 31
- Already-covered nodes skipped: 2
- New sources: 6
- New organizations: 8
- New people: 3
- New media/communication surfaces: 1
- New explicit relations: 11
- Inferred relations: 0
- Identity collisions retained unresolved: 0
- Recursive targets: 1
- Unique primary source domains: 2
- Localities/states represented by explicit current leadership: Washington and Utah
- Unresolved graph leads: remaining ERIC member-state agencies and board members, advisory-board institutions, state voter-contact implementations, public procurement records, report-use notices, and further technical/data-service dependencies.

## New graph surface

The Electronic Registration Information Center (ERIC) is represented as a current state-election-official membership organization. Current first-party material lists 27 states plus the District of Columbia as members.

Technical and data-supply edges materialized from ERIC's current security documentation include ERIC's use of Senzing-developed entity-resolution software licensed through IBM, official Social Security Administration death data, USPS change-of-address data, A-LIGN SOC 2 assessment history, and CISA security-assessment services. NTIS is separately represented as the administrator of certified access to the SSA-owned Limited Access Death Master File.

Current ERIC governance is expanded into canonical people for Executive Director Shane Hamlin, Chair Stuart Holmes, and Vice Chair Ryan Cowley. Their public ERIC roles are represented as explicit relations instead of remaining embedded text.

A public ERIC information/media contact surface is represented from the organization's published general-information and media-inquiry channels.

## Evidence discipline

All materialized relations in this pass are explicit public-source observations. No cross-source identity merge was made from name similarity. No state is represented as granting ERIC control of a voter-registration system; ERIC's own security material explicitly says its servers are not connected to state voter-registration systems and members retain control of their records.

## Recursive frontier

Expand the remaining current ERIC member-state election agencies, board/advisory network, state-level public explanations of ERIC report use, list-maintenance notices, voter-contact workflows, procurement records, public service vendors, and observable data/report distribution paths. Preserve the distinction between ERIC-produced candidate reports and the member jurisdiction's legal/administrative decisions.

## Canonical write path

Mature findings are materialized in `digs/anarchist-violence/2026-09-10-election-comms-voter-roll-data-pass-20/starintel-documents.jsonl`. This connector-created packet follows the repository's GitHub fallback path and is subject to exact-head CI validation before merge.
