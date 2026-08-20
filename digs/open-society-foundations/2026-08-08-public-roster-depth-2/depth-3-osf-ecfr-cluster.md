# Depth 3 — Open Society Foundations ↔ ECFR Institutional Cluster

**Parent:** Open Society Foundations public-roster depth-2 pass  
**Run:** `2026-08-08`  
**Status:** public-source evidence staging; canonical import pending

## Executive finding

The Open Society Foundations ↔ European Council on Foreign Relations relationship is not a single-person coincidence. Current and historical first-party records establish multiple independent layers:

1. **institutional origin/support** — OSF's own institutional history says the Foundations supported the creation of ECFR in 2006;
2. **current funding** — ECFR's current donor page lists Open Society Foundations among its foundations/associations donors;
3. **current board overlap** — Ivan Krastev is a current OSF director and a current ECFR trustee/founding board member;
4. **current Council overlap** — Alex Soros, George Soros, and Daniel Sachs are current ECFR Council members while holding current OSF roles;
5. **former-leadership overlap** — Mark Malloch-Brown is a current ECFR Council member and is identified there as former President of the OSF Board of Directors;
6. **current fellow/board overlap** — James C. O'Brien is a current OSF director and a current ECFR Distinguished Visiting Fellow.

These layers should be represented separately. Funding, governance, Council membership, employment/fellowship, and historical institutional support are different predicates.

Nothing here establishes improper coordination or misconduct. The finding is a dense, publicly documented institutional relationship.

## 1. Historical creation/support relationship

OSF's current institutional-history page states that, during its engagement with the European Union, Open Society supported efforts including **the creation of the European Council on Foreign Relations in 2006**.

This is a first-party OSF statement and is stronger than describing the organizations merely as ideologically adjacent.

Suggested evidence model:

```text
Open Society Foundations --supported_creation_of--> European Council on Foreign Relations
```

The exact predicate must be selected from the executable schema/predicate vocabulary. Do not silently transform `supported creation` into `founded`, `owns`, or `controls`.

## 2. Current donor relationship

ECFR's current `Our funding` page states that it relies on support from foundations, governments, and corporations and lists **Open Society Foundations (OSF)** in its current Foundations / Associations donor list.

Suggested evidence model:

```text
Open Society Foundations --donor_to--> European Council on Foreign Relations
```

The page does not expose an OSF-specific amount in the parsed donor list used in this pass. Do not invent a value or infer one from total ECFR income.

ECFR's donor page also lists the **European Investment Bank** as a government/public-body donor. Separately, the EIB Global Advisory Council currently includes ECFR director Mark Leonard and ECFR trustee Ivan Krastev. These are separate relationship types and should not be conflated.

## 3. Current governance overlap: Ivan Krastev

OSF's current Board of Directors lists Ivan Krastev as a board member.

ECFR's current Board of Trustees lists Ivan Krastev, and ECFR's profile describes him as a founding board member.

```text
Open Society Foundations --board_member--> Ivan Krastev <--board_member-- European Council on Foreign Relations
```

This is the cleanest current board-to-board interlock in the cluster.

## 4. Current Council overlap

ECFR's current Council directory includes:

- **Alex Soros** — Chair of the Board of Directors, Open Society Foundations;
- **George Soros** — Founder, Open Society Foundations;
- **Daniel Sachs** — Vice Chair of the Board of Directors, Open Society Foundations;
- **Mark Malloch-Brown** — former President of the Board of Directors, Open Society Foundations.

The Council is not the same body as ECFR's Board of Trustees. Preserve `council_member_of` separately from board membership.

### Alex Soros discrepancy remains

OSF's Alex Soros biography says he sits on ECFR's board. ECFR's current Board of Trustees does not list Alex Soros, while its current Council does list him.

Therefore:

```text
Alex Soros --council_member_of--> ECFR                     [current, ECFR primary]
OSF biography --claims--> Alex Soros board role at ECFR  [attributed/unresolved]
```

Do not promote the second edge to a current board relation without ECFR-side evidence or a dated historical board record.

## 5. Current OSF board member → ECFR fellow: James C. O'Brien

OSF's current Board of Directors lists **James C. O'Brien** as a board member.

ECFR's current profile lists **Jim O'Brien** as a **Distinguished Visiting Fellow**, working on transatlantic partnership issues. The biography matches the former U.S. Assistant Secretary of State for European and Eurasian Affairs and former Albright Stonebridge Group founder/vice chair described by OSF's board profile context.

This is a current cross-institution role, distinct from Council or trustee membership:

```text
James C. O'Brien --board_member_of--> Open Society Foundations
James C. O'Brien --distinguished_visiting_fellow_of--> European Council on Foreign Relations
```

Before canonicalization, resolve `James C. O'Brien` and `Jim O'Brien` through the repository's entity-resolution conventions rather than creating duplicate people.

## 6. Wider current ECFR Council OSF overlap: stale-title caution

ECFR's current Council directory also lists **Sandra Breka** with an OSF Vice President/COO title. OSF's current leadership page no longer lists Breka and instead identifies Leela Ramdhani as Chief Operating Officer.

This appears to be another temporal/title drift issue. Preserve the ECFR directory as evidence of Council membership, but do not use its displayed OSF title as authoritative for current OSF employment without dating it or reconciling it against OSF's live leadership roster.

The pattern reinforces a core ingestion rule: **organization directories can be current as membership lists while containing stale descriptive titles for members' outside jobs.**

## 7. Historical and operational collaboration surface

OSF pages also document repeated operational overlap with ECFR beyond donor/governance relations, including:

- OSF publication pages redistributing or discussing ECFR policy briefs;
- OSF events held in partnership with ECFR offices;
- OSF staff appearing in ECFR-linked policy discussions;
- ECFR events featuring George Soros and other OSF-linked participants.

These are useful historical evidence but should not be converted into durable governance predicates. Event participation, publication syndication, partnership, and employment are separate relation types.

## 8. Graph model

### Institution-level

```text
Open Society Foundations --supported_creation_of--> European Council on Foreign Relations
Open Society Foundations --donor_to--> European Council on Foreign Relations
```

### Current person-level

```text
Ivan Krastev --board_member_of--> Open Society Foundations
Ivan Krastev --board_member_of--> European Council on Foreign Relations
Alex Soros --chairs--> Open Society Foundations
Alex Soros --council_member_of--> European Council on Foreign Relations
George Soros --founder_of--> Open Society Foundations
George Soros --council_member_of--> European Council on Foreign Relations
Daniel Sachs --vice_chair_of--> Open Society Foundations
Daniel Sachs --council_member_of--> European Council on Foreign Relations
James C. O'Brien --board_member_of--> Open Society Foundations
James C. O'Brien --distinguished_visiting_fellow_of--> European Council on Foreign Relations
Mark Malloch-Brown --former_president_of--> Open Society Foundations
Mark Malloch-Brown --council_member_of--> European Council on Foreign Relations
```

### Attributed unresolved

```text
OSF Alex Soros biography --claims--> Alex Soros board membership at ECFR
```

## 9. Repository impact

The repository already has `starintel:org:european-council-on-foreign-relations`, but that node currently has low completeness and an empty member extraction.

This packet supplies primary-source material sufficient to materially improve that existing component once the writer/import path and validation gate are available.

Exact-name repository searches during this pass did not return existing person records for Ivan Krastev, Daniel Sachs, or Mark Malloch-Brown. Entity resolution should still be run before creation because exact GitHub code search is not a substitute for the canonical importer/index.

## 10. Next recursive targets

1. **ECFR donor history** — retrieve audited accounts and donor data by year; quantify OSF funding only where ECFR or OSF discloses an amount.
2. **OSF grant-directory ECFR records** — search the full 20,566-record grant corpus for ECFR and legal-entity-specific awards.
3. **James C. O'Brien identity resolution** — current OSF board and ECFR fellow role, plus any existing government/consulting records already in StarIntel.
4. **Sandra Breka temporal history** — date OSF executive tenure and preserve current ECFR Council membership without stale-job-title contamination.
5. **ECFR Board / EIB Global Advisory Council overlap** — Ivan Krastev, Arancha González Laya, Mark Leonard and other current institutional bridges.
6. **ECFR full Council cross-resolution** — compare all current Council members against existing StarIntel datasets rather than manually selecting politically salient names.

## Source index

| Publisher | Source | URL |
|---|---|---|
| Open Society Foundations | Our History | https://www.opensocietyfoundations.org/who-we-are/our-history |
| Open Society Foundations | Board of Directors | https://www.opensocietyfoundations.org/who-we-are/board-of-directors |
| Open Society Foundations | Leadership | https://www.opensocietyfoundations.org/who-we-are/leadership?search=1 |
| Open Society Foundations | Alex Soros profile | https://www.opensocietyfoundations.org/who-we-are/board-of-directors/alex-soros |
| European Council on Foreign Relations | Our funding | https://ecfr.eu/donors/funding/ |
| European Council on Foreign Relations | Council members | https://ecfr.eu/council/members/ |
| European Council on Foreign Relations | About / Board of Trustees | https://ecfr.eu/about/ |
| European Council on Foreign Relations | Jim O'Brien | https://ecfr.eu/profile/jim-obrien/ |
| European Council on Foreign Relations | Ivan Krastev | https://ecfr.eu/profile/ivan-krastev/ |
| European Investment Bank | Global Advisory Council | https://www.eib.org/en/projects/topics/global/global-advisory-council.htm |

## Validation status

Research staging only. No normalized `db/` record was hand-written. Canonicalization must use the repository-approved writer/import path and pass `python3 scripts/validate-for-merge.py --site` on the exact PR head.
