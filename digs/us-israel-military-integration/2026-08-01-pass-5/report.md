# U.S.–Israel Military Integration — Pass 5

**Run:** `2026-08-01`  
**Dataset:** `us-israel-military-integration`  
**New records:** `252` StarIntel v0.9.0 documents  
**Merged import plan:** `643` records through pass 5  
**JSONL SHA-256:** `52af5421a36212ef650f9c84002e315c1a01de20b36f393bef0acfe54856bf9c`  
**Selected filing amounts represented:** `$3,520,000`

## Added

- **140 relations**
- **41 organizations**
- **33 people**
- **13 LDA lobbying filings**
- **4 FARA filings**
- **16 recursive investigation targets**
- three analytic claims, one analysis, and one research-pass record

This pass resolves high-signal pass-4 targets into public-record relationships among defense companies, U.S. subsidiaries of foreign defense companies, lobbying firms, registered lobbyists, corporate directors, former government officials, commands, committees, trade associations, think tanks, PAC infrastructure, and FARA registrants.

Lobbying, FARA, board and employment records establish disclosed relationships. They do not independently establish corruption, policy capture or illegal conduct.

## Lobbying channels captured

| Client | Channels represented | Selected filing amounts |
|---|---|---:|
| Lockheed Martin | Etherton and Associates; Penn Avenue Partners | $90,000 |
| RTX | Akin Gump; J.A. Green; Forbes Tate | $110,000 |
| Boeing | In-house; Crossroads Strategies; Doerrer Group | $2,860,000 |
| Rafael USA | Pillsbury | $180,000 |
| Elbit Systems of America | In-house; Stapleton & Associates | $230,000 |
| Leonardo DRS | Ballard Partners | $50,000 |

The `$3,520,000` total is the sum of the selected filings represented here. The filings span different reporting periods and do not constitute an annual or company-wide total.

## High-value people

- **Robert O. Work** — RTX director; former Deputy Secretary of Defense; former CNAS chief executive; former CSBA vice president; Govini director.
- **Heather Wilson** — Lockheed director and classified-business committee chair; former Secretary of the Air Force; UTEP president; National Science Board and Google Public Sector roles.
- **John C. Aquilino** — Lockheed director; former commander of INDOPACOM, Pacific Fleet and Fifth Fleet/NAVCENT.
- **Kelly Ortberg** — Boeing chief executive and director; former RTX director; former Aptiv director; former Aerospace Industries Association Board of Governors chair.
- **Jeff Shockey** — Boeing government-operations executive; previously led RTX global government relations; former senior HPSCI and House Appropriations staff.
- **Justin Rubin** — Pillsbury lobbyist appearing in Rafael USA and IAI North America disclosures; prior Army roles disclosed in the IAI registration.
- **Brian Ballard and Daniel McFaul** — Ballard Partners lobbyists for Leonardo DRS; McFaul disclosed former congressional employment.
- **Moshe Schwartz** — Etherton lobbyist for Lockheed on NDAA, acquisition, software procurement, the industrial base and intelligence matters.

## New organization layer

The graph now includes lobbying and legal firms such as Etherton, Penn Avenue Partners, Akin Gump, Crossroads Strategies, Doerrer Group, Forbes Tate, Pillsbury, Stapleton & Associates, Ballard Partners, Holland & Knight, Steptoe and Bridges Partners.

It also adds Rafael USA, IAI North America, Elbit Systems of America, Leonardo DRS, Leonardo S.p.A., Government of Italy, Aerospace Industries Association, CNAS, CSBA, Govini, Google Public Sector, UTEP, the National Science Board, Lockheed Government Affairs, LMEPAC, and Lockheed's Classified Business and Security Committee.

## FARA layer

Four current FARA records connect:

- Holland & Knight → Israel Ministry of Foreign Affairs;
- Steptoe → Economic and Trade Mission at the Embassy of Israel;
- Bridges Partners through Havas Media Group Germany → Government of Israel;
- Show Faith by Works → Israel Ministry of Foreign Affairs.

A separate historical record links Rafael Armament Development Authority and Zvi Rafiah.

## Relations created

The packet uses explicit edges for:

`member_of`, `board_member_of`, `chairs`, `lobbied_for`, `filed_by`, `reports_representation_of`, `registered_under_fara_for`, `subsidiary_or_us_arm_of`, `indirectly_owned_by`, `partially_state_owned_by`, `formerly_commanded`, `formerly_served_as_deputy_secretary_of`, `formerly_ceo_of`, `formerly_vice_president_of`, `formerly_led`, `formerly_board_member_of`, `formerly_chair_of`, `leads_government_operations_at`, `formerly_led_government_relations_at`, `formerly_staff_director_of`, `formerly_staff_director_or_deputy_of`, and `manages_public_policy_through`.

## Targets queued

- complete Lockheed, RTX and Boeing lobbying rosters;
- complete Rafael USA, IAI North America and Elbit Systems of America influence networks;
- map board interlocks and former-government personnel;
- map defense trade associations;
- map current Israel FARA registrants and subcontractors;
- map lobbyist/PAC contribution networks;
- map congressional-committee revolving doors;
- map F-35 and missile-defense lobbying;
- map WRSA-I lobbying and oversight;
- map Government of Israel communications contractors.

## Merge

`merged-quasar-manifest.json` imports the baseline and passes 2–5 in order into one graph, deduplicating on `_id` with last-write-wins semantics.

`merge-packets.py` verifies every parent decoded SHA-256 and can generate a physical merged JSONL and compressed transport from a local checkout.

## Limits

“Key people” means people identifiable from high-signal official filings and corporate or government governance records. It is not a claim that every employee, informal participant or undisclosed relationship has been identified.
