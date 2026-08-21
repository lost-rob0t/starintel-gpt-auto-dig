# Trilateral Commission policy-attribution methodology pass — 2026-08-08

## Scope

This pass tests a narrow question: **when can a later government action be attributed to a Trilateral Commission recommendation, and when is the evidence only contact, shared personnel, shared vocabulary, or policy similarity?**

It uses one unusually strong 1978–1979 food-policy trace and one explicit counterexample from international financial policy to define evidence tiers for future StarIntel relations.

## Evidence tiers

### Tier A — direct government citation of a named Commission work

Strongest ordinary documentary evidence short of an explicit adoption statement.

Requirements:

- a government or official-policy document cites a named Trilateral report, task force, or recommendation; and
- the cited proposition is identifiable.

This supports `cited`, `relied_on_as_source`, or similarly narrow predicates. It does not by itself prove adoption.

### Tier B — cited recommendation carried forward inside the government policy process

Requirements:

- Tier A is satisfied; and
- a later government planning/recommendation document explicitly says it is following or building on the intermediary official report or recommendation.

This supports a documented policy-process chain, not exclusive causation.

### Tier C — related recommendation appears in final policy or declaration

Requirements:

- Tier A/B chain exists; and
- the final policy contains materially similar recommendations.

Unless the final policy itself identifies the Trilateral source, this should be classified as **downstream overlap / plausible contribution**, not `caused`, `authored`, or exclusive `influenced`.

### Tier D — shared personnel, venue, vocabulary, or policy similarity only

Insufficient for attribution.

Examples:

- an official was a Commission member;
- government documents call countries "Trilateral nations";
- officials continued discussions at a Commission meeting;
- a later policy resembles a Commission paper without a citation chain.

These facts can support membership, event, communication, or similarity relations, but not Commission authorship of policy.

## Strong trace: 1978 Trilateral food study → 1979 U.S. summit policy process

### Step 1 — the underlying Trilateral work is identifiable

FAO AGRIS catalogs the 1978 Trilateral Commission publication `Reducing Malnutrition in Developing Countries: Increasing Rice Production in South and Southeast Asia`, authored by Umberto Colombo, D. Gale Johnson, and Toshio Shishido and produced by the Trilateral North-South Food Task Force.

### Step 2 — a U.S. presidential commission directly cited the Trilateral report

On June 8, 1979, the Presidential Commission on World Hunger prepared `Recommendations Concerning Hunger for the President’s Use at the Tokyo Summit`.

In its water-resources recommendation, the presidential commission said improved water management would require several things, including **extensive long-term capital investments**, and explicitly attributed that point to a recent Trilateral report. The State Department editor identifies the cited source as the 1978 Trilateral malnutrition/rice report.

This is **Tier A** evidence: a specific Commission work is cited for a specific proposition in an official U.S. policy recommendation.

### Step 3 — Carter summit preparations explicitly carried the Hunger Commission report forward

A June 22, 1979 memorandum from Special Representative for Economic Summits Henry Owen to President Carter introduced its food recommendations with `In line with Sol Linowitz' Hunger Commission report to you`.

The memo then recommended, among other things:

- stronger food-storage capacity/reserves;
- national food-production strategies;
- increased bilateral and multilateral agricultural-research aid; and
- doubling resources for the Consultative Group on International Agricultural Research.

This is **Tier B** evidence for the presidential commission report entering the summit policy process.

### Step 4 — the final Tokyo declaration contains several related food/research priorities

The State Department's FRUS annotation reproduces the relevant final Tokyo Summit language: more cooperation against hunger/malnutrition, effective food-sector strategies, stronger national food reserves, increased bilateral/multilateral agricultural-research aid, and technical cooperation.

This is **Tier C** downstream overlap with the Hunger Commission/Carter preparation chain.

### Attribution limit

The exact Trilateral-cited proposition in the Hunger Commission paper was the need for extensive long-term capital investment for water-management improvements. The final Tokyo declaration language reproduced in FRUS does not preserve that specific water-investment point or cite the Trilateral Commission.

Therefore the defensible conclusion is:

> A Trilateral study is directly documented as one source inside the U.S. presidential-commission process that fed Carter's Tokyo Summit preparations; several related food/research recommendations appear in the final declaration. The documents do not establish that the Trilateral Commission authored, uniquely caused, or controlled the final G7 policy.

## Counterexample: OECD Financial Support Fund

A February 24, 1977 National Security Council memorandum describes U.S. participation in the OECD Financial Support Fund as a major manifestation of financial cooperation among the `Trilateral nations`.

But the same official record explicitly says the FSF was **originally proposed by Henry Kissinger** and identifies his November 14, 1974 University of Chicago speech as the proposal's origin.

This is a critical skeptic example:

- `Trilateral nations` vocabulary: yes;
- Commission-linked officials/personnel: yes;
- international economic cooperation among Commission-region countries: yes;
- evidence the Trilateral Commission originated the FSF policy: **no**.

Shared vocabulary and network overlap would have produced a false attribution here.

## Data-model implications

1. Do not use generic `influenced` for policy attribution without a defined evidence tier.
2. Prefer exact predicates such as `cited`, `recommended`, `carried_forward_by`, `included_in_final_policy`, `attended`, and `discussed_at`.
3. Store the exact proposition that was cited, not merely the document title.
4. Separate source citation from recommendation adoption.
5. Require a policy chronology: Commission publication must predate the official document that cites or adopts it.
6. Preserve counterexamples where shared personnel/vocabulary do **not** establish Commission authorship.
7. For final-policy attribution, record competing/independent policy inputs where known rather than assigning exclusive causation.

## Next frontier

- apply the tier system to early Commission energy reports and compare them with later DOE/IEA policy documents;
- search government archives for explicit citations of Commission reports on monetary reform, North-South relations, trade, and East-West economic relations;
- create exact event/citation relations only after canonical identities are resolved;
- retain failed attribution tests as negative evidence so future graph traversal does not recreate them.

## Primary sources

- https://history.state.gov/historicaldocuments/frus1977-80v02/d257
- https://history.state.gov/historicaldocuments/frus1977-80v03/d221
- https://history.state.gov/historicaldocuments/frus1977-80v03/d6fn3
- https://agris.fao.org/search/en/providers/122535/records/65de086f7c7033e84be95b47
