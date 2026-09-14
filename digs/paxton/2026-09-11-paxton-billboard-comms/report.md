# Paxton mobile billboard and convention communications

## Scope

Bounded public-source pass for #2577 under the `paxton` dataset.

## Materialized findings

- The packet records the Texas Democratic Party as the sponsoring organization for the public mobile-billboard campaign targeting Ken Paxton around the 2026 Republican midterm convention in Dallas, based on the cited party post and news coverage.
- The packet records Ken Paxton, James Talarico, Texas Democratic Party spokesperson Ryan Martin, the convention, the billboard campaign event, the public Texas Democratic Party X post, and explicit evidence-backed relations among those public entities and events.
- Vendor identity and ad-funding documentation remained unresolved in the public sources searched; this pass does not infer either relationship.

## Canonicalization note

The live v0.9 schema requires `source.data.retrieved_at` and `social-media-post.data.posted_at` to be nullable date-times. Legacy date-only values were corrected conservatively to `null` rather than inventing clock times, with the known calendar dates retained in notes. Normalized `db/` records were regenerated through the repository-required `scripts/starintel.py import ... --replace` path.

## Validation

The exact-head GitHub validation workflows, including the complete canonical merge-gate step in `Validate StarIntel documents`, are the merge gate for this pull request.
