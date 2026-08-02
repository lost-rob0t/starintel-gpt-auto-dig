# U.S.–Israel Military Integration — Pass 5: People, Memberships, Lobbying and Merge

**Run:** `2026-08-01`  
**Dataset:** `us-israel-military-integration`  
**New records:** `252` StarIntel v0.9.0 documents  
**Cumulative import plan:** `643` records through pass 5  
**JSONL SHA-256:** `52af5421a36212ef650f9c84002e315c1a01de20b36f393bef0acfe54856bf9c`  
**Selected filing amounts represented:** `$3,520,000`

## What changed

This pass converts the pass-4 target queue into a documented influence graph:

- key people linked to employers, boards, former government commands, committees, think tanks and trade associations;
- lobbying firms linked to defense-company clients and individual lobbyists;
- lobbying filings represented as first-class records with explicit filing → registrant and filing → client relations;
- Israeli-owned or Israel-linked U.S. subsidiaries linked to U.S. lobbying channels;
- current and historical FARA records linked to foreign principals and registrants;
- new recursive targets for PAC money, trade associations, lobbying rosters, F-35 appropriations, missile defense, WRSA-I and Government of Israel communications contractors.

Lobbying and FARA filings prove disclosed representation relationships. They do not independently prove corruption, policy capture or unlawful coordination.

## Packet counts

```json
{
  "analysis": 1,
  "claim": 3,
  "fara-filing": 4,
  "investigation-target": 16,
  "lobbying-filing": 13,
  "org": 41,
  "person": 33,
  "relation": 140,
  "research-pass": 1
}
```

## Selected lobbying network

| Client | Disclosed channels captured | Filing-specific amount |
|---|---|---:|
| Lockheed Martin | Etherton and Associates; Penn Avenue Partners | $90,000 selected Q1–Q2 2026 filings |
| RTX | Akin Gump; J.A. Green; Forbes Tate | $110,000 selected 2025–Q1 2026 filings |
| Boeing | In-house; Crossroads Strategies; Doerrer Group | $2,860,000 selected Q1–Q2 2026 filings |
| Rafael USA | Pillsbury | $180,000 selected 2025 filing |
| Elbit Systems of America | In-house; Stapleton & Associates | $230,000 selected 2025 filings |
| Leonardo DRS | Ballard Partners | $50,000 selected Q1 2026 filing |

The `$3,520,000` figure is only the sum of the selected filings represented in this packet. It is not a company-wide, annual or all-time total.

## Key people and cross-organizational memberships

- **Robert O. Work** — RTX director; former U.S. Deputy Secretary of Defense; former CNAS CEO; former CSBA vice president; Govini board member.
- **Heather Wilson** — Lockheed director and classified-business committee chair; former Secretary of the Air Force; UTEP president; National Science Board and Google Public Sector roles.
- **John C. Aquilino** — Lockheed director; former commander of INDOPACOM, Pacific Fleet, and Fifth Fleet/NAVCENT.
- **Kelly Ortberg** — Boeing CEO and director; former RTX director; former Aptiv director; former Aerospace Industries Association Board of Governors chair.
- **Jeff Shockey** — Boeing government-operations executive; previously led RTX global government relations; former HPSCI and House Appropriations senior staff.
- **Justin Rubin** — Pillsbury lobbyist appearing in Rafael USA and IAI North America filings; former U.S. Army roles disclosed in the IAI registration.
- **Brian Ballard / Daniel McFaul** — Ballard Partners lobbyists for Leonardo DRS; McFaul disclosed prior congressional roles.
- **Moshe Schwartz** — Etherton lobbyist for Lockheed on NDAA, acquisition, software procurement, industrial-base and intelligence issues.

The packet also creates person and relation records for lobbying teams associated with Etherton, Penn Avenue Partners, Akin Gump, J.A. Green, Forbes Tate, Crossroads Strategies, Doerrer Group, Pillsbury, Stapleton & Associates and Ballard Partners.

## New organizations

- `starintel:org:akin-gump` — Akin Gump Strauss Hauer & Feld
- `starintel:org:aerospace-industries-association` — Aerospace Industries Association
- `starintel:org:alliance-hispanic-serving-research-universities` — Alliance of Hispanic Serving Research Universities
- `starintel:org:aptiv` — Aptiv PLC
- `starintel:org:bridges-partners` — Bridges Partners LLC
- `starintel:org:center-new-american-security` — Center for a New American Security
- `starintel:org:center-strategic-budgetary-assessments` — Center for Strategic and Budgetary Assessments
- `starintel:org:crossroads-strategies` — Crossroads Strategies, LLC
- `starintel:org:doerrer-group` — The Doerrer Group LLC
- `starintel:org:economic-trade-mission-israel-embassy` — Economic and Trade Mission at the Embassy of Israel
- `starintel:org:elbit-systems-america` — Elbit Systems of America, LLC
- `starintel:org:etherton-associates` — Etherton and Associates, Inc.
- `starintel:org:forbes-tate` — Forbes Tate
- `starintel:org:google-public-sector` — Google Public Sector
- `starintel:org:government-of-israel` — Government of Israel
- `starintel:org:government-of-italy` — Government of Italy
- `starintel:org:govini` — Govini
- `starintel:org:havas-media-group-germany` — Havas Media Group Germany
- `starintel:org:holland-knight` — Holland & Knight
- `starintel:org:house-appropriations-committee` — House Appropriations Committee
- `starintel:org:house-armed-services-committee` — House Armed Services Committee
- `starintel:org:house-permanent-select-committee-intelligence` — House Permanent Select Committee on Intelligence
- `starintel:org:iai-north-america` — IAI North America
- `starintel:org:israel-ministry-foreign-affairs` — Israel Ministry of Foreign Affairs
- `starintel:org:leonardo-drs` — Leonardo DRS, Inc.
- `starintel:org:leonardo-spa` — Leonardo S.p.A.
- `starintel:org:lockheed-classified-business-security-committee` — Lockheed Martin Classified Business and Security Committee
- `starintel:org:lockheed-government-affairs` — Lockheed Martin Government Affairs
- `starintel:org:lockheed-martin-employees-pac` — Lockheed Martin Employees' Political Action Committee
- `starintel:org:national-science-board` — National Science Board
- `starintel:org:penn-avenue-partners` — Penn Avenue Partners
- `starintel:org:pillsbury` — Pillsbury Winthrop Shaw Pittman LLP
- `starintel:org:rafael-usa` — Rafael USA, Inc.
- `starintel:org:show-faith-by-works` — Show Faith by Works, LLC
- `starintel:org:stapleton-associates` — Stapleton & Associates, LLC
- `starintel:org:steptoe` — Steptoe LLP
- `starintel:org:united-states-air-force` — United States Air Force
- `starintel:org:united-states-house-representatives` — United States House of Representatives
- `starintel:org:us-indo-pacific-command` — U.S. Indo-Pacific Command
- `starintel:org:us-pacific-fleet` — U.S. Pacific Fleet
- `starintel:org:utep` — University of Texas at El Paso

## FARA layer

The pass adds:

- Holland & Knight → Israel Ministry of Foreign Affairs;
- Steptoe → Economic and Trade Mission at the Embassy of Israel;
- Bridges Partners / Havas Media Group Germany → Government of Israel;
- Show Faith by Works → Israel Ministry of Foreign Affairs;
- a historical Rafael Armament Development Authority ↔ Zvi Rafiah FARA record.

These records are kept distinct from ordinary LDA lobbying filings.

## Relation families

- `member_of`
- `board_member_of`
- `chairs`
- `lobbied_for`
- `filed_by`
- `reports_representation_of`
- `registered_under_fara_for`
- `subsidiary_or_us_arm_of`
- `indirectly_owned_by`
- `partially_state_owned_by`
- `formerly_commanded`
- `formerly_served_as_deputy_secretary_of`
- `formerly_ceo_of`
- `formerly_vice_president_of`
- `formerly_led`
- `formerly_board_member_of`
- `formerly_chair_of`
- `leads_government_operations_at`
- `formerly_led_government_relations_at`
- `formerly_staff_director_of`
- `formerly_staff_director_or_deputy_of`
- `manages_public_policy_through`

## Recursive targets added

- `starintel:investigation-target:defense-board-interlocks` — Map defense-company board interlocks
- `starintel:investigation-target:defense-trade-associations` — Map defense trade-association memberships
- `starintel:investigation-target:elbit-us-influence-roster` — Complete Elbit Systems of America influence network
- `starintel:investigation-target:f35-lobbying-appropriations` — Map F-35 lobbying and appropriations
- `starintel:investigation-target:government-israel-communications-contractors` — Map Government of Israel U.S. communications contractors
- `starintel:investigation-target:iai-us-influence-roster` — Complete IAI North America influence network
- `starintel:investigation-target:israel-fara-current-network` — Map current Israel FARA network
- `starintel:investigation-target:lobbyist-pac-contributions` — Map lobbyist and PAC contribution network
- `starintel:investigation-target:lockheed-lobbying-roster` — Complete Lockheed Martin lobbying roster
- `starintel:investigation-target:missile-defense-lobbying` — Map missile-defense lobbying
- `starintel:investigation-target:rafael-us-influence-roster` — Complete Rafael U.S. influence network
- `starintel:investigation-target:revolving-door-congressional-committees` — Map congressional committee revolving door
- `starintel:investigation-target:rtx-lobbying-roster` — Complete RTX lobbying roster
- `starintel:investigation-target:us-israel-military-integration-pass-5` — Merge and recurse the U.S.–Israel military influence network
- `starintel:investigation-target:wrsa-i-lobbying-oversight` — Map WRSA-I lobbying and oversight
- `starintel:investigation-target:boeing-lobbying-roster` — Complete Boeing lobbying roster

## Merge

`merged-quasar-manifest.json` defines one ordered Quasar import over the baseline and passes 2–5. It imports all eight transport files into the same graph, deduplicates on `_id`, and applies last-write-wins semantics.

`merge-packets.py` performs the same operation in a local checkout and generates a physically merged JSONL plus compressed base64 transport after verifying every parent decoded hash.

## Source index

- U.S. Senate Lobbying Disclosure Act filing system
- U.S. House/Senate LDA filing pages
- U.S. Department of Justice FARA eFile system
- Lockheed Martin political-disclosure and board-governance pages
- Boeing executive biographies and investor releases
- RTX board biographies

## Limits

- “Key people” means high-signal people visible in official filings and corporate/government governance records; it is not a claim that every employee or informal participant has been identified.
- Filing amounts are reported values for specific filings and periods.
- Board membership, former government service and lobbying registration are documented relationships, not misconduct findings.
