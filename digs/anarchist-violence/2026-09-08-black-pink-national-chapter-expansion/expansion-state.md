# Black & Pink chapter/affiliate expansion state

Last pass: 2026-09-08T18:36:49Z
Dataset: `anarchist-violence`
Worker: chapter/affiliate expansion

## Resolved this pass

- Black & Pink National: current first-party site verified; current homepage reports 11 volunteer-led chapters.
- Southern Colorado Black & Pink: current live National chapter entry plus current chapter-owned site; relation `local_chapter_of` Black & Pink National.
- Black & Pink Missoula: current live National chapter entry; relation `local_chapter_of` Black & Pink National.
- Black & Pink Providence: current live National chapter entry with recurring meeting schedule; relation `local_chapter_of` Black & Pink National.
- Black and Pink Massachusetts: existing org reused; Black & Pink National's 2020 first-party release records it as a former chapter that became independent. No current National affiliation inferred.
- Black and Pink Massachusetts Coalition (BPMC): current first-party site resolves a separate Massachusetts 501(c)(3) advocacy organization. Kept distinct from Black and Pink Massachusetts.
- Public account endpoints queued for cross-enumeration: Instagram `@blackandpinkorg`, Facebook `blackandpinknational`, Facebook `blackandpinkmassachusettscoalitioninc`.

## Stats

- seed/dependency-ready org leads processed: 6
- new org records: 5
- reused existing org records: 1
- new investigation targets: 5
- new current chapter relations: 3
- new historical structural relations: 1
- new public social endpoints: 3
- new public communications surfaces preserved in sources: 9 (3 social endpoints + 6 published email/contact surfaces)
- source records: 9
- source domains: 4 (`blackandpink.org`, `coblackandpink.org`, `bpmcoalition.com`, `prisonactivist.org`)
- current-active orgs newly verified/materialized: 5
- historical-only orgs promoted to active: 0
- duplicate/name collisions intentionally kept separate: 1 Massachusetts naming cluster
- unresolved structural leads: 8 unnamed/unexposed chapters plus chapter-local social/coalition follow-ups

## Unresolved structural leads

1. Black & Pink National says it has 11 volunteer-led chapters, but current first-party navigation exposes only Southern Colorado, Missoula, and Providence. Resolve the remaining eight from current first-party or chapter-owned sources before materializing them as active.
2. Resolve exact current social accounts for Southern Colorado, Missoula, and Providence from first-party/public chapter links; do not reuse stale historical handles without current verification.
3. Expand current Providence coalition relationships from organization-level supporter/member evidence; never infer individual membership from meeting attendance.
4. Expand Southern Colorado public partner organizations from current chapter-owned or co-sponsor evidence.
5. Resolve BPMC's explicit current coalition/member relationships and newsletter surface. Do not merge it with `starintel:org:black-and-pink-massachusetts` based on branding similarity.

## Reprocessing rule

Do not reprocess the three live chapter identities at this same shallow depth unless Black & Pink National changes its current directory, a chapter's first-party status/contact changes, or a deeper affiliate/social pass is selected.
