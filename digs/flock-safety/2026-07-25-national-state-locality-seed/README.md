# Flock Safety national state and locality seed

Generated: `2026-07-25T17:58:54-04:00`

This packet starts a nationwide recursive StarIntel dig into Flock Safety. It completes the state-first seed pass and emits locality targets for every Flock-linked agency in the July 25, 2026 Atlas of Surveillance ALPR export.

## Output

- 50 state jurisdiction records
- 50 state analysis records
- 50 state investigation targets
- 2,629 locality investigation targets
- one Flock Safety organization record
- one Atlas dataset source record
- one national root target
- one research-pass record
- **2,783 canonical StarIntel v0.9.0 documents total**

## National seed findings

- Atlas ALPR export rows: 4,084
- Rows naming Flock Safety: 2,629
- States represented: 45
- States without a Flock row in this export: Alaska, Hawaii, Montana, New Hampshire, Vermont
- Rows with parseable camera quantities: 1,807
- Lower-bound camera total from parseable summaries: 29,446

The no-entry states are encoded as absence-of-evidence targets. The packet does not claim that Flock has no deployment, reseller sale, private installation, pilot, mobile unit, or indirect data-access relationship in those states.

Flock advertises more than 5,000 law-enforcement customers and more than 6,000 communities. The difference between those vendor claims and the Atlas rows is itself a research target.

## State queue

| State | Atlas-indexed Flock agency records |
|---|---:|
| Alabama | 109 |
| Alaska | 0 |
| Arizona | 28 |
| Arkansas | 38 |
| California | 195 |
| Colorado | 42 |
| Connecticut | 12 |
| Delaware | 2 |
| Florida | 88 |
| Georgia | 150 |
| Hawaii | 0 |
| Idaho | 6 |
| Illinois | 222 |
| Indiana | 202 |
| Iowa | 30 |
| Kansas | 42 |
| Kentucky | 53 |
| Louisiana | 19 |
| Maine | 1 |
| Maryland | 1 |
| Massachusetts | 17 |
| Michigan | 116 |
| Minnesota | 15 |
| Mississippi | 29 |
| Missouri | 96 |
| Montana | 0 |
| Nebraska | 14 |
| Nevada | 6 |
| New Hampshire | 0 |
| New Jersey | 6 |
| New Mexico | 7 |
| New York | 34 |
| North Carolina | 113 |
| North Dakota | 2 |
| Ohio | 220 |
| Oklahoma | 37 |
| Oregon | 16 |
| Pennsylvania | 9 |
| Rhode Island | 15 |
| South Carolina | 45 |
| South Dakota | 4 |
| Tennessee | 98 |
| Texas | 222 |
| Utah | 28 |
| Vermont | 0 |
| Virginia | 52 |
| Washington | 73 |
| West Virginia | 1 |
| Wisconsin | 112 |
| Wyoming | 2 |

## Recursion model

- depth 0: national corporate-government network
- depth 1: all 50 states
- depth 2: every Atlas-indexed locality or agency
- depth 3: contracts, grants, lobbyists, officials, administrators, resellers, policies, audits, sharing relationships, controversies, renewals, and terminations

Every locality target requires primary-source verification before its Atlas-derived lead is promoted into stronger entity, relation, contract, lobbying, policy, or event records.

## Validation

The generator validates every record with `starintel_doc.validate_document`, then checks unique IDs, target seed references, related-document references, and source URL schemes.

The generated packet passed `python3 scripts/validate-for-merge.py --site`, and the repository's canonical `Validate StarIntel DB` workflow was dispatched against the generated commit before this documentation-only follow-up commit.
