# Auto-Dig request #1907 — Onondaga incoming-sharing portal history, batch 2

Worker 3/8 bounded additive continuation for issue #1907.

## Scope

This pass extends the already-merged public-portal history without changing the evidence level. It records three additional donor-agency Flock Transparency Portal snapshots that were not found in the current canonical corpus and that list `Onondaga County NY SO` under the donor agency's `Sharing Network Data With` surface.

## Additive evidence

- **Saratoga Springs NY PD** — vendor portal displays `Last updated: Wed Jul 22 2026` and lists `Onondaga County NY SO` among organizations granted access to Saratoga Springs network data.
- **Newport RI PD** — vendor portal displays `Last updated: Sat Jul 25 2026` and lists `Onondaga County NY SO` among organizations granted access to Newport network data.
- **Mint Hill NC PD** — vendor portal displays `Last updated: Sat Jul 25 2026` and lists `Onondaga County NY SO` among organizations granted access to Mint Hill network data.

Primary/vendor-public sources:

- https://transparency.flocksafety.com/saratoga-springs-ny-pd
- https://transparency.flocksafety.com/newport-ri-pd
- https://transparency.flocksafety.com/Mint-Hill-nc-pd

## Evidence boundary

These are historical vendor-published portal observations keyed to each page's own displayed July 2026 update date. They establish only a directed donor-agency portal listing naming Onondaga County NY SO as a recipient. They do **not** prove:

- unchanged September 2026 native `SharedNetworks` state;
- reciprocity;
- exact approval/effective/end dates;
- Onondaga user/admin account identity;
- actual Onondaga searches or query/event activity;
- the vendor, ownership, serial inventory, or configuration of Onondaga County SO's own readers.

Syracuse, the Sheriff, OCC, East Syracuse, DeWitt, Camillus, and other county operators remain separate network/control surfaces unless native evidence joins them.

## Canonical records

- `starintel:analysis:onondaga-county-incoming-sharing-public-portal-history-batch2-2026-09-15`
- `starintel:research-pass:request-1907-onondaga-incoming-sharing-history-batch2-2026-09-15`

The packet in `starintel-documents.jsonl` must be materialized with the repository's canonical `python3 scripts/starintel.py import ...` path. Issue #1907 remains open after this bounded pass because native sharing/audit evidence and the county-wide operator/reader inventory are still incomplete.
