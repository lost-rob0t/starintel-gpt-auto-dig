# Free-Range — SmartStart stale target resolution

**Date:** 2026-08-08  
**Dataset:** `wef`  
**Schema:** StarIntel v0.9.0

## Why this exists

A manual Free-Range run selected `starintel:investigation-target:smartstart-government-records` as ready even though the SmartStart recursive path later reached its configured depth-5 stop condition.

The completed depth-5 pass records a bounded public-source result: SmartStart USA is launching in New York and an August 2026 partner-high-school pilot was planned, but the reviewed sources did not identify the exact school or district, a SmartStart-specific public award or implementation agreement, the portal vendor, or a named credential provider.

This packet emits a newer terminal state for the **same logical `target_id`**. The original target record remains part of provenance; the newer state supersedes it for frontier planning.

## Planner invariant

Free-Range now resolves multiple `target` / `investigation-target` records by logical `data.target_id` before planning. The newest state wins. A later `completed` or `superseded` event therefore closes an older `queued` event, while a still-later `queued` event can intentionally reopen it.

## Reopen condition

Reopen this SmartStart branch only when new primary evidence identifies one of the unresolved implementation surfaces, such as the school or district, implementation agreement, funding award, credential provider, or portal vendor.
