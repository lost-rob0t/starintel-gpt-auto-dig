# Hunter Biden — BHR Partners pre-2021 ownership unwind

**Dataset:** `hunter-biden`  
**Run:** `2026-07-31-bhr-partners-depth-3`  
**Schema:** StarIntel v0.9.0  
**Status:** depth-3 evidence packet; Skaneateles ownership and 2019 unwind substantially resolved

## What this pass resolves

This pass uses Eric Schwerin's official House transcript to reconstruct the BHR ownership segment before Hunter Biden became Skaneateles's sole owner.

It records:

- Hunter Biden and Eric Schwerin's joint creation of Skaneateles;
- the **75 percent / 25 percent** Skaneateles ownership split;
- Skaneateles's joint **10 percent interest in BHR's management company** beginning around 2017;
- the partners' September 2017 business unwind, legally completed in **March 2019**;
- the no-cash asset swap under which Schwerin received the Rosemont Seneca Partners investments business while Hunter received BHR and Rosemont Seneca Advisors;
- Schwerin's recollection that the joint 10 percent BHR management-company interest was worth about **$450,000** based on registered capital;
- Schwerin's BHR board-meeting attendance when Hunter did not attend;
- Schwerin's testimony that Devon Archer controlled Rosemont Seneca Bohai and Rosemont Seneca Thornton accounts.

## Analytic correction

The transcript narrows the ownership object: the 10 percent position was an interest in **BHR's management company**, not automatically a 10 percent interest in every BHR-managed fund or portfolio company.

## Remaining hard gaps

1. The 2017–2019 separation and assignment documents.
2. The precise date Hunter became sole owner of Skaneateles.
3. The accounting difference between the roughly $450,000 and roughly $420,000 valuations.
4. Formal BHR board appointments, alternates, and voting rights.
5. The economic distinction between management-company equity, fund LP interests, fees, carry, and portfolio ownership.

## Counts

- Sources: 1
- People: 1
- Organizations: 1
- Relations: 10
- Investigation targets: 4
- Total: 17

## Import order

1. `sources.jsonl`
2. `entities.jsonl`
3. `relations.jsonl`
4. `investigation-targets.jsonl`

Additional files:

- `sources.md` — evidence ledger and extraction notes
- `manifest.json` — counts, hashes, and validation state
