# Flock organization rosters and WEF cross-match

Generated: `2026-07-31T03:09:00-04:00`

This is the fifth recursive pass over the Columbus/Flock graph. It expands every organization lead into member-roster, capital/control, and World Economic Forum affiliation targets.

## Output

- **368 typed StarIntel v0.9 records**
- **43 organization leads**
- **28 publicly named person leads**
- **66 typed relations**
- **196 recursive investigation targets**
- **34 reviewed sources**
- 1 research pass

## Organization groups

- Flock Safety founders, executives, board members, sales, public affairs, legal, security, recruiting, aviation, and private-sector strategy
- Flock investors from the March 2025 financing and earlier Series E
- Columbus municipal, police, council, airport, university, hospital, and public-record organizations
- Private-sector, nonprofit, healthcare, university, retail, and aviation leads
- World Economic Forum, Young Global Leaders, Global Shapers, and Annual Meeting partner controls

## Confirmed WEF cross-matches

| Person | Organization link | WEF evidence boundary |
|---|---|---|
| Peter A. Thiel | Founders Fund partner | Official WEF people profile |
| Ken Howery | Founders Fund co-founder and partner | Official WEF people profile |
| Sam Altman | Former Y Combinator president | Official WEF people profile; 2016 Young Global Leader |
| Arnav Sahu | Y Combinator investor | Official WEF agenda contributor |
| Arianna Simpson | Andreessen Horowitz deal partner | Official WEF people profile |
| Ray Lane | Kleiner Perkins managing partner on profile | Official WEF people profile; role requires current-status revalidation |
| John Maeda | Former Kleiner Perkins design partner | WEF profile states former Global Agenda Council membership |
| Sally Shin | Kleiner Perkins scout | WEF profile states Young Global Leader |
| Maggie Romero | WEF profile title references Andreessen Horowitz | Profile body references TPG; conflict queued for resolution |

## WEF classification rules

This packet does **not** collapse every WEF-related fact into `member_of`.

- `member_of`: used only for documented community membership such as Young Global Leaders.
- `has_official_profile_at`: an official WEF people profile.
- `agenda_contributor_to`: an official WEF agenda-contributor page.
- `served_on_wef_council`: a documented council role.
- `partner_of`: institutional or meeting-partner status for an organization.
- Employment at a WEF partner does not establish personal WEF membership.
- Absence from one current WEF list is a dated negative result, not proof of no WEF relationship.

## Roster completion boundary

A private company does not publish a complete employee database. “Complete roster” therefore means all publicly documented current and historical members recoverable from official team pages, filings, Form ADV, board biographies, archived official pages, conference programmes, public contracts, lobbying registrations, and public records.

Private contact data, home addresses, credentials, and unrelated family information are out of scope.

## High-priority targets

1. Enumerate all publicly identifiable Flock employees across the reported 1,400-person workforce.
2. Recover Flock's full board, observers, governance committees, and investor appointment rights.
3. Enumerate public affairs, government relations, legal, policy, compliance, and lobbying personnel.
4. Enumerate every publicly disclosed private Flock-network organization and its law-enforcement integrations.
5. Batch cross-match every employee and alumnus of every Flock investor against all WEF affiliation surfaces.
6. Recover complete CPD and airport-authority Flock user and administrator rosters.
7. Resolve the conflicting employer fields on Maggie Romero's WEF profile.
8. Expand Ohio university, hospital, airport, and private-security access networks.

## Validation

- deterministic JSONL serialization
- unique document IDs
- all relation endpoints resolve
- all investigation-target seed IDs resolve
- gzip+base64 multipart round-trip verified
- SHA-256: `c4edfd4d448666e8c1d585fde5a5d6fd98ded1f3c43c4664d070b2263d94eb16`

Repository merge validation remains affected by the unrelated corrupt gzip already present on the current `main` merge base.
