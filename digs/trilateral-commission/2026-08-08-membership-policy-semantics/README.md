# Trilateral Commission membership-policy semantics pass — 2026-08-08

## Scope

This same-depth pass resolves a classification problem found during the freshness audit: the global membership page uses broad government-role rotation language, while regional rules and the current roster show that eligibility is more specific. It also separates David Rockefeller Fellows from ordinary membership.

## Findings

### 1. Do not implement a universal `public_office => former_member` rule

The current global `Leadership, Members & Fellows` page says that members who enter a government role must rotate off, and immediately notes that rotation and recruitment procedures vary by national group.

The North America regional page gives a materially narrower rule for the U.S. group: if a U.S. member is elected or appointed to a position in the **Executive Branch of the U.S. government**, that member steps down because of the Commission's unofficial character.

That distinction matters. The current roster also includes serving legislators, including Canadian Senator Yuen Pau Woo and Japanese House of Representatives member Taro Kono. A classifier that treats any current public office as incompatible with membership would therefore generate false negatives.

### 2. Rotation rules should be national-group and office-type aware

The safe implementation is:

- apply an explicit national-group rule only when the Commission publishes one;
- distinguish executive-branch, legislative, judicial, diplomatic, central-bank, and other public roles;
- retain observed current-roster membership when an individual appears on the current roster even if a broad policy sentence seems inconsistent;
- create a policy-conflict/unresolved marker when the specific national rule is unknown.

No equally explicit government-role rule was found on the Europe or Asia Pacific regional pages reviewed in this pass.

### 3. David Rockefeller Fellow is a distinct time-bounded affiliation

The North American David Rockefeller Fellows page says:

- the program was created by Executive Committee vote in March 2013;
- fellows serve **three-year terms**;
- applicants must be **35 or younger** at the application deadline;
- a current Commission member must nominate the applicant;
- selection involves conditional approval by a selection committee and final approval by the **Trustees and Executive Committee**;
- fellows attend annual meetings and are invited to participate as full members do.

That last phrase describes meeting participation. It does not erase the site's separate `Fellows` category. In StarIntel, `David Rockefeller Fellow` should therefore remain a separate, time-bounded status/relation rather than being flattened to ordinary `member_of`.

## Data-model implications

1. Current status classification must carry `national_group` and, where relevant, `office_type`.
2. Store the source/observation date for eligibility rules; do not encode website prose as timeless law.
3. Use a dedicated fellow relation/status with start/end or observed term information.
4. Keep `member`, `fellow`, `leadership`, and `executive committee` semantically separate even when one person occupies more than one category.
5. Prefer the current roster as an observed-status fact; surface policy contradictions as research issues instead of silently overriding the roster.

## Next frontier

- enumerate national-group-specific rotation rules for Canada, Mexico, Europe, and Asia Pacific where available;
- reconcile all 484 archive profiles into current member / leadership / DRF / global member / archive-only / unresolved;
- extract current fellows from the dedicated DRF surfaces rather than the generic profile archive;
- time-bound former fellows and leadership roles from historical rosters.

## Sources

- https://www.trilateral.org/about/members-fellows/
- https://www.trilateral.org/regions/north-american-group/
- https://www.trilateral.org/about/david-rockefeller-fellows-north-america/
- https://www.trilateral.org/regions/asia-pacific-group/
