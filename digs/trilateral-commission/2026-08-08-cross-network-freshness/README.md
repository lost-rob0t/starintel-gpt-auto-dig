# Trilateral Commission cross-network and freshness pass — 2026-08-08

## Scope

This is a depth-2 follow-up to the roster/provenance audit. It checks selected high-signal current Trilateral roster entries against authoritative current employer, governance, and public-office sources. The goal is to separate **current roster status** from **current biography/role freshness**, and to identify cross-network bridges that can be modeled without inferring coordination or wrongdoing.

## Findings

### 1. Roster status and biography freshness are different dimensions

The Commission's current `Leadership, Members & Fellows` page is useful for current inclusion, but role text on that same page can be stale.

Confirmed examples:

- **John B. Hess** is still rendered as `CEO, Hess Corporation` on the current Trilateral page. Chevron completed its acquisition of Hess Corporation on 2025-07-18 and described John Hess as the former Hess Corporation CEO; Chevron then appointed him to its board on 2025-07-29.
- **Marek Belka** is rendered as a `Member of the European Parliament`, while the European Parliament records his ninth-term service ending on 2024-07-15.

Therefore a `current_member=true`-style conclusion must not automatically make copied employer/title text current. The model needs independent timestamps or provenance for membership state and biography fields.

### 2. Laurence D. Fink is a high-confidence Trilateral ↔ WEF bridge

The current Trilateral roster lists Laurence D. Fink as Chairman and CEO of BlackRock. The current World Economic Forum governance page identifies Larry Fink as a Co-Chair of the Forum and a member of its Board of Trustees.

The repository already contains a separate Larry Fink dossier in `digs/larry-fink/2026-07-25-comprehensive/`. This is primarily an **identity-resolution problem**, not a reason to create another person entity.

High-value next action: resolve `starintel:person:trilateral-commission:laurence-d-fink` to the existing canonical Larry Fink identity and emit explicit, source-timestamped affiliation/governance relations.

### 3. Jared Cohen is a high-confidence Trilateral ↔ Goldman Sachs ↔ CFR ↔ CNAS bridge

The current Trilateral roster lists Jared Cohen. Goldman Sachs currently identifies him as President of Global Affairs and Co-Head of the Goldman Sachs Global Institute. Goldman also explicitly states that Cohen is:

- a member of the Trilateral Commission;
- a member and adjunct senior fellow at the Council on Foreign Relations; and
- an adjunct senior fellow at the Center for a New American Security.

This is unusually strong cross-network evidence because one authoritative current bio explicitly enumerates the affiliations rather than requiring inference from name matching alone.

### 4. The rotate-off language cannot be implemented as a naive public-office exclusion rule

The Trilateral page states that members who enter government roles must rotate off. However, current roster entries include people described with public-office titles.

A skeptic check matters here: **Peter Harder's `Senator, Canada` title is not stale**. Senate of Canada records show Harder actively chairing a Senate committee on 2026-05-05.

So the policy language needs interpretation of scope, timing, regional procedure, or exceptions. Do not hard-code `has current public office => cannot be current member` from the existing text alone.

### 5. Ajay Banga demonstrates why archive/current separation matters across networks

Ajay Banga retains a Trilateral people-profile page but was not found on the current Trilateral roster in the first pass. At the same time, the current World Economic Forum governance page lists Ajay S. Banga, President of the World Bank Group, on the WEF Board of Trustees.

That supports keeping his historical/archive Trilateral evidence while independently modeling current WEF governance. Cross-network recurrence must carry per-relation time/status instead of turning every discovered affiliation into one timeless membership blob.

## Data-model implications

1. Track `membership_status_observed_at` separately from role/employer freshness.
2. Do not promote profile-page biography text to a current role without a current authoritative source.
3. Resolve aliases/canonical identities before creating duplicate person nodes across datasets.
4. Use exact governance predicates where supported (`co_chair_of`, `trustee_of`, `executive_director_of`, etc.) rather than flattening everything to `member_of`.
5. Preserve historical/archive affiliations with time/status qualifiers instead of deleting them.
6. Treat cross-network affiliation as an edge, not as evidence of control, coordination, wrongdoing, or shared views.

## Priority targets from this pass

1. `starintel:target:trilateral-commission:laurence-d-fink-cross-ties` — identity-resolve to existing Larry Fink dossier and current WEF governance.
2. `starintel:target:trilateral-commission:jared-cohen-cross-ties` — add Goldman/CFR/CNAS current affiliations from the Goldman bio.
3. `starintel:target:trilateral-commission:john-b-hess-cross-ties` — refresh post-Hess-acquisition role state while preserving current Trilateral roster inclusion.
4. `starintel:target:trilateral-commission:ajay-banga-cross-ties` — preserve archive Trilateral evidence and current WEF trustee role as separately timestamped relations.
5. Full 484-profile reconciliation remains the larger deterministic pass.

## Primary sources

- https://www.trilateral.org/about/members-fellows/
- https://www.weforum.org/about/leadership-and-governance/
- https://www.goldmansachs.com/our-firm/our-people-and-leadership/leadership/management-committee/jared-cohen.html
- https://www.chevron.com/newsroom/2025/q3/chevron-completes-acquisition-of-hess-corporation
- https://www.chevron.com/newsroom/2025/q3/john-b-hess-joins-chevrons-board-of-directors
- https://www.europarl.europa.eu/meps/en/197496/MAREK_BELKA/history/9
- https://sencanada.ca/en/content/sen/committee/451/rprd/16ev-57683-e

## Repository records inspected

- `db/person/starintel:person:trilateral-commission:jared-cohen.ndjson`
- `db/person/starintel:person:trilateral-commission:ajay-banga.ndjson`
- `db/relation/starintel:relation:trilateral-commission:richard-fontaine-member_of-the-trilateral-commission.ndjson`
- `db/target/starintel:target:trilateral-commission:laurence-d-fink-cross-ties.ndjson`
- `digs/larry-fink/2026-07-25-comprehensive/starintel-documents.jsonl`
