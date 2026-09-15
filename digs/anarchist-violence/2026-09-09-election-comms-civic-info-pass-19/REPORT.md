# Election communications / civic-information infrastructure — bounded pass 19

## Current-main reconciliation

This PR was reconciled against current `main` after a real canonical-ID collision with the later merged `2026-09-10-election-comms-info-distribution-pass-21` packet.

The later packet already owns the canonical Democracy Works / Google / OpenAI / Civic Alliance / CAA Foundation graph and Luis Lozada leadership surface. Those superseded records and their redundant source records are removed here rather than replayed.

## Additive payload

`starintel-documents.jsonl` now contains 16 typed StarIntel v0.9 records:

- 7 `source`
- 4 `org`: Vote.org; Rock the Vote; Center for Tech and Civic Life (CTCL); Cox / Cox Communications
- 2 public professional `person`: Andrea Hailey; Tiana Epps-Johnson
- 3 explicit evidence-backed `relation`
- 0 inferred relations promoted as direct observations
- 0 normalized `db/` hand edits

The retained explicit relations are:

- Andrea Hailey `executive_of` Vote.org.
- Tiana Epps-Johnson `executive_of` CTCL.
- Cox `partnered_with` Rock the Vote for the public 2026 voter-tool surface.

## Evidence boundary

Current-status claims use first-party public pages. Employment and leadership evidence is limited to public professional roles. No political belief, partisan affiliation, private membership, private contact information, or unrelated personal-life data is inferred or collected.

## Write / validation path

This repair exists only because current `main` contains canonical IDs that collide with the original packet. The existing PR is preserved instead of opening a competitor. The repaired packet remains draft until fresh exact-head `Validate StarIntel documents` succeeds with `Run complete canonical merge gate`, the required site/ADAR workflow succeeds, and GitHub reports the exact head mergeable.
