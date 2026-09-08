# Ohio Food Not Bombs Dayton/Athens expansion state

Last bounded pass: 2026-09-08T20:40:12Z

## Resolved this pass

- Materialized **Food Not Bombs Dayton** from its current first-party site, which explicitly self-identifies as the Dayton, Ohio chapter.
- Materialized **Food Not Bombs Athens, Ohio** from current Ohio University and Athens-area public resource listings.
- Added autonomous `local_chapter_of` relations from both locals to the existing Food Not Bombs movement; these edges do not imply hierarchy.
- Recorded Dayton's public email `foodnotbombs937@gmail.com` as a current communications surface in source provenance.
- Added Instagram `@fnbathens` as a cross-enumeration lead only. Current community evidence points to the handle, but direct first-party account control was not independently verified in this pass.
- Preserved the Columbus/Central Ohio naming conflict instead of collapsing competing identities.

## Do not reprocess without new evidence

- Food Not Bombs Dayton -> Food Not Bombs movement.
- Food Not Bombs Athens, Ohio -> Food Not Bombs movement at current institutional/resource-directory confidence.
- Dayton public website and email.
- `@fnbathens` as an unresolved social lead; only raise confidence when direct first-party evidence appears.

## Next unresolved queue

1. Resolve a current first-party Athens Food Not Bombs site/profile and verify `@fnbathens` directly.
2. Cross-enumerate `fnbathens` on supported public platforms without assuming same-handle identity.
3. Enumerate Dayton public social profiles from a first-party link or exact current public directory; do not guess handles from the chapter email.
4. Test Dayton's stated Yankee Street Market partnership for its exact relationship type before creating any org relation.
5. Continue Ohio Food Not Bombs expansion with current-status checks for other historical directory seeds.
6. Keep Central Ohio Food Not Bombs and Columbus Food Not Bombs distinct until direct current organizational evidence resolves their relationship.

## Pass statistics

- seed orgs processed: 3 (Food Not Bombs movement plus Dayton and Athens leads)
- new locals/chapters: 2
- new parent orgs: 0
- new chapter relations: 2
- new public social endpoints: 1 discovery lead
- new public communications surfaces: 2 (Dayton website + public email)
- source records: 4
- source domains: 4
- current orgs confirmed/materialized: 2
- historical-only orgs promoted: 0
- duplicate/identity collisions preserved: 1 (Central Ohio/Columbus)
- unresolved structural leads: 6
