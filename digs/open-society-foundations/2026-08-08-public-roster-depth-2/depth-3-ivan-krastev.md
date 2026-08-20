# Depth 3 — Ivan Krastev Institutional Map

**Parent:** Open Society Foundations public-roster depth-2 pass  
**Run:** `2026-08-08`  
**Status:** public-source evidence staging; canonical import pending  
**Handling:** public institutional affiliations only; no private identifiers or contact enrichment

## Why this node was selected

Ivan Krastev is a current Open Society Foundations board member and a current European Council on Foreign Relations Board of Trustees member. That makes him a verified bridge between the queued OSF target and an existing StarIntel ECFR organization node.

Exact-name repository search did not return an existing Ivan Krastev person record during this pass. Following the current institutional links therefore expands the graph rather than duplicating a known person node.

## Current institutional map

### Open Society Foundations

Current OSF Board of Directors member.

### European Council on Foreign Relations

ECFR's current governance pages list Krastev on the Board of Trustees. ECFR's profile describes him as a **founding board member**.

### Centre for Liberal Strategies

The Centre for Liberal Strategies (CLS) currently lists Krastev as **Founder and Chairman of the Board** and Global Affairs Programme Director. CLS states it was established in 1994 as an independent nongovernmental organization.

This is a first-party confirmation and should be preferred over secondary biographies for the current CLS relationship.

### Institute for Human Sciences / IWM Vienna

IWM's current Ivan Krastev profile identifies him as:

- **Rector ad Interim**;
- holder of the **Albert Hirschman Permanent Fellowship**.

IWM's current academic-staff page also lists him as Rector ad Interim. This is a stronger present-tense source than older cached pages that may still expose prior rectors.

### GLOBSEC

GLOBSEC's current Board of Directors page lists Ivan Krastev as a board member and identifies him as chairman of the Centre for Liberal Strategies.

GLOBSEC's 2026 Forum speaker page also identifies him as a Member of the Board of Directors, providing current-event corroboration.

### European Investment Bank Global Advisory Council

The European Investment Bank's current Global Advisory Council page lists Ivan Krastev as a council member. The EIB's December 2025 announcement creating the council also named him among the members.

The same current EIB council includes **Mark Leonard**, co-founder and director of ECFR. This creates another OSF/ECFR-adjacent institutional overlap at one recursion step beyond Krastev.

### International Crisis Group

A direct current Crisis Group board page was not reliably retrievable/indexable in this pass, so this relationship is not being labeled institution-side verified here.

However, several independent first-party institutional biographies currently describe Krastev as a member of the International Crisis Group's Board of Trustees or board, including:

- IWM;
- ECFR;
- GLOBSEC;
- Centre for Liberal Strategies.

That is strong cross-corroboration but still warrants a dedicated Crisis Group-side verification pass before canonicalizing a present-tense trustee predicate.

## Cross-source terminology discrepancy

CLS's current Ivan Krastev profile describes the Crisis Group relationship as an **Advisory Board** membership, while IWM, ECFR, and GLOBSEC describe it as **Board of Trustees** membership.

Do not collapse those titles. The exact current Crisis Group governance body must be resolved from Crisis Group's own records before selecting the canonical predicate.

## WEF surface

The World Economic Forum currently exposes a public Ivan Krastev profile identifying him as chairman of CLS and describing ECFR, ICG, and GLOBSEC affiliations. WEF also has a public organization page for the Centre for Liberal Strategies.

This is useful for source discovery and cross-dataset matching, but **the existence of a WEF profile or organization page is not itself evidence of WEF membership, partnership, or funding**. Do not infer such an edge without an explicit WEF roster or relationship source.

## Verified current graph candidates

These are research candidates only and must go through the repository writer/import path and executable predicate vocabulary.

```text
Ivan Krastev --board_member_of--> Open Society Foundations
Ivan Krastev --founding_board_member_of--> European Council on Foreign Relations
Ivan Krastev --founder_and_chair_of_board--> Centre for Liberal Strategies
Ivan Krastev --rector_ad_interim_of--> Institute for Human Sciences (IWM Vienna)
Ivan Krastev --permanent_fellow_of--> Institute for Human Sciences (IWM Vienna)
Ivan Krastev --board_member_of--> GLOBSEC
Ivan Krastev --member_of--> EIB Global Advisory Council
```

## Strong but title-unresolved candidate

```text
Ivan Krastev --governance_role_at--> International Crisis Group
```

Evidence currently conflicts between `Board of Trustees` and `Advisory Board` terminology. Preserve source attribution until the institution-side governance roster resolves it.

## New organization candidates

Exact-name repository search during this pass returned no first-class result for:

- Centre for Liberal Strategies;
- GLOBSEC;
- European Investment Bank / EIB Global Advisory Council.

The repository does contain prior research mentions of the Institute for Human Sciences, but this pass did not establish a canonical first-class IWM organization node. Resolve before creating duplicates.

## Depth-4 targets generated

1. **Centre for Liberal Strategies** — management board, donors, partners, annual report, organizational registration, and public project network.
2. **EIB Global Advisory Council** — enumerate all current members and cross-resolve them against ECFR, OSF, WEF, government, and think-tank datasets.
3. **GLOBSEC Board of Directors** — enumerate current directors and cross-resolve institutional roles.
4. **International Crisis Group governance** — resolve current board/trustee/advisory terminology from Crisis Group primary records.
5. **IWM governance and institutional funders** — current rector/fellows, board/governance, partners and public financial/funding disclosures.
6. **Mark Leonard** — ECFR director plus EIB Global Advisory Council member; inspect current public board/advisory roles for cross-dataset recurrence.

## Assessment

Krastev is a high-value graph connector because the same person is independently present in the governance or senior institutional structure of several policy and research organizations. The evidence supports an institutional-network description; it does not by itself support claims of coordinated action, common funding, or improper influence.

## Source index

| Publisher | Source | URL |
|---|---|---|
| Open Society Foundations | Board of Directors | https://www.opensocietyfoundations.org/who-we-are/leadership?search=1 |
| European Council on Foreign Relations | About / Board of Trustees | https://ecfr.eu/about/ |
| European Council on Foreign Relations | Ivan Krastev profile | https://ecfr.eu/profile/ivan-krastev/ |
| Centre for Liberal Strategies | About / Management Board | https://cls-sofia.org/about |
| Centre for Liberal Strategies | Ivan Krastev | https://cls-sofia.org/ivan-krastev-en |
| Institute for Human Sciences | Ivan Krastev | https://www.iwm.at/fellow/ivan-krastev |
| Institute for Human Sciences | Academic Staff | https://www.iwm.at/about/academic-staff |
| GLOBSEC | Board of Directors | https://www.globsec.org/board-directors |
| GLOBSEC | Ivan Krastev | https://www.globsec.org/who-we-are/our-people/ivan-krastev |
| GLOBSEC Forum | Ivan Krastev 2026 speaker profile | https://events.globsec.org/?action=speakerDetail&ehash=l2KEn3Ozyb2toqqW2w%3D%3D&lang=en&page=eventDetail&speakerId=13320 |
| European Investment Bank | EIB Global Advisory Council | https://www.eib.org/en/projects/topics/global/global-advisory-council.htm |
| European Investment Bank | EIB Group creates advisory council | https://www.eib.org/press/all/2025-476-eib-group-creates-advisory-council-to-strengthen-its-global-impact |
| World Economic Forum | Ivan Krastev | https://www.weforum.org/people/ivan-krastev/ |
| World Economic Forum | Centre for Liberal Strategies | https://www.weforum.org/organizations/centre-for-liberal-strategies/ |

## Validation status

Research staging only. No normalized `db/` record was hand-written. Canonicalization must use the repository-approved writer/import path and pass `python3 scripts/validate-for-merge.py --site` on the exact PR head.
